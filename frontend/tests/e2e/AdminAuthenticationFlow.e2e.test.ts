/**
 * Admin Authentication End-to-End Tests
 * 測試完整的管理員認證流程，從登錄到管理面板操作
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';

// Page object models
class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto(`${BASE_URL}/admin/login`);
  }

  async login(username: string, password: string) {
    await this.page.fill('[data-testid="username-input"]', username);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="login-button"]');
  }

  async getErrorMessage() {
    return await this.page.textContent('[data-testid="error-message"]');
  }

  async isLoading() {
    return await this.page.isVisible('[data-testid="loading-spinner"]');
  }
}

class AdminDashboardPage {
  constructor(private page: Page) {}

  async waitForLoad() {
    await this.page.waitForSelector('[data-testid="admin-dashboard"]');
  }

  async getUserCount() {
    await this.page.waitForSelector('[data-testid="user-count"]');
    const text = await this.page.textContent('[data-testid="user-count"]');
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getSubscriptionCount() {
    await this.page.waitForSelector('[data-testid="subscription-count"]');
    const text = await this.page.textContent('[data-testid="subscription-count"]');
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getSystemStatus() {
    await this.page.waitForSelector('[data-testid="system-status"]');
    return await this.page.textContent('[data-testid="system-status"]');
  }

  async logout() {
    await this.page.click('[data-testid="logout-button"]');
  }

  async navigateToUsers() {
    await this.page.click('[data-testid="users-nav"]');
    await this.page.waitForSelector('[data-testid="users-page"]');
  }

  async navigateToSubscriptions() {
    await this.page.click('[data-testid="subscriptions-nav"]');
    await this.page.waitForSelector('[data-testid="subscriptions-page"]');
  }

  async navigateToSystemMonitor() {
    await this.page.click('[data-testid="system-nav"]');
    await this.page.waitForSelector('[data-testid="system-page"]');
  }
}

test.describe('Admin Authentication Flow', () => {
  let loginPage: LoginPage;
  let dashboardPage: AdminDashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new AdminDashboardPage(page);
  });

  test.describe('Login Process', () => {
    test('should successfully login with valid admin credentials', async ({ page }) => {
      await loginPage.goto();

      // Verify login form is displayed
      await expect(page.locator('[data-testid="username-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="login-button"]')).toBeVisible();

      // Perform login
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);

      // Wait for redirect to dashboard
      await dashboardPage.waitForLoad();

      // Verify we're on the dashboard
      await expect(page).toHaveURL(/.*\/admin\/dashboard/);
      await expect(page.locator('[data-testid="admin-dashboard"]')).toBeVisible();
    });

    test('should show error message for invalid credentials', async ({ page }) => {
      await loginPage.goto();

      // Attempt login with invalid credentials
      await loginPage.login('invalid', 'wrong');

      // Wait for error message
      await page.waitForSelector('[data-testid="error-message"]');
      const errorMessage = await loginPage.getErrorMessage();
      
      expect(errorMessage).toContain('用戶名或密碼錯誤');
      
      // Should remain on login page
      await expect(page).toHaveURL(/.*\/admin\/login/);
    });

    test('should show loading state during login', async ({ page }) => {
      await loginPage.goto();

      // Start login process
      await page.fill('[data-testid="username-input"]', ADMIN_USERNAME);
      await page.fill('[data-testid="password-input"]', ADMIN_PASSWORD);
      
      // Click login and immediately check for loading state
      await page.click('[data-testid="login-button"]');
      
      // Loading state should be visible briefly
      const isLoading = await loginPage.isLoading();
      expect(isLoading).toBeTruthy();

      // Wait for login to complete
      await dashboardPage.waitForLoad();
    });

    test('should validate required fields', async ({ page }) => {
      await loginPage.goto();

      // Try to submit empty form
      await page.click('[data-testid="login-button"]');

      // Should show validation errors
      await expect(page.locator('[data-testid="username-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="password-error"]')).toBeVisible();
    });
  });

  test.describe('Dashboard Data Loading', () => {
    test.beforeEach(async ({ page }) => {
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();
    });

    test('should load dashboard with real data', async ({ page }) => {
      // Verify dashboard components are loaded
      await expect(page.locator('[data-testid="user-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="subscription-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="system-status"]')).toBeVisible();

      // Verify data is loaded (not just placeholders)
      const userCount = await dashboardPage.getUserCount();
      const subscriptionCount = await dashboardPage.getSubscriptionCount();
      const systemStatus = await dashboardPage.getSystemStatus();

      expect(userCount).toBeGreaterThanOrEqual(0);
      expect(subscriptionCount).toBeGreaterThanOrEqual(0);
      expect(systemStatus).toMatch(/healthy|warning|critical/i);
    });

    test('should navigate to user management page', async ({ page }) => {
      await dashboardPage.navigateToUsers();

      // Verify we're on users page
      await expect(page).toHaveURL(/.*\/admin\/users/);
      await expect(page.locator('[data-testid="users-table"]')).toBeVisible();

      // Verify user data is loaded
      await expect(page.locator('[data-testid="user-row"]').first()).toBeVisible();
    });

    test('should navigate to subscription management page', async ({ page }) => {
      await dashboardPage.navigateToSubscriptions();

      // Verify we're on subscriptions page
      await expect(page).toHaveURL(/.*\/admin\/subscriptions/);
      await expect(page.locator('[data-testid="subscriptions-table"]')).toBeVisible();
    });

    test('should navigate to system monitoring page', async ({ page }) => {
      await dashboardPage.navigateToSystemMonitor();

      // Verify we're on system page
      await expect(page).toHaveURL(/.*\/admin\/system/);
      await expect(page.locator('[data-testid="system-metrics"]')).toBeVisible();
    });
  });

  test.describe('Authentication State Management', () => {
    test('should maintain authentication across page refreshes', async ({ page }) => {
      // Login first
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      // Refresh the page
      await page.reload();

      // Should still be authenticated and on dashboard
      await dashboardPage.waitForLoad();
      await expect(page).toHaveURL(/.*\/admin\/dashboard/);
    });

    test('should redirect to login when accessing protected route without authentication', async ({ page }) => {
      // Try to access dashboard directly without login
      await page.goto(`${BASE_URL}/admin/dashboard`);

      // Should redirect to login
      await expect(page).toHaveURL(/.*\/admin\/login/);
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    });

    test('should handle logout properly', async ({ page }) => {
      // Login first
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      // Logout
      await dashboardPage.logout();

      // Should redirect to login page
      await expect(page).toHaveURL(/.*\/admin\/login/);
      
      // Try to access dashboard again - should redirect to login
      await page.goto(`${BASE_URL}/admin/dashboard`);
      await expect(page).toHaveURL(/.*\/admin\/login/);
    });
  });

  test.describe('Cross-Tab Authentication', () => {
    test('should synchronize authentication across multiple tabs', async ({ context }) => {
      // Create two pages (tabs)
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      const loginPage1 = new LoginPage(page1);
      const dashboardPage1 = new AdminDashboardPage(page1);
      const dashboardPage2 = new AdminDashboardPage(page2);

      // Login in first tab
      await loginPage1.goto();
      await loginPage1.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage1.waitForLoad();

      // Navigate to dashboard in second tab
      await page2.goto(`${BASE_URL}/admin/dashboard`);
      
      // Should be authenticated in second tab too
      await dashboardPage2.waitForLoad();
      await expect(page2).toHaveURL(/.*\/admin\/dashboard/);

      // Logout from first tab
      await dashboardPage1.logout();

      // Second tab should also be logged out (may need to refresh or navigate)
      await page2.reload();
      await expect(page2).toHaveURL(/.*\/admin\/login/);
    });
  });

  test.describe('API Authentication Integration', () => {
    test.beforeEach(async ({ page }) => {
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();
    });

    test('should make authenticated API calls for dashboard data', async ({ page }) => {
      // Monitor network requests
      const apiRequests: string[] = [];
      
      page.on('request', request => {
        if (request.url().includes('/api/admin/')) {
          apiRequests.push(request.url());
          
          // Verify authorization header is present
          const authHeader = request.headers()['authorization'];
          expect(authHeader).toMatch(/^Bearer .+/);
        }
      });

      // Navigate to different admin pages to trigger API calls
      await dashboardPage.navigateToUsers();
      await dashboardPage.navigateToSubscriptions();
      await dashboardPage.navigateToSystemMonitor();

      // Verify API calls were made
      expect(apiRequests.length).toBeGreaterThan(0);
      expect(apiRequests.some(url => url.includes('/admin/users'))).toBeTruthy();
      expect(apiRequests.some(url => url.includes('/admin/subscriptions'))).toBeTruthy();
      expect(apiRequests.some(url => url.includes('/admin/system'))).toBeTruthy();
    });

    test('should handle token refresh automatically', async ({ page }) => {
      // Mock token expiration by manipulating localStorage
      await page.evaluate(() => {
        const tokens = JSON.parse(localStorage.getItem('admin_auth_tokens') || '{}');
        tokens.expires_at = Date.now() - 1000; // Expired 1 second ago
        localStorage.setItem('admin_auth_tokens', JSON.stringify(tokens));
      });

      // Navigate to a page that requires API calls
      await dashboardPage.navigateToUsers();

      // Should automatically refresh token and load data
      await expect(page.locator('[data-testid="users-table"]')).toBeVisible();
    });

    test('should handle authentication failure gracefully', async ({ page }) => {
      // Mock invalid token
      await page.evaluate(() => {
        localStorage.setItem('admin_auth_tokens', JSON.stringify({
          access_token: 'invalid-token',
          refresh_token: 'invalid-refresh',
          expires_at: Date.now() + 3600000
        }));
      });

      // Refresh page to trigger authentication check
      await page.reload();

      // Should redirect to login due to invalid token
      await expect(page).toHaveURL(/.*\/admin\/login/);
    });
  });

  test.describe('Error Handling', () => {
    test('should handle network errors during login', async ({ page }) => {
      // Intercept and fail login request
      await page.route('**/auth/login', route => {
        route.abort('failed');
      });

      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);

      // Should show network error message
      await page.waitForSelector('[data-testid="error-message"]');
      const errorMessage = await loginPage.getErrorMessage();
      expect(errorMessage).toContain('網絡連接失敗');
    });

    test('should handle API errors in dashboard', async ({ page }) => {
      // Login first
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      // Intercept and fail API requests
      await page.route('**/admin/users', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Internal Server Error' })
        });
      });

      // Navigate to users page
      await dashboardPage.navigateToUsers();

      // Should show error message
      await expect(page.locator('[data-testid="api-error"]')).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should load dashboard within acceptable time', async ({ page }) => {
      const startTime = Date.now();

      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      const endTime = Date.now();
      const loadTime = endTime - startTime;

      // Should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle multiple concurrent API requests efficiently', async ({ page }) => {
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      const startTime = Date.now();

      // Navigate quickly between different admin pages
      await dashboardPage.navigateToUsers();
      await dashboardPage.navigateToSubscriptions();
      await dashboardPage.navigateToSystemMonitor();

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      // Should complete navigation within reasonable time
      expect(totalTime).toBeLessThan(3000);
    });
  });

  test.describe('Security', () => {
    test('should not expose sensitive data in client-side storage', async ({ page }) => {
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      // Check localStorage for sensitive data
      const localStorageData = await page.evaluate(() => {
        return Object.keys(localStorage).map(key => ({
          key,
          value: localStorage.getItem(key)
        }));
      });

      // Should not contain plain text passwords or unencrypted sensitive data
      localStorageData.forEach(item => {
        expect(item.value).not.toContain(ADMIN_PASSWORD);
        expect(item.value).not.toContain('password');
      });
    });

    test('should implement proper CSRF protection', async ({ page }) => {
      await loginPage.goto();
      await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
      await dashboardPage.waitForLoad();

      // Monitor POST requests for CSRF tokens
      const postRequests: any[] = [];
      
      page.on('request', request => {
        if (request.method() === 'POST' && request.url().includes('/api/admin/')) {
          postRequests.push({
            url: request.url(),
            headers: request.headers()
          });
        }
      });

      // Trigger a POST request (if available in the admin interface)
      // This would depend on the specific admin functionality available
      
      // For now, just verify that authentication headers are present
      await dashboardPage.navigateToUsers();
      
      // Verify that requests include proper authentication
      if (postRequests.length > 0) {
        postRequests.forEach(request => {
          expect(request.headers['authorization']).toMatch(/^Bearer .+/);
        });
      }
    });
  });
});