/**
 * VoicePlayer - 企業級語音播放器組件
 * 支援TTS語音播放、控制和狀態管理
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { TTSApiService } from '../../services/TTSApiService';
import { useVoiceStore } from '../../store/voiceStore';
import './VoicePlayer.css';

export interface VoicePlayerProps {
  text: string;
  voiceId?: string;
  autoPlay?: boolean;
  showControls?: boolean;
  className?: string;
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
  onError?: (error: Error) => void;
  onProgressUpdate?: (progress: number) => void;
}

export interface PlaybackState {
  isPlaying: boolean;
  isLoading: boolean;
  isPaused: boolean;
  progress: number;
  duration: number;
  currentTime: number;
  volume: number;
  error: string | null;
}

export const VoicePlayer: React.FC<VoicePlayerProps> = ({
  text,
  voiceId,
  autoPlay = false,
  showControls = true,
  className = '',
  onPlayStart,
  onPlayEnd,
  onError,
  onProgressUpdate
}) => {
  // 音頻引用和狀態
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playbackState, setPlaybackState] = useState<PlaybackState>({
    isPlaying: false,
    isLoading: false,
    isPaused: false,
    progress: 0,
    duration: 0,
    currentTime: 0,
    volume: 1,
    error: null
  });

  // 全域語音狀態管理
  const { 
    currentVoice, 
    userPreferences, 
    addToHistory,
    setCurrentPlaying 
  } = useVoiceStore();

  // TTS API 服務
  const ttsService = TTSApiService.getInstance();

  // 獲取語音ID（使用傳入的或用戶偏好的）
  const getVoiceId = useCallback(() => {
    return voiceId || currentVoice?.model_id || userPreferences.defaultVoiceId || 'default-voice';
  }, [voiceId, currentVoice, userPreferences.defaultVoiceId]);

  // 語音合成和播放
  const playVoice = useCallback(async () => {
    try {
      setPlaybackState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const selectedVoiceId = getVoiceId();
      
      // 調用TTS API生成語音
      const audioBlob = await ttsService.synthesizeSpeech(text, selectedVoiceId);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.volume = userPreferences.volume;
        
        // 播放音頻
        await audioRef.current.play();
        
        setPlaybackState(prev => ({ 
          ...prev, 
          isPlaying: true, 
          isLoading: false 
        }));
        
        // 設置全域播放狀態
        setCurrentPlaying({
          text,
          voiceId: selectedVoiceId,
          startTime: new Date()
        });
        
        // 添加到播放歷史
        addToHistory({
          id: Date.now().toString(),
          text,
          voiceId: selectedVoiceId,
          playedAt: new Date(),
          duration: 0 // 將在播放結束時更新
        });
        
        onPlayStart?.();
      }
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error('語音播放失敗');
      setPlaybackState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorObj.message 
      }));
      onError?.(errorObj);
    }
  }, [text, getVoiceId, userPreferences.volume, ttsService, setCurrentPlaying, addToHistory, onPlayStart, onError]);

  // 暫停播放
  const pauseVoice = useCallback(() => {
    if (audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      setPlaybackState(prev => ({ 
        ...prev, 
        isPlaying: false, 
        isPaused: true 
      }));
    }
  }, []);

  // 繼續播放
  const resumeVoice = useCallback(() => {
    if (audioRef.current && audioRef.current.paused) {
      audioRef.current.play();
      setPlaybackState(prev => ({ 
        ...prev, 
        isPlaying: true, 
        isPaused: false 
      }));
    }
  }, []);

  // 停止播放
  const stopVoice = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setPlaybackState(prev => ({ 
        ...prev, 
        isPlaying: false, 
        isPaused: false,
        progress: 0,
        currentTime: 0
      }));
      setCurrentPlaying(null);
    }
  }, [setCurrentPlaying]);

  // 設置音量
  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume;
    }
    setPlaybackState(prev => ({ ...prev, volume: clampedVolume }));
  }, []);

  // 設置播放位置
  const seekTo = useCallback((time: number) => {
    if (audioRef.current && playbackState.duration > 0) {
      const seekTime = Math.max(0, Math.min(playbackState.duration, time));
      audioRef.current.currentTime = seekTime;
      setPlaybackState(prev => ({ 
        ...prev, 
        currentTime: seekTime,
        progress: (seekTime / prev.duration) * 100
      }));
    }
  }, [playbackState.duration]);

  // 音頻事件處理
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setPlaybackState(prev => ({ 
        ...prev, 
        duration: audio.duration || 0 
      }));
    };

    const handleTimeUpdate = () => {
      const currentTime = audio.currentTime || 0;
      const duration = audio.duration || 0;
      const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
      
      setPlaybackState(prev => ({ 
        ...prev, 
        currentTime, 
        progress 
      }));
      
      onProgressUpdate?.(progress);
    };

    const handleEnded = () => {
      setPlaybackState(prev => ({ 
        ...prev, 
        isPlaying: false, 
        isPaused: false,
        progress: 100
      }));
      setCurrentPlaying(null);
      onPlayEnd?.();
    };

    const handleError = () => {
      const error = new Error('音頻播放錯誤');
      setPlaybackState(prev => ({ 
        ...prev, 
        isPlaying: false, 
        isLoading: false,
        error: error.message 
      }));
      onError?.(error);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, [onProgressUpdate, onPlayEnd, onError, setCurrentPlaying]);

  // 自動播放
  useEffect(() => {
    if (autoPlay && text && !playbackState.isPlaying) {
      playVoice();
    }
  }, [autoPlay, text, playVoice, playbackState.isPlaying]);

  // 格式化時間顯示
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`voice-player ${className}`}>
      {/* 隱藏的音頻元素 */}
      <audio ref={audioRef} preload="metadata" />
      
      {/* 錯誤提示 */}
      {playbackState.error && (
        <div className="voice-player-error">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{playbackState.error}</span>
        </div>
      )}

      {/* 播放控制界面 */}
      {showControls && (
        <div className="voice-player-controls">
          {/* 主要控制按鈕 */}
          <div className="main-controls">
            {playbackState.isLoading ? (
              <button className="control-btn loading" disabled>
                <div className="spinner"></div>
              </button>
            ) : playbackState.isPlaying ? (
              <button 
                className="control-btn pause"
                onClick={pauseVoice}
                aria-label="暫停播放"
              >
                ⏸️
              </button>
            ) : playbackState.isPaused ? (
              <button 
                className="control-btn resume"
                onClick={resumeVoice}
                aria-label="繼續播放"
              >
                ▶️
              </button>
            ) : (
              <button 
                className="control-btn play"
                onClick={playVoice}
                aria-label="開始播放"
                disabled={!text}
              >
                ▶️
              </button>
            )}

            <button 
              className="control-btn stop"
              onClick={stopVoice}
              aria-label="停止播放"
              disabled={!playbackState.isPlaying && !playbackState.isPaused}
            >
              ⏹️
            </button>
          </div>

          {/* 進度條 */}
          <div className="progress-section">
            <span className="time-display current">
              {formatTime(playbackState.currentTime)}
            </span>
            
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const clickX = e.clientX - rect.left;
                  const percentage = (clickX / rect.width) * 100;
                  const seekTime = (percentage / 100) * playbackState.duration;
                  seekTo(seekTime);
                }}
              >
                <div 
                  className="progress-fill"
                  style={{ width: `${playbackState.progress}%` }}
                />
                <div 
                  className="progress-thumb"
                  style={{ left: `${playbackState.progress}%` }}
                />
              </div>
            </div>
            
            <span className="time-display total">
              {formatTime(playbackState.duration)}
            </span>
          </div>

          {/* 音量控制 */}
          <div className="volume-section">
            <span className="volume-icon">🔊</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={playbackState.volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="volume-slider"
              aria-label="音量控制"
            />
          </div>
        </div>
      )}

      {/* 語音資訊顯示 */}
      <div className="voice-player-info">
        <div className="text-preview">
          {text.substring(0, 100)}{text.length > 100 ? '...' : ''}
        </div>
        <div className="voice-info">
          <span className="voice-name">
            語音: {currentVoice?.name || '預設語音'}
          </span>
          {playbackState.isPlaying && (
            <span className="playing-indicator">🎵 播放中</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoicePlayer;