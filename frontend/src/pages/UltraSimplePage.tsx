import React from 'react';

const UltraSimplePage = () => {
  // 嘗試多種日誌方式
  console.log('🚨🚨🚨 UltraSimplePage 已載入 - 超級簡單版本！');
  console.warn('⚠️ UltraSimplePage WARNING 測試');
  console.error('❌ UltraSimplePage ERROR 測試');
  
  // 嘗試 alert
  setTimeout(() => {
    alert('🚨 UltraSimplePage 組件已載入！如果您看到這個彈窗，說明組件正常執行。');
  }, 100);
  
  return React.createElement('div', {
    style: { 
      padding: '50px', 
      textAlign: 'center', 
      backgroundColor: '#ff6b6b', 
      color: 'white',
      fontSize: '24px'
    }
  }, '🚨 超級簡單測試頁面 - 如果您看到這個，說明組件載入正常！當前時間：' + new Date().toLocaleTimeString());
};

export default UltraSimplePage;