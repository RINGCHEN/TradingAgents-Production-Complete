/**
 * 用戶登錄端到端測試
 * 測試完整的用戶登錄流程和各種場景
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TestHelpers, TestDataFactory, ApiMocker } from '../utils/test-helpers';

test.describe('用戶登錄 E2E 測試', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let helpers: TestHelpers;
  let apiMocker: ApiMocker;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    helpers = new TestHelpers(page);
    apiMocker = new ApiMocker(page);

    // 清理存儲
    await helpers.clearStorage();
  });

  test.describe('成功登錄場景', () => {
    test('應該能夠使用有效憑證成功登錄', async ({ page }) => {
      // 模擬成功的API響應
      await apiMocker.mockSuccessfulLogin();

      // 導航到登錄頁面
      await loginPage.goto();
      
      // 驗證頁面載入
      expect(await loginPage.isOnLoginPage()).toBe(true);
      expect(await loginPage.getPageTitle()).toContain('登錄');

      // 執行登錄
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);

      // 等待登錄完成
      await loginPage.waitForLoginComplete();

      // 驗證重定向到儀表板
      await loginPage.waitForRedirectToDashboard();
      expect(await dashboardPage.isOnDashboard()).toBe(true);

      // 驗證儀表板內容載入
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
      expect(await dashboardPage.getCurrentUsername()).toBe(validUser.username);
    });

    test('應該在登錄後保持認證狀態', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 執行登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 刷新頁面
      await page.reload();
      await dashboardPage.waitForPageReady();

      // 驗證仍然在儀表板頁面
      expect(await dashboardPage.isOnDashboard()).toBe(true);
      expect(await dashboardPage.isDashboardContentLoaded()).toBe(true);
    });

    test('應該能夠使用Enter鍵提交登錄表單', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      
      await loginPage.fillUsername(validUser.username);
      await loginPage.fillPassword(validUser.password);
      await loginPage.submitWithEnter();

      await loginPage.waitForRedirectToDashboard();
      expect(await dashboardPage.isOnDashboard()).toBe(true);
    });

    test('應該顯示正確的用戶信息', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 驗證用戶信息
      const username = await dashboardPage.getCurrentUsername();
      const welcomeMessage = await dashboardPage.getWelcomeMessage();
      
      expect(username).toBe(validUser.username);
      expect(welcomeMessage).toContain('歡迎');
    });
  });

  test.describe('登錄失敗場景', () => {
    test('應該顯示無效憑證錯誤', async ({ page }) => {
      await apiMocker.mockFailedLogin();

      await loginPage.goto();
      const invalidUser = TestDataFactory.createInvalidUser();
      await loginPage.login(invalidUser.username, invalidUser.password);

      // 驗證錯誤消息
      expect(await loginPage.hasErrorMessage()).toBe(true);
      const errorMessage = await loginPage.getErrorMessage();
      expect(errorMessage).toMatch(/用戶名或密碼錯誤|Invalid credentials/i);

      // 驗證仍在登錄頁面
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('應該處理網絡錯誤', async ({ page }) => {
      await apiMocker.mockNetworkError();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);

      // 驗證網絡錯誤消息
      expect(await loginPage.hasErrorMessage()).toBe(true);
      const errorMessage = await loginPage.getErrorMessage();
      expect(errorMessage).toMatch(/網絡|連接|Network/i);
    });

    test('應該處理服務器錯誤', async ({ page }) => {
      await apiMocker.mockServerError();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);

      // 驗證服務器錯誤消息
      expect(await loginPage.hasErrorMessage()).toBe(true);
      const errorMessage = await loginPage.getErrorMessage();
      expect(errorMessage).toMatch(/服務器錯誤|Server Error/i);
    });

    test('應該在多次失敗後顯示適當的錯誤', async ({ page }) => {
      await apiMocker.mockFailedLogin();

      await loginPage.goto();
      const invalidUser = TestDataFactory.createInvalidUser();

      // 嘗試多次登錄
      for (let i = 0; i < 3; i++) {
        await loginPage.clearForm();
        await loginPage.login(invalidUser.username, invalidUser.password);
        
        expect(await loginPage.hasErrorMessage()).toBe(true);
        await page.waitForTimeout(1000); // 等待錯誤消息穩定
      }

      // 驗證錯誤消息仍然顯示
      expect(await loginPage.hasErrorMessage()).toBe(true);
    });
  });

  test.describe('表單驗證', () => {
    test('應該驗證必填字段', async ({ page }) => {
      await loginPage.goto();

      // 嘗試提交空表單
      await loginPage.clickLogin();

      // 驗證驗證錯誤
      const validationErrors = await loginPage.getValidationErrors();
      expect(Object.keys(validationErrors).length).toBeGreaterThan(0);
    });

    test('應該驗證用戶名格式', async ({ page }) => {
      await loginPage.goto();

      // 輸入無效用戶名
      await loginPage.fillUsername('');
      await loginPage.fillPassword('validpassword');
      await loginPage.clickLogin();

      const validationErrors = await loginPage.getValidationErrors();
      expect(validationErrors.username).toBeDefined();
    });

    test('應該驗證密碼長度', async ({ page }) => {
      await loginPage.goto();

      // 輸入過短密碼
      await loginPage.fillUsername('validuser');
      await loginPage.fillPassword('123');
      await loginPage.clickLogin();

      const validationErrors = await loginPage.getValidationErrors();
      expect(validationErrors.password).toBeDefined();
    });

    test('應該在用戶開始輸入時清除錯誤', async ({ page }) => {
      await apiMocker.mockFailedLogin();

      await loginPage.goto();
      const invalidUser = TestDataFactory.createInvalidUser();
      await loginPage.login(invalidUser.username, invalidUser.password);

      // 驗證錯誤顯示
      expect(await loginPage.hasErrorMessage()).toBe(true);

      // 開始輸入新內容
      await loginPage.fillUsername('newuser');

      // 等待錯誤消息消失
      await page.waitForTimeout(500);
      expect(await loginPage.hasErrorMessage()).toBe(false);
    });
  });

  test.describe('用戶體驗', () => {
    test('應該顯示載入狀態', async ({ page }) => {
      // 模擬慢速響應
      await page.route('**/auth/login', async route => {
        await page.waitForTimeout(2000);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(TestDataFactory.createMockTokens())
        });
      });

      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      
      await loginPage.fillUsername(validUser.username);
      await loginPage.fillPassword(validUser.password);
      await loginPage.clickLogin();

      // 驗證載入狀態
      expect(await loginPage.isLoading()).toBe(true);
      expect(await loginPage.isLoginButtonDisabled()).toBe(true);

      // 等待載入完成
      await loginPage.waitForLoginComplete();
      expect(await loginPage.isLoading()).toBe(false);
    });

    test('應該支持鍵盤導航', async ({ page }) => {
      await loginPage.goto();

      // 使用Tab鍵導航
      await page.keyboard.press('Tab');
      expect(await loginPage.isInputFocused('username')).toBe(true);

      await page.keyboard.press('Tab');
      expect(await loginPage.isInputFocused('password')).toBe(true);

      await page.keyboard.press('Tab');
      // 登錄按鈕應該獲得焦點
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBe('BUTTON');
    });

    test('應該支持密碼可見性切換', async ({ page }) => {
      await loginPage.goto();

      await loginPage.fillPassword('testpassword');
      
      // 檢查密碼初始狀態（隱藏）
      expect(await loginPage.isPasswordVisible()).toBe(false);

      // 切換密碼可見性
      await loginPage.togglePasswordVisibility();
      expect(await loginPage.isPasswordVisible()).toBe(true);

      // 再次切換
      await loginPage.togglePasswordVisibility();
      expect(await loginPage.isPasswordVisible()).toBe(false);
    });

    test('應該在不同視窗大小下正常工作', async ({ page }) => {
      const viewports = [
        { width: 1920, height: 1080 }, // Desktop
        { width: 768, height: 1024 },  // Tablet
        { width: 375, height: 667 }    // Mobile
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await loginPage.goto();

        // 驗證表單元素可見
        expect(await loginPage.usernameInput.isVisible()).toBe(true);
        expect(await loginPage.passwordInput.isVisible()).toBe(true);
        expect(await loginPage.loginButton.isVisible()).toBe(true);
      }
    });
  });

  test.describe('安全性測試', () => {
    test('應該清除敏感數據', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 返回登錄頁面
      await loginPage.goto();

      // 驗證表單已清空
      const formData = await loginPage.getFormData();
      expect(formData.username).toBe('');
      expect(formData.password).toBe('');
    });

    test('應該處理會話過期', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      // 登錄
      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.login(validUser.username, validUser.password);
      await loginPage.waitForRedirectToDashboard();

      // 模擬會話過期
      await helpers.clearStorage();

      // 刷新頁面
      await page.reload();

      // 應該重定向到登錄頁面
      await page.waitForURL('**/admin/login', { timeout: 10000 });
      expect(await loginPage.isOnLoginPage()).toBe(true);
    });

    test('應該防止XSS攻擊', async ({ page }) => {
      await apiMocker.mockFailedLogin();

      await loginPage.goto();

      // 嘗試XSS攻擊
      const xssPayload = '<script>alert("XSS")</script>';
      await loginPage.fillUsername(xssPayload);
      await loginPage.fillPassword('password');
      await loginPage.clickLogin();

      // 驗證XSS沒有執行
      const alerts = [];
      page.on('dialog', dialog => {
        alerts.push(dialog.message());
        dialog.dismiss();
      });

      await page.waitForTimeout(1000);
      expect(alerts).toHaveLength(0);
    });
  });

  test.describe('性能測試', () => {
    test('應該在合理時間內載入', async ({ page }) => {
      const startTime = Date.now();
      
      await loginPage.goto();
      await loginPage.waitForPageReady();
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(5000); // 5秒內載入
    });

    test('應該快速響應用戶輸入', async ({ page }) => {
      await loginPage.goto();

      const startTime = Date.now();
      await loginPage.fillUsername('testuser');
      const inputTime = Date.now() - startTime;

      expect(inputTime).toBeLessThan(1000); // 1秒內響應
    });

    test('應該處理大量快速點擊', async ({ page }) => {
      await apiMocker.mockSuccessfulLogin();

      await loginPage.goto();
      const validUser = TestDataFactory.createValidUser();
      await loginPage.fillUsername(validUser.username);
      await loginPage.fillPassword(validUser.password);

      // 快速多次點擊登錄按鈕
      for (let i = 0; i < 5; i++) {
        await loginPage.clickLogin();
      }

      // 應該只處理一次登錄
      await loginPage.waitForRedirectToDashboard();
      expect(await dashboardPage.isOnDashboard()).toBe(true);
    });
  });

  test.describe('可訪問性測試', () => {
    test('應該支持屏幕閱讀器', async ({ page }) => {
      await loginPage.goto();

      // 檢查ARIA標籤
      const usernameInput = loginPage.usernameInput;
      const passwordInput = loginPage.passwordInput;

      expect(await usernameInput.getAttribute('aria-label')).toBeTruthy();
      expect(await passwordInput.getAttribute('aria-label')).toBeTruthy();
    });

    test('應該有適當的焦點管理', async ({ page }) => {
      await loginPage.goto();

      // 頁面載入後，第一個輸入框應該獲得焦點
      expect(await loginPage.isInputFocused('username')).toBe(true);
    });

    test('應該支持高對比度模式', async ({ page }) => {
      await page.emulateMedia({ colorScheme: 'dark' });
      await loginPage.goto();

      // 驗證元素仍然可見
      expect(await loginPage.usernameInput.isVisible()).toBe(true);
      expect(await loginPage.passwordInput.isVisible()).toBe(true);
      expect(await loginPage.loginButton.isVisible()).toBe(true);
    });
  });
});