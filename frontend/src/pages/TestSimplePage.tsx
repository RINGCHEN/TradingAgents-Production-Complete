import React from 'react';

const TestSimplePage: React.FC = () => {
  console.log('🎯🎯🎯 TestSimplePage 已載入 - 最基本的測試頁面 - 新版本！');
  
  return (
    <div style={{ padding: '20px', textAlign: 'center', backgroundColor: '#e8f5e8' }}>
      <h1 style={{ color: '#155724' }}>🧪 測試頁面 - 更新版本</h1>
      <p style={{ fontSize: '1.2rem', color: '#155724' }}>如果您看到這個頁面，說明 React 路由系統正常運行</p>
      <div style={{ marginTop: '20px' }}>
        <button 
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
          onClick={() => console.log('✅✅✅ 按鈕點擊測試成功 - 新版本！')}
        >
          測試按鈕
        </button>
      </div>
      <div style={{ marginTop: '20px' }}>
        <p style={{ color: '#666' }}>當前時間：{new Date().toLocaleTimeString()}</p>
      </div>
    </div>
  );
};

export default TestSimplePage;