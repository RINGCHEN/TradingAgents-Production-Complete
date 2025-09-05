import React from 'react';
import { MembershipPlans } from '../components/PaymentSystem/MembershipPlans';

/**
 * 簡單的定價頁面
 * 專門用於PayUni支付整合測試
 */
const SimplePricingPage: React.FC = () => {
  console.log('🎯 SimplePricingPage 已載入');
  
  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '20px',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '40px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '16px', color: '#333' }}>
            🚀 TradingAgents 會員方案
          </h1>
          <p style={{ fontSize: '1.2rem', color: '#666', maxWidth: '600px', margin: '0 auto' }}>
            選擇最適合您的AI投資分析服務，立即升級享受專業級功能
          </p>
        </div>

        {/* PayUni整合的會員方案組件 */}
        <MembershipPlans />

        {/* 額外的服務說明 */}
        <div style={{ marginTop: '60px', padding: '30px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
            💎 為什麼選擇 TradingAgents？
          </h2>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
            gap: '20px' 
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>🤖</div>
              <h3 style={{ color: '#007bff' }}>AI智能分析</h3>
              <p style={{ color: '#666' }}>最先進的人工智能技術，提供精準的股市分析</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📊</div>
              <h3 style={{ color: '#28a745' }}>即時數據</h3>
              <p style={{ color: '#666' }}>即時股價數據，掌握市場脈動</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>🛡️</div>
              <h3 style={{ color: '#ffc107' }}>風險控制</h3>
              <p style={{ color: '#666' }}>智能風險評估，保護您的投資</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>🎯</div>
              <h3 style={{ color: '#dc3545' }}>個人化推薦</h3>
              <p style={{ color: '#666' }}>根據您的投資風格量身定制建議</p>
            </div>
          </div>
        </div>

        {/* PayUni支付安全說明 */}
        <div style={{ marginTop: '40px', textAlign: 'center', padding: '20px', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
          <h3 style={{ color: '#155724', marginBottom: '15px' }}>🔒 支付安全保障</h3>
          <p style={{ color: '#155724', fontSize: '1.1rem' }}>
            我們使用 PayUni 金流系統，符合國際 PCI DSS 安全標準
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '30px', marginTop: '15px', flexWrap: 'wrap' }}>
            <span style={{ color: '#6c757d' }}>🛡️ SSL 加密傳輸</span>
            <span style={{ color: '#6c757d' }}>🔐 不儲存卡號信息</span>
            <span style={{ color: '#6c757d' }}>✅ 金管會認證</span>
          </div>
        </div>

        {/* 聯絡信息 */}
        <div style={{ marginTop: '40px', textAlign: 'center', borderTop: '1px solid #dee2e6', paddingTop: '30px' }}>
          <p style={{ color: '#6c757d', marginBottom: '10px' }}>
            如有任何問題，歡迎聯繫我們的客服團隊
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap' }}>
            <a href="mailto:support@tradingagents.com" style={{ color: '#007bff', textDecoration: 'none' }}>
              📧 support@tradingagents.com
            </a>
            <span style={{ color: '#6c757d' }}>📞 02-1234-5678</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimplePricingPage;