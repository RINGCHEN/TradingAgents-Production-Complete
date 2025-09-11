import React from 'react';
import UpgradePromptTest from '../components/TieredAnalysis/UpgradePromptTest';

/**
 * 升級提示測試頁面 - 生產環境版本
 * 用於測試 GEMINI 升級提示整合功能
 */

const UpgradePromptTestPage: React.FC = () => {
  return (
    <div className="upgrade-prompt-test-page">
      <div style={{ padding: '20px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
        <div style={{ 
          maxWidth: '1200px', 
          margin: '0 auto',
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <h1 style={{ 
            textAlign: 'center', 
            color: '#2c3e50',
            marginBottom: '20px',
            fontSize: '2rem'
          }}>
            🎊 生產環境 - GEMINI 升級提示整合測試
          </h1>
          
          <div style={{
            padding: '15px',
            backgroundColor: '#e8f5e8',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid #4CAF50'
          }}>
            <p style={{ margin: 0, color: '#2e7d32', fontWeight: '500' }}>
              ✅ 功能已成功移植到生產環境 (TradingAgents-Production-Complete)
            </p>
            <p style={{ margin: '5px 0 0 0', color: '#2e7d32', fontSize: '0.9rem' }}>
              測試 GEMINI 結構化 upgrade_prompt 格式與舊格式兼容性
            </p>
          </div>

          <UpgradePromptTest />
          
          <div style={{
            marginTop: '30px',
            padding: '15px',
            backgroundColor: '#fff3cd',
            borderRadius: '8px',
            border: '1px solid #ffc107'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#856404' }}>📋 生產環境測試確認</h3>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#856404' }}>
              <li>✅ UpgradePromptComponent.tsx - 已移植</li>
              <li>✅ UpgradePromptComponent.css - 已移植</li>
              <li>✅ TieredReplayDecision.tsx - 已更新</li>
              <li>✅ useReplayDecision.ts - 已移植</li>
              <li>✅ UpgradePromptTest.tsx - 已移植</li>
              <li>🚀 準備部署到 DigitalOcean</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradePromptTestPage;