import React from 'react';

/**
 * 簡化版定價頁面 - 用於測試
 */
const SimplePricingPageSimple: React.FC = () => {
  console.log('🎯 SimplePricingPageSimple 已載入 - 這是簡化測試版本');
  
  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '20px',
      backgroundColor: '#f5f5f5',
      textAlign: 'center'
    }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '20px', color: '#333' }}>
        🚀 TradingAgents 會員方案 (測試版本)
      </h1>
      
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto', 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '20px',
        marginTop: '40px'
      }}>
        
        {/* 免費方案 */}
        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ color: '#333', marginBottom: '10px' }}>🆓 探索者方案</h2>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#666', marginBottom: '20px' }}>
            免費
          </div>
          <ul style={{ textAlign: 'left', listStyle: 'none', padding: 0 }}>
            <li style={{ padding: '5px 0' }}>✅ 基礎股票分析</li>
            <li style={{ padding: '5px 0' }}>✅ 每日5次查詢</li>
            <li style={{ padding: '5px 0' }}>✅ 基本技術指標</li>
            <li style={{ padding: '5px 0' }}>✅ 社群支援</li>
          </ul>
          <button 
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              fontSize: '1rem',
              cursor: 'pointer',
              marginTop: '20px'
            }}
            onClick={() => console.log('✅ 免費方案按鈕點擊')}
          >
            免費開始
          </button>
        </div>

        {/* 黃金方案 */}
        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(255,193,7,0.3)',
          border: '2px solid #ffc107',
          position: 'relative'
        }}>
          <div style={{
            position: 'absolute',
            top: '-10px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#ffc107',
            color: '#000',
            padding: '5px 15px',
            borderRadius: '15px',
            fontSize: '0.8rem',
            fontWeight: 'bold'
          }}>
            ⭐ 最受歡迎
          </div>
          
          <h2 style={{ color: '#333', marginBottom: '10px' }}>👑 專業投資者</h2>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ffc107', marginBottom: '20px' }}>
            $1,667<span style={{ fontSize: '1rem', color: '#666' }}>/月 (年付)</span>
          </div>
          <ul style={{ textAlign: 'left', listStyle: 'none', padding: 0 }}>
            <li style={{ padding: '5px 0' }}>✅ 完整基本面分析</li>
            <li style={{ padding: '5px 0' }}>✅ 每日50次查詢</li>
            <li style={{ padding: '5px 0' }}>✅ 進階技術分析</li>
            <li style={{ padding: '5px 0' }}>✅ 個人化投資建議</li>
            <li style={{ padding: '5px 0' }}>✅ ART智能學習</li>
            <li style={{ padding: '5px 0' }}>✅ 優先客服支援</li>
          </ul>
          <button 
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#ffc107',
              color: '#000',
              border: 'none',
              borderRadius: '5px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              marginTop: '20px'
            }}
            onClick={() => {
              console.log('🎯 黃金方案升級按鈕點擊');
              alert('黃金方案升級測試 - 這裡會調用 PayUni 支付');
            }}
          >
            🚀 立即升級
          </button>
        </div>

        {/* 鑽石方案 */}
        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(0,123,255,0.3)',
          border: '2px solid #007bff'
        }}>
          <h2 style={{ color: '#333', marginBottom: '10px' }}>💎 投資專家</h2>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#007bff', marginBottom: '20px' }}>
            $4,166<span style={{ fontSize: '1rem', color: '#666' }}>/月 (年付)</span>
          </div>
          <ul style={{ textAlign: 'left', listStyle: 'none', padding: 0 }}>
            <li style={{ padding: '5px 0' }}>✅ 全方位深度分析</li>
            <li style={{ padding: '5px 0' }}>✅ 無限次查詢</li>
            <li style={{ padding: '5px 0' }}>✅ 量化交易策略</li>
            <li style={{ padding: '5px 0' }}>✅ 機構級研究報告</li>
            <li style={{ padding: '5px 0' }}>✅ 專屬投資顧問</li>
            <li style={{ padding: '5px 0' }}>✅ API接口使用</li>
          </ul>
          <button 
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              marginTop: '20px'
            }}
            onClick={() => {
              console.log('💎 鑽石方案升級按鈕點擊');
              alert('鑽石方案升級測試 - 這裡會調用 PayUni 支付');
            }}
          >
            🚀 選擇專家方案
          </button>
        </div>
        
      </div>

      <div style={{ marginTop: '60px', padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
        <h3>🔒 支付安全保障</h3>
        <p>我們使用 PayUni 金流系統，符合國際 PCI DSS 安全標準</p>
      </div>
    </div>
  );
};

export default SimplePricingPageSimple;