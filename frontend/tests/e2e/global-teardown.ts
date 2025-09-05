/**
 * Playwright 全局清理
 * 清理E2E測試後的環境和數據
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 開始E2E測試全局清理...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // 訪問應用進行清理
    await page.goto('http://localhost:3000');
    
    // 清理測試數據
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
      
      // 清理可能的測試cookies
      document.cookie.split(";").forEach(function(c) { 
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
      });
    });
    
    console.log('✅ 測試數據清理完成');
    
  } catch (error) {
    console.error('❌ 全局清理失敗:', error);
    // 不拋出錯誤，避免影響測試結果
  } finally {
    await context.close();
    await browser.close();
  }
  
  console.log('🎯 E2E測試全局清理完成');
}

export default globalTeardown;