/**
 * TTS 組件使用示例和測試
 * 展示如何正確使用 TTS 前台組件
 * 
 * @author 魯班 (Code Artisan)
 * @version 1.0.0
 */

import React, { useState, useRef, useCallback } from 'react';
import { VoiceProvider, useVoice, useVoices, useCurrentPlayback } from '../../contexts/VoiceContext';
import VoicePlayer, { VoicePlayerRef } from './VoicePlayer';
import ttsApiService from '../../services/TTSApiService';
import './VoicePlayer.css';

/**
 * 基本使用示例
 * 展示最簡單的語音播放器使用方式
 */
export const BasicVoicePlayerExample: React.FC = () => {
  const [text, setText] = useState('歡迎使用 TradingAgents 語音合成系統！');
  const [voiceId, setVoiceId] = useState('voice-zh-tw-female-1');

  return (
    <div className="example-container">
      <h3>基本語音播放器示例</h3>
      
      <div className="example-controls">
        <div>
          <label>文字內容:</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            style={{ width: '100%', marginTop: '8px' }}
          />
        </div>
        
        <div style={{ marginTop: '16px' }}>
          <label>語音ID:</label>
          <input
            type="text"
            value={voiceId}
            onChange={(e) => setVoiceId(e.target.value)}
            style={{ width: '100%', marginTop: '8px' }}
          />
        </div>
      </div>
      
      <div className="example-player" style={{ marginTop: '24px' }}>
        <VoicePlayer
          text={text}
          voiceId={voiceId}
          showControls={true}
          showProgress={true}
          showTime={true}
          enableKeyboard={true}
          volume={0.8}
          playbackRate={1.0}
          onPlayStart={() => console.log('播放開始')}
          onPlayEnd={() => console.log('播放結束')}
          onError={(error) => console.error('播放錯誤:', error)}
        />
      </div>
    </div>
  );
};

/**
 * 進階使用示例
 * 展示使用 ref 控制播放器和處理事件
 */
export const AdvancedVoicePlayerExample: React.FC = () => {
  const [text, setText] = useState('這是一個進階的語音播放器控制示例。');
  const [voiceId, setVoiceId] = useState('voice-zh-tw-male-1');
  const [status, setStatus] = useState<string>('');
  
  const playerRef = useRef<VoicePlayerRef>(null);

  const handlePlay = useCallback(async () => {
    if (playerRef.current) {
      try {
        await playerRef.current.play();
        setStatus('播放中...');
      } catch (error) {
        setStatus(`播放失敗: ${error}`);
      }
    }
  }, []);

  const handlePause = useCallback(() => {
    if (playerRef.current) {
      playerRef.current.pause();
      setStatus('已暫停');
    }
  }, []);

  const handleStop = useCallback(() => {
    if (playerRef.current) {
      playerRef.current.stop();
      setStatus('已停止');
    }
  }, []);

  const handleSeek = useCallback((seconds: number) => {
    if (playerRef.current) {
      playerRef.current.seek(seconds);
      setStatus(`跳轉到 ${seconds} 秒`);
    }
  }, []);

  const handleVolumeChange = useCallback((volume: number) => {
    if (playerRef.current) {
      playerRef.current.setVolume(volume);
      setStatus(`音量設為 ${Math.round(volume * 100)}%`);
    }
  }, []);

  return (
    <div className="example-container">
      <h3>進階語音播放器示例</h3>
      
      <div className="example-controls">
        <div>
          <label>文字內容:</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            style={{ width: '100%', marginTop: '8px' }}
          />
        </div>
        
        <div style={{ marginTop: '16px' }}>
          <label>語音ID:</label>
          <input
            type="text"
            value={voiceId}
            onChange={(e) => setVoiceId(e.target.value)}
            style={{ width: '100%', marginTop: '8px' }}
          />
        </div>

        <div style={{ marginTop: '16px' }}>
          <button onClick={handlePlay} style={{ marginRight: '8px' }}>播放</button>
          <button onClick={handlePause} style={{ marginRight: '8px' }}>暫停</button>
          <button onClick={handleStop} style={{ marginRight: '8px' }}>停止</button>
          <button onClick={() => handleSeek(10)} style={{ marginRight: '8px' }}>跳到10秒</button>
          <button onClick={() => handleVolumeChange(0.5)}>音量50%</button>
        </div>

        {status && (
          <div style={{ marginTop: '16px', padding: '8px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            狀態: {status}
          </div>
        )}
      </div>
      
      <div className="example-player" style={{ marginTop: '24px' }}>
        <VoicePlayer
          ref={playerRef}
          text={text}
          voiceId={voiceId}
          showControls={false} // 隱藏內建控制項，使用自定義控制
          onPlayStart={() => setStatus('播放開始')}
          onPlayEnd={() => setStatus('播放結束')}
          onProgress={(progress, currentTime, duration) => {
            setStatus(`進度: ${progress.toFixed(1)}% (${currentTime.toFixed(1)}s / ${duration.toFixed(1)}s)`);
          }}
          onError={(error) => setStatus(`錯誤: ${error.message}`)}
          onLoaded={(duration) => setStatus(`音頻載入完成，時長: ${duration.toFixed(1)}秒`)}
        />
      </div>
    </div>
  );
};

/**
 * Context 使用示例
 * 展示如何使用 VoiceContext 進行狀態管理
 */
const VoiceContextExample: React.FC = () => {
  const { state, startPlayback, stopPlayback, updatePreferences } = useVoice();
  const { voices, loading: voicesLoading } = useVoices();
  const currentPlayback = useCurrentPlayback();
  
  const [testText, setTestText] = useState('這是使用 Context 管理的語音播放示例。');

  const handlePlayWithContext = useCallback(async () => {
    if (voices.length > 0) {
      try {
        await startPlayback(testText, voices[0].model_id);
      } catch (error) {
        console.error('播放失敗:', error);
      }
    }
  }, [testText, voices, startPlayback]);

  return (
    <div className="example-container">
      <h3>Context 狀態管理示例</h3>
      
      <div className="example-info">
        <p><strong>在線狀態:</strong> {state.isOnline ? '✅ 在線' : '❌ 離線'}</p>
        <p><strong>可用語音數量:</strong> {voicesLoading ? '載入中...' : voices.length}</p>
        <p><strong>播放狀態:</strong> {currentPlayback.isPlaying ? '🔊 播放中' : '⏸️ 已暫停'}</p>
        {currentPlayback.currentTrack && (
          <p><strong>當前音軌:</strong> {currentPlayback.currentTrack.voiceName}</p>
        )}
        <p><strong>播放歷史記錄:</strong> {state.playbackHistory.length} 條</p>
      </div>
      
      <div className="example-controls">
        <div>
          <label>測試文字:</label>
          <textarea
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            rows={2}
            style={{ width: '100%', marginTop: '8px' }}
          />
        </div>
        
        <div style={{ marginTop: '16px' }}>
          <button 
            onClick={handlePlayWithContext} 
            disabled={voicesLoading || voices.length === 0}
            style={{ marginRight: '8px' }}
          >
            使用 Context 播放
          </button>
          <button onClick={stopPlayback}>停止播放</button>
        </div>
      </div>

      <div style={{ marginTop: '24px' }}>
        <h4>偏好設置</h4>
        <div>
          <label>默認音量:</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={state.preferences.defaultVolume}
            onChange={(e) => updatePreferences({ defaultVolume: Number(e.target.value) })}
            style={{ width: '200px', marginLeft: '8px' }}
          />
          <span style={{ marginLeft: '8px' }}>{Math.round(state.preferences.defaultVolume * 100)}%</span>
        </div>
        
        <div style={{ marginTop: '8px' }}>
          <label>默認播放速度:</label>
          <select
            value={state.preferences.defaultPlaybackRate}
            onChange={(e) => updatePreferences({ defaultPlaybackRate: Number(e.target.value) })}
            style={{ marginLeft: '8px' }}
          >
            <option value="0.5">0.5x</option>
            <option value="0.75">0.75x</option>
            <option value="1">1x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2x</option>
          </select>
        </div>

        <div style={{ marginTop: '8px' }}>
          <label>
            <input
              type="checkbox"
              checked={state.preferences.autoPlay}
              onChange={(e) => updatePreferences({ autoPlay: e.target.checked })}
              style={{ marginRight: '8px' }}
            />
            自動播放
          </label>
        </div>
      </div>
    </div>
  );
};

/**
 * 包裝在 VoiceProvider 中的 Context 示例
 */
export const VoiceContextExampleWithProvider: React.FC = () => {
  return (
    <VoiceProvider>
      <VoiceContextExample />
    </VoiceProvider>
  );
};

/**
 * API 直接使用示例
 * 展示如何直接使用 TTSApiService
 */
export const APIDirectExample: React.FC = () => {
  const [voices, setVoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');

  const loadVoices = useCallback(async () => {
    setLoading(true);
    try {
      const voicesList = await ttsApiService.getVoices();
      setVoices(voicesList);
      setResult(`成功載入 ${voicesList.length} 個語音`);
    } catch (error) {
      setResult(`載入語音失敗: ${error}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const testSynthesis = useCallback(async () => {
    if (voices.length === 0) {
      setResult('請先載入語音列表');
      return;
    }

    setLoading(true);
    try {
      const response = await ttsApiService.testSynthesis(
        '這是一個API直接調用的測試。',
        voices[0].model_id
      );
      
      if (response.success && response.audio_url) {
        setResult(`語音合成成功！音頻URL: ${response.audio_url}`);
        
        // 播放音頻
        const audio = new Audio(response.audio_url);
        audio.play().catch(console.error);
      } else {
        setResult('語音合成失敗');
      }
    } catch (error) {
      setResult(`API調用失敗: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [voices]);

  const getStats = useCallback(async () => {
    setLoading(true);
    try {
      const stats = await ttsApiService.getStats();
      setResult(`統計數據: 總任務 ${stats.total_jobs}, 成功率 ${(stats.success_rate * 100).toFixed(1)}%`);
    } catch (error) {
      setResult(`獲取統計失敗: ${error}`);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="example-container">
      <h3>TTS API 直接使用示例</h3>
      
      <div className="example-controls">
        <button onClick={loadVoices} disabled={loading} style={{ marginRight: '8px' }}>
          載入語音列表
        </button>
        <button onClick={testSynthesis} disabled={loading} style={{ marginRight: '8px' }}>
          測試語音合成
        </button>
        <button onClick={getStats} disabled={loading}>
          獲取統計數據
        </button>
      </div>
      
      <div style={{ marginTop: '16px' }}>
        <p><strong>可用語音:</strong> {voices.length} 個</p>
        {voices.length > 0 && (
          <ul style={{ maxHeight: '150px', overflowY: 'auto', marginTop: '8px' }}>
            {voices.map((voice, index) => (
              <li key={index}>
                {voice.name} ({voice.language} - {voice.gender})
              </li>
            ))}
          </ul>
        )}
      </div>
      
      {result && (
        <div style={{ 
          marginTop: '16px', 
          padding: '12px', 
          backgroundColor: '#f8f9fa', 
          border: '1px solid #e9ecef',
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          <strong>結果:</strong> {result}
        </div>
      )}
      
      {loading && (
        <div style={{ marginTop: '16px', textAlign: 'center' }}>
          載入中...
        </div>
      )}
    </div>
  );
};

/**
 * 完整示例組件
 * 展示所有功能的綜合使用
 */
export const TTSCompleteExample: React.FC = () => {
  const [currentExample, setCurrentExample] = useState<string>('basic');

  const examples = [
    { id: 'basic', name: '基本使用', component: BasicVoicePlayerExample },
    { id: 'advanced', name: '進階控制', component: AdvancedVoicePlayerExample },
    { id: 'context', name: '狀態管理', component: VoiceContextExampleWithProvider },
    { id: 'api', name: 'API直接使用', component: APIDirectExample }
  ];

  const CurrentComponent = examples.find(ex => ex.id === currentExample)?.component || BasicVoicePlayerExample;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      <h1>TTS 組件使用示例</h1>
      <p style={{ color: '#666', marginBottom: '32px' }}>
        以下是 TradingAgents TTS 前台組件的使用示例，展示了不同場景下的最佳實踐。
      </p>
      
      <div style={{ marginBottom: '32px' }}>
        <h3>選擇示例:</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {examples.map((example) => (
            <button
              key={example.id}
              onClick={() => setCurrentExample(example.id)}
              style={{
                padding: '8px 16px',
                border: currentExample === example.id ? '2px solid #007bff' : '1px solid #ddd',
                backgroundColor: currentExample === example.id ? '#e3f2fd' : 'white',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {example.name}
            </button>
          ))}
        </div>
      </div>
      
      <div style={{
        border: '1px solid #e9ecef',
        borderRadius: '8px',
        padding: '24px',
        backgroundColor: '#f8f9fa'
      }}>
        <CurrentComponent />
      </div>
      
      <div style={{ marginTop: '32px', fontSize: '14px', color: '#666' }}>
        <h4>使用提示:</h4>
        <ul>
          <li>確保後端 TTS API 服務正常運行</li>
          <li>檢查網絡連接和認證token</li>
          <li>語音ID需要與後端配置的語音模型對應</li>
          <li>長文本建議分段處理以提高性能</li>
          <li>使用 VoiceProvider 包裝應用以獲得最佳體驗</li>
        </ul>
      </div>
    </div>
  );
};

// 樣式
const exampleStyles = `
.example-container {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.example-container h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.example-controls {
  margin-bottom: 24px;
}

.example-controls label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.example-controls input,
.example-controls textarea,
.example-controls select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.example-controls button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.example-controls button:hover:not(:disabled) {
  background: #0056b3;
}

.example-controls button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.example-info {
  background: #e9ecef;
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.example-info p {
  margin: 4px 0;
  font-size: 14px;
}

.example-player {
  border-top: 1px solid #eee;
  padding-top: 24px;
}
`;

// 注入樣式到頁面
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = exampleStyles;
  document.head.appendChild(styleElement);
}

export default TTSCompleteExample;