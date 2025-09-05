/**
 * ConsoleErrorCapture - JavaScript控制台錯誤捕獲和分析機制
 * 專門用於捕獲和分析JavaScript控制台錯誤，提供詳細的錯誤分類和解決建議
 */

import { reportComponentError } from './ErrorDiagnostics';

export interface ConsoleError {
  type: 'error' | 'warn' | 'info';
  message: string;
  timestamp: Date;
  stack?: string;
  source?: string;
  category: 'syntax' | 'reference' | 'type' | 'network' | 'auth' | 'coupon' | 'render' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  solution?: string;
}

export class ConsoleErrorCapture {
  private static instance: ConsoleErrorCapture;
  private originalConsole: {
    error: typeof console.error;
    warn: typeof console.warn;
    info: typeof console.info;
  };
  private capturedErrors: ConsoleError[] = [];
  private isCapturing = false;

  private constructor() {
    this.originalConsole = {
      error: console.error.bind(console),
      warn: console.warn.bind(console),
      info: console.info.bind(console)
    };
  }

  public static getInstance(): ConsoleErrorCapture {
    if (!ConsoleErrorCapture.instance) {
      ConsoleErrorCapture.instance = new ConsoleErrorCapture();
    }
    return ConsoleErrorCapture.instance;
  }

  /**
   * 開始捕獲控制台錯誤
   */
  public startCapture(): void {
    if (this.isCapturing) return;

    // 攔截console.error
    console.error = (...args: any[]) => {
      this.captureConsoleMessage('error', args);
      this.originalConsole.error(...args);
    };

    // 攔截console.warn
    console.warn = (...args: any[]) => {
      this.captureConsoleMessage('warn', args);
      this.originalConsole.warn(...args);
    };

    // 攔截console.info（可選）
    console.info = (...args: any[]) => {
      this.captureConsoleMessage('info', args);
      this.originalConsole.info(...args);
    };

    this.isCapturing = true;
    console.log('ConsoleErrorCapture started - 控制台錯誤捕獲已啟動');
  }

  /**
   * 停止捕獲控制台錯誤
   */
  public stopCapture(): void {
    if (!this.isCapturing) return;

    console.error = this.originalConsole.error;
    console.warn = this.originalConsole.warn;
    console.info = this.originalConsole.info;

    this.isCapturing = false;
    console.log('ConsoleErrorCapture stopped - 控制台錯誤捕獲已停止');
  }

  /**
   * 捕獲控制台消息
   */
  private captureConsoleMessage(type: 'error' | 'warn' | 'info', args: any[]): void {
    try {
      const message = this.formatConsoleMessage(args);
      const consoleError = this.analyzeConsoleMessage(type, message, args);
      
      this.capturedErrors.push(consoleError);
      
      // 保持錯誤列表在合理大小
      if (this.capturedErrors.length > 200) {
        this.capturedErrors = this.capturedErrors.slice(-100);
      }

      // 報告到錯誤診斷系統
      if (consoleError.severity === 'critical' || consoleError.severity === 'high') {
        this.reportToErrorDiagnostics(consoleError);
      }

    } catch (error) {
      // 避免在錯誤捕獲過程中產生新錯誤
      this.originalConsole.error('Error in ConsoleErrorCapture:', error);
    }
  }

  /**
   * 格式化控制台消息
   */
  private formatConsoleMessage(args: any[]): string {
    return args.map(arg => {
      if (typeof arg === 'string') {
        return arg;
      } else if (arg instanceof Error) {
        return `${arg.name}: ${arg.message}`;
      } else if (typeof arg === 'object') {
        try {
          return JSON.stringify(arg, null, 2);
        } catch {
          return '[Object]';
        }
      } else {
        return String(arg);
      }
    }).join(' ');
  }

  /**
   * 分析控制台消息
   */
  private analyzeConsoleMessage(type: 'error' | 'warn' | 'info', message: string, args: any[]): ConsoleError {
    const lowerMessage = message.toLowerCase();
    
    // 提取堆棧信息
    let stack: string | undefined;
    const errorArg = args.find(arg => arg instanceof Error);
    if (errorArg) {
      stack = errorArg.stack;
    }

    // 分類錯誤
    const category = this.categorizeError(lowerMessage);
    const severity = this.determineSeverity(type, lowerMessage, category);
    const solution = this.suggestSolution(category, lowerMessage);

    return {
      type,
      message,
      timestamp: new Date(),
      stack,
      category,
      severity,
      solution
    };
  }

  /**
   * 錯誤分類
   */
  private categorizeError(message: string): ConsoleError['category'] {
    // 語法錯誤
    if (message.includes('syntaxerror') || message.includes('unexpected token')) {
      return 'syntax';
    }

    // 引用錯誤
    if (message.includes('referenceerror') || message.includes('is not defined')) {
      return 'reference';
    }

    // 類型錯誤
    if (message.includes('typeerror') || message.includes('cannot read property') || 
        message.includes('cannot read properties') || message.includes('is not a function')) {
      return 'type';
    }

    // 網路錯誤
    if (message.includes('network') || message.includes('fetch') || 
        message.includes('cors') || message.includes('failed to load')) {
      return 'network';
    }

    // 認證錯誤
    if (message.includes('auth') || message.includes('login') || 
        message.includes('token') || message.includes('unauthorized')) {
      return 'auth';
    }

    // 優惠券相關錯誤
    if (message.includes('coupon') || message.includes('載入優惠券失敗')) {
      return 'coupon';
    }

    // 渲染錯誤
    if (message.includes('react') || message.includes('render') || 
        message.includes('component') || message.includes('hook')) {
      return 'render';
    }

    return 'unknown';
  }

  /**
   * 確定錯誤嚴重程度
   */
  private determineSeverity(
    type: 'error' | 'warn' | 'info', 
    message: string, 
    category: ConsoleError['category']
  ): ConsoleError['severity'] {
    // 基於類型的基礎嚴重程度
    let baseSeverity: ConsoleError['severity'] = 'medium';
    
    switch (type) {
      case 'error':
        baseSeverity = 'high';
        break;
      case 'warn':
        baseSeverity = 'medium';
        break;
      case 'info':
        baseSeverity = 'low';
        break;
    }

    // 基於分類調整嚴重程度
    switch (category) {
      case 'syntax':
      case 'reference':
        return 'critical';
      
      case 'type':
        return message.includes('cannot read') ? 'critical' : 'high';
      
      case 'network':
      case 'auth':
        return 'high';
      
      case 'coupon':
        return message.includes('syntaxerror') ? 'critical' : 'high';
      
      case 'render':
        return 'high';
      
      default:
        return baseSeverity;
    }
  }

  /**
   * 建議解決方案
   */
  private suggestSolution(category: ConsoleError['category'], message: string): string {
    switch (category) {
      case 'syntax':
        return '檢查JavaScript語法，確認括號、分號和引號是否正確配對';
      
      case 'reference':
        return '檢查變量是否正確聲明和導入，確認作用域是否正確';
      
      case 'type':
        if (message.includes('cannot read property')) {
          return '檢查對象是否為null或undefined，添加適當的空值檢查';
        }
        if (message.includes('is not a function')) {
          return '檢查函數是否正確導入和定義，確認調用方式是否正確';
        }
        return '檢查數據類型和變量值，添加類型檢查';
      
      case 'network':
        return '檢查網路連接和API端點可用性，確認CORS配置';
      
      case 'auth':
        return '檢查認證服務配置，確認token有效性和認證流程';
      
      case 'coupon':
        return '修復優惠券API端點，確保返回JSON格式而非HTML';
      
      case 'render':
        return '檢查React組件邏輯，確認props和state的正確性';
      
      default:
        return '查看完整錯誤信息和堆棧跟蹤，檢查相關代碼邏輯';
    }
  }

  /**
   * 報告到錯誤診斷系統
   */
  private reportToErrorDiagnostics(consoleError: ConsoleError): void {
    const diagnosticCategory = this.mapToDiagnosticCategory(consoleError.category);
    
    reportComponentError(
      diagnosticCategory,
      `Console ${consoleError.type}: ${consoleError.message}`,
      {
        consoleError,
        category: consoleError.category,
        severity: consoleError.severity,
        stack: consoleError.stack,
        solution: consoleError.solution
      }
    );
  }

  /**
   * 映射到診斷系統分類
   */
  private mapToDiagnosticCategory(category: ConsoleError['category']): 'auth' | 'api' | 'render' | 'network' | 'javascript' | 'coupon' {
    switch (category) {
      case 'auth':
        return 'auth';
      case 'network':
        return 'network';
      case 'coupon':
        return 'coupon';
      case 'render':
        return 'render';
      case 'syntax':
      case 'reference':
      case 'type':
      case 'unknown':
      default:
        return 'javascript';
    }
  }

  /**
   * 獲取捕獲的錯誤
   */
  public getCapturedErrors(): ConsoleError[] {
    return [...this.capturedErrors];
  }

  /**
   * 清除捕獲的錯誤
   */
  public clearCapturedErrors(): void {
    this.capturedErrors = [];
  }

  /**
   * 獲取錯誤統計
   */
  public getErrorStatistics(): {
    total: number;
    byType: Record<string, number>;
    byCategory: Record<string, number>;
    bySeverity: Record<string, number>;
  } {
    const stats = {
      total: this.capturedErrors.length,
      byType: {} as Record<string, number>,
      byCategory: {} as Record<string, number>,
      bySeverity: {} as Record<string, number>
    };

    this.capturedErrors.forEach(error => {
      // 按類型統計
      stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
      
      // 按分類統計
      stats.byCategory[error.category] = (stats.byCategory[error.category] || 0) + 1;
      
      // 按嚴重程度統計
      stats.bySeverity[error.severity] = (stats.bySeverity[error.severity] || 0) + 1;
    });

    return stats;
  }

  /**
   * 檢查是否有特定類型的錯誤
   */
  public hasErrorsOfType(category: ConsoleError['category']): boolean {
    return this.capturedErrors.some(error => error.category === category);
  }

  /**
   * 獲取最近的嚴重錯誤
   */
  public getRecentCriticalErrors(minutes: number = 5): ConsoleError[] {
    const cutoffTime = new Date(Date.now() - minutes * 60 * 1000);
    
    return this.capturedErrors.filter(error => 
      error.severity === 'critical' && error.timestamp > cutoffTime
    );
  }
}

// 導出單例實例
export const consoleErrorCapture = ConsoleErrorCapture.getInstance();

// 自動啟動捕獲（在生產環境中可能需要條件性啟動）
if (typeof window !== 'undefined') {
  consoleErrorCapture.startCapture();
}

// 導出便利函數
export const getConsoleErrors = () => consoleErrorCapture.getCapturedErrors();
export const getConsoleErrorStats = () => consoleErrorCapture.getErrorStatistics();
export const hasConsoleErrorsOfType = (category: ConsoleError['category']) => 
  consoleErrorCapture.hasErrorsOfType(category);

export default ConsoleErrorCapture;