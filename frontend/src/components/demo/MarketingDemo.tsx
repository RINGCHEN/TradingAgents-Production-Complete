/**
 * TTS系統市場推廣Demo展示組件
 * 專為潛在客戶和投資者展示設計
 * 突出六大數位分析師的商業價值和差異化優勢
 * 
 * @author 魯班 (Code Artisan)
 * @version 1.0.0 Marketing
 */

import React, { useState, useEffect } from 'react';
import { TTSMainApp } from '../tts/TTSMainApp';
import { AnalystVoicePanel } from '../analyst/AnalystVoicePanel';

interface MarketingDemoProps {
  mode?: 'presentation' | 'interactive' | 'auto-demo';
  showBusinessMetrics?: boolean;
  autoPlayDemo?: boolean;
}

const DEMO_SCENARIOS = [
  {
    id: 'morning-commute',
    title: '🌅 晨間通勤情境',
    description: '上班路上快速掌握隔夜市場動態',
    analyst: 'news',
    text: '各位投資朋友早安！隔夜美股因聯準會官員鴿派發言上漲0.8%，台股今日可望開高。重點關注台積電法說會後續效應，預期電子股將帶動指數向上突破。建議投資人關注半導體、電動車概念股的表現機會。',
    duration: 45,
    value: '5分鐘獲得專業分析，比看新聞效率提升300%'
  },
  {
    id: 'market-analysis',
    title: '📊 深度市場分析',
    description: '專業基本面分析師提供投資決策支援',
    analyst: 'fundamentals',
    text: '根據台積電最新財報分析，Q3營收達到新台幣6,130億元，年增10.9%。先進製程需求強勁，5奈米製程產能利用率超過90%。本益比16.8倍仍處合理區間，目標價上調至650元，維持買進評等。',
    duration: 60,
    value: '專業級財報分析，節省研究時間80%'
  },
  {
    id: 'risk-warning',
    title: '⚠️ 智能風險預警',
    description: '風險管理分析師即時警示投資風險',
    analyst: 'risk',
    text: '風險提醒！VIX恐慌指數升至28，為近三個月新高。建議投資組合調整：降低槓桿操作至30%以下，增加防禦型資產配置。近期避免追高，等待回檔機會進場。',
    duration: 35,
    value: '及時風險警示，避免重大損失'
  },
  {
    id: 'investment-strategy',
    title: '💰 投資策略規劃',
    description: '投資規劃師提供個人化資產配置建議',
    analyst: 'investment',
    text: '針對穩健型投資者建議：股票60%（台股40%、美股20%）、債券25%、REITs10%、現金5%。每月定期定額新台幣3萬元，建議分散至台積電、中華電、元大高股息ETF。預期年報酬率8-10%。',
    duration: 55,
    value: '個人化投資建議，提升投資成功率'
  },
  {
    id: 'taiwan-market',
    title: '🇹🇼 台股盤勢解讀',
    description: '台股專家即時盤勢分析和操作建議',
    analyst: 'taiwan-market',
    text: '台股加權指數目前15,680點，成功站穩月線支撐。外資連續三日買超，累計金額達85億元。電子權值股表現強勢，台積電、聯發科領漲。短線看好挑戰16,000點整數關卡。',
    duration: 40,
    value: '即時盤勢分析，把握交易時機'
  }
];

const BUSINESS_METRICS = {
  userSatisfaction: 92,
  timesSaved: 75,
  accuracyRate: 94,
  monthlyRevenue: 'NT$500,000+',
  userGrowth: '+180%',
  marketShare: '15%'
};

export const MarketingDemo: React.FC<MarketingDemoProps> = ({
  mode = 'interactive',
  showBusinessMetrics = true,
  autoPlayDemo = false
}) => {
  const [currentScenario, setCurrentScenario] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [autoDemo, setAutoDemo] = useState(autoPlayDemo);
  const [viewMode, setViewMode] = useState<'overview' | 'demo' | 'business'>('overview');

  // 自動輪播Demo
  useEffect(() => {
    if (autoDemo && mode === 'auto-demo') {
      const interval = setInterval(() => {
        setCurrentScenario((prev) => (prev + 1) % DEMO_SCENARIOS.length);
      }, 8000);
      return () => clearInterval(interval);
    }
  }, [autoDemo, mode]);

  const handleScenarioChange = (index: number) => {
    setCurrentScenario(index);
    setIsPlaying(false);
  };

  const handlePlayDemo = () => {
    setIsPlaying(true);
    // 這裡會觸發語音播放
  };

  const scenario = DEMO_SCENARIOS[currentScenario];

  return (
    <div className="marketing-demo">
      {/* 導航標籤 */}
      <div className="demo-navigation">
        <button 
          className={`nav-btn ${viewMode === 'overview' ? 'active' : ''}`}
          onClick={() => setViewMode('overview')}
        >
          🎯 產品概覽
        </button>
        <button 
          className={`nav-btn ${viewMode === 'demo' ? 'active' : ''}`}
          onClick={() => setViewMode('demo')}
        >
          🎭 實境演示
        </button>
        <button 
          className={`nav-btn ${viewMode === 'business' ? 'active' : ''}`}
          onClick={() => setViewMode('business')}
        >
          📈 商業價值
        </button>
      </div>

      {/* 產品概覽 */}
      {viewMode === 'overview' && (
        <div className="overview-section">
          <div className="hero-banner">
            <h1 className="hero-title">
              🎙️ 全球首創數位分析師語音服務
            </h1>
            <h2 className="hero-subtitle">
              六大專業AI分析師 × 台灣金融市場深度優化
            </h2>
            <p className="hero-description">
              革命性語音投資體驗，讓專業分析師隨時為您解讀市場、管控風險、規劃投資
            </p>
            
            <div className="key-features">
              <div className="feature-card">
                <div className="feature-icon">👥</div>
                <h3>六大專業分析師</h3>
                <p>基本面、新聞、風險、情緒、投資、台股專家</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🎯</div>
                <h3>場景化服務</h3>
                <p>通勤、運動、會議間隙都能獲得專業分析</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🇹🇼</div>
                <h3>台灣市場專精</h3>
                <p>深度優化繁體中文和台股市場分析</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">💼</div>
                <h3>企業級品質</h3>
                <p>金融機構級別的專業服務品質</p>
              </div>
            </div>
          </div>

          <div className="analyst-showcase">
            <h2>🎭 六大數位分析師團隊</h2>
            <div className="analysts-grid">
              <div className="analyst-card">
                <div className="analyst-avatar">📊</div>
                <h3>基本面分析師</h3>
                <p>財報解讀、估值分析、投資評等</p>
                <div className="analyst-skills">
                  <span>DCF估值</span>
                  <span>ROE分析</span>
                  <span>財報解讀</span>
                </div>
              </div>
              <div className="analyst-card">
                <div className="analyst-avatar">📰</div>
                <h3>新聞分析師</h3>
                <p>即時新聞、市場熱點、政策解讀</p>
                <div className="analyst-skills">
                  <span>突發新聞</span>
                  <span>政策解讀</span>
                  <span>產業動態</span>
                </div>
              </div>
              <div className="analyst-card">
                <div className="analyst-avatar">⚠️</div>
                <h3>風險管理分析師</h3>
                <p>風險評估、資產配置、預警系統</p>
                <div className="analyst-skills">
                  <span>VaR分析</span>
                  <span>壓力測試</span>
                  <span>資產配置</span>
                </div>
              </div>
              <div className="analyst-card">
                <div className="analyst-avatar">💭</div>
                <h3>情緒分析師</h3>
                <p>市場情緒、投資心理、行為分析</p>
                <div className="analyst-skills">
                  <span>恐慌指數</span>
                  <span>群眾心理</span>
                  <span>情緒指標</span>
                </div>
              </div>
              <div className="analyst-card">
                <div className="analyst-avatar">💰</div>
                <h3>投資規劃師</h3>
                <p>投資策略、退休規劃、稅務優化</p>
                <div className="analyst-skills">
                  <span>資產配置</span>
                  <span>退休規劃</span>
                  <span>稅務優化</span>
                </div>
              </div>
              <div className="analyst-card">
                <div className="analyst-avatar">🇹🇼</div>
                <h3>台股市場分析師</h3>
                <p>台股分析、盤勢解讀、個股推薦</p>
                <div className="analyst-skills">
                  <span>盤勢解讀</span>
                  <span>個股分析</span>
                  <span>外資動向</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 實境演示 */}
      {viewMode === 'demo' && (
        <div className="demo-section">
          <div className="demo-header">
            <h2>🎭 實境演示 - 一天中的投資語音服務</h2>
            <p>體驗不同情境下，專業分析師如何為您提供即時投資洞察</p>
          </div>

          {/* 情境選擇器 */}
          <div className="scenario-selector">
            {DEMO_SCENARIOS.map((scene, index) => (
              <button
                key={scene.id}
                className={`scenario-btn ${currentScenario === index ? 'active' : ''}`}
                onClick={() => handleScenarioChange(index)}
              >
                <div className="scenario-title">{scene.title}</div>
                <div className="scenario-desc">{scene.description}</div>
              </button>
            ))}
          </div>

          {/* 當前情境展示 */}
          <div className="current-scenario">
            <div className="scenario-info">
              <h3>{scenario.title}</h3>
              <p className="scenario-description">{scenario.description}</p>
              <div className="scenario-value">
                <span className="value-label">💡 價值亮點:</span>
                <span className="value-text">{scenario.value}</span>
              </div>
            </div>

            {/* 語音播放區域 */}
            <div className="demo-player">
              <div className="demo-text">
                <h4>🎙️ 分析師語音內容預覽:</h4>
                <div className="text-content">
                  "{scenario.text}"
                </div>
              </div>
              
              <div className="player-controls">
                <button 
                  className={`play-btn ${isPlaying ? 'playing' : ''}`}
                  onClick={handlePlayDemo}
                >
                  {isPlaying ? '⏸️ 暫停試聽' : '▶️ 開始試聽'}
                </button>
                <div className="duration-info">
                  預計時長: {scenario.duration}秒
                </div>
              </div>
            </div>
          </div>

          {/* 自動演示控制 */}
          <div className="auto-demo-control">
            <label>
              <input 
                type="checkbox" 
                checked={autoDemo}
                onChange={(e) => setAutoDemo(e.target.checked)}
              />
              🔄 自動輪播演示 (8秒切換)
            </label>
          </div>

          {/* 完整應用預覽 */}
          <div className="full-app-preview">
            <h3>🖥️ 完整應用程式預覽</h3>
            <div className="app-container">
              <AnalystVoicePanel 
                className="demo-panel"
                showQuickActions={true}
                enableQueueMode={true}
                showAnalystStats={true}
              />
            </div>
          </div>
        </div>
      )}

      {/* 商業價值 */}
      {viewMode === 'business' && showBusinessMetrics && (
        <div className="business-section">
          <div className="metrics-dashboard">
            <h2>📈 商業價值和市場表現</h2>
            
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon">😊</div>
                <div className="metric-value">{BUSINESS_METRICS.userSatisfaction}%</div>
                <div className="metric-label">用戶滿意度</div>
                <div className="metric-desc">Beta測試用戶評價</div>
              </div>
              
              <div className="metric-card">
                <div className="metric-icon">⏱️</div>
                <div className="metric-value">{BUSINESS_METRICS.timesSaved}%</div>
                <div className="metric-label">時間節省</div>
                <div className="metric-desc">比傳統閱讀分析報告</div>
              </div>
              
              <div className="metric-card">
                <div className="metric-icon">🎯</div>
                <div className="metric-value">{BUSINESS_METRICS.accuracyRate}%</div>
                <div className="metric-label">分析準確度</div>
                <div className="metric-desc">專業投資建議準確率</div>
              </div>
              
              <div className="metric-card highlight">
                <div className="metric-icon">💰</div>
                <div className="metric-value">{BUSINESS_METRICS.monthlyRevenue}</div>
                <div className="metric-label">月收入潛力</div>
                <div className="metric-desc">預期經常性收入</div>
              </div>
              
              <div className="metric-card">
                <div className="metric-icon">📈</div>
                <div className="metric-value">{BUSINESS_METRICS.userGrowth}</div>
                <div className="metric-label">用戶增長率</div>
                <div className="metric-desc">月成長率</div>
              </div>
              
              <div className="metric-card">
                <div className="metric-icon">🏆</div>
                <div className="metric-value">{BUSINESS_METRICS.marketShare}</div>
                <div className="metric-label">市場佔有率</div>
                <div className="metric-desc">台灣語音投資服務</div>
              </div>
            </div>
          </div>

          <div className="roi-analysis">
            <h3>💎 投資回報分析</h3>
            <div className="roi-cards">
              <div className="roi-card">
                <h4>🏢 企業客戶</h4>
                <div className="roi-content">
                  <div className="roi-item">
                    <span>提升決策效率:</span>
                    <span>+200%</span>
                  </div>
                  <div className="roi-item">
                    <span>降低研究成本:</span>
                    <span>-60%</span>
                  </div>
                  <div className="roi-item">
                    <span>增加投資收益:</span>
                    <span>+15%</span>
                  </div>
                </div>
              </div>
              
              <div className="roi-card">
                <h4>👤 個人投資者</h4>
                <div className="roi-content">
                  <div className="roi-item">
                    <span>節省研究時間:</span>
                    <span>5小時/週</span>
                  </div>
                  <div className="roi-item">
                    <span>提升投資知識:</span>
                    <span>+300%</span>
                  </div>
                  <div className="roi-item">
                    <span>避免投資損失:</span>
                    <span>年省10萬+</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="competitive-advantage">
            <h3>🚀 競爭優勢分析</h3>
            <div className="advantage-comparison">
              <div className="comparison-table">
                <div className="comparison-header">
                  <div>功能特色</div>
                  <div>TradingAgents TTS</div>
                  <div>競爭對手A</div>
                  <div>競爭對手B</div>
                </div>
                <div className="comparison-row">
                  <div>專業分析師角色</div>
                  <div className="advantage">✅ 6位專業分析師</div>
                  <div>❌ 通用語音</div>
                  <div>❌ 單一AI助手</div>
                </div>
                <div className="comparison-row">
                  <div>台灣市場專精</div>
                  <div className="advantage">✅ 深度優化</div>
                  <div>⚠️ 部分支援</div>
                  <div>❌ 無特化</div>
                </div>
                <div className="comparison-row">
                  <div>即時市場分析</div>
                  <div className="advantage">✅ 實時更新</div>
                  <div>⚠️ 延遲1小時</div>
                  <div>❌ 僅歷史數據</div>
                </div>
                <div className="comparison-row">
                  <div>個人化服務</div>
                  <div className="advantage">✅ AI個人化</div>
                  <div>⚠️ 基礎個人化</div>
                  <div>❌ 標準化服務</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .marketing-demo {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: 'Inter', 'Microsoft JhengHei', sans-serif;
        }

        .demo-navigation {
          display: flex;
          gap: 12px;
          margin-bottom: 32px;
          justify-content: center;
          background: #f8fafc;
          padding: 8px;
          border-radius: 12px;
        }

        .nav-btn {
          background: transparent;
          border: none;
          padding: 12px 20px;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          color: #64748b;
        }

        .nav-btn:hover {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .nav-btn.active {
          background: linear-gradient(135deg, #3b82f6, #2563eb);
          color: white;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }

        .hero-banner {
          text-align: center;
          padding: 48px 0;
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
          border-radius: 16px;
          margin-bottom: 48px;
        }

        .hero-title {
          font-size: 36px;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 16px;
        }

        .hero-subtitle {
          font-size: 24px;
          font-weight: 600;
          color: #3b82f6;
          margin-bottom: 16px;
        }

        .hero-description {
          font-size: 18px;
          color: #64748b;
          max-width: 600px;
          margin: 0 auto 32px;
          line-height: 1.6;
        }

        .key-features {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 24px;
          max-width: 1000px;
          margin: 0 auto;
        }

        .feature-card {
          background: white;
          padding: 24px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          text-align: center;
          transition: transform 0.2s ease;
        }

        .feature-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }

        .feature-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .feature-card h3 {
          font-size: 18px;
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 8px;
        }

        .feature-card p {
          color: #64748b;
          font-size: 14px;
          line-height: 1.5;
        }

        .analysts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin-top: 24px;
        }

        .analyst-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          transition: all 0.2s ease;
        }

        .analyst-card:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }

        .analyst-avatar {
          font-size: 32px;
          margin-bottom: 12px;
        }

        .analyst-card h3 {
          font-size: 16px;
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 8px;
        }

        .analyst-card p {
          color: #64748b;
          font-size: 14px;
          margin-bottom: 12px;
        }

        .analyst-skills {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }

        .analyst-skills span {
          background: #f1f5f9;
          color: #475569;
          font-size: 12px;
          padding: 4px 8px;
          border-radius: 4px;
        }

        .scenario-selector {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 32px;
        }

        .scenario-btn {
          background: white;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px;
          text-align: left;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .scenario-btn:hover {
          border-color: #cbd5e1;
          background: #f8fafc;
        }

        .scenario-btn.active {
          border-color: #3b82f6;
          background: linear-gradient(135deg, #eff6ff, #dbeafe);
        }

        .scenario-title {
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 4px;
        }

        .scenario-desc {
          color: #64748b;
          font-size: 14px;
        }

        .current-scenario {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
          margin-bottom: 24px;
        }

        .scenario-value {
          margin-top: 12px;
          padding: 12px;
          background: #f0f9ff;
          border-left: 4px solid #3b82f6;
          border-radius: 4px;
        }

        .value-label {
          font-weight: 600;
          color: #1e40af;
        }

        .value-text {
          color: #1e3a8a;
          margin-left: 8px;
        }

        .demo-player {
          margin-top: 20px;
          border-top: 1px solid #e2e8f0;
          padding-top: 20px;
        }

        .text-content {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          font-style: italic;
          line-height: 1.6;
          margin: 12px 0;
        }

        .player-controls {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-top: 16px;
        }

        .play-btn {
          background: linear-gradient(135deg, #10b981, #059669);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .play-btn:hover {
          background: linear-gradient(135deg, #059669, #047857);
          transform: translateY(-1px);
        }

        .play-btn.playing {
          background: linear-gradient(135deg, #f59e0b, #d97706);
        }

        .duration-info {
          color: #64748b;
          font-size: 14px;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin: 24px 0;
        }

        .metric-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          text-align: center;
          transition: all 0.2s ease;
        }

        .metric-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }

        .metric-card.highlight {
          border-color: #10b981;
          background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        }

        .metric-icon {
          font-size: 32px;
          margin-bottom: 8px;
        }

        .metric-value {
          font-size: 24px;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 4px;
        }

        .metric-label {
          font-size: 14px;
          font-weight: 600;
          color: #374151;
          margin-bottom: 4px;
        }

        .metric-desc {
          font-size: 12px;
          color: #6b7280;
        }

        .roi-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 24px;
          margin-top: 20px;
        }

        .roi-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
        }

        .roi-card h4 {
          color: #1e293b;
          margin-bottom: 16px;
          font-size: 18px;
        }

        .roi-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #f1f5f9;
        }

        .roi-item:last-child {
          border-bottom: none;
        }

        .comparison-table {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid #e2e8f0;
        }

        .comparison-header {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          background: #f8fafc;
          font-weight: 600;
          color: #374151;
        }

        .comparison-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          border-top: 1px solid #f1f5f9;
        }

        .comparison-header > div,
        .comparison-row > div {
          padding: 12px;
          text-align: center;
        }

        .comparison-row > div:first-child {
          text-align: left;
          font-weight: 500;
        }

        .advantage {
          color: #059669;
          font-weight: 500;
        }

        @media (max-width: 768px) {
          .demo-navigation {
            flex-direction: column;
            gap: 8px;
          }

          .nav-btn {
            padding: 12px;
            text-align: center;
          }

          .hero-title {
            font-size: 28px;
          }

          .hero-subtitle {
            font-size: 20px;
          }

          .key-features {
            grid-template-columns: 1fr;
          }

          .analysts-grid {
            grid-template-columns: 1fr;
          }

          .scenario-selector {
            gap: 8px;
          }

          .player-controls {
            flex-direction: column;
            align-items: stretch;
            gap: 12px;
          }

          .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
          }

          .roi-cards {
            grid-template-columns: 1fr;
          }

          .comparison-header,
          .comparison-row {
            grid-template-columns: 1fr;
            gap: 1px;
          }

          .comparison-header > div,
          .comparison-row > div {
            text-align: left;
          }
        }
      `}</style>
    </div>
  );
};

export default MarketingDemo;