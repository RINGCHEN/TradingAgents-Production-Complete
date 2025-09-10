/**
 * 緊急CORS修復 - 立即生效
 * 強制重寫所有API請求到正確的後端
 */

console.log('🚨 緊急CORS修復腳本載入...');

// 立即保存原始fetch
if (typeof window !== 'undefined' && !window.originalFetchBackup) {
  window.originalFetchBackup = window.fetch;
  
  // 強制重寫fetch函數
  window.fetch = function(input, init = {}) {
    let url = typeof input === 'string' ? input : input.url;
    
    // 強制將任何API請求轉換到後端
    if (url.includes('/api/')) {
      const originalUrl = url;
      if (url.startsWith('/api/')) {
        url = 'https://twshocks-app-79rsx.ondigitalocean.app' + url;
      } else if (url.includes('03king.web.app/api/') || url.includes('03king.com/api/')) {
        url = url.replace(/https?:\/\/[^\/]+\/api\//, 'https://twshocks-app-79rsx.ondigitalocean.app/api/');
      }
      
      console.log('🔧 緊急CORS修復:', originalUrl, '→', url);
      
      // 確保使用正確的headers
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...init.headers
      };
      
      init = {
        ...init,
        headers,
        mode: 'cors',
        credentials: 'include'
      };
    }
    
    return window.originalFetchBackup(url, init);
  };
  
  console.log('✅ 緊急CORS修復已啟用');
  console.log('🎯 所有API請求將強制路由到後端');
}

// 額外的全域錯誤處理
window.addEventListener('error', function(e) {
  if (e.message && e.message.includes('CORS')) {
    console.error('🚨 CORS錯誤檢測到:', e.message);
    console.log('💡 請確保已清除瀏覽器緩存並重新整理頁面');
  }
});

console.log('🎉 緊急CORS修復腳本載入完成');