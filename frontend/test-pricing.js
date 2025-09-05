// 測試 pricing 頁面是否正常載入的簡單腳本
const puppeteer = require('puppeteer');

(async () => {
  try {
    console.log('🚀 啟動瀏覽器測試...');
    
    const browser = await puppeteer.launch({ 
      headless: false,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // 監聽控制台輸出
    page.on('console', msg => {
      if (msg.text().includes('SimplePricingPage') || msg.text().includes('MembershipPlans')) {
        console.log('✅ 組件載入:', msg.text());
      }
      if (msg.type() === 'error') {
        console.log('❌ 錯誤:', msg.text());
      }
    });
    
    // 監聽頁面錯誤
    page.on('pageerror', error => {
      console.log('❌ 頁面錯誤:', error.message);
    });
    
    console.log('🔍 訪問 http://localhost:3002/pricing...');
    await page.goto('http://localhost:3002/pricing', { waitUntil: 'networkidle2' });
    
    // 等待頁面載入
    await page.waitForTimeout(3000);
    
    // 檢查頁面標題
    const title = await page.title();
    console.log('📄 頁面標題:', title);
    
    // 檢查是否有會員方案內容
    const hasPlans = await page.$('div:contains("會員方案")') !== null;
    console.log('💰 是否包含會員方案:', hasPlans);
    
    // 等待用戶檢查
    console.log('🔎 請在瀏覽器中檢查頁面內容，按 Ctrl+C 結束...');
    await page.waitForTimeout(30000);
    
    await browser.close();
    
  } catch (error) {
    console.error('❌ 測試失敗:', error);
  }
})();