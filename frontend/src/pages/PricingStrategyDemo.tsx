import React, { useState } from 'react';
import PricingStrategy from '../components/PricingStrategy';
import './PricingStrategyDemo.css';

// 多層次定價策略演示頁面
// Task 5.3 - 多層次定價策略的演示實現

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  userAttributes: {
    user_id?: number;
    session_id: string;
    user_type: string;
    source: string;
    [key: string]: any;
  };
  expectedFeatures: string[];
}

const PricingStrategyDemo: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('new_user');
  const [demoMode, setDemoMode] = useState<'scenarios' | 'pricing'>('scenarios');
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [finalPrice, setFinalPrice] = useState<number | null>(null);

  // 預定義的演示場景
  const demoScenarios: DemoScenario[] = [
    {
      id: 'new_user',
      name: '新用戶場景',
      description: '首次訪問的新用戶，展示歡迎優惠和價格錨定策略',
      userAttributes: {
        session_id: 'demo_new_user',
        user_type: 'new',
        source: 'google_ads',
        utm_campaign: 'welcome_offer'
      },
      expectedFeatures: [
        '新用戶50%歡迎折扣',
        '價格錨定顯示原價對比',
        '推薦標準版方案',
        '競爭對手價格對比'
      ]
    },
    {
      id: 'returning_user',
      name: '回頭客場景',
      description: '多次訪問的用戶，展示個性化定價和忠誠度優惠',
      userAttributes: {
        user_id: 12345,
        session_id: 'demo_returning_user',
        user_type: 'returning',
        source: 'direct',
        visit_count: 5,
        engagement_score: 75
      },
      expectedFeatures: [
        '回頭客15%忠誠度折扣',
        '基於行為的動態定價',
        '個性化方案推薦',
        '升級優惠券展示'
      ]
    },
    {
      id: 'premium_prospect',
      name: '高價值用戶場景',
      description: '高參與度用戶，展示高級版推薦和專屬優惠',
      userAttributes: {
        user_id: 67890,
        session_id: 'demo_premium_user',
        user_type: 'premium_prospect',
        source: 'referral',
        engagement_score: 90,
        portfolio_size: 500000,
        investment_experience: 'advanced'
      },
      expectedFeatures: [
        '高價值用戶25%專屬折扣',
        '高級版方案突出顯示',
        '專業功能價值強調',
        '企業級服務介紹'
      ]
    },
    {
      id: 'price_sensitive',
      name: '價格敏感用戶場景',
      description: '對價格敏感的用戶，展示基礎版價值和優惠券策略',
      userAttributes: {
        session_id: 'demo_price_sensitive',
        user_type: 'price_sensitive',
        source: 'price_comparison',
        budget_range: 'low',
        price_sensitivity: 'high'
      },
      expectedFeatures: [
        '基礎版方案突出顯示',
        '最大折扣優惠券',
        '性價比價值強調',
        '分期付款選項'
      ]
    }
  ];

  const handlePlanSelection = (planId: string, price: number) => {
    setSelectedPlan(planId);
    setFinalPrice(price);
    
    // 模擬跳轉到支付頁面
    setTimeout(() => {
      alert(`方案選擇成功！\n方案ID: ${planId}\n最終價格: $${price}\n\n在實際應用中，這裡會跳轉到支付頁面。`);
    }, 500);
  };

  const renderScenarioCard = (scenario: DemoScenario) => (
    <div 
      key={scenario.id} 
      className={`scenario-card ${selectedScenario === scenario.id ? 'selected' : ''}`}
      onClick={() => setSelectedScenario(scenario.id)}
    >
      <div className="scenario-header">
        <h3>{scenario.name}</h3>
        <div className="scenario-type">{scenario.userAttributes.user_type}</div>
      </div>
      
      <div className="scenario-body">
        <p>{scenario.description}</p>
        
        <div className="scenario-attributes">
          <h4>用戶屬性:</h4>
          <ul>
            <li>來源: {scenario.userAttributes.source}</li>
            <li>類型: {scenario.userAttributes.user_type}</li>
            {scenario.userAttributes.engagement_score && (
              <li>參與度: {scenario.userAttributes.engagement_score}</li>
            )}
            {scenario.userAttributes.portfolio_size && (
              <li>投資組合: ${scenario.userAttributes.portfolio_size.toLocaleString()}</li>
            )}
          </ul>
        </div>
        
        <div className="expected-features">
          <h4>預期功能:</h4>
          <ul>
            {scenario.expectedFeatures.map((feature, index) => (
              <li key={index}>
                <span className="feature-icon">✓</span>
                {feature}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );

  const renderScenarios = () => (
    <div className="demo-scenarios">
      <div className="scenarios-header">
        <h2>多層次定價策略演示</h2>
        <p>選擇不同的用戶場景，體驗智能定價系統如何根據用戶特徵調整價格和推薦</p>
      </div>
      
      <div className="scenarios-grid">
        {demoScenarios.map(renderScenarioCard)}
      </div>
      
      <div className="demo-actions">
        <button 
          className="btn btn-primary"
          onClick={() => setDemoMode('pricing')}
          disabled={!selectedScenario}
        >
          體驗定價策略
        </button>
      </div>
    </div>
  );

  const renderPricingDemo = () => {
    const currentScenario = demoScenarios.find(s => s.id === selectedScenario);
    
    if (!currentScenario) {
      return <div>場景不存在</div>;
    }

    return (
      <div className="pricing-demo">
        <div className="demo-header">
          <h2>定價策略演示 - {currentScenario.name}</h2>
          <div className="scenario-info">
            <span>當前場景: {currentScenario.description}</span>
            <button 
              className="btn btn-link"
              onClick={() => setDemoMode('scenarios')}
            >
              更換場景
            </button>
          </div>
        </div>
        
        <div className="pricing-container">
          <PricingStrategy
            apiBaseUrl="/api/pricing"
            userId={currentScenario.userAttributes.user_id}
            sessionId={currentScenario.userAttributes.session_id}
            onPlanSelected={handlePlanSelection}
          />
        </div>
        
        <div className="demo-insights">
          <h3>定價策略洞察</h3>
          <div className="insights-grid">
            <div className="insight-card">
              <h4>🎯 價格錨定</h4>
              <p>通過展示更高的原價或競爭對手價格，讓當前價格顯得更有吸引力</p>
            </div>
            <div className="insight-card">
              <h4>🔄 動態定價</h4>
              <p>根據用戶行為、來源和特徵自動調整價格，提供個性化優惠</p>
            </div>
            <div className="insight-card">
              <h4>🎫 優惠券策略</h4>
              <p>針對不同用戶群體提供專屬優惠券，提高轉換率</p>
            </div>
            <div className="insight-card">
              <h4>📊 方案對比</h4>
              <p>清晰展示不同方案的價值差異，引導用戶選擇推薦方案</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="pricing-strategy-demo">
      <div className="demo-navigation">
        <button 
          className={`nav-btn ${demoMode === 'scenarios' ? 'active' : ''}`}
          onClick={() => setDemoMode('scenarios')}
        >
          場景選擇
        </button>
        <button 
          className={`nav-btn ${demoMode === 'pricing' ? 'active' : ''}`}
          onClick={() => setDemoMode('pricing')}
          disabled={!selectedScenario}
        >
          定價演示
        </button>
      </div>
      
      <div className="demo-content">
        {demoMode === 'scenarios' ? renderScenarios() : renderPricingDemo()}
      </div>
      
      <div className="demo-footer">
        <div className="strategy-benefits">
          <h3>多層次定價策略的商業價值</h3>
          <div className="benefits-grid">
            <div className="benefit-item">
              <div className="benefit-icon">💰</div>
              <h4>收入最大化</h4>
              <p>通過價格錨定和動態定價，平均提升15-25%的客單價</p>
            </div>
            <div className="benefit-item">
              <div className="benefit-icon">🎯</div>
              <h4>轉換率提升</h4>
              <p>個性化定價和優惠券策略，提高20-30%的轉換率</p>
            </div>
            <div className="benefit-item">
              <div className="benefit-icon">👥</div>
              <h4>用戶細分</h4>
              <p>精準識別不同價值用戶，提供差異化的定價策略</p>
            </div>
            <div className="benefit-item">
              <div className="benefit-icon">📈</div>
              <h4>競爭優勢</h4>
              <p>智能定價系統幫助在競爭中保持價格優勢</p>
            </div>
          </div>
        </div>
        
        <div className="implementation-notes">
          <h3>實施要點</h3>
          <div className="notes-list">
            <div className="note-item">
              <span className="note-number">1</span>
              <div className="note-content">
                <h4>數據驅動</h4>
                <p>基於用戶行為數據和市場分析制定定價策略</p>
              </div>
            </div>
            <div className="note-item">
              <span className="note-number">2</span>
              <div className="note-content">
                <h4>A/B測試</h4>
                <p>持續測試不同定價策略的效果，優化轉換率</p>
              </div>
            </div>
            <div className="note-item">
              <span className="note-number">3</span>
              <div className="note-content">
                <h4>透明度平衡</h4>
                <p>在個性化定價和價格透明度之間找到平衡點</p>
              </div>
            </div>
            <div className="note-item">
              <span className="note-number">4</span>
              <div className="note-content">
                <h4>合規性</h4>
                <p>確保定價策略符合相關法規和行業標準</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingStrategyDemo;