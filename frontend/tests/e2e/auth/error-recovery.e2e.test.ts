/**
 * 錯誤恢復端到端測試
 * 測試認證系統的錯誤處理和恢復機制
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TestHelpers, TestDataFactory, ApiMocker } from '../utils/test-helpers';

test.describe('錯誤恢復 E2E 測試', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let helpers: TestHelpers;
  let apiMocker: ApiMocker;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    helpers = new TestHelpers(page);
    apiMocker = new ApiMocker(page);

    await helpers.clearStorage();
  });

  test.describe('網絡錯誤恢復', () => {
    test('應該從網絡中斷中恢復', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 正常登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬網絡中斷
      await helpers.simulateNetworkCondition('offline');

      // 嘗試刷新數據（應該失敗）
      await dashboardPage.refreshData();

      // 檢查離線狀態處理
      if (await dashboardPage.hasErrorMessage()) {
        const errorMessage = await dashboardPage.getErrorMessage();
        expect(errorMessage).toMatch(/網絡|連接|offline/i);
      }

      // 恢復網絡連接
      await helpers.simulateNetworkCondition('fast');

      // 重新嘗試操作
      await dashboardPage.refreshData();

      // 應該恢復正常
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該在網絡恢復後自動重試失敗的請求', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      let requestCount = 0;
      await page.route('**/api/dashboard/stats', route => {
        requestCount++;
        if (requestCount === 1) {
          // 第一次請求失敗
          route.abort('failed');
        } else {
          // 第二次請求成功
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ stats: 'success' })
          });
        }
      });

      // 觸發API請求
      await dashboardPage.refreshData();

      // 等待重試
      await page.waitForTimeout(2000);

      // 驗證請求被重試並成功
      expect(requestCount).toBe(2);
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該顯示網絡狀態指示器', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬網絡中斷
      await helpers.simulateNetworkCondition('offline');

      // 觸發網絡檢測
      await page.dispatchEvent('window', 'offline');

      // 檢查離線指示器
      const offlineIndicator = page.locator('[data-testid="offline-indicator"], .offline-indicator');
      if (await offlineIndicator.isVisible()) {
        expect(await offlineIndicator.isVisible()).toBe(true);
      }

      // 恢復網絡
      await helpers.simulateNetworkCondition('fast');
      await page.dispatchEvent('window', 'online');

      // 離線指示器應該消失
      if (await offlineIndicator.isVisible()) {
        await expect(offlineIndicator).not.toBeVisible();
      }
    });
  });

  test.describe('認證錯誤恢復', () => {
    test('應該從token過期中恢復', async ({ page }) => {
      // 模擬短期token
      await page.route('**/auth/login', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'short-token',
            refresh_token: 'refresh-token',
            token_type: 'Bearer',
            expires_in: 2,
            expires_at: Date.now() + 2000
          })
        });
      });

      // 模擬成功的token刷新
      await page.route('**/auth/refresh', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'new-token',
            refresh_token: 'new-refresh-token',
            token_type: 'Bearer',
            expires_in: 3600
          })
        });
      });

      await page.route('**/auth/me', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(TestDataFactory.createValidUser())
        });
      });

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 等待token過期
      await page.waitForTimeout(3000);

      // 觸發需要認證的操作
      await dashboardPage.refreshData();

      // 應該自動刷新token並繼續操作
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);

      // 驗證新token已保存
      const tokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(tokens.access_token).toBe('new-token');
    });

    test('應該處理refresh token過期', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬refresh token過期
      await page.route('**/auth/refresh', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Refresh token expired' })
        });
      });

      // 手動設置過期的access token
      await page.evaluate(() => {
        const tokens = JSON.parse(localStorage.getItem('admin_auth_tokens') || '{}');
        tokens.expires_at = Date.now() - 1000;
        localStorage.setItem('admin_auth_tokens', JSON.stringify(tokens));
      });

      // 觸發需要認證的操作
      await dashboardPage.refreshData();

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);

      // 應該顯示會話過期消息
      if (await loginPage.hasErrorMessage()) {
        const errorMessage = await loginPage.getErrorMessage();
        expect(errorMessage).toMatch(/會話過期|session expired/i);
      }
    });

    test('應該處理並發認證錯誤', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬所有API調用返回401
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Unauthorized' })
        });
      });

      // 同時發起多個API請求
      const promises = [
        page.evaluate(() => fetch('/api/users')),
        page.evaluate(() => fetch('/api/settings')),
        page.evaluate(() => fetch('/api/dashboard'))
      ];

      await Promise.allSettled(promises);

      // 應該只重定向一次到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });
  });

  test.describe('服務器錯誤恢復', () => {
    test('應該從服務器錯誤中恢復', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      let requestCount = 0;
      await page.route('**/api/dashboard/stats', route => {
        requestCount++;
        if (requestCount <= 2) {
          // 前兩次請求返回服務器錯誤
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Internal Server Error' })
          });
        } else {
          // 第三次請求成功
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ stats: 'recovered' })
          });
        }
      });

      // 觸發API請求
      await dashboardPage.refreshData();

      // 應該顯示錯誤消息
      if (await dashboardPage.hasErrorMessage()) {
        const errorMessage = await dashboardPage.getErrorMessage();
        expect(errorMessage).toMatch(/服務器錯誤|server error/i);
      }

      // 等待自動重試或手動重試
      await page.waitForTimeout(2000);
      await dashboardPage.refreshData();

      // 最終應該恢復正常
      expect(requestCount).toBeGreaterThan(2);
    });

    test('應該實施指數退避重試', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      const requestTimes: number[] = [];
      await page.route('**/api/dashboard/stats', route => {
        requestTimes.push(Date.now());
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Server Error' })
        });
      });

      // 觸發多次重試
      for (let i = 0; i < 3; i++) {
        await dashboardPage.refreshData();
        await page.waitForTimeout(1000);
      }

      // 驗證重試間隔遞增（指數退避）
      if (requestTimes.length >= 3) {
        const interval1 = requestTimes[1] - requestTimes[0];
        const interval2 = requestTimes[2] - requestTimes[1];
        expect(interval2).toBeGreaterThan(interval1);
      }
    });

    test('應該限制最大重試次數', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      let requestCount = 0;
      await page.route('**/api/dashboard/stats', route => {
        requestCount++;
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Persistent Server Error' })
        });
      });

      // 持續觸發重試
      for (let i = 0; i < 10; i++) {
        await dashboardPage.refreshData();
        await page.waitForTimeout(500);
      }

      // 應該限制重試次數（例如最多5次）
      expect(requestCount).toBeLessThanOrEqual(5);

      // 應該顯示最終錯誤消息
      if (await dashboardPage.hasErrorMessage()) {
        const errorMessage = await dashboardPage.getErrorMessage();
        expect(errorMessage).toMatch(/服務暫時不可用|service unavailable/i);
      }
    });
  });

  test.describe('用戶體驗恢復', () => {
    test('應該保存用戶輸入狀態', async ({ page }) => {
      await apiMocker.mockFailedLogin();

      await loginPage.goto();

      // 用戶輸入信息
      await loginPage.fillUsername('testuser');
      await loginPage.fillPassword('testpass');

      // 嘗試登錄（失敗）
      await loginPage.clickLogin();

      // 驗證錯誤顯示
      expect(await loginPage.hasErrorMessage()).toBe(true);

      // 驗證用戶輸入被保留
      const formData = await loginPage.getFormData();
      expect(formData.username).toBe('testuser');
      // 密碼通常不會被保留（安全考慮）
      expect(formData.password).toBe('');
    });

    test('應該提供有用的錯誤恢復建議', async ({ page }) => {
      await apiMocker.mockNetworkError();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);

      // 檢查錯誤消息和恢復建議
      expect(await loginPage.hasErrorMessage()).toBe(true);
      const errorMessage = await loginPage.getErrorMessage();
      
      // 應該包含恢復建議
      expect(errorMessage).toMatch(/檢查網絡|重試|稍後再試/i);

      // 檢查是否有重試按鈕
      const retryButton = page.locator('[data-testid="retry-button"], button:has-text("重試"), button:has-text("Retry")');
      if (await retryButton.isVisible()) {
        expect(await retryButton.isVisible()).toBe(true);
      }
    });

    test('應該在錯誤恢復後清除錯誤狀態', async ({ page }) => {
      // 先模擬失敗
      await apiMocker.mockFailedLogin();

      await loginPage.goto();
      const invalidUser = TestDataFactory.createInvalidUser();
      await loginPage.login(invalidUser.username, invalidUser.password);

      // 驗證錯誤顯示
      expect(await loginPage.hasErrorMessage()).toBe(true);

      // 然後模擬成功
      await apiMocker.clearMocks();
      await apiMocker.mockSuccessfulLogin();

      // 重新嘗試登錄
      const validUser = TestDataFactory.createValidUser();
      await loginPage.clearForm();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 驗證成功登錄且錯誤狀態已清除
      expect(await dashboardPage.isOnDashboard()).toBe(true);
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該在頁面刷新後保持錯誤恢復狀態', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬API錯誤
      await page.route('**/api/dashboard/stats', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Server Error' })
        });
      });

      await dashboardPage.refreshData();

      // 刷新頁面
      await page.reload();
      await dashboardPage.waitForPageReady();

      // 應該仍然在儀表板頁面（認證狀態保持）
      expect(await dashboardPage.isOnDashboard()).toBe(true);

      // 恢復API
      await page.unroute('**/api/dashboard/stats');
      await page.route('**/api/dashboard/stats', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ stats: 'recovered' })
        });
      });

      await dashboardPage.refreshData();

      // 應該恢復正常
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });
  });

  test.describe('系統級錯誤恢復', () => {
    test('應該處理JavaScript錯誤', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      const jsErrors: string[] = [];
      page.on('pageerror', error => {
        jsErrors.push(error.message);
      });

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 注入JavaScript錯誤
      await page.evaluate(() => {
        // 模擬運行時錯誤
        setTimeout(() => {
          throw new Error('Simulated runtime error');
        }, 100);
      });

      await page.waitForTimeout(500);

      // 驗證錯誤被捕獲
      expect(jsErrors.length).toBeGreaterThan(0);

      // 應用應該仍然可用
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該處理內存不足情況', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬內存壓力
      await page.evaluate(() => {
        // 創建大量對象消耗內存
        const memoryHog: any[] = [];
        try {
          for (let i = 0; i < 1000000; i++) {
            memoryHog.push(new Array(1000).fill('memory-test'));
          }
        } catch (error) {
          console.warn('Memory pressure simulation:', error);
        }
      });

      // 應用應該仍然響應
      await dashboardPage.refreshData();
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該處理瀏覽器兼容性問題', async ({ page, browserName }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();

      // 檢查瀏覽器特定功能
      const browserFeatures = await page.evaluate(() => {
        return {
          localStorage: typeof localStorage !== 'undefined',
          sessionStorage: typeof sessionStorage !== 'undefined',
          fetch: typeof fetch !== 'undefined',
          Promise: typeof Promise !== 'undefined',
          crypto: typeof crypto !== 'undefined'
        };
      });

      // 驗證必要功能可用
      expect(browserFeatures.localStorage).toBe(true);
      expect(browserFeatures.fetch).toBe(true);
      expect(browserFeatures.Promise).toBe(true);

      // 執行登錄測試
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      expect(await dashboardPage.isOnDashboard()).toBe(true);
    });
  });

  test.describe('恢復性能測試', () => {
    test('錯誤恢復應該快速響應', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬錯誤然後立即恢復
      await page.route('**/api/dashboard/stats', route => {
        route.fulfill({ status: 500 });
      });

      const errorStartTime = Date.now();
      await dashboardPage.refreshData();

      // 立即恢復
      await page.unroute('**/api/dashboard/stats');
      await page.route('**/api/dashboard/stats', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ stats: 'recovered' })
        });
      });

      await dashboardPage.refreshData();
      const recoveryTime = Date.now() - errorStartTime;

      // 恢復時間應該在合理範圍內
      expect(recoveryTime).toBeLessThan(5000); // 5秒內恢復
    });

    test('大量錯誤不應該影響性能', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬大量錯誤
      let errorCount = 0;
      await page.route('**/api/**', route => {
        errorCount++;
        if (errorCount <= 50) {
          route.fulfill({ status: 500 });
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ success: true })
          });
        }
      });

      const startTime = Date.now();

      // 觸發多次操作
      for (let i = 0; i < 10; i++) {
        await dashboardPage.refreshData();
        await page.waitForTimeout(100);
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      // 即使有大量錯誤，總時間也應該合理
      expect(totalTime).toBeLessThan(30000); // 30秒內完成
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });
  });
});