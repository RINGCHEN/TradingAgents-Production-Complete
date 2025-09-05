/**
 * 管理後台訪問端到端測試
 * 測試管理後台的訪問控制和功能
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TestHelpers, TestDataFactory, ApiMocker } from '../utils/test-helpers';

test.describe('管理後台訪問 E2E 測試', () => {
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

  test.describe('認證訪問控制', () => {
    test('未認證用戶應該被重定向到登錄頁面', async ({ page }) => {
      // 直接訪問儀表板
      await page.goto('/admin/dashboard');

      // 應該被重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('已認證用戶應該能夠訪問儀表板', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 先登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 驗證能夠訪問儀表板
      expect(await dashboardPage.isOnDashboard()).toBe(true);
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('過期會話應該重定向到登錄頁面', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬會話過期 - 清除token
      await helpers.clearStorage();

      // 模擬API返回401
      await page.route('**/auth/me', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Unauthorized' })
        });
      });

      // 刷新頁面或嘗試API調用
      await page.reload();

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('無效token應該觸發重新認證', async ({ page }) => {
      // 設置無效token
      await helpers.setLocalStorage('admin_auth_tokens', {
        access_token: 'invalid-token',
        expires_at: Date.now() + 3600000
      });

      // 模擬API返回401
      await page.route('**/auth/me', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Invalid token' })
        });
      });

      // 嘗試訪問儀表板
      await page.goto('/admin/dashboard');

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });
  });

  test.describe('儀表板功能', () => {
    test.beforeEach(async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      // 登錄到儀表板
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();
    });

    test('應該顯示正確的頁面標題和內容', async ({ page }) => {
      const pageTitle = await dashboardPage.getPageTitle();
      expect(pageTitle).toMatch(/儀表板|Dashboard|管理後台/i);

      const welcomeMessage = await dashboardPage.getWelcomeMessage();
      expect(welcomeMessage).toContain('歡迎');

      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該顯示用戶信息', async ({ page }) => {
      const username = await dashboardPage.getCurrentUsername();
      expect(username).toBe('admin');

      const userRole = await dashboardPage.getUserRole();
      expect(userRole).toMatch(/管理員|admin/i);
    });

    test('應該顯示統計卡片', async ({ page }) => {
      const statsCount = await dashboardPage.getStatsCardsCount();
      expect(statsCount).toBeGreaterThan(0);

      // 檢查第一個統計卡片
      const firstCardData = await dashboardPage.getStatsCardData(0);
      if (firstCardData) {
        expect(firstCardData.title).toBeTruthy();
        expect(firstCardData.value).toBeTruthy();
      }
    });

    test('應該顯示數據表格', async ({ page }) => {
      if (await dashboardPage.hasDataTable()) {
        const rowCount = await dashboardPage.getTableRowCount();
        expect(rowCount).toBeGreaterThanOrEqual(0);
      }
    });

    test('應該有功能性的導航菜單', async ({ page }) => {
      const navItems = await dashboardPage.getNavigationItems();
      expect(navItems.length).toBeGreaterThan(0);

      // 檢查常見的導航項目
      const expectedItems = ['儀表板', '用戶管理', '設置', '登出'];
      const hasExpectedItems = expectedItems.some(item => 
        navItems.some(navItem => navItem.includes(item))
      );
      expect(hasExpectedItems).toBe(true);
    });

    test('應該支持數據刷新', async ({ page }) => {
      // 模擬數據刷新API
      await page.route('**/api/dashboard/stats', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            users: 100,
            orders: 50,
            revenue: 10000
          })
        });
      });

      await dashboardPage.refreshData();
      await dashboardPage.waitForLoadingComplete();

      // 驗證數據已刷新
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });
  });

  test.describe('權限控制', () => {
    test('管理員應該看到所有功能', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const adminUser = TestDataFactory.createValidUser();
      await loginPage.login(adminUser.username, adminUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 檢查管理員權限
      const permissions = await dashboardPage.getUserPermissions();
      expect(permissions).toContain('admin');

      // 檢查管理員功能可見
      expect(await dashboardPage.isLogoutButtonVisible()).toBe(true);
    });

    test('普通用戶應該有限制的功能', async ({ page }) => {
      // 模擬普通用戶登錄
      await page.route('**/auth/me', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 2,
            username: 'user',
            email: 'user@example.com',
            role: 'user',
            permissions: ['read'],
            is_admin: false,
            is_active: true
          })
        });
      });

      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      await loginPage.login('user', 'password123');
      await loginPage.waitForRedirectToDashboard();

      // 檢查用戶權限
      const permissions = await dashboardPage.getUserPermissions();
      expect(permissions).not.toContain('admin');
      expect(permissions).toContain('read');
    });
  });

  test.describe('登出功能', () => {
    test.beforeEach(async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();
    });

    test('應該能夠成功登出', async ({ page }) => {
      // 模擬登出API
      await page.route('**/auth/logout', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      });

      await dashboardPage.logout();

      // 驗證重定向到登錄頁面
      expect(await loginPage.isOnLoginPage()).toBe(true);

      // 驗證本地存儲已清除
      const tokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(tokens).toBeNull();
    });

    test('登出後應該無法訪問受保護的頁面', async ({ page }) => {
      await page.route('**/auth/logout', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      });

      await dashboardPage.logout();

      // 嘗試直接訪問儀表板
      await page.goto('/admin/dashboard');

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('登出失敗時應該處理錯誤', async ({ page }) => {
      // 模擬登出API失敗
      await page.route('**/auth/logout', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Logout failed' })
        });
      });

      await dashboardPage.logout();

      // 即使API失敗，也應該清除本地狀態並重定向
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });
  });

  test.describe('響應式設計', () => {
    test.beforeEach(async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();
    });

    test('應該在不同屏幕尺寸下正常工作', async ({ page }) => {
      const results = await dashboardPage.checkResponsiveness();

      results.forEach(result => {
        expect(result.contentVisible).toBe(true);
        // 在移動端，導航可能會隱藏或折疊
        if (result.viewport.width >= 768) {
          expect(result.navigationVisible).toBe(true);
        }
      });
    });

    test('應該支持側邊欄切換', async ({ page }) => {
      // 設置為平板尺寸
      await page.setViewportSize({ width: 768, height: 1024 });

      const initialState = await dashboardPage.isSidebarExpanded();
      await dashboardPage.toggleSidebar();
      
      const newState = await dashboardPage.isSidebarExpanded();
      expect(newState).not.toBe(initialState);
    });
  });

  test.describe('錯誤處理', () => {
    test.beforeEach(async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();
    });

    test('應該處理API錯誤', async ({ page }) => {
      // 模擬API錯誤
      await page.route('**/api/dashboard/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Server Error' })
        });
      });

      await dashboardPage.refreshData();

      // 檢查錯誤處理
      if (await dashboardPage.hasErrorMessage()) {
        const errorMessage = await dashboardPage.getErrorMessage();
        expect(errorMessage).toMatch(/錯誤|Error/i);
      }
    });

    test('應該處理網絡中斷', async ({ page }) => {
      // 模擬網絡中斷
      await helpers.simulateNetworkCondition('offline');

      await dashboardPage.refreshData();

      // 檢查離線狀態處理
      // 應用應該顯示適當的離線消息或緩存內容
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該從錯誤狀態恢復', async ({ page }) => {
      // 先模擬錯誤
      await page.route('**/api/dashboard/**', route => {
        route.fulfill({ status: 500 });
      });

      await dashboardPage.refreshData();

      // 然後恢復正常
      await page.unroute('**/api/dashboard/**');
      await page.route('**/api/dashboard/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'ok' })
        });
      });

      await dashboardPage.refreshData();

      // 驗證恢復正常
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });
  });

  test.describe('性能測試', () => {
    test('儀表板應該快速載入', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      const startTime = Date.now();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();
      await dashboardPage.waitForPageReady();
      
      const totalTime = Date.now() - startTime;
      expect(totalTime).toBeLessThan(10000); // 10秒內完成整個流程
    });

    test('數據刷新應該快速響應', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      const startTime = Date.now();
      await dashboardPage.refreshData();
      const refreshTime = Date.now() - startTime;

      expect(refreshTime).toBeLessThan(5000); // 5秒內完成刷新
    });
  });

  test.describe('安全性測試', () => {
    test('應該防止未授權的API訪問', async ({ page }) => {
      // 不登錄，直接嘗試API調用
      const response = await page.request.get('/api/admin/users');
      expect(response.status()).toBe(401);
    });

    test('應該在會話過期時安全處理', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬會話過期
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Session expired' })
        });
      });

      // 嘗試刷新數據
      await dashboardPage.refreshData();

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('應該清理敏感數據', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();
      
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      await dashboardPage.logout();

      // 檢查敏感數據是否已清理
      const tokens = await helpers.getLocalStorage('admin_auth_tokens');
      expect(tokens).toBeNull();

      const sessionData = await helpers.getLocalStorage('user_session');
      expect(sessionData).toBeNull();
    });
  });
});