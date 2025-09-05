/**
 * 企業級語音播放器組件
 * 提供高品質的 TTS 語音播放功能，支援商業化需求
 */

import React, { 
  useState, 
  useRef, 
  useEffect, 
  useCallback, 
  memo,
  forwardRef,
  useImperativeHandle
} from 'react';
import { createApiUrl } from '../../config/apiConfig';

// TypeScript 接口定義
export interface VoicePlayerProps {
  /** 要播放的文字內容 */
  text: string;
  /** 語音ID */
  voiceId: string;
  /** 是否自動播放 */
  autoPlay?: boolean;
  /** 是否顯示控制項 */
  showControls?: boolean;
  /** 自定義樣式類名 */
  className?: string;
  /** 播放開始回調 */
  onPlayStart?: () => void;
  /** 播放結束回調 */
  onPlayEnd?: () => void;
  /** 播放進度回調 */
  onProgress?: (progress: number, currentTime: number, duration: number) => void;
  /** 錯誤回調 */
  onError?: (error: Error) => void;
  /** 載入完成回調 */
  onLoaded?: (duration: number) => void;
  /** 音量控制 (0-1) */
  volume?: number;
  /** 播放速率 (0.25-4.0) */
  playbackRate?: number;
  /** 是否顯示進度條 */
  showProgress?: boolean;
  /** 是否顯示時間 */
  showTime?: boolean;
  /** 是否啟用快捷鍵 */
  enableKeyboard?: boolean;
  /** 自定義主題 */
  theme?: 'light' | 'dark' | 'auto';
}

export interface VoicePlayerRef {
  play: () => Promise<void>;
  pause: () => void;
  stop: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  setPlaybackRate: (rate: number) => void;
  getCurrentTime: () => number;
  getDuration: () => number;
  isPlaying: () => boolean;
  isLoading: () => boolean;
}

interface PlaybackState {
  isPlaying: boolean;
  isLoading: boolean;
  currentTime: number;
  duration: number;
  progress: number;
  volume: number;
  playbackRate: number;
  error: string | null;
  isBuffering: boolean;
}

// 音頻緩存管理
class AudioCache {
  private static instance: AudioCache;
  private cache = new Map<string, string>();
  private readonly maxCacheSize = 50; // 最多緩存50個音頻文件

  static getInstance(): AudioCache {
    if (!AudioCache.instance) {
      AudioCache.instance = new AudioCache();
    }
    return AudioCache.instance;
  }

  getCacheKey(text: string, voiceId: string): string {
    return `${voiceId}-${btoa(encodeURIComponent(text)).substring(0, 32)}`;
  }

  get(key: string): string | undefined {
    return this.cache.get(key);
  }

  set(key: string, audioUrl: string): void {
    if (this.cache.size >= this.maxCacheSize) {
      // 移除最舊的條目
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, audioUrl);
  }

  clear(): void {
    this.cache.clear();
  }
}

/**
 * 企業級語音播放器組件
 */
export const VoicePlayer = memo(forwardRef<VoicePlayerRef, VoicePlayerProps>(({
  text,
  voiceId,
  autoPlay = false,
  showControls = true,
  className = '',
  onPlayStart,
  onPlayEnd,
  onProgress,
  onError,
  onLoaded,
  volume: initialVolume = 1.0,
  playbackRate: initialPlaybackRate = 1.0,
  showProgress = true,
  showTime = true,
  enableKeyboard = true,
  theme = 'auto'
}, ref) => {
  // 狀態管理
  const [state, setState] = useState<PlaybackState>({
    isPlaying: false,
    isLoading: false,
    currentTime: 0,
    duration: 0,
    progress: 0,
    volume: initialVolume,
    playbackRate: initialPlaybackRate,
    error: null,
    isBuffering: false
  });

  // Refs
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const audioCache = AudioCache.getInstance();

  // 錯誤處理
  const handleError = useCallback((error: Error) => {
    console.error('VoicePlayer Error:', error);
    setState(prev => ({ 
      ...prev, 
      error: error.message, 
      isPlaying: false, 
      isLoading: false 
    }));
    onError?.(error);
  }, [onError]);

  // 合成語音
  const synthesizeAudio = useCallback(async (text: string, voiceId: string): Promise<string> => {
    if (!text.trim()) {
      throw new Error('文字內容不能為空');
    }

    const cacheKey = audioCache.getCacheKey(text, voiceId);
    const cachedUrl = audioCache.get(cacheKey);
    
    if (cachedUrl) {
      return cachedUrl;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(createApiUrl('/admin/tts/test-synthesis'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        body: JSON.stringify({
          text: text.substring(0, 5000), // 限制文字長度
          voice_id: voiceId
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '語音合成失敗' }));
        throw new Error(errorData.detail || '語音合成失敗');
      }

      const result = await response.json();
      
      if (!result.success || !result.data?.audio_url) {
        throw new Error('語音合成響應格式無效');
      }

      const audioUrl = result.data.audio_url;
      audioCache.set(cacheKey, audioUrl);
      
      return audioUrl;
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [audioCache]);

  // 播放控制
  const play = useCallback(async (): Promise<void> => {
    if (!audioRef.current) return;

    try {
      if (audioRef.current.src) {
        await audioRef.current.play();
        return;
      }

      // 合成新的音頻
      const audioUrl = await synthesizeAudio(text, voiceId);
      audioRef.current.src = audioUrl;
      await audioRef.current.play();
    } catch (error) {
      handleError(error instanceof Error ? error : new Error('播放失敗'));
    }
  }, [text, voiceId, synthesizeAudio, handleError]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, []);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(time, state.duration));
    }
  }, [state.duration]);

  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume;
    }
    setState(prev => ({ ...prev, volume: clampedVolume }));
  }, []);

  const setPlaybackRate = useCallback((rate: number) => {
    const clampedRate = Math.max(0.25, Math.min(4, rate));
    if (audioRef.current) {
      audioRef.current.playbackRate = clampedRate;
    }
    setState(prev => ({ ...prev, playbackRate: clampedRate }));
  }, []);

  // 公開 API
  useImperativeHandle(ref, () => ({
    play,
    pause,
    stop,
    seek,
    setVolume,
    setPlaybackRate,
    getCurrentTime: () => audioRef.current?.currentTime || 0,
    getDuration: () => audioRef.current?.duration || 0,
    isPlaying: () => state.isPlaying,
    isLoading: () => state.isLoading
  }), [play, pause, stop, seek, setVolume, setPlaybackRate, state.isPlaying, state.isLoading]);

  // 音頻事件處理
  const setupAudioEvents = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      const duration = audio.duration || 0;
      setState(prev => ({ 
        ...prev, 
        duration,
        error: null 
      }));
      onLoaded?.(duration);
    };

    const handlePlay = () => {
      setState(prev => ({ 
        ...prev, 
        isPlaying: true, 
        error: null 
      }));
      onPlayStart?.();
    };

    const handlePause = () => {
      setState(prev => ({ ...prev, isPlaying: false }));
    };

    const handleEnded = () => {
      setState(prev => ({ 
        ...prev, 
        isPlaying: false, 
        currentTime: 0, 
        progress: 0 
      }));
      onPlayEnd?.();
    };

    const handleTimeUpdate = () => {
      const currentTime = audio.currentTime || 0;
      const duration = audio.duration || 0;
      const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
      
      setState(prev => ({ 
        ...prev, 
        currentTime, 
        progress 
      }));
      
      onProgress?.(progress, currentTime, duration);
    };

    const handleError = () => {
      const error = new Error('音頻載入或播放失敗');
      handleError(error);
    };

    const handleWaiting = () => {
      setState(prev => ({ ...prev, isBuffering: true }));
    };

    const handleCanPlay = () => {
      setState(prev => ({ ...prev, isBuffering: false }));
    };

    // 綁定事件
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('error', handleError);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('canplay', handleCanPlay);

    // 清理函數
    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [onLoaded, onPlayStart, onPlayEnd, onProgress, handleError]);

  // 鍵盤快捷鍵
  useEffect(() => {
    if (!enableKeyboard) return;

    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.target !== document.body) return;

      switch (event.key) {
        case ' ':
          event.preventDefault();
          state.isPlaying ? pause() : play();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          seek(Math.max(0, state.currentTime - 10));
          break;
        case 'ArrowRight':
          event.preventDefault();
          seek(Math.min(state.duration, state.currentTime + 10));
          break;
        case 'ArrowUp':
          event.preventDefault();
          setVolume(Math.min(1, state.volume + 0.1));
          break;
        case 'ArrowDown':
          event.preventDefault();
          setVolume(Math.max(0, state.volume - 0.1));
          break;
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [enableKeyboard, state.isPlaying, state.currentTime, state.duration, state.volume, play, pause, seek, setVolume]);

  // 初始化音頻和自動播放
  useEffect(() => {
    const cleanup = setupAudioEvents();

    if (autoPlay && text && voiceId) {
      play().catch(console.error);
    }

    // 設置初始音量和播放速率
    if (audioRef.current) {
      audioRef.current.volume = initialVolume;
      audioRef.current.playbackRate = initialPlaybackRate;
    }

    return cleanup;
  }, [setupAudioEvents, autoPlay, text, voiceId, play, initialVolume, initialPlaybackRate]);

  // 進度條點擊處理
  const handleProgressClick = useCallback((event: React.MouseEvent) => {
    if (!progressBarRef.current || state.duration === 0) return;

    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * state.duration;
    
    seek(newTime);
  }, [state.duration, seek]);

  // 格式化時間
  const formatTime = useCallback((seconds: number): string => {
    if (!isFinite(seconds)) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // 主題樣式
  const getThemeClass = useCallback(() => {
    if (theme === 'dark') return 'voice-player--dark';
    if (theme === 'light') return 'voice-player--light';
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches 
      ? 'voice-player--dark' 
      : 'voice-player--light';
  }, [theme]);

  if (state.error) {
    return (
      <div className={`voice-player voice-player--error ${className}`}>
        <div className="voice-player__error">
          <span className="voice-player__error-icon">⚠️</span>
          <span className="voice-player__error-text">播放失敗: {state.error}</span>
          <button 
            className="voice-player__retry-btn"
            onClick={() => {
              setState(prev => ({ ...prev, error: null }));
              play();
            }}
            title="重試"
          >
            🔄
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`voice-player ${getThemeClass()} ${className}`}>
      <audio
        ref={audioRef}
        preload="none"
        style={{ display: 'none' }}
        crossOrigin="anonymous"
      />
      
      {showControls && (
        <div className="voice-player__controls">
          {/* 主要播放控制 */}
          <div className="voice-player__main-controls">
            <button
              className={`voice-player__play-btn ${state.isPlaying ? 'voice-player__play-btn--playing' : ''}`}
              onClick={() => state.isPlaying ? pause() : play()}
              disabled={state.isLoading || state.isBuffering}
              title={state.isPlaying ? '暫停' : '播放'}
              aria-label={state.isPlaying ? '暫停播放' : '開始播放'}
            >
              {state.isLoading || state.isBuffering ? (
                <span className="voice-player__loading-spinner">⏳</span>
              ) : state.isPlaying ? (
                <span>⏸️</span>
              ) : (
                <span>▶️</span>
              )}
            </button>

            <button
              className="voice-player__stop-btn"
              onClick={stop}
              disabled={state.isLoading || (!state.isPlaying && state.currentTime === 0)}
              title="停止"
              aria-label="停止播放"
            >
              ⏹️
            </button>
          </div>

          {/* 進度條 */}
          {showProgress && (
            <div className="voice-player__progress-container">
              <div 
                ref={progressBarRef}
                className="voice-player__progress-bar"
                onClick={handleProgressClick}
                role="slider"
                aria-valuemin={0}
                aria-valuemax={state.duration}
                aria-valuenow={state.currentTime}
                aria-label="播放進度"
              >
                <div 
                  className="voice-player__progress-fill"
                  style={{ width: `${state.progress}%` }}
                />
                <div 
                  className="voice-player__progress-handle"
                  style={{ left: `${state.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* 時間顯示 */}
          {showTime && (
            <div className="voice-player__time">
              <span className="voice-player__current-time">
                {formatTime(state.currentTime)}
              </span>
              <span className="voice-player__time-separator">/</span>
              <span className="voice-player__duration">
                {formatTime(state.duration)}
              </span>
            </div>
          )}

          {/* 音量控制 */}
          <div className="voice-player__volume-container">
            <span className="voice-player__volume-icon">🔊</span>
            <input
              type="range"
              className="voice-player__volume-slider"
              min="0"
              max="1"
              step="0.05"
              value={state.volume}
              onChange={(e) => setVolume(Number(e.target.value))}
              title={`音量: ${Math.round(state.volume * 100)}%`}
              aria-label="音量控制"
            />
          </div>

          {/* 速度控制 */}
          <div className="voice-player__speed-container">
            <span className="voice-player__speed-label">速度</span>
            <select
              className="voice-player__speed-select"
              value={state.playbackRate}
              onChange={(e) => setPlaybackRate(Number(e.target.value))}
              title="播放速度"
              aria-label="播放速度"
            >
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1">1x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2">2x</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}));

VoicePlayer.displayName = 'VoicePlayer';

export default VoicePlayer;