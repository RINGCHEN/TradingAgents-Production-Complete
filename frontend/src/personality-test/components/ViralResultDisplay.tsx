import React, { useState, useEffect } from 'react';
import './ViralResultDisplay.css';
import PersonalityRadarChart from './PersonalityRadarChart';
import SocialShareButtons from './SocialShareButtons';

interface ViralElements {
  title: string;
  shock_description: string;
  celebrity_match: string;
  extreme_trait: string;
  percentile: number;
  comparison_text: string;
  extreme_scores: {
    risk_level: string;
    risk_description: string;
    emotion_level: string;
    emotion_description: string;
    analysis_level: string;
    analysis_description: string;
  };
  share_hooks: string[];
  challenge_friends: string;
}

interface ViralResultDisplayProps {
  personalityType: {
    type: string;
    display_name: string;
    icon: string;
    description: string;
  };
  dimensionScores: {
    risk_tolerance: number;
    emotional_control: number;
    analytical_thinking: number;
    market_sensitivity: number;
    long_term_vision: number;
  };
  viralElements: ViralElements;
  onShare: (platform: string, content: string) => void;
  onRegisterClick: () => void;
}

export const ViralResultDisplay: React.FC<ViralResultDisplayProps> = ({
  personalityType,
  dimensionScores,
  viralElements,
  onShare,
  onRegisterClick
}) => {
  const [showShockReveal, setShowShockReveal] = useState(false);
  const [currentHookIndex, setCurrentHookIndex] = useState(0);

  useEffect(() => {
    // 延遲顯示震撼揭示效果
    const timer = setTimeout(() => {
      setShowShockReveal(true);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // 輪播分享鉤子
    const interval = setInterval(() => {
      setCurrentHookIndex((prev) => (prev + 1) % viralElements.share_hooks.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [viralElements.share_hooks.length]);


  return (
    <div className="viral-result-display">
      {/* 震撼標題區域 */}
      <div className={`shock-header ${showShockReveal ? 'revealed' : ''}`}>
        <div className="personality-icon-large">
          {personalityType.icon}
        </div>
        <h1 className="viral-title">
          {viralElements.title}
        </h1>
        <div className="percentile-shock">
          <span className="percentile-number">{viralElements.percentile}%</span>
          <span className="percentile-text">{viralElements.comparison_text}</span>
        </div>
      </div>

      {/* 極端特質展示 */}
      <div className="extreme-traits-section">
        <h2>🔥 你的極端投資特質</h2>
        <div className="extreme-traits-grid">
          <div className="extreme-trait-card risk">
            <div className="trait-icon">🎯</div>
            <div className="trait-title">風險承受度</div>
            <div className="trait-level">{viralElements.extreme_scores.risk_level}</div>
            <div className="trait-description">{viralElements.extreme_scores.risk_description}</div>
          </div>
          
          <div className="extreme-trait-card emotion">
            <div className="trait-icon">🧠</div>
            <div className="trait-title">情緒控制力</div>
            <div className="trait-level">{viralElements.extreme_scores.emotion_level}</div>
            <div className="trait-description">{viralElements.extreme_scores.emotion_description}</div>
          </div>
          
          <div className="extreme-trait-card analysis">
            <div className="trait-icon">📊</div>
            <div className="trait-title">分析能力</div>
            <div className="trait-level">{viralElements.extreme_scores.analysis_level}</div>
            <div className="trait-description">{viralElements.extreme_scores.analysis_description}</div>
          </div>
        </div>
      </div>

      {/* 名人比較區域 */}
      <div className="celebrity-comparison">
        <h3>🌟 投資風格名人比較</h3>
        <div className="celebrity-match">
          <div className="celebrity-text">{viralElements.celebrity_match}</div>
          <div className="extreme-trait-highlight">{viralElements.extreme_trait}</div>
        </div>
      </div>

      {/* 雷達圖 */}
      <div className="radar-chart-section">
        <h3>📡 你的投資人格雷達圖</h3>
        <PersonalityRadarChart scores={dimensionScores} />
      </div>

      {/* 震撼描述 */}
      <div className="shock-description">
        <h3>💀 殘酷真相</h3>
        <p className="description-text">{viralElements.shock_description}</p>
      </div>

      {/* 病毒式分享區域 */}
      <div className="viral-share-section">
        <h3>🚀 挑戰你的朋友</h3>
        <div className="rotating-hook">
          <p className="share-hook">{viralElements.share_hooks[currentHookIndex]}</p>
        </div>
        <div className="challenge-text">
          <p>{viralElements.challenge_friends}</p>
        </div>
        
        <SocialShareButtons
          shareData={{
            image_url: '',
            share_text: viralElements.share_hooks[currentHookIndex],
            share_url: window.location.href,
            result_id: 'viral-result'
          }}
          onShareComplete={(platform, success) => {
            if (success) {
              onShare(platform, viralElements.share_hooks[currentHookIndex]);
            }
          }}
        />
      </div>

      {/* 強力CTA區域 */}
      <div className="viral-cta-section">
        <div className="cta-card">
          <h3>🎯 想要更深入的投資分析？</h3>
          <p className="cta-description">
            基於你的 <strong>{personalityType.display_name}</strong> 特質，
            我們為你準備了專屬的投資策略和阿爾法洞察！
          </p>
          
          <div className="cta-benefits">
            <div className="benefit-item">
              <span className="benefit-icon">🧠</span>
              <span>個性化投資建議</span>
            </div>
            <div className="benefit-item">
              <span className="benefit-icon">📈</span>
              <span>專業分析師洞察</span>
            </div>
            <div className="benefit-item">
              <span className="benefit-icon">💎</span>
              <span>阿爾法級別策略</span>
            </div>
            <div className="benefit-item">
              <span className="benefit-icon">🎯</span>
              <span>實時市場警報</span>
            </div>
          </div>
          
          <button 
            className="viral-cta-button"
            onClick={onRegisterClick}
          >
            🚀 免費獲得專屬投資策略
          </button>
          
          <p className="cta-urgency">
            ⚡ 限時免費！只有前1000名{personalityType.display_name}投資者可享受
          </p>
        </div>
      </div>

      {/* 社交證明 */}
      <div className="social-proof">
        <div className="proof-stats">
          <div className="stat-item">
            <span className="stat-number">50,000+</span>
            <span className="stat-label">已測試</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">4.9/5</span>
            <span className="stat-label">準確度</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">95%</span>
            <span className="stat-label">推薦率</span>
          </div>
        </div>
      </div>
    </div>
  );
};