import React, { useState, useEffect } from 'react';
import { User } from '../../services/AuthService';
import UpgradePromptComponent from './UpgradePromptComponent';
import './UpgradePromptComponent.css';

/**
 * 4層級用戶分級渲染組件 - 配合GEMINI後端API改造
 * 根據用戶等級顯示不同程度的投資分析內容
 */

interface ReplayDecisionResponse {
  user_tier: 'visitor' | 'trial' | 'free' | 'paid';
  trial_days_remaining?: number;
  analysis: {
    technical_analysis: string;
    fundamental_analysis: string;
    news_sentiment: string;
    recommendation?: {
      action: 'buy' | 'sell' | 'hold';
      confidence: number;
      target_price?: number;
      reasoning: string;
    };
  };
  upgrade_prompt?: string | {
    title: string;
    value_prop: string;
    cta: string;
  };
}

interface TieredReplayDecisionProps {
  stockSymbol: string;
  user?: User;
  className?: string;
}

const TieredReplayDecision: React.FC<TieredReplayDecisionProps> = ({
  stockSymbol,
  user,
  className = ''
}) => {
  const [data, setData] = useState<ReplayDecisionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 獲取分級分析數據
  const fetchReplayDecision = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('authToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/replay/decision?stock_symbol=${stockSymbol}`,
        { headers }
      );

      if (!response.ok) {
        throw new Error(`API錯誤: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取分析數據失敗');
      console.error('獲取分析數據錯誤:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (stockSymbol) {
      fetchReplayDecision();
    }
  }, [stockSymbol]);

  // 訪客體驗UI
  const renderVisitorView = () => (
    <div className="tiered-analysis visitor-tier">
      <div className="demo-banner">
        <h3>🎯 AI投資分析演示</h3>
        <p>體驗我們強大的AI分析能力，立即註冊享受7天完整功能！</p>
      </div>
      
      <div className="demo-analysis">
        <h4>📊 演示分析結果</h4>
        <div className="analysis-content">
          <div className="demo-section">
            <strong>技術分析:</strong>
            <p>這是一個演示案例，顯示技術指標分析過程...</p>
          </div>
          <div className="demo-section">
            <strong>基本面分析:</strong>
            <p>演示基本面指標分析，包含財務比率評估...</p>
          </div>
        </div>
      </div>

      {/* 結構化升級提示區域 */}
      <UpgradePromptComponent 
        upgradePrompt={data?.upgrade_prompt}
        userTier={data?.user_tier}
        className="visitor-upgrade-prompt"
      />
    </div>
  );

  // 試用期體驗UI
  const renderTrialView = () => (
    <div className="tiered-analysis trial-tier">
      <div className="trial-banner">
        <div className="trial-status">
          ⏰ 試用期剩餘 <strong>{data?.trial_days_remaining || 0}</strong> 天
        </div>
        <p>享受完整AI投資分析功能，建立您的投資習慣！</p>
      </div>

      <div className="full-analysis">
        <h4>📈 完整投資分析</h4>
        
        {/* 技術分析 */}
        <div className="analysis-section">
          <h5>🔍 技術分析</h5>
          <p>{data?.analysis.technical_analysis}</p>
        </div>

        {/* 基本面分析 */}
        <div className="analysis-section">
          <h5>📊 基本面分析</h5>
          <p>{data?.analysis.fundamental_analysis}</p>
        </div>

        {/* 新聞情感 */}
        <div className="analysis-section">
          <h5>📰 新聞情感分析</h5>
          <p>{data?.analysis.news_sentiment}</p>
        </div>

        {/* 投資建議 - 試用期完整顯示 */}
        {data?.analysis.recommendation && (
          <div className="recommendation-section highlight">
            <h5>🎯 AI投資建議</h5>
            <div className="recommendation-content">
              <div className="action-badge">
                操作建議: <strong className={`action-${data.analysis.recommendation.action}`}>
                  {data.analysis.recommendation.action === 'buy' ? '買入' : 
                   data.analysis.recommendation.action === 'sell' ? '賣出' : '持有'}
                </strong>
              </div>
              <div className="confidence">
                信心度: <strong>{data.analysis.recommendation.confidence}%</strong>
              </div>
              {data.analysis.recommendation.target_price && (
                <div className="target-price">
                  目標價位: <strong>NT$ {data.analysis.recommendation.target_price}</strong>
                </div>
              )}
              <div className="reasoning">
                <strong>分析推理:</strong>
                <p>{data.analysis.recommendation.reasoning}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="trial-reminder">
        <div className="reminder-content">
          <h4>💎 繼續享受完整功能？</h4>
          <p>試用期結束後，升級為付費會員持續獲得專業投資建議</p>
          <button 
            className="btn btn-primary upgrade-btn"
            onClick={() => window.location.href = '/pricing'}
          >
            立即升級
          </button>
        </div>
      </div>
    </div>
  );

  // 免費會員體驗UI - 隱藏核心建議
  const renderFreeView = () => (
    <div className="tiered-analysis free-tier">
      <div className="free-banner">
        <h3>📚 投資學習中心</h3>
        <p>查看分析過程，學習投資知識，升級獲取專業建議</p>
      </div>

      <div className="limited-analysis">
        {/* 技術分析 - 可見 */}
        <div className="analysis-section">
          <h5>🔍 技術分析過程</h5>
          <p>{data?.analysis.technical_analysis}</p>
        </div>

        {/* 基本面分析 - 可見 */}
        <div className="analysis-section">
          <h5>📊 基本面分析過程</h5>
          <p>{data?.analysis.fundamental_analysis}</p>
        </div>

        {/* 新聞情感 - 可見 */}
        <div className="analysis-section">
          <h5>📰 市場情感分析</h5>
          <p>{data?.analysis.news_sentiment}</p>
        </div>

        {/* 投資建議 - 被隱藏，顯示結構化升級提示 */}
        <div className="locked-recommendation">
          <div className="locked-content">
            <div className="lock-icon">🔒</div>
            <UpgradePromptComponent 
              upgradePrompt={data?.upgrade_prompt}
              userTier={data?.user_tier}
              className="embedded-upgrade-prompt"
            />
          </div>
        </div>
      </div>

      <div className="educational-content">
        <h4>📖 投資教育內容</h4>
        <p>繼續學習投資分析技巧，提升您的投資決策能力</p>
      </div>
    </div>
  );

  // 付費會員完整體驗UI
  const renderPaidView = () => (
    <div className="tiered-analysis paid-tier">
      <div className="paid-banner">
        <h3>💎 專業投資分析</h3>
        <p>完整的AI投資分析服務，助您做出明智投資決策</p>
      </div>

      <div className="premium-analysis">
        {/* 技術分析 */}
        <div className="analysis-section">
          <h5>🔍 技術分析</h5>
          <p>{data?.analysis.technical_analysis}</p>
        </div>

        {/* 基本面分析 */}
        <div className="analysis-section">
          <h5>📊 基本面分析</h5>
          <p>{data?.analysis.fundamental_analysis}</p>
        </div>

        {/* 新聞情感 */}
        <div className="analysis-section">
          <h5>📰 新聞情感分析</h5>
          <p>{data?.analysis.news_sentiment}</p>
        </div>

        {/* 投資建議 - 完整顯示 */}
        {data?.analysis.recommendation && (
          <div className="recommendation-section premium">
            <h5>🎯 專業投資建議</h5>
            <div className="recommendation-content">
              <div className="action-badge premium">
                操作建議: <strong className={`action-${data.analysis.recommendation.action}`}>
                  {data.analysis.recommendation.action === 'buy' ? '買入' : 
                   data.analysis.recommendation.action === 'sell' ? '賣出' : '持有'}
                </strong>
              </div>
              <div className="confidence">
                AI信心度: <strong>{data.analysis.recommendation.confidence}%</strong>
              </div>
              {data.analysis.recommendation.target_price && (
                <div className="target-price">
                  目標價位: <strong>NT$ {data.analysis.recommendation.target_price}</strong>
                </div>
              )}
              <div className="reasoning">
                <strong>詳細分析推理:</strong>
                <p>{data.analysis.recommendation.reasoning}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="premium-features">
        <h4>🌟 專業會員特權</h4>
        <div className="features-grid">
          <div className="feature-item">
            <strong>🔄 實時更新</strong>
            <p>市場變化即時反映</p>
          </div>
          <div className="feature-item">
            <strong>📱 移動通知</strong>
            <p>重要訊號推送提醒</p>
          </div>
          <div className="feature-item">
            <strong>📈 組合建議</strong>
            <p>個人化投資組合</p>
          </div>
        </div>
      </div>
    </div>
  );

  // 登入提示UI
  const renderLoginPrompt = () => (
    <div className="tiered-analysis login-required">
      <div className="login-prompt">
        <h3>🔐 請先登入</h3>
        <p>登入後享受個人化AI投資分析服務</p>
        <button 
          className="btn btn-primary login-btn"
          onClick={() => window.location.href = '/auth'}
        >
          立即登入
        </button>
      </div>
    </div>
  );

  // 載入狀態
  const renderLoading = () => (
    <div className="tiered-analysis loading">
      <div className="analysis-loader">
        <div className="loader-animation"></div>
        <p>AI正在分析中...</p>
      </div>
    </div>
  );

  // 錯誤狀態
  const renderError = () => (
    <div className="tiered-analysis error">
      <div className="error-content">
        <h4>❌ 載入失敗</h4>
        <p>{error}</p>
        <button 
          className="btn btn-secondary retry-btn"
          onClick={fetchReplayDecision}
        >
          重新載入
        </button>
      </div>
    </div>
  );

  // 主要渲染邏輯
  const renderByUserTier = () => {
    if (loading) return renderLoading();
    if (error) return renderError();
    if (!data) return renderLoginPrompt();

    switch (data.user_tier) {
      case 'visitor':
        return renderVisitorView();
      case 'trial':
        return renderTrialView();
      case 'free':
        return renderFreeView();
      case 'paid':
        return renderPaidView();
      default:
        return renderLoginPrompt();
    }
  };

  return (
    <div className={`tiered-replay-decision ${className}`}>
      <div className="analysis-header">
        <h2>📊 {stockSymbol} AI投資決策復盤</h2>
      </div>
      {renderByUserTier()}
    </div>
  );
};

export default TieredReplayDecision;