/**
 * 登錄頁面對象模型
 * 封裝登錄頁面的元素和操作
 */

import { Page, Locator } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';

export class LoginPage {
  private helpers: TestHelpers;

  // 頁面元素選擇器
  private readonly selectors = {
    usernameInput: '[data-testid="username-input"], input[name="username"], input[type="text"]',
    passwordInput: '[data-testid="password-input"], input[name="password"], input[type="password"]',
    loginButton: '[data-testid="login-button"], button[type="submit"], button:has-text("登錄"), button:has-text("Login")',
    errorMessage: '[data-testid="error-message"], .error-message, .alert-error',
    loadingIndicator: '[data-testid="loading"], .loading, .spinner',
    forgotPasswordLink: '[data-testid="forgot-password"], a:has-text("忘記密碼"), a:has-text("Forgot Password")',
    rememberMeCheckbox: '[data-testid="remember-me"], input[name="remember"]',
    
    // 表單驗證錯誤
    usernameError: '[data-testid="username-error"], .username-error',
    passwordError: '[data-testid="password-error"], .password-error',
    
    // 成功狀態
    successMessage: '[data-testid="success-message"], .success-message, .alert-success'
  };

  constructor(private page: Page) {
    this.helpers = new TestHelpers(page);
  }

  /**
   * 導航到登錄頁面
   */
  async goto() {
    await this.page.goto('/admin/login');
    await this.helpers.waitForPageLoad();
    await this.waitForPageReady();
  }

  /**
   * 等待頁面準備就緒
   */
  async waitForPageReady() {
    await this.helpers.waitForElement(this.selectors.usernameInput);
    await this.helpers.waitForElement(this.selectors.passwordInput);
    await this.helpers.waitForElement(this.selectors.loginButton);
  }

  /**
   * 獲取頁面元素
   */
  get usernameInput(): Locator {
    return this.page.locator(this.selectors.usernameInput).first();
  }

  get passwordInput(): Locator {
    return this.page.locator(this.selectors.passwordInput).first();
  }

  get loginButton(): Locator {
    return this.page.locator(this.selectors.loginButton).first();
  }

  get errorMessage(): Locator {
    return this.page.locator(this.selectors.errorMessage).first();
  }

  get loadingIndicator(): Locator {
    return this.page.locator(this.selectors.loadingIndicator).first();
  }

  get successMessage(): Locator {
    return this.page.locator(this.selectors.successMessage).first();
  }

  /**
   * 執行登錄操作
   */
  async login(username: string, password: string) {
    await this.fillUsername(username);
    await this.fillPassword(password);
    await this.clickLogin();
  }

  /**
   * 填寫用戶名
   */
  async fillUsername(username: string) {
    await this.usernameInput.clear();
    await this.usernameInput.fill(username);
  }

  /**
   * 填寫密碼
   */
  async fillPassword(password: string) {
    await this.passwordInput.clear();
    await this.passwordInput.fill(password);
  }

  /**
   * 點擊登錄按鈕
   */
  async clickLogin() {
    await this.loginButton.click();
  }

  /**
   * 等待登錄完成
   */
  async waitForLoginComplete() {
    // 等待載入指示器出現然後消失
    try {
      await this.loadingIndicator.waitFor({ state: 'visible', timeout: 2000 });
      await this.loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 });
    } catch {
      // 如果沒有載入指示器，直接等待頁面穩定
      await this.helpers.waitForPageLoad();
    }
  }

  /**
   * 等待並獲取錯誤消息
   */
  async getErrorMessage(): Promise<string> {
    await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 });
    return await this.errorMessage.textContent() || '';
  }

  /**
   * 檢查是否顯示錯誤消息
   */
  async hasErrorMessage(): Promise<boolean> {
    try {
      await this.errorMessage.waitFor({ state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 檢查是否顯示成功消息
   */
  async hasSuccessMessage(): Promise<boolean> {
    try {
      await this.successMessage.waitFor({ state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 檢查登錄按鈕是否被禁用
   */
  async isLoginButtonDisabled(): Promise<boolean> {
    return await this.loginButton.isDisabled();
  }

  /**
   * 檢查是否顯示載入狀態
   */
  async isLoading(): Promise<boolean> {
    try {
      await this.loadingIndicator.waitFor({ state: 'visible', timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 清空表單
   */
  async clearForm() {
    await this.usernameInput.clear();
    await this.passwordInput.clear();
  }

  /**
   * 檢查表單驗證錯誤
   */
  async getValidationErrors() {
    const errors: { [key: string]: string } = {};
    
    try {
      const usernameError = this.page.locator(this.selectors.usernameError);
      if (await usernameError.isVisible()) {
        errors.username = await usernameError.textContent() || '';
      }
    } catch {}

    try {
      const passwordError = this.page.locator(this.selectors.passwordError);
      if (await passwordError.isVisible()) {
        errors.password = await passwordError.textContent() || '';
      }
    } catch {}

    return errors;
  }

  /**
   * 檢查記住我選項
   */
  async checkRememberMe() {
    const checkbox = this.page.locator(this.selectors.rememberMeCheckbox);
    if (await checkbox.isVisible()) {
      await checkbox.check();
    }
  }

  /**
   * 點擊忘記密碼鏈接
   */
  async clickForgotPassword() {
    const link = this.page.locator(this.selectors.forgotPasswordLink);
    if (await link.isVisible()) {
      await link.click();
    }
  }

  /**
   * 使用鍵盤提交表單
   */
  async submitWithEnter() {
    await this.passwordInput.press('Enter');
  }

  /**
   * 檢查頁面標題
   */
  async getPageTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * 檢查URL是否正確
   */
  async isOnLoginPage(): Promise<boolean> {
    const url = this.page.url();
    return url.includes('/admin/login') || url.includes('/login');
  }

  /**
   * 等待重定向到儀表板
   */
  async waitForRedirectToDashboard() {
    await this.page.waitForURL('**/admin/dashboard', { timeout: 10000 });
  }

  /**
   * 檢查是否已重定向到儀表板
   */
  async isRedirectedToDashboard(): Promise<boolean> {
    const url = this.page.url();
    return url.includes('/admin/dashboard') || url.includes('/dashboard');
  }

  /**
   * 模擬慢速輸入
   */
  async slowType(selector: string, text: string, delay = 100) {
    const element = this.page.locator(selector);
    await element.clear();
    
    for (const char of text) {
      await element.type(char);
      await this.page.waitForTimeout(delay);
    }
  }

  /**
   * 檢查輸入框焦點狀態
   */
  async isInputFocused(inputType: 'username' | 'password'): Promise<boolean> {
    const selector = inputType === 'username' ? this.selectors.usernameInput : this.selectors.passwordInput;
    const element = this.page.locator(selector);
    return await element.evaluate(el => el === document.activeElement);
  }

  /**
   * 獲取表單數據
   */
  async getFormData() {
    return {
      username: await this.usernameInput.inputValue(),
      password: await this.passwordInput.inputValue()
    };
  }

  /**
   * 檢查密碼可見性切換
   */
  async togglePasswordVisibility() {
    const toggleButton = this.page.locator('[data-testid="password-toggle"], .password-toggle');
    if (await toggleButton.isVisible()) {
      await toggleButton.click();
    }
  }

  /**
   * 檢查密碼是否可見
   */
  async isPasswordVisible(): Promise<boolean> {
    const type = await this.passwordInput.getAttribute('type');
    return type === 'text';
  }
}