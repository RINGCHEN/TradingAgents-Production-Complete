/**
 * NavigationChecker - 專門的導航元素檢查工具
 * 針對React SPA應用優化，會等待組件完全載入
 */

export interface NavigationCheckResult {
  found: boolean;
  element?: Element;
  selector: string;
  timing: number;
  retryCount: number;
}

export class NavigationChecker {
  private static readonly NAVIGATION_SELECTORS = [
    'nav.navbar',
    'nav',
    '.navbar',
    '[role="navigation"]',
    '.landing-page nav',
    '.landing-page .navbar'
  ];

  private static readonly MAX_RETRIES = 5;
  private static readonly RETRY_INTERVAL = 1000; // 1秒

  /**
   * 檢查導航元素是否存在，支援重試機制
   */
  public static async checkNavigation(): Promise<NavigationCheckResult> {
    const startTime = Date.now();
    
    for (let retryCount = 0; retryCount < this.MAX_RETRIES; retryCount++) {
      for (const selector of this.NAVIGATION_SELECTORS) {
        const element = document.querySelector(selector);
        
        if (element) {
          // 檢查元素是否真的可見
          const rect = element.getBoundingClientRect();
          const isVisible = rect.width > 0 && rect.height > 0;
          
          if (isVisible) {
            return {
              found: true,
              element,
              selector,
              timing: Date.now() - startTime,
              retryCount
            };
          }
        }
      }
      
      // 如果沒找到，等待一段時間後重試
      if (retryCount < this.MAX_RETRIES - 1) {
        await this.delay(this.RETRY_INTERVAL);
      }
    }
    
    // 所有重試都失敗了
    return {
      found: false,
      selector: this.NAVIGATION_SELECTORS.join(', '),
      timing: Date.now() - startTime,
      retryCount: this.MAX_RETRIES
    };
  }

  /**
   * 檢查React應用是否完全載入
   */
  public static checkReactAppLoaded(): boolean {
    const rootElement = document.getElementById('root');
    if (!rootElement || !rootElement.hasChildNodes()) {
      return false;
    }

    // 檢查是否有React應用的標誌性元素
    const reactIndicators = [
      '.landing-page',
      '.App',
      '[data-testid="app-root"]'
    ];

    return reactIndicators.some(selector => 
      document.querySelector(selector) !== null
    );
  }

  /**
   * 等待React應用載入完成
   */
  public static async waitForReactApp(maxWaitTime: number = 10000): Promise<boolean> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
      if (this.checkReactAppLoaded()) {
        return true;
      }
      
      await this.delay(500);
    }
    
    return false;
  }

  /**
   * 獲取導航元素的詳細信息
   */
  public static getNavigationInfo(): {
    found: boolean;
    elements: Array<{
      selector: string;
      element: Element;
      visible: boolean;
      position: DOMRect;
      textContent: string;
    }>;
  } {
    const elements: Array<{
      selector: string;
      element: Element;
      visible: boolean;
      position: DOMRect;
      textContent: string;
    }> = [];

    for (const selector of this.NAVIGATION_SELECTORS) {
      const foundElements = document.querySelectorAll(selector);
      
      foundElements.forEach(element => {
        const rect = element.getBoundingClientRect();
        const isVisible = rect.width > 0 && rect.height > 0;
        
        elements.push({
          selector,
          element,
          visible: isVisible,
          position: rect,
          textContent: element.textContent?.trim() || ''
        });
      });
    }

    return {
      found: elements.length > 0,
      elements
    };
  }

  /**
   * 診斷導航問題
   */
  public static async diagnoseNavigationIssues(): Promise<{
    reactAppLoaded: boolean;
    navigationFound: boolean;
    possibleIssues: string[];
    recommendations: string[];
  }> {
    const reactAppLoaded = this.checkReactAppLoaded();
    const navigationResult = await this.checkNavigation();
    const possibleIssues: string[] = [];
    const recommendations: string[] = [];

    if (!reactAppLoaded) {
      possibleIssues.push('React應用未完全載入');
      recommendations.push('等待React應用完全載入後再檢查導航');
    }

    if (!navigationResult.found) {
      possibleIssues.push('導航元素未找到或不可見');
      
      if (reactAppLoaded) {
        recommendations.push('檢查LandingPage.tsx中的導航元素實現');
        recommendations.push('檢查CSS樣式是否隱藏了導航元素');
        recommendations.push('檢查ErrorBoundary是否捕獲了渲染錯誤');
      } else {
        recommendations.push('等待React應用完全載入');
      }
    }

    if (navigationResult.retryCount > 0) {
      possibleIssues.push(`導航載入較慢，需要${navigationResult.retryCount}次重試`);
      recommendations.push('考慮優化React組件的載入性能');
    }

    return {
      reactAppLoaded,
      navigationFound: navigationResult.found,
      possibleIssues,
      recommendations
    };
  }

  /**
   * 延遲函數
   */
  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 導出便捷函數
export const checkNavigation = () => NavigationChecker.checkNavigation();
export const waitForReactApp = (maxWaitTime?: number) => NavigationChecker.waitForReactApp(maxWaitTime);
export const diagnoseNavigationIssues = () => NavigationChecker.diagnoseNavigationIssues();