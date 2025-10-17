// @ts-nocheck
/**
 * ErrorDiagnostics - 錯誤診斷系統
 * 自動識別和分類首頁渲染錯誤，實施JavaScript控制台錯誤捕獲和分析機制
 * 建立網路請求失敗檢測和API響應格式驗證
 */

export interface DiagnosticResult {
  category: 'auth' | 'api' | 'render' | 'network' | 'javascript' | 'coupon';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  solution?: string;
  timestamp: Date;
  details?: any;
  stack?: string;
}

export interface DiagnosticReport {
  id: string;
  timestamp: Date;
  overallHealth: 'healthy' | 'degraded' | 'critical';
  issues: DiagnosticResult[];
  recommendations: string[];
  autoFixApplied: boolean;
}

export interface NetworkRequestInfo {
  url: string;
  method: string;
  status?: number;
  responseType?: string;
  error?: any;
  timestamp: Date;
}

export class ErrorDiagnostics {
  private static instance: ErrorDiagnostics;
  private errors: DiagnosticResult[] = [];
  private networkRequests: NetworkRequestInfo[] = [];
  private isInitialized = false;

  private constructor() {
    this.initializeErrorCapture();
  }

  public static getInstance(): ErrorDiagnostics {
    if (!ErrorDiagnostics.instance) {
      ErrorDiagnostics.instance = new ErrorDiagnostics();
    }
    return ErrorDiagnostics.instance;
  }

  /**
   * 初始化錯誤捕獲機制
   */
  private initializeErrorCapture(): void {
    if (this.isInitialized) return;

    // 捕獲全局JavaScript錯誤
    window.addEventListener('error', (event) => {
      this.captureJavaScriptError(event.error, event.message, event.filename, event.lineno);
    });

    // 捕獲Promise未處理的拒絕
    window.addEventListener('unhandledrejection', (event) => {
      this.capturePromiseRejection(event.reason);
    });

    // 攔截fetch請求進行網路監控
    this.interceptFetchRequests();

    // 攔截XMLHttpRequest請求
    this.interceptXHRRequests();

    this.isInitialized = true;
    console.log('ErrorDiagnostics initialized - 錯誤診斷系統已初始化');
  }

  /**
   * 捕獲JavaScript錯誤
   */
  private captureJavaScriptError(error: Error, message: string, filename?: string, lineno?: number): void {
    const diagnosticResult: DiagnosticResult = {
      category: 'javascript',
      severity: this.determineSeverity(error, message),
      message: message || error?.message || 'Unknown JavaScript error',
      timestamp: new Date(),
      details: {
        filename,
        lineno,
        errorName: error?.name,
        errorMessage: error?.message
      },
      stack: error?.stack,
      solution: this.suggestJavaScriptSolution(error, message)
    };

    this.addError(diagnosticResult);
  }

  /**
   * 捕獲Promise拒絕錯誤
   */
  private capturePromiseRejection(reason: any): void {
    const diagnosticResult: DiagnosticResult = {
      category: 'javascript',
      severity: 'high',
      message: `Unhandled Promise Rejection: ${reason?.message || reason}`,
      timestamp: new Date(),
      details: { reason },
      solution: 'Check async/await usage and add proper error handling'
    };

    this.addError(diagnosticResult);
  }

  /**
   * 攔截fetch請求進行監控
   */
  private interceptFetchRequests(): void {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const [url, options] = args;
      const requestInfo: NetworkRequestInfo = {
        url: url.toString(),
        method: options?.method || 'GET',
        timestamp: new Date()
      };

      try {
        const response = await originalFetch(...args);
        
        requestInfo.status = response.status;
        requestInfo.responseType = response.headers.get('content-type') || 'unknown';
        
        // 檢查API響應格式
        this.validateApiResponse(response, requestInfo);
        
        this.networkRequests.push(requestInfo);
        return response;
      } catch (error) {
        requestInfo.error = error;
        this.networkRequests.push(requestInfo);
        this.captureNetworkError(requestInfo, error);
        throw error;
      }
    };
  }

  /**
   * 攔截XMLHttpRequest請求
   */
  private interceptXHRRequests(): void {
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method: string, url: string | URL, ...args) {
      (this as any)._requestInfo = {
        method,
        url: url.toString(),
        timestamp: new Date()
      };
      return originalXHROpen.call(this, method, url, ...args);
    };

    XMLHttpRequest.prototype.send = function(...args) {
      const requestInfo = (this as any)._requestInfo as NetworkRequestInfo;
      
      this.addEventListener('load', () => {
        if (requestInfo) {
          requestInfo.status = this.status;
          requestInfo.responseType = this.getResponseHeader('content-type') || 'unknown';
          ErrorDiagnostics.getInstance().networkRequests.push(requestInfo);
          
          // 檢查響應格式
          ErrorDiagnostics.getInstance().validateXHRResponse(this, requestInfo);
        }
      });

      this.addEventListener('error', () => {
        if (requestInfo) {
          requestInfo.error = new Error(`XHR request failed: ${this.status}`);
          ErrorDiagnostics.getInstance().networkRequests.push(requestInfo);
          ErrorDiagnostics.getInstance().captureNetworkError(requestInfo, requestInfo.error);
        }
      });

      return originalXHRSend.call(this, ...args);
    };
  }

  /**
   * 驗證API響應格式
   */
  private validateApiResponse(response: Response, requestInfo: NetworkRequestInfo): void {
    const contentType = response.headers.get('content-type') || '';
    
    // 檢查是否期望JSON但收到HTML
    if (requestInfo.url.includes('/api/') && contentType.includes('text/html')) {
      const diagnosticResult: DiagnosticResult = {
        category: 'api',
        severity: 'high',
        message: `API endpoint returned HTML instead of JSON: ${requestInfo.url}`,
        timestamp: new Date(),
        details: {
          url: requestInfo.url,
          expectedType: 'application/json',
          actualType: contentType,
          status: response.status
        },
        solution: 'Check API routing configuration and ensure endpoint returns JSON'
      };
      
      this.addError(diagnosticResult);
    }

    // 檢查HTTP錯誤狀態
    if (!response.ok) {
      const diagnosticResult: DiagnosticResult = {
        category: response.status >= 500 ? 'api' : 'network',
        severity: response.status >= 500 ? 'critical' : 'high',
        message: `HTTP ${response.status} error for ${requestInfo.url}`,
        timestamp: new Date(),
        details: {
          url: requestInfo.url,
          status: response.status,
          statusText: response.statusText
        },
        solution: this.suggestHttpErrorSolution(response.status)
      };
      
      this.addError(diagnosticResult);
    }
  }

  /**
   * 驗證XHR響應格式
   */
  private validateXHRResponse(xhr: XMLHttpRequest, requestInfo: NetworkRequestInfo): void {
    const contentType = xhr.getResponseHeader('content-type') || '';
    
    // 檢查優惠券API特定錯誤
    if (requestInfo.url.includes('coupon') && contentType.includes('text/html')) {
      const diagnosticResult: DiagnosticResult = {
        category: 'coupon',
        severity: 'high',
        message: 'Coupon API returned HTML instead of JSON - SyntaxError likely',
        timestamp: new Date(),
        details: {
          url: requestInfo.url,
          responseText: xhr.responseText?.substring(0, 200) + '...',
          contentType
        },
        solution: 'Fix coupon API endpoint to return proper JSON format'
      };
      
      this.addError(diagnosticResult);
    }
  }

  /**
   * 捕獲網路錯誤
   */
  private captureNetworkError(requestInfo: NetworkRequestInfo, error: any): void {
    const diagnosticResult: DiagnosticResult = {
      category: 'network',
      severity: 'high',
      message: `Network request failed: ${requestInfo.url}`,
      timestamp: new Date(),
      details: {
        url: requestInfo.url,
        method: requestInfo.method,
        error: error?.message || error
      },
      solution: 'Check network connectivity and API endpoint availability'
    };

    this.addError(diagnosticResult);
  }

  /**
   * 診斷認證錯誤
   */
  public diagnoseAuthErrors(): DiagnosticResult[] {
    const authErrors: DiagnosticResult[] = [];

    // 檢查認證相關的錯誤
    const authRelatedErrors = this.errors.filter(error => 
      error.category === 'auth' || 
      error.message.toLowerCase().includes('auth') ||
      error.message.toLowerCase().includes('login') ||
      error.message.toLowerCase().includes('token')
    );

    authRelatedErrors.forEach(error => {
      authErrors.push({
        ...error,
        solution: error.solution || 'Check authentication service and token validity'
      });
    });

    // 檢查認證狀態初始化問題
    try {
      const authContext = document.querySelector('[data-auth-context]');
      if (!authContext) {
        authErrors.push({
          category: 'auth',
          severity: 'medium',
          message: 'Authentication context not found in DOM',
          timestamp: new Date(),
          solution: 'Ensure AuthProvider is properly wrapped around the app'
        });
      }
    } catch (error) {
      // DOM檢查失敗，可能還在初始化
    }

    return authErrors;
  }

  /**
   * 診斷API錯誤
   */
  public diagnoseApiErrors(): DiagnosticResult[] {
    const apiErrors: DiagnosticResult[] = [];

    // 檢查API相關錯誤
    const apiRelatedErrors = this.errors.filter(error => 
      error.category === 'api' || error.category === 'network'
    );

    apiErrors.push(...apiRelatedErrors);

    // 檢查CORS問題
    const corsErrors = this.networkRequests.filter(req => 
      req.error && req.error.message?.includes('CORS')
    );

    corsErrors.forEach(req => {
      apiErrors.push({
        category: 'api',
        severity: 'high',
        message: `CORS error for ${req.url}`,
        timestamp: new Date(),
        details: { request: req },
        solution: 'Configure CORS headers on the server or check API domain'
      });
    });

    return apiErrors;
  }

  /**
   * 診斷渲染錯誤
   */
  public diagnoseRenderErrors(): DiagnosticResult[] {
    const renderErrors: DiagnosticResult[] = [];

    // 檢查React渲染錯誤
    const reactErrors = this.errors.filter(error => 
      error.category === 'render' ||
      error.message.includes('React') ||
      error.message.includes('render') ||
      error.message.includes('component')
    );

    renderErrors.push(...reactErrors);

    // 檢查DOM掛載問題
    try {
      const rootElement = document.getElementById('root');
      if (!rootElement) {
        renderErrors.push({
          category: 'render',
          severity: 'critical',
          message: 'Root DOM element not found',
          timestamp: new Date(),
          solution: 'Ensure HTML has <div id="root"></div> element'
        });
      } else if (!rootElement.hasChildNodes()) {
        renderErrors.push({
          category: 'render',
          severity: 'high',
          message: 'React app not mounted to root element',
          timestamp: new Date(),
          solution: 'Check React app initialization and mounting process'
        });
      }
    } catch (error) {
      renderErrors.push({
        category: 'render',
        severity: 'high',
        message: 'Error checking DOM structure',
        timestamp: new Date(),
        details: { error }
      });
    }

    return renderErrors;
  }

  /**
   * 生成診斷報告
   */
  public generateReport(): DiagnosticReport {
    const allIssues = [
      ...this.diagnoseAuthErrors(),
      ...this.diagnoseApiErrors(),
      ...this.diagnoseRenderErrors(),
      ...this.errors
    ];

    // 去重
    const uniqueIssues = allIssues.filter((issue, index, self) => 
      index === self.findIndex(i => i.message === issue.message && i.category === issue.category)
    );

    const criticalIssues = uniqueIssues.filter(issue => issue.severity === 'critical');
    const highIssues = uniqueIssues.filter(issue => issue.severity === 'high');

    let overallHealth: 'healthy' | 'degraded' | 'critical' = 'healthy';
    if (criticalIssues.length > 0) {
      overallHealth = 'critical';
    } else if (highIssues.length > 0) {
      overallHealth = 'degraded';
    }

    const recommendations = this.generateRecommendations(uniqueIssues);

    return {
      id: `diagnostic-${Date.now()}`,
      timestamp: new Date(),
      overallHealth,
      issues: uniqueIssues,
      recommendations,
      autoFixApplied: false
    };
  }

  /**
   * 生成修復建議
   */
  private generateRecommendations(issues: DiagnosticResult[]): string[] {
    const recommendations: string[] = [];

    const hasAuthIssues = issues.some(i => i.category === 'auth');
    const hasApiIssues = issues.some(i => i.category === 'api');
    const hasRenderIssues = issues.some(i => i.category === 'render');
    const hasCouponIssues = issues.some(i => i.category === 'coupon');

    if (hasAuthIssues) {
      recommendations.push('檢查認證服務配置和JWT token處理');
      recommendations.push('實施認證錯誤容錯處理和訪客模式降級');
    }

    if (hasApiIssues) {
      recommendations.push('檢查API路由配置和CORS設定');
      recommendations.push('確保API端點返回正確的JSON格式');
    }

    if (hasRenderIssues) {
      recommendations.push('檢查React組件渲染邏輯和錯誤邊界');
      recommendations.push('確保DOM結構正確且React應用正常掛載');
    }

    if (hasCouponIssues) {
      recommendations.push('修復優惠券API端點，確保返回JSON而非HTML');
      recommendations.push('實施優惠券載入錯誤的降級處理');
    }

    if (recommendations.length === 0) {
      recommendations.push('系統運行正常，建議定期監控');
    }

    return recommendations;
  }

  /**
   * 確定錯誤嚴重程度
   */
  private determineSeverity(error: Error, message: string): 'low' | 'medium' | 'high' | 'critical' {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('syntaxerror') || lowerMessage.includes('referenceerror')) {
      return 'critical';
    }
    
    if (lowerMessage.includes('typeerror') || lowerMessage.includes('network')) {
      return 'high';
    }
    
    if (lowerMessage.includes('warning') || lowerMessage.includes('deprecated')) {
      return 'low';
    }
    
    return 'medium';
  }

  /**
   * 建議JavaScript錯誤解決方案
   */
  private suggestJavaScriptSolution(error: Error, message: string): string {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('syntaxerror')) {
      return 'Check for syntax errors in JavaScript code, missing brackets or semicolons';
    }
    
    if (lowerMessage.includes('referenceerror')) {
      return 'Check if variables are properly declared and imported';
    }
    
    if (lowerMessage.includes('typeerror')) {
      return 'Check data types and null/undefined values';
    }
    
    if (lowerMessage.includes('coupon')) {
      return 'Fix coupon API to return JSON instead of HTML';
    }
    
    return 'Review error stack trace and check related code logic';
  }

  /**
   * 建議HTTP錯誤解決方案
   */
  private suggestHttpErrorSolution(status: number): string {
    switch (Math.floor(status / 100)) {
      case 4:
        if (status === 404) return 'Check API endpoint URL and routing configuration';
        if (status === 401) return 'Check authentication credentials and token';
        if (status === 403) return 'Check user permissions and access rights';
        return 'Check request parameters and client-side logic';
      case 5:
        return 'Server error - check backend service and database connectivity';
      default:
        return 'Check network connectivity and server status';
    }
  }

  /**
   * 添加錯誤到診斷列表
   */
  private addError(error: DiagnosticResult): void {
    this.errors.push(error);
    
    // 保持錯誤列表在合理大小
    if (this.errors.length > 100) {
      this.errors = this.errors.slice(-50);
    }

    // 輸出到控制台以便調試
    console.warn('ErrorDiagnostics captured:', error);
  }

  /**
   * 清除所有錯誤記錄
   */
  public clearErrors(): void {
    this.errors = [];
    this.networkRequests = [];
  }

  /**
   * 獲取所有錯誤
   */
  public getAllErrors(): DiagnosticResult[] {
    return [...this.errors];
  }

  /**
   * 獲取網路請求記錄
   */
  public getNetworkRequests(): NetworkRequestInfo[] {
    return [...this.networkRequests];
  }

  /**
   * 手動添加錯誤（用於組件內部錯誤報告）
   */
  public reportError(category: DiagnosticResult['category'], message: string, details?: any): void {
    const error: DiagnosticResult = {
      category,
      severity: 'medium',
      message,
      timestamp: new Date(),
      details,
      solution: 'Check component logic and error handling'
    };
    
    this.addError(error);
  }
}

// 導出單例實例
export const errorDiagnostics = ErrorDiagnostics.getInstance();

// 全局錯誤診斷函數
export const diagnoseHomepageErrors = (): DiagnosticReport => {
  return errorDiagnostics.generateReport();
};

// 手動錯誤報告函數
export const reportComponentError = (
  category: DiagnosticResult['category'], 
  message: string, 
  details?: any
): void => {
  errorDiagnostics.reportError(category, message, details);
};