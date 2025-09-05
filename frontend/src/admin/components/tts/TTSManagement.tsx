/**
 * TTS 管理組件
 * 提供完整的語音合成管理功能，整合 VoicePlayer 和 TTS API
 * 
 * @author 魯班 (Code Artisan)
 * @version 1.0.0
 */

import React, { 
  useState, 
  useEffect, 
  useCallback, 
  useMemo,
  useRef
} from 'react';
import { 
  TTSVoice, 
  TTSJob, 
  TTSStats,
  JobStatus,
  VoiceGender,
  AudioFormat,
  TTSProvider
} from '../../types/AdminTypes';
import ttsApiService from '../../../services/TTSApiService';
import { VoiceProvider, useVoice } from '../../../contexts/VoiceContext';
import VoicePlayer, { VoicePlayerRef } from '../../../components/tts/VoicePlayer';
import '../../../components/tts/VoicePlayer.css';
import './TTSManagement.css';

// 頁籤類型
type TabType = 'voices' | 'jobs' | 'test' | 'stats' | 'settings';

// 語音測試接口
interface VoiceTest {
  text: string;
  voiceId: string;
  isPlaying: boolean;
  audioUrl?: string;
  error?: string;
}

// 過濾器接口
interface VoiceFilter {
  language?: string;
  gender?: VoiceGender;
  provider?: TTSProvider;
  activeOnly: boolean;
  searchText: string;
}

interface JobFilter {
  status?: JobStatus;
  startDate?: string;
  endDate?: string;
  searchText: string;
}

/**
 * TTS 管理主組件
 */
const TTSManagement: React.FC = () => {
  return (
    <VoiceProvider>
      <TTSManagementContent />
    </VoiceProvider>
  );
};

/**
 * TTS 管理內容組件
 */
const TTSManagementContent: React.FC = () => {
  // 狀態管理
  const [activeTab, setActiveTab] = useState<TabType>('voices');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 語音相關狀態
  const [voices, setVoices] = useState<TTSVoice[]>([]);
  const [voiceFilter, setVoiceFilter] = useState<VoiceFilter>({
    activeOnly: true,
    searchText: ''
  });
  
  // 任務相關狀態
  const [jobs, setJobs] = useState<TTSJob[]>([]);
  const [jobFilter, setJobFilter] = useState<JobFilter>({
    searchText: ''
  });
  
  // 統計數據
  const [stats, setStats] = useState<TTSStats | null>(null);
  
  // 語音測試
  const [voiceTest, setVoiceTest] = useState<VoiceTest>({
    text: '這是一個語音合成測試。Hello, this is a text-to-speech test.',
    voiceId: '',
    isPlaying: false
  });
  
  // 使用 Voice Context
  const { 
    state: voiceState, 
    startPlayback, 
    stopPlayback 
  } = useVoice();
  
  // Refs
  const testPlayerRef = useRef<VoicePlayerRef>(null);

  // 加載語音列表
  const loadVoices = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await ttsApiService.getVoices({
        language: voiceFilter.language,
        gender: voiceFilter.gender,
        active_only: voiceFilter.activeOnly
      });
      setVoices(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加載語音列表失敗';
      setError(errorMessage);
      console.error('Load voices error:', err);
    } finally {
      setLoading(false);
    }
  }, [voiceFilter]);

  // 加載任務列表
  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await ttsApiService.getJobs({
        status: jobFilter.status,
        start_date: jobFilter.startDate,
        end_date: jobFilter.endDate,
        page: 1,
        limit: 50
      });
      setJobs(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加載任務列表失敗';
      setError(errorMessage);
      console.error('Load jobs error:', err);
    } finally {
      setLoading(false);
    }
  }, [jobFilter]);

  // 加載統計數據
  const loadStats = useCallback(async () => {
    try {
      const response = await ttsApiService.getStats();
      setStats(response);
    } catch (err) {
      console.error('Load stats error:', err);
    }
  }, []);

  // 初始化加載
  useEffect(() => {
    if (activeTab === 'voices') {
      loadVoices();
    } else if (activeTab === 'jobs') {
      loadJobs();
    } else if (activeTab === 'stats') {
      loadStats();
    }
  }, [activeTab, loadVoices, loadJobs, loadStats]);

  // 過濾語音列表
  const filteredVoices = useMemo(() => {
    return voices.filter(voice => {
      if (voiceFilter.searchText) {
        const searchLower = voiceFilter.searchText.toLowerCase();
        if (!voice.name.toLowerCase().includes(searchLower) &&
            !voice.language.toLowerCase().includes(searchLower) &&
            !(voice.description || '').toLowerCase().includes(searchLower)) {
          return false;
        }
      }
      
      if (voiceFilter.language && voice.language !== voiceFilter.language) {
        return false;
      }
      
      if (voiceFilter.gender && voice.gender !== voiceFilter.gender) {
        return false;
      }
      
      if (voiceFilter.provider && voice.provider !== voiceFilter.provider) {
        return false;
      }
      
      return true;
    });
  }, [voices, voiceFilter]);

  // 過濾任務列表
  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      if (jobFilter.searchText) {
        const searchLower = jobFilter.searchText.toLowerCase();
        if (!job.text_content.toLowerCase().includes(searchLower) &&
            !(job.voice_name || '').toLowerCase().includes(searchLower) &&
            !(job.user_email || '').toLowerCase().includes(searchLower)) {
          return false;
        }
      }
      
      return true;
    });
  }, [jobs, jobFilter]);

  // 語音測試處理
  const handleVoiceTest = useCallback(async () => {
    if (!voiceTest.voiceId || !voiceTest.text.trim()) {
      setError('請選擇語音並輸入測試文字');
      return;
    }

    setVoiceTest(prev => ({ ...prev, isPlaying: true, error: undefined }));
    
    try {
      await startPlayback(voiceTest.text, voiceTest.voiceId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '語音測試失敗';
      setVoiceTest(prev => ({ ...prev, error: errorMessage, isPlaying: false }));
    }
  }, [voiceTest.voiceId, voiceTest.text, startPlayback]);

  // 停止語音測試
  const handleStopTest = useCallback(() => {
    stopPlayback();
    setVoiceTest(prev => ({ ...prev, isPlaying: false }));
  }, [stopPlayback]);

  // 重試任務
  const handleRetryJob = useCallback(async (jobId: string) => {
    try {
      await ttsApiService.retryJob(jobId);
      await loadJobs(); // 重新加載任務列表
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '重試任務失敗';
      setError(errorMessage);
    }
  }, [loadJobs]);

  // 取消任務
  const handleCancelJob = useCallback(async (jobId: string) => {
    try {
      await ttsApiService.cancelJob(jobId);
      await loadJobs(); // 重新加載任務列表
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '取消任務失敗';
      setError(errorMessage);
    }
  }, [loadJobs]);

  // 渲染頁籤導航
  const renderTabs = () => (
    <div className="tts-tabs">
      <button
        className={`tts-tab ${activeTab === 'voices' ? 'tts-tab--active' : ''}`}
        onClick={() => setActiveTab('voices')}
      >
        語音管理
      </button>
      <button
        className={`tts-tab ${activeTab === 'jobs' ? 'tts-tab--active' : ''}`}
        onClick={() => setActiveTab('jobs')}
      >
        任務管理
      </button>
      <button
        className={`tts-tab ${activeTab === 'test' ? 'tts-tab--active' : ''}`}
        onClick={() => setActiveTab('test')}
      >
        語音測試
      </button>
      <button
        className={`tts-tab ${activeTab === 'stats' ? 'tts-tab--active' : ''}`}
        onClick={() => setActiveTab('stats')}
      >
        統計分析
      </button>
    </div>
  );

  // 渲染語音管理頁面
  const renderVoicesTab = () => (
    <div className="tts-voices-tab">
      {/* 過濾器 */}
      <div className="tts-filters">
        <input
          type="text"
          placeholder="搜索語音..."
          className="tts-search-input"
          value={voiceFilter.searchText}
          onChange={(e) => setVoiceFilter(prev => ({ ...prev, searchText: e.target.value }))}
        />
        
        <select
          value={voiceFilter.language || ''}
          onChange={(e) => setVoiceFilter(prev => ({ 
            ...prev, 
            language: e.target.value || undefined 
          }))}
          className="tts-filter-select"
        >
          <option value="">所有語言</option>
          <option value="zh-TW">繁體中文</option>
          <option value="zh-CN">简体中文</option>
          <option value="en-US">English (US)</option>
          <option value="ja-JP">日本語</option>
        </select>
        
        <select
          value={voiceFilter.gender || ''}
          onChange={(e) => setVoiceFilter(prev => ({ 
            ...prev, 
            gender: e.target.value as VoiceGender || undefined 
          }))}
          className="tts-filter-select"
        >
          <option value="">所有性別</option>
          <option value="male">男性</option>
          <option value="female">女性</option>
          <option value="neutral">中性</option>
        </select>
        
        <label className="tts-checkbox-label">
          <input
            type="checkbox"
            checked={voiceFilter.activeOnly}
            onChange={(e) => setVoiceFilter(prev => ({ ...prev, activeOnly: e.target.checked }))}
          />
          只顯示啟用的語音
        </label>
        
        <button onClick={loadVoices} className="tts-refresh-btn" disabled={loading}>
          🔄 重新載入
        </button>
      </div>

      {/* 語音列表 */}
      <div className="tts-voices-grid">
        {filteredVoices.map((voice) => (
          <div key={voice.id || voice.model_id} className="tts-voice-card">
            <div className="tts-voice-header">
              <h3 className="tts-voice-name">{voice.name}</h3>
              <span className={`tts-voice-status ${voice.is_active ? 'active' : 'inactive'}`}>
                {voice.is_active ? '啟用' : '停用'}
              </span>
            </div>
            
            <div className="tts-voice-details">
              <div className="tts-voice-info">
                <span className="tts-voice-lang">{voice.language}</span>
                <span className="tts-voice-gender">{voice.gender}</span>
                <span className="tts-voice-provider">{voice.provider}</span>
              </div>
              
              {voice.description && (
                <p className="tts-voice-description">{voice.description}</p>
              )}
              
              <div className="tts-voice-meta">
                <span>採樣率: {voice.sample_rate}Hz</span>
                <span>格式: {voice.audio_format.toUpperCase()}</span>
                {voice.is_premium && <span className="tts-premium-badge">Premium</span>}
              </div>
              
              {voice.cost_per_character > 0 && (
                <div className="tts-voice-cost">
                  成本: ${voice.cost_per_character.toFixed(4)}/字符
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染任務管理頁面
  const renderJobsTab = () => (
    <div className="tts-jobs-tab">
      {/* 過濾器 */}
      <div className="tts-filters">
        <input
          type="text"
          placeholder="搜索任務..."
          className="tts-search-input"
          value={jobFilter.searchText}
          onChange={(e) => setJobFilter(prev => ({ ...prev, searchText: e.target.value }))}
        />
        
        <select
          value={jobFilter.status || ''}
          onChange={(e) => setJobFilter(prev => ({ 
            ...prev, 
            status: e.target.value as JobStatus || undefined 
          }))}
          className="tts-filter-select"
        >
          <option value="">所有狀態</option>
          <option value="pending">等待中</option>
          <option value="processing">處理中</option>
          <option value="completed">已完成</option>
          <option value="failed">失敗</option>
          <option value="cancelled">已取消</option>
        </select>
        
        <button onClick={loadJobs} className="tts-refresh-btn" disabled={loading}>
          🔄 重新載入
        </button>
      </div>

      {/* 任務列表 */}
      <div className="tts-jobs-list">
        {filteredJobs.map((job) => (
          <div key={job.id || job.job_id} className="tts-job-card">
            <div className="tts-job-header">
              <span className="tts-job-id">#{job.job_id}</span>
              <span className={`tts-job-status tts-job-status--${job.status}`}>
                {getStatusText(job.status)}
              </span>
              <span className="tts-job-created">{formatDate(job.created_at)}</span>
            </div>
            
            <div className="tts-job-content">
              <p className="tts-job-text">{truncateText(job.text_content, 150)}</p>
              
              <div className="tts-job-details">
                <span>語音: {job.voice_name || 'N/A'}</span>
                <span>字符數: {job.character_count || 'N/A'}</span>
                {job.actual_duration && (
                  <span>時長: {formatDuration(job.actual_duration)}</span>
                )}
              </div>
              
              {job.error_message && (
                <div className="tts-job-error">
                  錯誤: {job.error_message}
                </div>
              )}
            </div>
            
            <div className="tts-job-actions">
              {job.status === 'failed' && (
                <button
                  onClick={() => handleRetryJob(job.job_id)}
                  className="tts-job-btn tts-job-btn--retry"
                >
                  重試
                </button>
              )}
              
              {['pending', 'processing'].includes(job.status) && (
                <button
                  onClick={() => handleCancelJob(job.job_id)}
                  className="tts-job-btn tts-job-btn--cancel"
                >
                  取消
                </button>
              )}
              
              {job.output_file_url && (
                <a
                  href={job.output_file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="tts-job-btn tts-job-btn--download"
                >
                  下載
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染語音測試頁面
  const renderTestTab = () => (
    <div className="tts-test-tab">
      <div className="tts-test-form">
        <h3>語音測試</h3>
        
        <div className="tts-form-group">
          <label>選擇語音:</label>
          <select
            value={voiceTest.voiceId}
            onChange={(e) => setVoiceTest(prev => ({ ...prev, voiceId: e.target.value }))}
            className="tts-voice-select"
          >
            <option value="">請選擇語音...</option>
            {voices.filter(v => v.is_active).map((voice) => (
              <option key={voice.id || voice.model_id} value={voice.model_id}>
                {voice.name} ({voice.language} - {voice.gender})
              </option>
            ))}
          </select>
        </div>
        
        <div className="tts-form-group">
          <label>測試文字:</label>
          <textarea
            value={voiceTest.text}
            onChange={(e) => setVoiceTest(prev => ({ ...prev, text: e.target.value }))}
            className="tts-test-textarea"
            placeholder="輸入要測試的文字內容..."
            rows={4}
            maxLength={500}
          />
          <div className="tts-text-counter">
            {voiceTest.text.length} / 500 字符
          </div>
        </div>
        
        <div className="tts-test-actions">
          <button
            onClick={handleVoiceTest}
            disabled={!voiceTest.voiceId || !voiceTest.text.trim() || voiceState.currentPlayback.isLoading}
            className="tts-test-btn tts-test-btn--play"
          >
            {voiceState.currentPlayback.isLoading ? '合成中...' : '🔊 播放測試'}
          </button>
          
          <button
            onClick={handleStopTest}
            disabled={!voiceState.currentPlayback.isPlaying}
            className="tts-test-btn tts-test-btn--stop"
          >
            ⏹️ 停止
          </button>
        </div>
        
        {voiceTest.error && (
          <div className="tts-test-error">
            {voiceTest.error}
          </div>
        )}
      </div>

      {/* 語音播放器 */}
      {voiceTest.voiceId && voiceTest.text && (
        <div className="tts-test-player">
          <VoicePlayer
            ref={testPlayerRef}
            text={voiceTest.text}
            voiceId={voiceTest.voiceId}
            showControls={true}
            showProgress={true}
            showTime={true}
            enableKeyboard={true}
            onError={(error) => setVoiceTest(prev => ({ ...prev, error: error.message }))}
          />
        </div>
      )}
    </div>
  );

  // 渲染統計分析頁面
  const renderStatsTab = () => (
    <div className="tts-stats-tab">
      {stats ? (
        <div className="tts-stats-grid">
          <div className="tts-stat-card">
            <h4>總任務數</h4>
            <div className="tts-stat-value">{stats.total_jobs}</div>
          </div>
          
          <div className="tts-stat-card">
            <h4>成功率</h4>
            <div className="tts-stat-value">{(stats.success_rate * 100).toFixed(1)}%</div>
          </div>
          
          <div className="tts-stat-card">
            <h4>平均處理時間</h4>
            <div className="tts-stat-value">{stats.avg_processing_time.toFixed(1)}秒</div>
          </div>
          
          <div className="tts-stat-card">
            <h4>總字符數</h4>
            <div className="tts-stat-value">{stats.total_characters.toLocaleString()}</div>
          </div>
          
          <div className="tts-stat-card">
            <h4>總音頻時長</h4>
            <div className="tts-stat-value">{formatDuration(stats.total_duration)}</div>
          </div>
          
          <div className="tts-stat-card">
            <h4>可用語音</h4>
            <div className="tts-stat-value">{stats.active_voices} / {stats.total_voices}</div>
          </div>
        </div>
      ) : (
        <div className="tts-stats-loading">載入統計數據中...</div>
      )}
    </div>
  );

  return (
    <div className="tts-management">
      <div className="tts-header">
        <h2>TTS 語音合成管理</h2>
        <div className="tts-header-actions">
          {error && (
            <div className="tts-error-message">
              <span className="tts-error-icon">⚠️</span>
              {error}
              <button onClick={() => setError(null)} className="tts-error-close">×</button>
            </div>
          )}
        </div>
      </div>
      
      {renderTabs()}
      
      <div className="tts-content">
        {loading && <div className="tts-loading">載入中...</div>}
        
        {activeTab === 'voices' && renderVoicesTab()}
        {activeTab === 'jobs' && renderJobsTab()}
        {activeTab === 'test' && renderTestTab()}
        {activeTab === 'stats' && renderStatsTab()}
      </div>
    </div>
  );
};

// 實用函數
const getStatusText = (status: JobStatus): string => {
  const statusMap: Record<JobStatus, string> = {
    pending: '等待中',
    processing: '處理中',
    completed: '已完成',
    failed: '失敗',
    cancelled: '已取消'
  };
  return statusMap[status] || status;
};

const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-TW');
};

const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}分${remainingSeconds}秒`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}時${minutes}分`;
  }
};

const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export default TTSManagement;