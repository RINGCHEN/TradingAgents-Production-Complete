/**
 * TTS主應用程式 - 企業級語音服務整合中心
 * 統一整合六大分析師語音、播放控制和用戶偏好管理
 * 為TradingAgents系統提供完整的語音服務體驗
 * 
 * @author 魯班 (Code Artisan) & 梁建築師 (Code Architect)  
 * @version 1.0.0 Enterprise
 */

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { AnalystVoicePanel } from '../analyst/AnalystVoicePanel';
import { VoicePlayer } from '../voice/VoicePlayer';
import { useVoiceStore, useVoiceQueue, useVoiceStats } from '../../store/voiceStore';
import { TTSApiService } from '../../services/TTSApiService';
import { TTSVoice, TTSStats } from '../../admin/types/AdminTypes';
import './TTSMainApp.css';

// 懶加載組件
const VoiceHistoryPanel = React.lazy(() => import('./VoiceHistoryPanel'));
const VoiceSettingsPanel = React.lazy(() => import('./VoiceSettingsPanel'));
const VoiceAnalyticsPanel = React.lazy(() => import('./VoiceAnalyticsPanel'));

// ==================== 介面定義 ====================

export interface TTSMainAppProps {
  className?: string;
  initialTab?: 'analyst' | 'queue' | 'history' | 'settings' | 'analytics';
  showNavigation?: boolean;
  enableAdvancedFeatures?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  compactMode?: boolean;
}

interface TabConfig {
  id: string;
  name: string;
  icon: string;
  description: string;
  component: React.ComponentType<any>;
  requiresAuth?: boolean;
  premium?: boolean;
}

interface AppStats {
  totalVoices: number;
  activeAnalysts: number;
  queueSize: number;
  todayUsage: number;
  systemHealth: 'healthy' | 'warning' | 'error';
}

// ==================== 標籤配置 ====================

const TAB_CONFIGS: TabConfig[] = [
  {
    id: 'analyst',
    name: '數位分析師',
    icon: '👥',
    description: '六大專業分析師語音服務',
    component: AnalystVoicePanel,
    requiresAuth: false,
    premium: false
  },
  {
    id: 'queue',
    name: '播放佇列',
    icon: '📝',
    description: '管理和控制語音播放順序',
    component: React.Fragment, // 內嵌組件
    requiresAuth: false,
    premium: false
  },
  {
    id: 'history',
    name: '播放記錄',
    icon: '📚',
    description: '查看語音播放歷史記錄',
    component: VoiceHistoryPanel,
    requiresAuth: true,
    premium: false
  },
  {
    id: 'settings',
    name: '偏好設定',
    icon: '⚙️',
    description: '個人化語音偏好配置',
    component: VoiceSettingsPanel,
    requiresAuth: true,
    premium: false
  },
  {
    id: 'analytics',
    name: '使用分析',
    icon: '📊',
    description: '語音使用統計和趨勢分析',
    component: VoiceAnalyticsPanel,
    requiresAuth: true,
    premium: true
  }
];

// ==================== 主組件實現 ====================

export const TTSMainApp: React.FC<TTSMainAppProps> = ({
  className = '',
  initialTab = 'analyst',
  showNavigation = true,
  enableAdvancedFeatures = true,
  theme = 'auto',
  compactMode = false
}) => {
  // ==================== 狀態管理 ====================
  const [activeTab, setActiveTab] = useState<string>(initialTab);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [appStats, setAppStats] = useState<AppStats>({
    totalVoices: 0,
    activeAnalysts: 6,
    queueSize: 0,
    todayUsage: 0,
    systemHealth: 'healthy'
  });
  const [systemError, setSystemError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState<boolean>(false);

  // ==================== Store Hooks ====================
  const {
    voices,
    setVoices,
    currentPlayback,
    isGloballyPlaying,
    error: storeError,
    setError,
    setLoading,
    refreshCache
  } = useVoiceStore();

  const {
    queue,
    currentIndex,
    isPlaying: isQueuePlaying,
    repeatMode,
    shuffleMode,
    clearQueue,
    nextInQueue,
    previousInQueue,
    setRepeatMode,
    setShuffleMode
  } = useVoiceQueue();

  const { stats, incrementPlayCount, addPlayDuration } = useVoiceStats();

  // ==================== 服務實例 ====================
  const ttsService = TTSApiService.getInstance();

  // ==================== 初始化應用程式 ====================
  const initializeApp = useCallback(async () => {
    try {
      setIsLoading(true);
      setSystemError(null);

      // 檢查服務健康狀態
      const healthCheck = await ttsService.healthCheck();
      
      if (!healthCheck.success) {
        throw new Error('TTS服務不可用');
      }

      // 載入可用語音列表
      const voicesResponse = await ttsService.getVoices();
      const availableVoices = voicesResponse.success ? voicesResponse.data || [] : [];
      setVoices(availableVoices);

      // 載入系統統計
      const systemStats = await ttsService.getTTSStats();
      if (systemStats.success && systemStats.data) {
        setAppStats(prev => ({
          ...prev,
          totalVoices: systemStats.data.total_voices || 0,
          systemHealth: systemStats.data.success_rate > 0.9 ? 'healthy' : 
                       systemStats.data.success_rate > 0.7 ? 'warning' : 'error'
        }));
      }

      setIsInitialized(true);
    } catch (error) {
      console.error('TTS應用程式初始化失敗:', error);
      const errorMessage = error instanceof Error ? error.message : '初始化失敗';
      setSystemError(errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setLoading(false);
    }
  }, [ttsService, setVoices, setError, setLoading]);

  // ==================== 效果處理 ====================
  
  // 初始化應用程式
  useEffect(() => {
    initializeApp();
  }, [initializeApp]);

  // 監聽佇列變化並更新統計
  useEffect(() => {
    setAppStats(prev => ({ ...prev, queueSize: queue.length }));
  }, [queue.length]);

  // 監聽播放狀態變化
  useEffect(() => {
    if (currentPlayback) {
      incrementPlayCount(currentPlayback.voiceId, currentPlayback.analystId);
    }
  }, [currentPlayback, incrementPlayCount]);

  // 定期更新統計數據
  useEffect(() => {
    const updateStats = async () => {
      try {
        const systemStats = await ttsService.getTTSStats('today');
        if (systemStats.success && systemStats.data) {
          setAppStats(prev => ({
            ...prev,
            todayUsage: systemStats.data.total_jobs || 0
          }));
        }
      } catch (error) {
        console.warn('統計更新失敗:', error);
      }
    };

    const interval = setInterval(updateStats, 5 * 60 * 1000); // 每5分鐘更新
    return () => clearInterval(interval);
  }, [ttsService]);

  // ==================== 事件處理函數 ====================
  
  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId);
  }, []);

  const handleAnalystSelect = useCallback((analystId: string) => {
    console.log(`選擇分析師: ${analystId}`);
    // 這裡可以添加分析師選擇的額外邏輯
  }, []);

  const handlePlayStart = useCallback((analystId: string, text: string) => {
    console.log(`開始播放: ${analystId} - ${text.substring(0, 50)}...`);
    // 記錄播放開始事件
  }, []);

  const handlePlayEnd = useCallback((analystId: string) => {
    console.log(`播放結束: ${analystId}`);
    // 記錄播放結束事件
    const duration = currentPlayback ? 
      (Date.now() - currentPlayback.startTime.getTime()) / 1000 : 0;
    if (duration > 0) {
      addPlayDuration(duration);
    }
  }, [currentPlayback, addPlayDuration]);

  const handleRefresh = useCallback(() => {
    refreshCache();
    initializeApp();
  }, [refreshCache, initializeApp]);

  const handleClearError = useCallback(() => {
    setSystemError(null);
    setError(null);
  }, [setError]);

  // ==================== 渲染函數 ====================

  // 載入狀態
  if (isLoading) {
    return (
      <div className={`tts-main-app loading ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <h2>初始化TTS語音服務...</h2>
          <p>正在連接後端API並載入語音模型</p>
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (systemError && !isInitialized) {
    return (
      <div className={`tts-main-app error ${className}`}>
        <div className="error-container">
          <div className="error-icon">❌</div>
          <h2>語音服務暫時不可用</h2>
          <p>{systemError}</p>
          <div className="error-actions">
            <button onClick={handleRefresh} className="retry-button">
              重試連接
            </button>
            <button onClick={handleClearError} className="dismiss-button">
              忽略錯誤
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 主要內容渲染
  return (
    <div className={`tts-main-app ${theme} ${compactMode ? 'compact' : ''} ${className}`}>
      {/* 應用程式標頭 */}
      <header className="app-header">
        <div className="header-content">
          <div className="app-info">
            <h1 className="app-title">
              <span className="title-icon">🎙️</span>
              TTS語音服務中心
            </h1>
            <p className="app-subtitle">
              專業級數位分析師語音合成平台
            </p>
          </div>
          
          {/* 系統狀態指示器 */}
          <div className="system-status">
            <div className={`status-indicator ${appStats.systemHealth}`}>
              <span className="status-icon">
                {appStats.systemHealth === 'healthy' ? '🟢' : 
                 appStats.systemHealth === 'warning' ? '🟡' : '🔴'}
              </span>
              <span className="status-text">
                {appStats.systemHealth === 'healthy' ? '服務正常' :
                 appStats.systemHealth === 'warning' ? '性能警告' : '服務異常'}
              </span>
            </div>
            
            {/* 快速統計 */}
            <div className="quick-stats">
              <span className="stat-item">
                <span className="stat-icon">👥</span>
                {appStats.activeAnalysts} 分析師
              </span>
              <span className="stat-item">
                <span className="stat-icon">🎵</span>
                {appStats.totalVoices} 語音
              </span>
              <span className="stat-item">
                <span className="stat-icon">📝</span>
                {appStats.queueSize} 佇列
              </span>
            </div>
          </div>
        </div>

        {/* 全域播放控制 */}
        {(currentPlayback || isQueuePlaying) && (
          <div className="global-player">
            <div className="player-info">
              <span className="player-icon">🎵</span>
              <div className="player-text">
                {currentPlayback ? (
                  <>
                    <span className="player-analyst">
                      {currentPlayback.analystId ? `${currentPlayback.analystId} - ` : ''}
                    </span>
                    <span className="player-content">
                      {currentPlayback.text.substring(0, 80)}
                      {currentPlayback.text.length > 80 ? '...' : ''}
                    </span>
                  </>
                ) : (
                  <span className="player-content">播放佇列進行中...</span>
                )}
              </div>
            </div>
            
            {isQueuePlaying && (
              <div className="queue-controls">
                <button onClick={previousInQueue} className="queue-btn">
                  ⏮️
                </button>
                <button onClick={nextInQueue} className="queue-btn">
                  ⏭️
                </button>
                <button 
                  onClick={() => setRepeatMode(
                    repeatMode === 'none' ? 'all' : 
                    repeatMode === 'all' ? 'one' : 'none'
                  )}
                  className={`queue-btn ${repeatMode !== 'none' ? 'active' : ''}`}
                >
                  {repeatMode === 'one' ? '🔂' : '🔁'}
                </button>
                <button 
                  onClick={() => setShuffleMode(!shuffleMode)}
                  className={`queue-btn ${shuffleMode ? 'active' : ''}`}
                >
                  🔀
                </button>
              </div>
            )}
          </div>
        )}
      </header>

      {/* 導航標籤 */}
      {showNavigation && (
        <nav className="app-navigation">
          <div className="nav-tabs">
            {TAB_CONFIGS.map((tab) => (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''} ${
                  tab.premium ? 'premium' : ''
                }`}
                onClick={() => handleTabChange(tab.id)}
                title={tab.description}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-name">{tab.name}</span>
                {tab.premium && <span className="premium-badge">PRO</span>}
              </button>
            ))}
          </div>
        </nav>
      )}

      {/* 錯誤提示條 */}
      {(systemError || storeError) && (
        <div className="error-banner">
          <div className="error-content">
            <span className="error-icon">⚠️</span>
            <span className="error-message">
              {systemError || storeError}
            </span>
            <button onClick={handleClearError} className="error-dismiss">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* 主要內容區域 */}
      <main className="app-main">
        <Suspense
          fallback={
            <div className="content-loading">
              <div className="content-spinner"></div>
              <p>載入組件中...</p>
            </div>
          }
        >
          {/* 數位分析師標籤 */}
          {activeTab === 'analyst' && (
            <AnalystVoicePanel
              className="tab-content"
              showQuickActions={enableAdvancedFeatures}
              enableQueueMode={enableAdvancedFeatures}
              showAnalystStats={enableAdvancedFeatures}
              onAnalystSelect={handleAnalystSelect}
              onPlayStart={handlePlayStart}
              onPlayEnd={handlePlayEnd}
            />
          )}

          {/* 播放佇列標籤 */}
          {activeTab === 'queue' && (
            <div className="tab-content queue-panel">
              <div className="queue-header">
                <h2>播放佇列管理</h2>
                <div className="queue-actions">
                  <button 
                    onClick={clearQueue}
                    className="clear-queue-btn"
                    disabled={queue.length === 0}
                  >
                    清空佇列
                  </button>
                </div>
              </div>
              
              {queue.length === 0 ? (
                <div className="empty-queue">
                  <div className="empty-icon">📝</div>
                  <h3>播放佇列為空</h3>
                  <p>請到「數位分析師」頁面添加語音內容到佇列</p>
                </div>
              ) : (
                <div className="queue-list">
                  {queue.map((item, index) => (
                    <div
                      key={item.id}
                      className={`queue-item ${index === currentIndex ? 'current' : ''}`}
                    >
                      <div className="item-index">
                        {index === currentIndex && isQueuePlaying ? '🎵' : index + 1}
                      </div>
                      <div className="item-content">
                        <div className="item-meta">
                          <span className="item-analyst">
                            {item.analystId || '通用語音'}
                          </span>
                          <span className="item-scenario">
                            {item.scenario || '預設'}
                          </span>
                        </div>
                        <div className="item-text">
                          {item.text}
                        </div>
                      </div>
                      <div className="item-actions">
                        <button className="item-remove">🗑️</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 其他標籤的懶加載組件 */}
          {activeTab === 'history' && (
            <VoiceHistoryPanel className="tab-content" />
          )}
          
          {activeTab === 'settings' && (
            <VoiceSettingsPanel className="tab-content" />
          )}
          
          {activeTab === 'analytics' && enableAdvancedFeatures && (
            <VoiceAnalyticsPanel className="tab-content" stats={stats} />
          )}
        </Suspense>
      </main>

      {/* 應用程式底部 */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-info">
            <span>TradingAgents TTS v2.0.0</span>
            <span>•</span>
            <span>企業級語音服務</span>
          </div>
          <div className="footer-actions">
            <button onClick={handleRefresh} className="footer-btn">
              🔄 重新整理
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default TTSMainApp;