import React, { useState, useEffect } from 'react';
import { PersonalityTestResult } from '../services/PersonalityTestAPI';
import './ConversionCTA.css';

interface ConversionCTAProps {
  result: PersonalityTestResult;
  variant: 'A' | 'B';
  onRegisterClick: () => void;
  onSecondaryAction?: () => void;
}

interface PersonalityBenefit {
  icon: string;
  title: string;
  description: string;
}

const ConversionCTA: React.FC<ConversionCTAProps> = ({
  result,
  variant,
  onRegisterClick,
  onSecondaryAction
}) => {
  const [showUrgency, setShowUrgency] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5分鐘倒計時

  // 根據人格類型定制化的好處
  const getPersonalizedBenefits = (): PersonalityBenefit[] => {
    const personalityType = result.personality_type.type;
    
    const benefitsByType: Record<string, PersonalityBenefit[]> = {
      'conservative': [
        { icon: '🛡️', title: '風險控制策略', description: '專為保守型投資者設計的風險管理方案' },
        { icon: '📊', title: '穩健投資組合', description: '基於你的風險偏好的穩定收益策略' },
        { icon: '🎯', title: '個人化建議', description: '符合你投資風格的專業分析師推薦' },
        { icon: '📈', title: '長期規劃', description: '適合保守投資者的長期財富增長計劃' }
      ],
      'aggressive': [
        { icon: '🚀', title: '高收益機會', description: '發掘適合積極投資者的高潛力標的' },
        { icon: '⚡', title: '即時市場警報', description: '第一時間獲得重要市場動態和交易機會' },
        { icon: '🎯', title: '專業分析', description: '深度技術分析和基本面研究報告' },
        { icon: '💎', title: '獨家策略', description: '專為積極投資者設計的進階交易策略' }
      ],
      'balanced': [
        { icon: '⚖️', title: '平衡投資組合', description: '風險與收益完美平衡的投資方案' },
        { icon: '🎯', title: '多元化策略', description: '涵蓋不同資產類別的分散投資建議' },
        { icon: '📊', title: '智能配置', description: '基於你的風險承受度的資產配置' },
        { icon: '🔄', title: '動態調整', description: '根據市場變化自動調整投資策略' }
      ]
    };

    return benefitsByType[personalityType] || benefitsByType['balanced'];
  };

  // 社會證明數據
  const getSocialProof = () => {
    const proofData = {
      totalUsers: '50,000+',
      avgReturn: '15.2%',
      satisfaction: '4.8/5',
      successRate: '87%'
    };

    return proofData;
  };

  // 緊迫感倒計時
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setShowUrgency(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const benefits = getPersonalizedBenefits();
  const socialProof = getSocialProof();

  return (
    <div className={`conversion-cta variant-${variant}`}>
      {/* 變體A：強調個人化 */}
      {variant === 'A' && (
        <div className="cta-content">
          <div className="cta-header">
            <div className="personality-badge">
              <span className="badge-icon">{result.personality_type.icon || '🧠'}</span>
              <div className="badge-text">
                <h3 className="cta-title">
                  專為 <span className="highlight">{result.personality_type.display_name}</span> 設計
                </h3>
                <p className="cta-subtitle">
                  你擊敗了 <strong>{result.percentile}%</strong> 的投資者，現在獲得更專業的投資建議！
                </p>
              </div>
            </div>
          </div>

          <div className="benefits-grid">
            {benefits.map((benefit, index) => (
              <div key={index} className="benefit-item">
                <div className="benefit-icon">{benefit.icon}</div>
                <div className="benefit-content">
                  <h4 className="benefit-title">{benefit.title}</h4>
                  <p className="benefit-description">{benefit.description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="social-proof">
            <div className="proof-stats">
              <div className="stat-item">
                <span className="stat-number">{socialProof.totalUsers}</span>
                <span className="stat-label">用戶信賴</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{socialProof.avgReturn}</span>
                <span className="stat-label">平均年化收益</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{socialProof.satisfaction}</span>
                <span className="stat-label">用戶評分</span>
              </div>
            </div>
          </div>

          <div className="cta-actions">
            <button 
              type="button"
              className="primary-cta"
              onClick={onRegisterClick}
            >
              <span className="cta-text">免費獲得專屬投資建議</span>
              <span className="cta-subtext">基於你的 {result.personality_type.display_name} 特質</span>
            </button>
            
            {onSecondaryAction && (
              <button 
                type="button"
                className="secondary-cta"
                onClick={onSecondaryAction}
              >
                了解更多詳情
              </button>
            )}
          </div>

          {timeLeft > 0 && (
            <div className="urgency-timer">
              <span className="timer-icon">⏰</span>
              <span className="timer-text">
                限時優惠還剩 <strong>{formatTime(timeLeft)}</strong>
              </span>
            </div>
          )}
        </div>
      )}

      {/* 變體B：強調收益和成功 */}
      {variant === 'B' && (
        <div className="cta-content">
          <div className="cta-header">
            <h3 className="cta-title">
              🎉 恭喜！你的投資潛力超越 <span className="highlight">{result.percentile}%</span> 的人
            </h3>
            <p className="cta-subtitle">
              現在就解鎖你的完整投資潛力，加入成功投資者的行列
            </p>
          </div>

          <div className="success-showcase">
            <div className="showcase-item">
              <div className="showcase-icon">📈</div>
              <div className="showcase-content">
                <h4>平均年化收益 {socialProof.avgReturn}</h4>
                <p>我們的用戶平均獲得超過市場的投資回報</p>
              </div>
            </div>
            <div className="showcase-item">
              <div className="showcase-icon">🏆</div>
              <div className="showcase-content">
                <h4>{socialProof.successRate} 成功率</h4>
                <p>87%的用戶在使用我們的建議後獲得正收益</p>
              </div>
            </div>
          </div>

          <div className="benefits-list">
            <h4 className="benefits-title">立即獲得：</h4>
            <ul className="benefits-items">
              {benefits.map((benefit, index) => (
                <li key={index} className="benefit-item">
                  <span className="benefit-check">✅</span>
                  <span className="benefit-text">
                    <strong>{benefit.title}</strong> - {benefit.description}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="cta-actions">
            <button 
              type="button"
              className="primary-cta"
              onClick={onRegisterClick}
            >
              <span className="cta-text">立即免費註冊</span>
              <span className="cta-subtext">開始你的成功投資之路</span>
            </button>
            
            <div className="guarantee">
              <span className="guarantee-icon">🛡️</span>
              <span className="guarantee-text">30天滿意保證，不滿意全額退款</span>
            </div>
          </div>

          {showUrgency && (
            <div className="urgency-banner">
              <span className="urgency-icon">🔥</span>
              <span className="urgency-text">
                限時免費！僅限前1000名用戶
              </span>
            </div>
          )}
        </div>
      )}

      <div className="trust-indicators">
        <div className="trust-item">
          <span className="trust-icon">🔒</span>
          <span className="trust-text">資料安全保護</span>
        </div>
        <div className="trust-item">
          <span className="trust-icon">📱</span>
          <span className="trust-text">隨時隨地使用</span>
        </div>
        <div className="trust-item">
          <span className="trust-icon">🎯</span>
          <span className="trust-text">個人化建議</span>
        </div>
      </div>
    </div>
  );
};

export default ConversionCTA;