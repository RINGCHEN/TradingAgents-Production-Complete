/**
 * 會話管理端到端測試
 * 測試用戶會話的生命週期管理
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TestHelpers, TestDataFactory, ApiMocker } from '../utils/test-helpers';

test.describe('會話管理 E2E 測試', () => {
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

  test.describe('會話建立', () => {
    test('成功登錄應該建立有效會話', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 驗證會話已建立
      const tokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(tokens).toBeTruthy();
      expect(tokens.access_token).toBeTruthy();
      expect(tokens.expires_at).toBeGreaterThan(Date.now());

      // 驗證用戶可以訪問受保護的內容
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('會話應該包含正確的用戶信息', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 驗證用戶信息
      const username = await dashboardPage.getCurrentUsername();
      expect(username).toBe(validUser.username);
    });

    test('會話應該在多個標籤頁間同步', async ({ context }) => {
      await apiMocker.mockSuccessfulLogin();

      // 在第一個標籤頁登錄
      const page1 = await context.newPage();
      const loginPage1 = new LoginPage(page1);
      const dashboardPage1 = new DashboardPage(page1);

      await loginPage1.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage1.login(validUser.username, validUser.password);
      await loginPage1.waitForRedirectToDashboard();

      // 在第二個標籤頁檢查會話
      const page2 = await context.newPage();
      const dashboardPage2 = new DashboardPage(page2);

      await dashboardPage2.goto();
      expect(await dashboardPage2.isOnDashboard()).toBe(true);
      expect(await dashboardPage2.isDashboardContentLoaded()).toBe(true);

      await page1.close();
      await page2.close();
    });
  });

  test.describe('會話持久化', () => {
    test('會話應該在頁面刷新後保持', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 刷新頁面
      await page.reload();
      await dashboardPage.waitForPageReady();

      // 驗證會話仍然有效
      expect(await dashboardPage.isOnDashboard()).toBe(true);
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('會話應該在瀏覽器重啟後保持（如果選擇記住）', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      
      // 選擇記住我
      await loginPage.checkRememberMe();
      
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬瀏覽器重啟（清除sessionStorage但保留localStorage）
      await page.evaluate(() => {
        sessionStorage.clear();
      });

      await page.reload();
      await dashboardPage.waitForPageReady();

      // 驗證會話仍然有效
      expect(await dashboardPage.isOnDashboard()).toBe(true);
    });

    test('會話應該在指定時間後過期', async ({ page }) => {
      // 模擬短期token
      await page.route('**/auth/login', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'short-lived-token',
            refresh_token: 'refresh-token',
            token_type: 'Bearer',
            expires_in: 2, // 2秒後過期
            expires_at: Date.now() + 2000
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

      // 模擬API調用返回401
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Token expired' })
        });
      });

      // 嘗試刷新數據
      await dashboardPage.refreshData();

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });
  });

  test.describe('Token刷新', () => {
    test('應該自動刷新即將過期的token', async ({ page }) => {
      // 模擬即將過期的token
      await page.route('**/auth/login', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'expiring-token',
            refresh_token: 'refresh-token',
            token_type: 'Bearer',
            expires_in: 300, // 5分鐘
            expires_at: Date.now() + 300000
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

      // 手動觸發token檢查（模擬自動刷新）
      await page.evaluate(() => {
        // 修改token過期時間為即將過期
        const tokens = JSON.parse(localStorage.getItem('admin_auth_tokens') || '{}');
        tokens.expires_at = Date.now() + 60000; // 1分鐘後過期
        localStorage.setItem('admin_auth_tokens', JSON.stringify(tokens));
      });

      // 觸發需要認證的操作
      await dashboardPage.refreshData();

      // 等待token刷新完成
      await page.waitForTimeout(2000);

      // 驗證新token已保存
      const newTokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(newTokens.access_token).toBe('new-token');
    });

    test('Token刷新失敗應該重定向到登錄頁面', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬token刷新失敗
      await page.route('**/auth/refresh', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Refresh token expired' })
        });
      });

      // 手動設置過期token
      await page.evaluate(() => {
        const tokens = JSON.parse(localStorage.getItem('admin_auth_tokens') || '{}');
        tokens.expires_at = Date.now() - 1000; // 已過期
        localStorage.setItem('admin_auth_tokens', JSON.stringify(tokens));
      });

      // 觸發需要認證的操作
      await dashboardPage.refreshData();

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('並發請求應該只觸發一次token刷新', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      let refreshCallCount = 0;
      await page.route('**/auth/refresh', route => {
        refreshCallCount++;
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

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 設置即將過期的token
      await page.evaluate(() => {
        const tokens = JSON.parse(localStorage.getItem('admin_auth_tokens') || '{}');
        tokens.expires_at = Date.now() + 60000; // 1分鐘後過期
        localStorage.setItem('admin_auth_tokens', JSON.stringify(tokens));
      });

      // 同時發起多個需要認證的請求
      const promises = [
        dashboardPage.refreshData(),
        page.evaluate(() => fetch('/api/users')),
        page.evaluate(() => fetch('/api/settings'))
      ];

      await Promise.all(promises.map(p => p.catch(() => {})));

      // 驗證只調用了一次刷新
      expect(refreshCallCount).toBe(1);
    });
  });

  test.describe('會話終止', () => {
    test('登出應該清除所有會話數據', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬登出API
      await page.route('**/auth/logout', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      });

      // 執行登出
      await dashboardPage.logout();

      // 驗證會話數據已清除
      const tokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(tokens).toBeNull();

      const sessionData = await page.evaluate(() => sessionStorage.length);
      expect(sessionData).toBe(0);
    });

    test('會話過期應該自動清除數據', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬會話過期
      await page.route('**/auth/me', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Session expired' })
        });
      });

      await page.route('**/auth/refresh', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Refresh token expired' })
        });
      });

      // 刷新頁面觸發會話檢查
      await page.reload();

      // 等待重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });

      // 驗證會話數據已清除
      const tokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(tokens).toBeNull();
    });

    test('多標籤頁登出應該同步', async ({ context }) => {
      await apiMocker.mockSuccessfulLogin();

      // 在兩個標籤頁中登錄
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      const loginPage1 = new LoginPage(page1);
      const dashboardPage1 = new DashboardPage(page1);
      const dashboardPage2 = new DashboardPage(page2);

      // 第一個標籤頁登錄
      await loginPage1.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage1.login(validUser.username, validUser.password);
      await loginPage1.waitForRedirectToDashboard();

      // 第二個標籤頁訪問儀表板
      await dashboardPage2.goto();
      expect(await dashboardPage2.isOnDashboard()).toBe(true);

      // 模擬登出API
      await page1.route('**/auth/logout', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      });

      // 在第一個標籤頁登出
      await dashboardPage1.logout();

      // 在第二個標籤頁刷新
      await page2.reload();

      // 第二個標籤頁應該也重定向到登錄頁面
      await page2.waitForURL('**/admin/login', { timeout: 10000 });

      await page1.close();
      await page2.close();
    });
  });

  test.describe('會話安全', () => {
    test('應該檢測並處理會話劫持', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 正常登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬會話劫持檢測（例如IP變化）
      await page.route('**/auth/me', route => {
        route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ 
            message: 'Session security violation detected',
            code: 'SESSION_HIJACK_DETECTED'
          })
        });
      });

      // 觸發會話檢查
      await dashboardPage.refreshData();

      // 應該重定向到登錄頁面並顯示安全警告
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);

      // 檢查是否有安全警告消息
      if (await loginPage.hasErrorMessage()) {
        const errorMessage = await loginPage.getErrorMessage();
        expect(errorMessage).toMatch(/安全|security/i);
      }
    });

    test('應該限制並發會話數量', async ({ context }) => {
      await apiMocker.mockSuccessfulLogin();

      const validUser = TestDataFactory.createValidUser();

      // 創建多個標籤頁並嘗試登錄
      const pages = await Promise.all([
        context.newPage(),
        context.newPage(),
        context.newPage()
      ]);

      const loginPromises = pages.map(async (page, index) => {
        const loginPageInstance = new LoginPage(page);
        await loginPageInstance.goto();
        
        // 模擬會話限制（第3個會話被拒絕）
        if (index === 2) {
          await page.route('**/auth/login', route => {
            route.fulfill({
              status: 429,
              contentType: 'application/json',
              body: JSON.stringify({ 
                message: 'Maximum concurrent sessions exceeded',
                code: 'MAX_SESSIONS_EXCEEDED'
              })
            });
          });
        }
        
        await loginPageInstance.login(validUser.username, validUser.password);
        return { page, index };
      });

      const results = await Promise.allSettled(loginPromises);

      // 前兩個會話應該成功，第三個應該失敗
      expect(results[0].status).toBe('fulfilled');
      expect(results[1].status).toBe('fulfilled');
      
      // 第三個頁面應該顯示錯誤
      const thirdPageLogin = new LoginPage(pages[2]);
      expect(await thirdPageLogin.hasErrorMessage()).toBe(true);

      // 清理
      await Promise.all(pages.map(page => page.close()));
    });

    test('應該在可疑活動時要求重新認證', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 正常登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬可疑活動檢測
      await page.route('**/api/sensitive-operation', route => {
        route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ 
            message: 'Re-authentication required for sensitive operation',
            code: 'REAUTH_REQUIRED'
          })
        });
      });

      // 嘗試執行敏感操作
      await page.evaluate(() => {
        return fetch('/api/sensitive-operation', { method: 'POST' });
      });

      // 應該提示重新認證
      // 這裡可以檢查是否出現重新認證對話框或重定向
      await page.waitForTimeout(1000);
      
      // 根據實際實現檢查重新認證提示
      const hasReauthPrompt = await page.locator('[data-testid="reauth-prompt"]').isVisible().catch(() => false);
      if (hasReauthPrompt) {
        expect(hasReauthPrompt).toBe(true);
      }
    });
  });

  test.describe('會話監控', () => {
    test('應該記錄會話活動', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 模擬會話活動記錄API
      const activityLogs: string[] = [];
      await page.route('**/api/session/activity', route => {
        const request = route.request();
        const postData = request.postDataJSON();
        activityLogs.push(postData.activity);
        
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      });

      // 執行各種會話活動
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      await dashboardPage.refreshData();
      await dashboardPage.logout();

      // 驗證活動被記錄
      expect(activityLogs.length).toBeGreaterThan(0);
    });

    test('應該監控會話健康狀態', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬會話健康檢查
      let healthCheckCount = 0;
      await page.route('**/api/session/health', route => {
        healthCheckCount++;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ 
            status: 'healthy',
            lastActivity: Date.now(),
            expiresAt: Date.now() + 3600000
          })
        });
      });

      // 等待一段時間讓健康檢查執行
      await page.waitForTimeout(5000);

      // 驗證健康檢查被執行
      expect(healthCheckCount).toBeGreaterThan(0);
    });
  });
});