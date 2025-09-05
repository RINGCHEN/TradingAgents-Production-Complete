import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { redirectToPayUniPayment } from '../services/PayUniService';
import './ProfessionalPricingPage.css';

// 開發模式下導入測試工具
if (process.env.NODE_ENV === 'development') {
  import('../utils/testProfessionalPricing');
}

/**
 * 專業級定價頁面 - 符合不老傳說品牌形象
 * 集成 PayUni 支付系統
 */

interface PricingPlan {
  id: string;
  name: string;
  displayName: string;
  monthlyPrice: number;
  yearlyPrice: number;
  features: string[];
  popular?: boolean;
  description: string;
  color: string;
  icon: string;
  apiQuota: number;
  analysisTypes: string[];
  support: string;
}

const pricingPlans: PricingPlan[] = [
  {
    id: 'free',
    name: '探索者方案',
    displayName: '免費體驗',
    monthlyPrice: 0,
    yearlyPrice: 0,
    description: '適合投資新手，體驗AI分析功能',
    color: 'from-gray-400 to-gray-600',
    icon: '🎯',
    apiQuota: 5,
    analysisTypes: ['基礎分析'],
    support: '社群支援',
    features: [
      '基礎股票分析',
      '每日5次查詢',
      '基本技術指標',
      '社群討論區',
      '投資教學資源'
    ]
  },
  {
    id: 'gold',
    name: '專業投資者',
    displayName: '黃金方案',
    monthlyPrice: 1999,
    yearlyPrice: 19990,
    description: '專業投資者的最佳選擇，全方位分析服務',
    color: 'from-yellow-400 to-orange-500',
    icon: '👑',
    apiQuota: 50,
    analysisTypes: ['基本面', '技術面', '情緒分析'],
    support: '優先客服',
    popular: true,
    features: [
      '完整基本面分析',
      '每日50次查詢',
      '進階技術分析',
      '個人化投資建議',
      'ART智能學習系統',
      '投資組合追蹤',
      '風險評估報告',
      '優先客服支援'
    ]
  },
  {
    id: 'diamond',
    name: '投資專家',
    displayName: '鑽石方案',
    monthlyPrice: 4999,
    yearlyPrice: 49990,
    description: '頂級投資專家專用，機構級研究服務',
    color: 'from-blue-500 to-purple-600',
    icon: '💎',
    apiQuota: -1,
    analysisTypes: ['全方位分析'],
    support: '專屬顧問',
    features: [
      '全方位深度分析',
      '無限次查詢',
      '量化交易策略',
      '機構級研究報告',
      '專屬投資顧問',
      '即時市場警報',
      'API接口使用',
      '自定義分析模型',
      '機構級數據源',
      '白手套專屬服務'
    ]
  }
];

const ProfessionalPricingPage: React.FC = () => {
  console.log('🎯 ProfessionalPricingPage 專業級定價頁面已載入');
  
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('yearly');
  const [processingPayment, setProcessingPayment] = useState<string | null>(null);
  const [currentTier, setCurrentTier] = useState<string>('free');

  useEffect(() => {
    // 檢查用戶當前方案
    const userTier = localStorage.getItem('user_tier') || 'free';
    setCurrentTier(userTier);
  }, []);

  const formatPrice = (monthlyPrice: number, yearlyPrice: number): { price: string; period: string; savings?: string } => {
    if (monthlyPrice === 0) {
      return { price: '免費', period: '' };
    }

    if (billingCycle === 'monthly') {
      return {
        price: `NT$ ${monthlyPrice.toLocaleString()}`,
        period: ' /月'
      };
    } else {
      const monthlyFromYearly = Math.round(yearlyPrice / 12);
      const savingsPercent = Math.round((1 - yearlyPrice / (monthlyPrice * 12)) * 100);
      return {
        price: `NT$ ${monthlyFromYearly.toLocaleString()}`,
        period: ' /月 (年付)',
        savings: savingsPercent > 0 ? `省 ${savingsPercent}%` : undefined
      };
    }
  };

  const handleUpgrade = async (planId: string) => {
    console.log('🔥 ProfessionalPricingPage.handleUpgrade 被調用！', { planId, billingCycle });

    // 免費方案處理
    if (planId === 'free') {
      setCurrentTier('free');
      localStorage.setItem('user_tier', 'free');
      console.log('✅ 已切換到免費方案');
      alert('🎉 歡迎使用探索者方案！您可以立即開始體驗基礎分析功能。');
      return;
    }

    // 🔒 檢查會員登入狀態 - 付費方案需要登入
    const isAuthenticated = localStorage.getItem('frontend_google_auth') === 'true' || 
                           localStorage.getItem('auth_token') !== null;
    
    if (!isAuthenticated) {
      console.log('❌ 用戶未登入，需要先登入才能購買付費方案');
      alert('請先登入會員再購買付費方案\n\n點擊確定將跳轉到登入頁面');
      window.location.href = '/auth';
      return;
    }
    
    console.log('✅ 用戶已登入，可以繼續支付流程');

    // 避免重複點擊
    if (processingPayment) {
      console.log('⚠️ 支付處理中，請勿重複點擊');
      return;
    }

    try {
      setProcessingPayment(planId);
      console.log(`🚀 開始處理 ${planId} 方案升級`);
      console.log('💡 支付模式：會員認證支付');

      // 調用 PayUni 支付（支援訪客模式）
      const success = await redirectToPayUniPayment(planId, billingCycle);
      
      if (!success) {
        console.error('❌ PayUni 支付跳轉失敗');
        alert('支付系統暫時無法使用，請稍後再試或聯繫客服');
        setProcessingPayment(null);
      } else {
        console.log('✅ PayUni 支付跳轉成功，即將跳轉到支付頁面');
        // 支付成功後會跳轉到 PayUni，不需要重置狀態
      }

    } catch (error) {
      console.error('❌ 支付處理錯誤:', error);
      const errorMessage = error instanceof Error ? error.message : '未知錯誤';
      console.error('詳細錯誤:', errorMessage);
      
      alert(`支付處理失敗: ${errorMessage}\n請稍後再試或聯繫客服 support@03king.com`);
      setProcessingPayment(null);
    }
  };

  const goBack = () => {
    navigate(-1);
  };

  return (
    <div className="professional-pricing">
      {/* 導航欄 */}
      <nav className="pricing-navbar">
        <div className="navbar-content">
          <div className="navbar-brand" onClick={goBack}>
            <img src="/favicon.ico" alt="不老傳說" />
            不老傳說
          </div>
          <div className="navbar-actions">
            <button className="btn-back" onClick={goBack}>
              ← 返回
            </button>
          </div>
        </div>
      </nav>

      {/* 英雄區塊 */}
      <section className="pricing-hero">
        <div className="hero-content">
          <h1 className="hero-title">
            選擇您的
            <span className="highlight"> AI 投資分析</span>
            方案
          </h1>
          <p className="hero-subtitle">
            從基礎體驗到專業級機構服務，我們提供適合每個投資階段的解決方案
          </p>

          {/* 計費周期選擇 */}
          <div className="billing-toggle">
            <button
              className={`toggle-btn ${billingCycle === 'monthly' ? 'active' : ''}`}
              onClick={() => setBillingCycle('monthly')}
            >
              月付
            </button>
            <button
              className={`toggle-btn ${billingCycle === 'yearly' ? 'active' : ''}`}
              onClick={() => setBillingCycle('yearly')}
            >
              年付
              <span className="savings-badge">省17%</span>
            </button>
          </div>
        </div>
      </section>

      {/* 定價方案卡片 */}
      <section className="pricing-plans">
        <div className="plans-container">
          {pricingPlans.map((plan) => {
            const priceInfo = formatPrice(plan.monthlyPrice, plan.yearlyPrice);
            const isCurrentPlan = currentTier === plan.id;
            const isProcessing = processingPayment === plan.id;

            return (
              <div
                key={plan.id}
                className={`plan-card ${plan.popular ? 'popular' : ''} ${isCurrentPlan ? 'current' : ''}`}
              >
                {plan.popular && (
                  <div className="popular-badge">
                    ⭐ 最受歡迎
                  </div>
                )}

                <div className="plan-header">
                  <div className={`plan-icon bg-gradient-to-r ${plan.color}`}>
                    <span className="icon-emoji">{plan.icon}</span>
                  </div>
                  <h3 className="plan-name">{plan.displayName}</h3>
                  <p className="plan-description">{plan.description}</p>
                </div>

                <div className="plan-pricing">
                  <div className="price-display">
                    <span className="price">{priceInfo.price}</span>
                    <span className="period">{priceInfo.period}</span>
                  </div>
                  {priceInfo.savings && (
                    <div className="savings-info">
                      💰 {priceInfo.savings}
                    </div>
                  )}
                </div>

                <div className="plan-stats">
                  <div className="stat">
                    <span className="stat-value">
                      {plan.apiQuota === -1 ? '無限' : plan.apiQuota}
                    </span>
                    <span className="stat-label">每日查詢</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">
                      {plan.analysisTypes.length === 1 && plan.analysisTypes[0] === '全方位分析' 
                        ? '全部' 
                        : plan.analysisTypes.length}
                    </span>
                    <span className="stat-label">分析類型</span>
                  </div>
                </div>

                <div className="plan-features">
                  {plan.features.map((feature, index) => (
                    <div key={index} className="feature-item">
                      <span className="feature-check">✓</span>
                      <span className="feature-text">{feature}</span>
                    </div>
                  ))}
                </div>

                <div className="plan-action">
                  {isCurrentPlan ? (
                    <button className="btn-current" disabled>
                      🛡️ 目前方案
                    </button>
                  ) : (
                    <button
                      className={`btn-upgrade ${plan.id === 'free' ? 'btn-free' : 'btn-premium'}`}
                      onClick={() => handleUpgrade(plan.id)}
                      disabled={isProcessing}
                    >
                      {isProcessing ? (
                        <>
                          <span className="spinner">⚡</span>
                          處理中...
                        </>
                      ) : plan.id === 'free' ? (
                        '免費開始'
                      ) : (
                        '立即升級'
                      )}
                    </button>
                  )}
                  
                  {plan.id !== 'free' && currentTier === 'free' && (
                    <div className="trial-info">
                      🎁 享有 7 天免費試用
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 保證與安全說明 */}
      <section className="pricing-guarantee">
        <div className="guarantee-content">
          <h2 className="guarantee-title">🔒 安全支付保障</h2>
          <div className="guarantee-grid">
            <div className="guarantee-item">
              <div className="guarantee-icon">🛡️</div>
              <h3>PayUni 金流系統</h3>
              <p>符合國際 PCI DSS 安全標準</p>
            </div>
            <div className="guarantee-item">
              <div className="guarantee-icon">🔐</div>
              <h3>SSL 加密傳輸</h3>
              <p>所有支付資料均加密保護</p>
            </div>
            <div className="guarantee-item">
              <div className="guarantee-icon">💳</div>
              <h3>多元支付方式</h3>
              <p>支援信用卡、金融卡、行動支付</p>
            </div>
            <div className="guarantee-item">
              <div className="guarantee-icon">⏰</div>
              <h3>隨時可取消</h3>
              <p>無綁定期限，隨時取消訂閱</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ 區域 */}
      <section className="pricing-faq">
        <div className="faq-content">
          <h2 className="faq-title">常見問題</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <h4>💡 如何開始使用？</h4>
              <p>選擇適合的方案後，完成付款即可立即使用所有功能。免費方案無需付款。</p>
            </div>
            <div className="faq-item">
              <h4>🔄 可以隨時更換方案嗎？</h4>
              <p>可以隨時升級或降級方案。費用差額會在下個計費周期調整。</p>
            </div>
            <div className="faq-item">
              <h4>💰 支援哪些支付方式？</h4>
              <p>支援信用卡、金融卡、行動支付(Apple Pay, Google Pay)及銀行轉帳。</p>
            </div>
            <div className="faq-item">
              <h4>📞 如需協助該聯繫誰？</h4>
              <p>可透過客服信箱 support@03king.com 或線上客服取得協助。</p>
            </div>
          </div>
        </div>
      </section>

      {/* 頁尾 */}
      <footer className="pricing-footer">
        <div className="footer-content">
          <p>
            © 2024 不老傳說 AI 投資分析平台 · 
            <a href="/privacy">隱私權政策</a> · 
            <a href="/terms">服務條款</a>
          </p>
        </div>
      </footer>
    </div>
  );
};

export default ProfessionalPricingPage;