/**
 * E2E測試工具函數
 * 提供常用的測試操作和斷言
 */

import { Page, expect } from '@playwright/test';

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * 等待頁面載入完成
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForLoadState('domcontentloaded');
  }

  /**
   * 等待元素可見並可交互
   */
  async waitForElement(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { 
      state: 'visible', 
      timeout 
    });
    return this.page.locator(selector);
  }

  /**
   * 安全點擊元素（等待可見後點擊）
   */
  async safeClick(selector: string) {
    const element = await this.waitForElement(selector);
    await element.click();
  }

  /**
   * 安全輸入文本（清空後輸入）
   */
  async safeType(selector: string, text: string) {
    const element = await this.waitForElement(selector);
    await element.clear();
    await element.type(text);
  }

  /**
   * 等待並驗證文本內容
   */
  async expectText(selector: string, expectedText: string | RegExp) {
    const element = await this.waitForElement(selector);
    await expect(element).toHaveText(expectedText);
  }

  /**
   * 等待並驗證元素存在
   */
  async expectVisible(selector: string) {
    const element = await this.waitForElement(selector);
    await expect(element).toBeVisible();
  }

  /**
   * 驗證元素不存在或不可見
   */
  async expectNotVisible(selector: string) {
    await expect(this.page.locator(selector)).not.toBeVisible();
  }

  /**
   * 等待API請求完成
   */
  async waitForApiRequest(urlPattern: string | RegExp, method = 'GET') {
    return this.page.waitForRequest(request => {
      const url = request.url();
      const requestMethod = request.method();
      
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern) && requestMethod === method;
      } else {
        return urlPattern.test(url) && requestMethod === method;
      }
    });
  }

  /**
   * 等待API響應
   */
  async waitForApiResponse(urlPattern: string | RegExp, method = 'GET') {
    return this.page.waitForResponse(response => {
      const url = response.url();
      const request = response.request();
      
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern) && request.method() === method;
      } else {
        return urlPattern.test(url) && request.method() === method;
      }
    });
  }

  /**
   * 模擬網絡條件
   */
  async simulateNetworkCondition(condition: 'offline' | 'slow' | 'fast') {
    const context = this.page.context();
    
    switch (condition) {
      case 'offline':
        await context.setOffline(true);
        break;
      case 'slow':
        await context.setOffline(false);
        // 模擬慢速網絡
        await this.page.route('**/*', route => {
          setTimeout(() => route.continue(), 1000);
        });
        break;
      case 'fast':
        await context.setOffline(false);
        await this.page.unroute('**/*');
        break;
    }
  }

  /**
   * 截圖並附加到測試報告
   */
  async takeScreenshot(name: string) {
    const screenshot = await this.page.screenshot({ 
      fullPage: true,
      path: `test-results/screenshots/${name}-${Date.now()}.png`
    });
    return screenshot;
  }

  /**
   * 獲取控制台錯誤
   */
  getConsoleErrors() {
    const errors: string[] = [];
    
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    return errors;
  }

  /**
   * 獲取網絡錯誤
   */
  getNetworkErrors() {
    const errors: string[] = [];
    
    this.page.on('requestfailed', request => {
      errors.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });
    
    return errors;
  }

  /**
   * 清理本地存儲
   */
  async clearStorage() {
    await this.page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  }

  /**
   * 設置本地存儲
   */
  async setLocalStorage(key: string, value: any) {
    await this.page.evaluate(
      ({ key, value }) => {
        localStorage.setItem(key, JSON.stringify(value));
      },
      { key, value }
    );
  }

  /**
   * 獲取本地存儲
   */
  async getLocalStorage(key: string) {
    return this.page.evaluate(
      (key) => {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
      },
      key
    );
  }

  /**
   * 等待載入狀態消失
   */
  async waitForLoadingToFinish() {
    // 等待常見的載入指示器消失
    const loadingSelectors = [
      '[data-testid="loading"]',
      '.loading',
      '.spinner',
      '[aria-label*="loading" i]',
      '[aria-label*="載入" i]'
    ];

    for (const selector of loadingSelectors) {
      try {
        await this.page.waitForSelector(selector, { state: 'hidden', timeout: 5000 });
      } catch {
        // 忽略超時錯誤，可能該載入器不存在
      }
    }
  }

  /**
   * 驗證頁面無JavaScript錯誤
   */
  async expectNoJavaScriptErrors() {
    const errors = this.getConsoleErrors();
    expect(errors).toHaveLength(0);
  }

  /**
   * 驗證頁面無網絡錯誤
   */
  async expectNoNetworkErrors() {
    const errors = this.getNetworkErrors();
    expect(errors).toHaveLength(0);
  }
}

/**
 * 測試數據工廠
 */
export class TestDataFactory {
  static createValidUser() {
    return {
      username: 'admin',
      password: 'password123',
      email: 'admin@example.com'
    };
  }

  static createInvalidUser() {
    return {
      username: 'invalid',
      password: 'wrong',
      email: 'invalid@example.com'
    };
  }

  static createMockTokens() {
    return {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'Bearer',
      expires_in: 3600,
      expires_at: Date.now() + 3600000
    };
  }
}

/**
 * API模擬工具
 */
export class ApiMocker {
  constructor(private page: Page) {}

  /**
   * 模擬成功登錄
   */
  async mockSuccessfulLogin() {
    await this.page.route('**/auth/login', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(TestDataFactory.createMockTokens())
      });
    });

    await this.page.route('**/auth/me', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'admin',
          email: 'admin@example.com',
          role: 'admin',
          permissions: ['read', 'write'],
          is_admin: true,
          is_active: true
        })
      });
    });
  }

  /**
   * 模擬登錄失敗
   */
  async mockFailedLogin() {
    await this.page.route('**/auth/login', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Invalid credentials' })
      });
    });
  }

  /**
   * 模擬網絡錯誤
   */
  async mockNetworkError() {
    await this.page.route('**/auth/login', route => {
      route.abort('failed');
    });
  }

  /**
   * 模擬服務器錯誤
   */
  async mockServerError() {
    await this.page.route('**/auth/login', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Internal Server Error' })
      });
    });
  }

  /**
   * 清除所有路由模擬
   */
  async clearMocks() {
    await this.page.unroute('**/*');
  }
}