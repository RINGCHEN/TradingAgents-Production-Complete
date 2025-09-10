import React, { useState } from 'react';

/**
 * 測試PayUni支付的最簡單應用
 */
const TestPricingApp: React.FC = () => {
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // 會員方案數據
  const plans = [
    {
      id: 'gold',
      name: '黃金會員',
      price: 1999,
      features: ['完整基本面分析', '每日50次查詢', 'AI智能學習', '優先客服']
    },
    {
      id: 'diamond',
      name: '鑽石會員',
      price: 4999,
      features: ['全方位深度分析', '無限次查詢', '量化交易策略', '專屬投資顧問']
    }
  ];

  // 處理PayUni支付
  const handlePayment = async (planId: string) => {
    setIsLoading(true);
    setSelectedPlan(planId);

    try {
      const plan = plans.find(p => p.id === planId);
      if (!plan) return;

      console.log('🚀 開始PayUni支付流程:', plan);

      // 準備PayUni支付數據
      const paymentData = {
        subscription_id: planId === 'gold' ? 1 : 2,
        amount: plan.price,
        description: `${plan.name} - 年付方案`,
        tier_type: planId
      };

      console.log('📋 支付數據:', paymentData);

      // 調用後端測試API (無需認證)
      const response = await fetch('https://twshocks-app-79rsx.ondigitalocean.app/api/v1/payuni/test-payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(paymentData)
      });

      console.log('📡 API響應狀態:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('✅ PayUni API成功:', result);
        
        if (result.payment_url) {
          console.log('🔗 跳轉到PayUni:', result.payment_url);
          window.location.href = result.payment_url;
        } else {
          alert('支付創建成功，但沒有返回支付URL');
        }
      } else {
        const error = await response.json().catch(() => ({ error: '未知錯誤' }));
        console.error('❌ PayUni API錯誤:', error);
        alert(`支付創建失敗: ${error.detail || error.error || '請稍後再試'}`);
      }

    } catch (error) {
      console.error('❌ 支付流程錯誤:', error);
      alert(`支付系統錯誤: ${error}`);
    } finally {
      setIsLoading(false);
      setSelectedPlan('');
    }
  };

  return (
    <div style={{ 
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px',
      backgroundColor: '#f5f5f5',
      minHeight: '100vh'
    }}>
      {/* 頁面標題 */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '40px',
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '10px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ color: '#333', fontSize: '2.5rem', marginBottom: '10px' }}>
          🚀 TradingAgents PayUni 測試
        </h1>
        <p style={{ color: '#666', fontSize: '1.1rem' }}>
          測試PayUni支付整合功能
        </p>
      </div>

      {/* 會員方案 */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '20px',
        marginBottom: '40px'
      }}>
        {plans.map((plan) => (
          <div key={plan.id} style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '10px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            textAlign: 'center',
            border: selectedPlan === plan.id ? '3px solid #007bff' : '1px solid #ddd'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '15px' }}>
              {plan.id === 'gold' ? '👑' : '💎'}
            </div>
            
            <h2 style={{ color: '#333', marginBottom: '10px' }}>
              {plan.name}
            </h2>
            
            <div style={{ 
              fontSize: '2rem', 
              color: '#007bff', 
              fontWeight: 'bold',
              marginBottom: '20px' 
            }}>
              NT$ {plan?.price?.toLocaleString() || '--'}
              <div style={{ fontSize: '1rem', color: '#666', fontWeight: 'normal' }}>
                / 年 (省17%)
              </div>
            </div>

            <div style={{ marginBottom: '30px', textAlign: 'left' }}>
              {plan.features.map((feature, index) => (
                <div key={index} style={{ 
                  padding: '8px 0', 
                  borderBottom: '1px solid #eee',
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <span style={{ color: '#28a745', marginRight: '10px' }}>✓</span>
                  {feature}
                </div>
              ))}
            </div>

            <button
              onClick={() => handlePayment(plan.id)}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '15px',
                fontSize: '1.1rem',
                backgroundColor: isLoading && selectedPlan === plan.id ? '#6c757d' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                transition: 'background-color 0.3s'
              }}
            >
              {isLoading && selectedPlan === plan.id ? (
                <>
                  ⏳ 處理中...
                </>
              ) : (
                <>
                  💳 立即購買
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* 測試信息 */}
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '10px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ color: '#333', marginBottom: '15px' }}>🔧 測試信息</h3>
        <div style={{ color: '#666', fontSize: '0.9rem', lineHeight: '1.6' }}>
          <p><strong>後端API:</strong> https://twshocks-app-79rsx.ondigitalocean.app</p>
          <p><strong>PayUni商店:</strong> U03823060 (正式環境)</p>
          <p><strong>測試流程:</strong> 點擊購買 → PayUni API → 跳轉支付頁面</p>
          <p><strong>開發者工具:</strong> 打開Console (F12) 查看詳細日誌</p>
        </div>
      </div>

      {/* 底部信息 */}
      <div style={{ 
        textAlign: 'center', 
        marginTop: '40px',
        padding: '20px',
        backgroundColor: 'white',
        borderRadius: '10px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <p style={{ color: '#666' }}>
          🔒 PayUni 金流系統 | 🛡️ SSL 加密 | ✅ 金管會認證
        </p>
        <p style={{ color: '#666', fontSize: '0.9rem' }}>
          測試環境 - TradingAgents PayUni 整合
        </p>
      </div>
    </div>
  );
};

export default TestPricingApp;