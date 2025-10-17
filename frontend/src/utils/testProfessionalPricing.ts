// @ts-nocheck
/**
 * 專業級定價頁面測試工具
 * 用於驗證 PayUni 支付功能
 */

import { redirectToPayUniPayment } from '../services/PayUniService';

export class ProfessionalPricingTester {
  
  /**
   * 模擬用戶登入狀態（前端模式）
   */
  static simulateLogin(userEmail: string = 'test@example.com', userName: string = 'Test User') {
    localStorage.setItem('frontend_google_auth', 'true');
    localStorage.setItem('frontend_user_email', userEmail);
    localStorage.setItem('frontend_user_name', userName);
    console.log('✅ 模擬用戶登入完成:', { userEmail, userName });
  }

  /**
   * 清除登入狀態
   */
  static clearLogin() {
    localStorage.removeItem('frontend_google_auth');
    localStorage.removeItem('frontend_user_email');
    localStorage.removeItem('frontend_user_name');
    console.log('🧹 登入狀態已清除');
  }

  /**
   * 測試支付功能
   */
  static async testPayment(tierType: string, billingCycle: 'monthly' | 'yearly' = 'yearly') {
    console.log(`🧪 開始測試 ${tierType} 支付功能 (${billingCycle})`);
    
    try {
      const success = await redirectToPayUniPayment(tierType, billingCycle);
      console.log(`${success ? '✅' : '❌'} 支付測試結果:`, success);
      return success;
    } catch (error) {
      console.error('❌ 支付測試失敗:', error);
      return false;
    }
  }

  /**
   * 驗證定價頁面組件載入
   */
  static validatePricingPage() {
    console.log('🔍 驗證定價頁面組件...');
    
    // 檢查是否有 ProfessionalPricingPage 組件的日誌
    const hasComponent = document.querySelector('.professional-pricing') !== null;
    console.log(`${hasComponent ? '✅' : '❌'} 定價頁面組件載入:`, hasComponent);
    
    // 檢查支付按鈕是否存在
    const paymentButtons = document.querySelectorAll('.btn-upgrade');
    console.log(`${paymentButtons.length > 0 ? '✅' : '❌'} 支付按鈕數量:`, paymentButtons.length);
    
    return {
      hasComponent,
      buttonCount: paymentButtons.length
    };
  }

  /**
   * 完整功能測試流程
   */
  static async runFullTest() {
    console.log('🚀 開始完整的定價頁面功能測試');
    
    // 1. 清理並模擬登入
    this.clearLogin();
    this.simulateLogin('tester@03king.com', 'Professional Tester');
    
    // 2. 驗證頁面組件
    const pageValidation = this.validatePricingPage();
    
    // 3. 測試各種支付方案
    const tests = [
      { tier: 'gold', cycle: 'yearly' as const },
      { tier: 'diamond', cycle: 'monthly' as const },
      { tier: 'free', cycle: 'yearly' as const }
    ];
    
    const results = [];
    for (const test of tests) {
      const success = await this.testPayment(test.tier, test.cycle);
      results.push({ ...test, success });
      
      // 等待一下再進行下個測試
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // 4. 總結報告
    console.log('📊 測試結果總結:');
    console.log('  - 頁面組件:', pageValidation);
    console.log('  - 支付測試:', results);
    
    const successCount = results.filter(r => r.success).length;
    console.log(`✨ 測試完成: ${successCount}/${results.length} 項測試通過`);
    
    return {
      pageValidation,
      paymentTests: results,
      overallSuccess: pageValidation.hasComponent && successCount >= 2
    };
  }
}

// 全域可用的測試函數
(window as any).testProfessionalPricing = ProfessionalPricingTester;