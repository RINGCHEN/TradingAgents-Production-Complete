import React from 'react';
import { MemberTier } from '../services/AuthService';
import './SubscriptionPlanCard.css';

interface SubscriptionPlanCardProps {
  tier: MemberTier;
  name: string;
  price: number;
  currency: string;
  period: string;
  features: string[];
  limitations?: string[];
  popular?: boolean;
  current?: boolean;
  onSelect: () => void;
  disabled?: boolean;
}

const SubscriptionPlanCard: React.FC<SubscriptionPlanCardProps> = ({
  tier,
  name,
  price,
  currency,
  period,
  features,
  limitations = [],
  popular = false,
  current = false,
  onSelect,
  disabled = false
}) => {
  
  const getCardClassName = () => {
    let className = 'subscription-plan-card';
    if (popular) className += ' popular';
    if (current) className += ' current';
    if (disabled) className += ' disabled';
    return className;
  };

  const getButtonText = () => {
    if (current) return '目前方案';
    if (tier === MemberTier.FREE) return '選擇免費方案';
    return `升級到 ${name}`;
  };

  const getButtonClassName = () => {
    if (current) return 'btn-current';
    if (tier === MemberTier.FREE) return 'btn-secondary';
    return 'btn-primary';
  };

  return (
    <div className={getCardClassName()}>
      {popular && <div className="popular-badge">最受歡迎</div>}
      
      <div className="plan-header">
        <div className="plan-name">{name}</div>
        <div className="plan-price">
          {price === 0 ? (
            <span className="free-price">免費</span>
          ) : (
            <>
              <span className="currency">{currency}</span>
              <span className="amount">${price?.toLocaleString() || '0'}</span>
              <span className="period">/{period === 'month' ? '月' : '年'}</span>
            </>
          )}
        </div>
      </div>

      <div className="plan-features">
        <div className="features-list">
          {(features || []).map((feature, index) => (
            <div key={index} className="feature-item">
              <span className="feature-icon">✓</span>
              <span className="feature-text">{feature}</span>
            </div>
          ))}
        </div>

        {(limitations || []).length > 0 && (
          <div className="limitations-list">
            {(limitations || []).map((limitation, index) => (
              <div key={index} className="limitation-item">
                <span className="limitation-icon">✗</span>
                <span className="limitation-text">{limitation}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="plan-action">
        <button
          className={`plan-button ${getButtonClassName()}`}
          onClick={onSelect}
          disabled={disabled || current}
        >
          {disabled ? '處理中...' : getButtonText()}
        </button>
      </div>

      {tier !== MemberTier.FREE && (
        <div className="plan-footer">
          <div className="payment-info">
            <span className="payment-icon">🔒</span>
            <span className="payment-text">PayUni 安全支付</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubscriptionPlanCard;