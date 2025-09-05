/**
 * 分析師語音面板 - 六大數位分析師語音播放控制中心
 * 整合六大分析師的語音合成與播放功能
 * 支援多場景語音切換和智能推薦播放
 * 
 * @author 魯班 (Code Artisan) & 梁建築師 (Code Architect)
 * @version 1.0.0 Enterprise
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { VoicePlayer } from '../voice/VoicePlayer';
import { useVoiceStore, useAnalystPreferences, useVoiceQueue } from '../../store/voiceStore';
import { TTSApiService, AnalystVoiceConfig } from '../../services/TTSApiService';
import { TTSVoice, AudioFormat } from '../../admin/types/AdminTypes';
import './AnalystVoicePanel.css';

// ==================== 介面定義 ====================

export interface AnalystInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  specialties: string[];
  defaultScenarios: string[];
}

export interface AnalystVoicePanelProps {
  className?: string;
  showQuickActions?: boolean;
  enableQueueMode?: boolean;
  showAnalystStats?: boolean;
  maxVisibleAnalysts?: number;
  onAnalystSelect?: (analystId: string) => void;
  onPlayStart?: (analystId: string, text: string) => void;
  onPlayEnd?: (analystId: string) => void;
}

export interface VoiceScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  sampleText: string;
}

// ==================== 六大分析師配置 ====================

const ANALYSTS_CONFIG: AnalystInfo[] = [
  {
    id: 'fundamentals',
    name: '基本面分析師',
    description: '專精財報分析、公司估值和基本面研究',
    icon: '📊',
    color: '#2563EB', // 藍色
    specialties: ['財報分析', 'DCF估值', 'ROE分析', '營收預測'],
    defaultScenarios: ['analysis', 'summary', 'forecast']
  },
  {
    id: 'news',
    name: '新聞分析師', 
    description: '即時新聞解讀、市場熱點追蹤和輿情分析',
    icon: '📰',
    color: '#DC2626', // 紅色
    specialties: ['即時新聞', '市場熱點', '政策解讀', '產業動態'],
    defaultScenarios: ['breaking', 'summary', 'analysis']
  },
  {
    id: 'risk',
    name: '風險管理分析師',
    description: '風險評估、資產配置和投資組合管理',
    icon: '⚠️',
    color: '#F59E0B', // 橙色
    specialties: ['風險評估', '資產配置', 'VaR分析', '壓力測試'],
    defaultScenarios: ['warning', 'report', 'recommendation']
  },
  {
    id: 'sentiment',
    name: '情緒分析師',
    description: '市場情緒分析、投資者行為和心理面研究',
    icon: '💭',
    color: '#8B5CF6', // 紫色
    specialties: ['市場情緒', '恐慌指數', '投資心理', '群眾行為'],
    defaultScenarios: ['positive', 'negative', 'neutral']
  },
  {
    id: 'investment',
    name: '投資規劃師',
    description: '投資策略制定、資產配置和長期規劃',
    icon: '💰',
    color: '#059669', // 綠色
    specialties: ['投資策略', '資產配置', '退休規劃', '稅務優化'],
    defaultScenarios: ['recommendation', 'strategy', 'planning']
  },
  {
    id: 'taiwan-market',
    name: '台股市場分析師',
    description: '台灣股市專精分析、盤勢解讀和個股推薦',
    icon: '🇹🇼',
    color: '#EC4899', // 粉色
    specialties: ['台股分析', '盤勢解讀', '個股推薦', '外資動向'],
    defaultScenarios: ['opening', 'closing', 'analysis', 'recommendation']
  }
];

const VOICE_SCENARIOS: VoiceScenario[] = [
  {
    id: 'analysis',
    name: '深度分析',
    description: '詳細的市場或個股分析報告',
    icon: '🔍',
    sampleText: '根據最新財報數據分析，該公司營運表現呈現穩定成長趨勢...'
  },
  {
    id: 'summary', 
    name: '重點摘要',
    description: '快速瀏覽重點資訊',
    icon: '📝',
    sampleText: '今日市場重點：台股收盤上漲0.8%，電子股表現亮眼...'
  },
  {
    id: 'breaking',
    name: '突發消息',
    description: '重要新聞即時播報',
    icon: '🚨',
    sampleText: '突發：央行宣布利率政策調整，預期將影響金融股表現...'
  },
  {
    id: 'recommendation',
    name: '投資建議',
    description: '具體的投資操作建議',
    icon: '💡',
    sampleText: '建議投資組合調整：增持科技股比重至30%，減持傳產股...'
  },
  {
    id: 'warning',
    name: '風險警示',
    description: '重要風險提醒和預警',
    icon: '⚠️',
    sampleText: '風險提醒：近期市場波動加劇，建議控制持股比例...'
  }
];

// ==================== 主組件實現 ====================

export const AnalystVoicePanel: React.FC<AnalystVoicePanelProps> = ({
  className = '',
  showQuickActions = true,
  enableQueueMode = true,
  showAnalystStats = false,
  maxVisibleAnalysts = 6,
  onAnalystSelect,
  onPlayStart,
  onPlayEnd
}) => {
  // ==================== 狀態管理 ====================
  const [selectedAnalystId, setSelectedAnalystId] = useState<string>('fundamentals');
  const [selectedScenario, setSelectedScenario] = useState<string>('analysis');
  const [customText, setCustomText] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
  const [loadingAnalysts, setLoadingAnalysts] = useState<Set<string>>(new Set());

  // ==================== Store Hooks ====================
  const {
    voices,
    currentPlayback,
    setCurrentPlaying,
    addToHistory,
    isGloballyPlaying
  } = useVoiceStore();

  const { preferences, updatePreference } = useAnalystPreferences();
  const { addToQueue, queue } = useVoiceQueue();

  // ==================== 服務實例 ====================
  const ttsService = TTSApiService.getInstance();

  // ==================== 計算屬性 ====================
  const visibleAnalysts = useMemo(() => 
    ANALYSTS_CONFIG.slice(0, maxVisibleAnalysts),
    [maxVisibleAnalysts]
  );

  const selectedAnalyst = useMemo(() => 
    ANALYSTS_CONFIG.find(analyst => analyst.id === selectedAnalystId),
    [selectedAnalystId]
  );

  const availableScenarios = useMemo(() => {
    if (!selectedAnalyst) return VOICE_SCENARIOS;
    
    return VOICE_SCENARIOS.filter(scenario => 
      selectedAnalyst.defaultScenarios.includes(scenario.id)
    );
  }, [selectedAnalyst]);

  const analystVoiceConfig = useMemo(() => 
    ttsService.getAnalystVoiceConfig(selectedAnalystId),
    [selectedAnalystId, ttsService]
  );

  // ==================== 事件處理函數 ====================

  const handleAnalystSelect = useCallback((analystId: string) => {
    setSelectedAnalystId(analystId);
    onAnalystSelect?.(analystId);
    
    // 自動選擇該分析師的預設場景
    const analyst = ANALYSTS_CONFIG.find(a => a.id === analystId);
    if (analyst && analyst.defaultScenarios.length > 0) {
      setSelectedScenario(analyst.defaultScenarios[0]);
    }
  }, [onAnalystSelect]);

  const handleScenarioSelect = useCallback((scenarioId: string) => {
    setSelectedScenario(scenarioId);
    
    // 自動填入該場景的範例文字
    const scenario = VOICE_SCENARIOS.find(s => s.id === scenarioId);
    if (scenario && !customText) {
      setCustomText(scenario.sampleText);
    }
  }, [customText]);

  const handlePlayAnalystVoice = useCallback(async () => {
    if (!selectedAnalystId || !customText.trim()) return;

    try {
      setLoadingAnalysts(prev => new Set(prev).add(selectedAnalystId));
      setIsPlaying(true);

      const audioBlob = await ttsService.synthesizeAnalystSpeech(
        selectedAnalystId,
        customText,
        selectedScenario
      );

      const audioUrl = URL.createObjectURL(audioBlob);
      setCurrentAudioUrl(audioUrl);

      // 更新全域播放狀態
      setCurrentPlaying({
        text: customText,
        voiceId: analystVoiceConfig?.defaultVoiceId || 'default',
        startTime: new Date(),
        analystId: selectedAnalystId,
        scenario: selectedScenario
      });

      // 記錄播放歷史
      addToHistory({
        id: Date.now().toString(),
        text: customText,
        voiceId: analystVoiceConfig?.defaultVoiceId || 'default',
        duration: 0,
        playedAt: new Date(),
        analystId: selectedAnalystId,
        scenario: selectedScenario,
        completed: false
      });

      onPlayStart?.(selectedAnalystId, customText);

    } catch (error) {
      console.error('語音合成失敗:', error);
      // 這裡可以添加錯誤提示UI
    } finally {
      setLoadingAnalysts(prev => {
        const newSet = new Set(prev);
        newSet.delete(selectedAnalystId);
        return newSet;
      });
    }
  }, [
    selectedAnalystId, 
    customText, 
    selectedScenario, 
    analystVoiceConfig, 
    ttsService,
    setCurrentPlaying,
    addToHistory,
    onPlayStart
  ]);

  const handleAddToQueue = useCallback(() => {
    if (!selectedAnalystId || !customText.trim()) return;

    addToQueue({
      id: `queue-${Date.now()}`,
      text: customText,
      voiceId: analystVoiceConfig?.defaultVoiceId || 'default',
      analystId: selectedAnalystId,
      scenario: selectedScenario,
      priority: 5,
      metadata: {
        title: `${selectedAnalyst?.name} - ${VOICE_SCENARIOS.find(s => s.id === selectedScenario)?.name}`,
        category: 'analyst-voice',
        timestamp: new Date()
      }
    });

    // 清空文字框準備下一個項目
    setCustomText('');
  }, [
    selectedAnalystId,
    customText,
    selectedScenario,
    selectedAnalyst,
    analystVoiceConfig,
    addToQueue
  ]);

  const handleStopPlayback = useCallback(() => {
    setIsPlaying(false);
    setCurrentPlaying(null);
    onPlayEnd?.(selectedAnalystId);
    
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      setCurrentAudioUrl(null);
    }
  }, [selectedAnalystId, currentAudioUrl, setCurrentPlaying, onPlayEnd]);

  // ==================== 渲染函數 ====================
  
  return (
    <div className={`analyst-voice-panel ${className}`}>
      {/* 標題區域 */}
      <div className="panel-header">
        <h2 className="panel-title">
          <span className="title-icon">🎙️</span>
          數位分析師語音中心
        </h2>
        <p className="panel-description">
          選擇您的專屬分析師，享受個人化的投資語音服務
        </p>
      </div>

      {/* 分析師選擇區域 */}
      <div className="analyst-selection">
        <h3 className="section-title">選擇分析師</h3>
        <div className="analyst-grid">
          {visibleAnalysts.map((analyst) => (
            <div
              key={analyst.id}
              className={`analyst-card ${selectedAnalystId === analyst.id ? 'selected' : ''} ${
                loadingAnalysts.has(analyst.id) ? 'loading' : ''
              }`}
              onClick={() => handleAnalystSelect(analyst.id)}
              style={{ borderColor: selectedAnalystId === analyst.id ? analyst.color : 'transparent' }}
            >
              <div className="analyst-icon" style={{ color: analyst.color }}>
                {analyst.icon}
              </div>
              <div className="analyst-info">
                <h4 className="analyst-name">{analyst.name}</h4>
                <p className="analyst-description">{analyst.description}</p>
                <div className="analyst-specialties">
                  {analyst.specialties.slice(0, 2).map((specialty) => (
                    <span key={specialty} className="specialty-tag">
                      {specialty}
                    </span>
                  ))}
                </div>
              </div>
              {loadingAnalysts.has(analyst.id) && (
                <div className="loading-indicator">
                  <div className="spinner"></div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 場景選擇區域 */}
      <div className="scenario-selection">
        <h3 className="section-title">語音場景</h3>
        <div className="scenario-tabs">
          {availableScenarios.map((scenario) => (
            <button
              key={scenario.id}
              className={`scenario-tab ${selectedScenario === scenario.id ? 'active' : ''}`}
              onClick={() => handleScenarioSelect(scenario.id)}
            >
              <span className="scenario-icon">{scenario.icon}</span>
              <span className="scenario-name">{scenario.name}</span>
            </button>
          ))}
        </div>
        
        {/* 場景描述 */}
        {VOICE_SCENARIOS.find(s => s.id === selectedScenario) && (
          <div className="scenario-description">
            <p>{VOICE_SCENARIOS.find(s => s.id === selectedScenario)?.description}</p>
          </div>
        )}
      </div>

      {/* 文字輸入區域 */}
      <div className="text-input-section">
        <h3 className="section-title">語音內容</h3>
        <div className="text-input-container">
          <textarea
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="輸入您希望分析師播報的內容，或使用上方場景的範例文字..."
            className="text-input"
            rows={4}
            maxLength={1000}
          />
          <div className="text-counter">
            {customText.length}/1000 字符
          </div>
        </div>
      </div>

      {/* 控制按鈕區域 */}
      <div className="control-section">
        <div className="main-controls">
          <button
            className="play-button primary"
            onClick={handlePlayAnalystVoice}
            disabled={!customText.trim() || loadingAnalysts.has(selectedAnalystId)}
          >
            <span className="button-icon">
              {loadingAnalysts.has(selectedAnalystId) ? '⏳' : '▶️'}
            </span>
            {loadingAnalysts.has(selectedAnalystId) ? '合成中...' : '開始播放'}
          </button>

          {isPlaying && (
            <button
              className="stop-button secondary"
              onClick={handleStopPlayback}
            >
              <span className="button-icon">⏹️</span>
              停止播放
            </button>
          )}
        </div>

        {/* 快速操作按鈕 */}
        {showQuickActions && (
          <div className="quick-actions">
            {enableQueueMode && (
              <button
                className="queue-button secondary"
                onClick={handleAddToQueue}
                disabled={!customText.trim()}
                title="加入播放佇列"
              >
                <span className="button-icon">➕</span>
                加入佇列
              </button>
            )}
            
            <button
              className="sample-button secondary"
              onClick={() => {
                const scenario = VOICE_SCENARIOS.find(s => s.id === selectedScenario);
                if (scenario) {
                  setCustomText(scenario.sampleText);
                }
              }}
              title="使用範例文字"
            >
              <span className="button-icon">📝</span>
              範例文字
            </button>
          </div>
        )}
      </div>

      {/* 語音播放器（當有音頻時顯示） */}
      {currentAudioUrl && (
        <div className="voice-player-section">
          <VoicePlayer
            text={customText}
            voiceId={analystVoiceConfig?.defaultVoiceId}
            autoPlay={true}
            showControls={true}
            onPlayStart={() => setIsPlaying(true)}
            onPlayEnd={() => {
              setIsPlaying(false);
              setCurrentPlaying(null);
              onPlayEnd?.(selectedAnalystId);
            }}
            onError={(error) => {
              console.error('播放錯誤:', error);
              handleStopPlayback();
            }}
          />
        </div>
      )}

      {/* 播放佇列顯示（如果啟用） */}
      {enableQueueMode && queue.length > 0 && (
        <div className="queue-section">
          <h3 className="section-title">
            播放佇列 ({queue.length} 項目)
          </h3>
          <div className="queue-list">
            {queue.slice(0, 3).map((item, index) => (
              <div key={item.id} className="queue-item">
                <span className="queue-index">{index + 1}</span>
                <span className="queue-analyst">
                  {ANALYSTS_CONFIG.find(a => a.id === item.analystId)?.icon}
                </span>
                <span className="queue-text">
                  {item.text.substring(0, 50)}
                  {item.text.length > 50 ? '...' : ''}
                </span>
              </div>
            ))}
            {queue.length > 3 && (
              <div className="queue-more">
                還有 {queue.length - 3} 個項目...
              </div>
            )}
          </div>
        </div>
      )}

      {/* 分析師統計（如果啟用） */}
      {showAnalystStats && (
        <div className="stats-section">
          <h3 className="section-title">使用統計</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">當前分析師</span>
              <span className="stat-value">{selectedAnalyst?.name}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">播放場景</span>
              <span className="stat-value">
                {VOICE_SCENARIOS.find(s => s.id === selectedScenario)?.name}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">佇列項目</span>
              <span className="stat-value">{queue.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalystVoicePanel;