/**
 * ApiErrorHandler - API錯誤處理器
 * 分類API錯誤、生成用戶友好錯誤信息、決定重試策略
 */

import { ApiError } from '../services/ApiClient';

export interface ErrorHandlingStrategy {
  shouldRetry: boolean;
  retryDelay?: number;
  maxRetries?: number;
  fallbackAction?: 'cache' | 'offline' | 'minimal' | 'none';
  userMessage: string;
  technicalMessage: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface ErrorContext {
  component?: string;
  feature?: string;
  userAction?: string;
  timestamp: Date;
}

export class ApiErrorHandler {
  private errorLog: Array<ApiError & ErrorContext> = [];
  private maxLogSize: number = 100;

  /**
   * 處理API錯誤並返回處理策略
   */
  handleError(error: ApiError, context: ErrorContext = { timestamp: new Date() }): ErrorHandlingStrategy {
    // 記錄錯誤
    this.logError(error, context);

    // 根據錯誤類型決定處理策略
    switch (error.type) {
      case 'format':
        return this.handleFormatError(error);
      
      case 'network':
        return this.handleNetworkError(error);
      
      case 'timeout':
        return this.handleTimeoutError(error);
      
      case 'cors':
        return this.handleCorsError(error);
      
      case 'not_found':
        return this.handleNotFoundError(error);
      
      case 'server':
        return this.handleServerError(error);
      
      case 'client':
        return this.handleClientError(error);
      
      default:
        return this.handleUnknownError(error);
    }
  }

  /**
   * 處理格式錯誤（HTML而非JSON）
   */
  private handleFormatError(error: ApiError): ErrorHandlingStrategy {
    const isHtmlResponse = error.details?.contentType?.includes('text/html');
    
    if (isHtmlResponse) {
      return {
        shouldRetry: false,
        fallbackAction: 'cache',
        userMessage: '服務暫時不可用，正在使用緩存數據',
        technicalMessage: `API返回HTML而非JSON: ${error.endpoint}`,
        severity: 'high'
      };
    }

    return {
      shouldRetry: false,
      fallbackAction: 'minimal',
      userMessage: '數據格式錯誤，請稍後重試',
      technicalMessage: `JSON解析失敗: ${error.message}`,
      severity: 'medium'
    };
  }

  /**
   * 處理網路錯誤
   */
  private handleNetworkError(error: ApiError): ErrorHandlingStrategy {
    return {
      shouldRetry: true,
      retryDelay: 2000,
      maxRetries: 3,
      fallbackAction: 'offline',
      userMessage: '網路連接問題，正在重試...',
      technicalMessage: `網路錯誤: ${error.message}`,
      severity: 'medium'
    };
  }

  /**
   * 處理超時錯誤
   */
  private handleTimeoutError(error: ApiError): ErrorHandlingStrategy {
    return {
      shouldRetry: true,
      retryDelay: 3000,
      maxRetries: 2,
      fallbackAction: 'cache',
      userMessage: '請求超時，正在重試...',
      technicalMessage: `請求超時: ${error.endpoint}`,
      severity: 'medium'
    };
  }

  /**
   * 處理CORS錯誤
   */
  private handleCorsError(error: ApiError): ErrorHandlingStrategy {
    return {
      shouldRetry: false,
      fallbackAction: 'minimal',
      userMessage: '服務配置問題，請聯繫技術支援',
      technicalMessage: `CORS錯誤: ${error.message}`,
      severity: 'critical'
    };
  }

  /**
   * 處理404錯誤
   */
  private handleNotFoundError(error: ApiError): ErrorHandlingStrategy {
    return {
      shouldRetry: false,
      fallbackAction: 'minimal',
      userMessage: '請求的資源不存在',
      technicalMessage: `API端點不存在: ${error.endpoint}`,
      severity: 'medium'
    };
  }

  /**
   * 處理服務器錯誤（5xx）
   */
  private handleServerError(error: ApiError): ErrorHandlingStrategy {
    const retryCount = this.getErrorCount(error.endpoint, 'server');
    
    return {
      shouldRetry: retryCount < 3,
      retryDelay: Math.min(1000 * Math.pow(2, retryCount), 10000), // 指數退避
      maxRetries: 3,
      fallbackAction: 'cache',
      userMessage: '服務器暫時不可用，正在重試...',
      technicalMessage: `服務器錯誤 ${error.status}: ${error.message}`,
      severity: 'high'
    };
  }

  /**
   * 處理客戶端錯誤（4xx）
   */
  private handleClientError(error: ApiError): ErrorHandlingStrategy {
    if (error.status === 401) {
      return {
        shouldRetry: false,
        fallbackAction: 'none',
        userMessage: '請重新登錄',
        technicalMessage: '認證失敗，需要重新登錄',
        severity: 'medium'
      };
    }

    if (error.status === 403) {
      return {
        shouldRetry: false,
        fallbackAction: 'minimal',
        userMessage: '沒有權限訪問此資源',
        technicalMessage: '權限不足',
        severity: 'medium'
      };
    }

    return {
      shouldRetry: false,
      fallbackAction: 'minimal',
      userMessage: '請求錯誤，請檢查輸入',
      technicalMessage: `客戶端錯誤 ${error.status}: ${error.message}`,
      severity: 'low'
    };
  }

  /**
   * 處理未知錯誤
   */
  private handleUnknownError(error: ApiError): ErrorHandlingStrategy {
    return {
      shouldRetry: true,
      retryDelay: 2000,
      maxRetries: 1,
      fallbackAction: 'minimal',
      userMessage: '發生未知錯誤，正在重試...',
      technicalMessage: `未知錯誤: ${error.message}`,
      severity: 'medium'
    };
  }

  /**
   * 記錄錯誤
   */
  private logError(error: ApiError, context: ErrorContext): void {
    const logEntry = { ...error, ...context };
    
    this.errorLog.unshift(logEntry);
    
    // 限制日誌大小
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }

    // 在開發環境中輸出到控制台
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', logEntry);
    }
  }

  /**
   * 獲取特定端點和錯誤類型的錯誤次數
   */
  private getErrorCount(endpoint: string, errorType: string): number {
    const recentErrors = this.errorLog.filter(log => 
      log.endpoint === endpoint && 
      log.type === errorType &&
      Date.now() - log.timestamp.getTime() < 300000 // 5分鐘內
    );
    
    return recentErrors.length;
  }

  /**
   * 獲取錯誤統計
   */
  getErrorStatistics(): {
    totalErrors: number;
    errorsByType: Record<string, number>;
    errorsByEndpoint: Record<string, number>;
    recentErrors: number;
  } {
    const now = Date.now();
    const recentThreshold = 300000; // 5分鐘

    const errorsByType: Record<string, number> = {};
    const errorsByEndpoint: Record<string, number> = {};
    let recentErrors = 0;

    this.errorLog.forEach(error => {
      // 按類型統計
      errorsByType[error.type] = (errorsByType[error.type] || 0) + 1;
      
      // 按端點統計
      errorsByEndpoint[error.endpoint] = (errorsByEndpoint[error.endpoint] || 0) + 1;
      
      // 最近錯誤統計
      if (now - error.timestamp.getTime() < recentThreshold) {
        recentErrors++;
      }
    });

    return {
      totalErrors: this.errorLog.length,
      errorsByType,
      errorsByEndpoint,
      recentErrors
    };
  }

  /**
   * 清除錯誤日誌
   */
  clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * 獲取最近的錯誤
   */
  getRecentErrors(limit: number = 10): Array<ApiError & ErrorContext> {
    return this.errorLog.slice(0, limit);
  }

  /**
   * 檢查是否有嚴重錯誤
   */
  hasCriticalErrors(): boolean {
    const recentCriticalErrors = this.errorLog.filter(error => 
      error.type === 'cors' || 
      (error.type === 'server' && error.status && error.status >= 500) ||
      Date.now() - error.timestamp.getTime() < 60000 // 1分鐘內
    );
    
    return recentCriticalErrors.length > 0;
  }

  /**
   * 生成錯誤報告
   */
  generateErrorReport(): {
    summary: string;
    statistics: ReturnType<typeof this.getErrorStatistics>;
    recommendations: string[];
    criticalIssues: string[];
  } {
    const stats = this.getErrorStatistics();
    const recommendations: string[] = [];
    const criticalIssues: string[] = [];

    // 分析錯誤模式並生成建議
    if (stats.errorsByType.cors > 0) {
      criticalIssues.push('檢測到CORS配置問題');
      recommendations.push('檢查服務器CORS配置');
    }

    if (stats.errorsByType.format > 5) {
      criticalIssues.push('頻繁的格式錯誤');
      recommendations.push('檢查API路由配置，確保返回JSON格式');
    }

    if (stats.errorsByType.network > 10) {
      recommendations.push('檢查網路連接穩定性');
    }

    if (stats.errorsByType.server > 5) {
      criticalIssues.push('服務器錯誤頻繁');
      recommendations.push('檢查後端服務狀態');
    }

    const summary = `總錯誤數: ${stats.totalErrors}, 最近錯誤: ${stats.recentErrors}`;

    return {
      summary,
      statistics: stats,
      recommendations,
      criticalIssues
    };
  }
}

// 創建全局錯誤處理器實例
export const apiErrorHandler = new ApiErrorHandler();

// 便捷函數
export const handleApiError = (error: ApiError, context?: ErrorContext): ErrorHandlingStrategy => {
  return apiErrorHandler.handleError(error, context);
};

export const getErrorStatistics = () => {
  return apiErrorHandler.getErrorStatistics();
};

export const generateErrorReport = () => {
  return apiErrorHandler.generateErrorReport();
};

export default ApiErrorHandler;