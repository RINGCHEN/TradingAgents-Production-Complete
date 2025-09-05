/**
 * 儀表板頁面對象模型
 * 封裝管理後台儀表板的元素和操作
 */

import { Page, Locator } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';

export class DashboardPage {
  private helpers: TestHelpers;

  // 頁面元素選擇器
  private readonly selectors = {
    // 頁面標識
    pageTitle: '[data-testid="page-title"], h1, .page-title',
    welcomeMessage: '[data-testid="welcome-message"], .welcome-message',
    
    // 用戶信息
    userInfo: '[data-testid="user-info"], .user-info',
    username: '[data-testid="username"], .username',
    userRole: '[data-testid="user-role"], .user-role',
    
    // 導航和菜單
    navigation: '[data-testid="navigation"], .navigation, nav',
    logoutButton: '[data-testid="logout-button"], button:has-text("登出"), button:has-text("Logout")',
    menuToggle: '[data-testid="menu-toggle"], .menu-toggle',
    
    // 儀表板內容
    dashboardContent: '[data-testid="dashboard-content"], .dashboard-content, main',
    statsCards: '[data-testid="stats-card"], .stats-card',
    dataTable: '[data-testid="data-table"], .data-table, table',
    
    // 載入和錯誤狀態
    loadingIndicator: '[data-testid="loading"], .loading, .spinner',
    errorMessage: '[data-testid="error-message"], .error-message, .alert-error',
    
    // 操作按鈕
    refreshButton: '[data-testid="refresh-button"], button:has-text("刷新"), button:has-text("Refresh")',
    settingsButton: '[data-testid="settings-button"], button:has-text("設置"), button:has-text("Settings")',
    
    // 側邊欄
    sidebar: '[data-testid="sidebar"], .sidebar',
    sidebarToggle: '[data-testid="sidebar-toggle"], .sidebar-toggle'
  };

  constructor(private page: Page) {
    this.helpers = new TestHelpers(page);
  }

  /**
   * 導航到儀表板頁面
   */
  async goto() {
    await this.page.goto('/admin/dashboard');
    await this.helpers.waitForPageLoad();
    await this.waitForPageReady();
  }

  /**
   * 等待頁面準備就緒
   */
  async waitForPageReady() {
    await this.helpers.waitForElement(this.selectors.dashboardContent);
    await this.helpers.waitForLoadingToFinish();
  }

  /**
   * 獲取頁面元素
   */
  get pageTitle(): Locator {
    return this.page.locator(this.selectors.pageTitle).first();
  }

  get welcomeMessage(): Locator {
    return this.page.locator(this.selectors.welcomeMessage).first();
  }

  get userInfo(): Locator {
    return this.page.locator(this.selectors.userInfo).first();
  }

  get username(): Locator {
    return this.page.locator(this.selectors.username).first();
  }

  get logoutButton(): Locator {
    return this.page.locator(this.selectors.logoutButton).first();
  }

  get dashboardContent(): Locator {
    return this.page.locator(this.selectors.dashboardContent).first();
  }

  get navigation(): Locator {
    return this.page.locator(this.selectors.navigation).first();
  }

  /**
   * 檢查是否在儀表板頁面
   */
  async isOnDashboard(): Promise<boolean> {
    const url = this.page.url();
    return url.includes('/admin/dashboard') || url.includes('/dashboard');
  }

  /**
   * 獲取頁面標題
   */
  async getPageTitle(): Promise<string> {
    try {
      await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
      return await this.pageTitle.textContent() || '';
    } catch {
      return await this.page.title();
    }
  }

  /**
   * 獲取歡迎消息
   */
  async getWelcomeMessage(): Promise<string> {
    try {
      await this.welcomeMessage.waitFor({ state: 'visible', timeout: 5000 });
      return await this.welcomeMessage.textContent() || '';
    } catch {
      return '';
    }
  }

  /**
   * 獲取當前用戶名
   */
  async getCurrentUsername(): Promise<string> {
    try {
      await this.username.waitFor({ state: 'visible', timeout: 5000 });
      return await this.username.textContent() || '';
    } catch {
      return '';
    }
  }

  /**
   * 獲取用戶角色
   */
  async getUserRole(): Promise<string> {
    try {
      const roleElement = this.page.locator(this.selectors.userRole);
      await roleElement.waitFor({ state: 'visible', timeout: 5000 });
      return await roleElement.textContent() || '';
    } catch {
      return '';
    }
  }

  /**
   * 執行登出操作
   */
  async logout() {
    await this.logoutButton.waitFor({ state: 'visible' });
    await this.logoutButton.click();
    
    // 等待登出完成
    await this.page.waitForURL('**/admin/login', { timeout: 10000 });
  }

  /**
   * 檢查登出按鈕是否可見
   */
  async isLogoutButtonVisible(): Promise<boolean> {
    try {
      await this.logoutButton.waitFor({ state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 刷新頁面數據
   */
  async refreshData() {
    const refreshButton = this.page.locator(this.selectors.refreshButton);
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await this.helpers.waitForLoadingToFinish();
    } else {
      // 如果沒有刷新按鈕，使用頁面刷新
      await this.page.reload();
      await this.waitForPageReady();
    }
  }

  /**
   * 檢查是否顯示載入狀態
   */
  async isLoading(): Promise<boolean> {
    try {
      const loading = this.page.locator(this.selectors.loadingIndicator);
      await loading.waitFor({ state: 'visible', timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 等待載入完成
   */
  async waitForLoadingComplete() {
    await this.helpers.waitForLoadingToFinish();
  }

  /**
   * 檢查是否有錯誤消息
   */
  async hasErrorMessage(): Promise<boolean> {
    try {
      const error = this.page.locator(this.selectors.errorMessage);
      await error.waitFor({ state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 獲取錯誤消息
   */
  async getErrorMessage(): Promise<string> {
    try {
      const error = this.page.locator(this.selectors.errorMessage);
      await error.waitFor({ state: 'visible', timeout: 5000 });
      return await error.textContent() || '';
    } catch {
      return '';
    }
  }

  /**
   * 檢查儀表板內容是否載入
   */
  async isDashboardContentLoaded(): Promise<boolean> {
    try {
      await this.dashboardContent.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 獲取統計卡片數量
   */
  async getStatsCardsCount(): Promise<number> {
    const cards = this.page.locator(this.selectors.statsCards);
    return await cards.count();
  }

  /**
   * 獲取統計卡片數據
   */
  async getStatsCardData(index: number) {
    const cards = this.page.locator(this.selectors.statsCards);
    const card = cards.nth(index);
    
    if (await card.isVisible()) {
      return {
        title: await card.locator('.title, .card-title').textContent(),
        value: await card.locator('.value, .card-value').textContent(),
        description: await card.locator('.description, .card-description').textContent()
      };
    }
    
    return null;
  }

  /**
   * 檢查數據表格是否存在
   */
  async hasDataTable(): Promise<boolean> {
    try {
      const table = this.page.locator(this.selectors.dataTable);
      await table.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 獲取數據表格行數
   */
  async getTableRowCount(): Promise<number> {
    const table = this.page.locator(this.selectors.dataTable);
    if (await table.isVisible()) {
      const rows = table.locator('tbody tr, .table-row');
      return await rows.count();
    }
    return 0;
  }

  /**
   * 切換側邊欄
   */
  async toggleSidebar() {
    const toggle = this.page.locator(this.selectors.sidebarToggle);
    if (await toggle.isVisible()) {
      await toggle.click();
    }
  }

  /**
   * 檢查側邊欄是否展開
   */
  async isSidebarExpanded(): Promise<boolean> {
    const sidebar = this.page.locator(this.selectors.sidebar);
    if (await sidebar.isVisible()) {
      const classes = await sidebar.getAttribute('class') || '';
      return classes.includes('expanded') || classes.includes('open');
    }
    return false;
  }

  /**
   * 導航到設置頁面
   */
  async goToSettings() {
    const settingsButton = this.page.locator(this.selectors.settingsButton);
    if (await settingsButton.isVisible()) {
      await settingsButton.click();
    }
  }

  /**
   * 檢查導航菜單項
   */
  async getNavigationItems(): Promise<string[]> {
    const nav = this.page.locator(this.selectors.navigation);
    if (await nav.isVisible()) {
      const items = nav.locator('a, .nav-item');
      const count = await items.count();
      const itemTexts: string[] = [];
      
      for (let i = 0; i < count; i++) {
        const text = await items.nth(i).textContent();
        if (text) {
          itemTexts.push(text.trim());
        }
      }
      
      return itemTexts;
    }
    return [];
  }

  /**
   * 點擊導航菜單項
   */
  async clickNavigationItem(itemText: string) {
    const nav = this.page.locator(this.selectors.navigation);
    const item = nav.locator(`a:has-text("${itemText}"), .nav-item:has-text("${itemText}")`);
    
    if (await item.isVisible()) {
      await item.click();
    }
  }

  /**
   * 檢查用戶權限指示器
   */
  async getUserPermissions(): Promise<string[]> {
    const permissions: string[] = [];
    
    // 檢查各種權限指示器
    const permissionSelectors = [
      '[data-permission]',
      '.permission-indicator',
      '.user-permission'
    ];
    
    for (const selector of permissionSelectors) {
      const elements = this.page.locator(selector);
      const count = await elements.count();
      
      for (let i = 0; i < count; i++) {
        const permission = await elements.nth(i).getAttribute('data-permission') ||
                          await elements.nth(i).textContent();
        if (permission) {
          permissions.push(permission.trim());
        }
      }
    }
    
    return permissions;
  }

  /**
   * 檢查頁面響應性
   */
  async checkResponsiveness() {
    const viewports = [
      { width: 1920, height: 1080 }, // Desktop
      { width: 1024, height: 768 },  // Tablet
      { width: 375, height: 667 }    // Mobile
    ];
    
    const results = [];
    
    for (const viewport of viewports) {
      await this.page.setViewportSize(viewport);
      await this.page.waitForTimeout(500); // Wait for layout adjustment
      
      const isContentVisible = await this.isDashboardContentLoaded();
      const isNavigationVisible = await this.navigation.isVisible();
      
      results.push({
        viewport,
        contentVisible: isContentVisible,
        navigationVisible: isNavigationVisible
      });
    }
    
    return results;
  }
}