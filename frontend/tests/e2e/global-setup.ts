/**
 * Playwright 全局設置
 * 為E2E測試準備環境和測試數據
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 開始E2E測試全局設置...');
  
  // 啟動瀏覽器進行初始設置
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // 等待應用啟動
    console.log('⏳ 等待應用啟動...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // 檢查應用是否正常運行
    await page.waitForSelector('body', { timeout: 30000 });
    console.log('✅ 應用啟動成功');
    
    // 清理可能存在的測試數據
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // 設置測試環境標識
    await page.evaluate(() => {
      window.localStorage.setItem('test-environment', 'e2e');
    });
    
    console.log('✅ 測試環境準備完成');
    
  } catch (error) {
    console.error('❌ 全局設置失敗:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
  
  console.log('🎯 E2E測試全局設置完成');
}

export default globalSetup;