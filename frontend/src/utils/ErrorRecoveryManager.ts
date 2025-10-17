// @ts-nocheck
/**
 * ErrorRecoveryManager - 錯誤恢復管理器
 * 處理複雜的錯誤恢復邏輯，包括自動恢復、降級策略和狀態管理
 */

import { reportComponentError } from './ErrorDiagnostics';

export interface RecoveryStrategy {
  id: string;
  name: string;
  description: string;
  priority: number;
  canApply: (error: Error, context: RecoveryContext) => boolean;
  apply: (error: Error, context: RecoveryContext) => Promise<RecoveryResult>;
  rollback?: (context: RecoveryContext) => Promise<void>;
}

export interface RecoveryContext {
  componentName: string;
  errorCount: number;
  lastErrorTime: Date;
  errorHistory: ErrorRecord[];
  userAgent: string;
  url: string;
  userId?: string;
  sessionId: string;
  retryAttempts: number;
  maxRetries: number;
}

export interface RecoveryResult {
  success: boolean;
  strategy: string;
  message: string;
  shouldRetry: boolean;
  fallbackMode?: 'minimal' | 'static' | 'offline';
  data?: any;
}

export interface ErrorRecord {
  error: Error;
  timestamp: Date;
  componentName: string;
  recoveryAttempted: boolean;
  recoveryStrategy?: string;
  recoverySuccess: boolean;
}

export class ErrorRecoveryManager {
  private static instance: ErrorRecoveryManager;
  private strategies: Map<string, RecoveryStrategy> = new Map();
  private errorHistory: ErrorRecord[] = [];
  private recoveryInProgress: Set<string> = new Set();

  private constructor() {
    this.initializeDefaultStrategies();
  }

  public static getInstance(): ErrorRecoveryManager {
    if (!ErrorRecoveryManager.instance) {
      ErrorRecoveryManager.instance = new ErrorRecoveryManager();
    }
    return ErrorRecoveryManager.instance;
  }

  /**
   * 初始化默認恢復策略
   */
  private initializeDefaultStrategies(): void {
    // 策略1: 清理localStorage
    this.registerStrategy({
      id: 'clear-local-storage',
      name: '清理本地存儲',
      description: '清理可能損壞的localStorage數據',
      priority: 1,
      canApply: (error, context) => {
        return error.message.includes('localStorage') || 
               error.message.includes('quota') ||
               context.errorCount >= 2;
      },
      apply: async (error, context) => {
        try {
          // 清理可能損壞的數據
          const suspiciousKeys = ['authToken', 'userInfo', 'couponData', 'analysisCache'];
          let clearedKeys = 0;

          suspiciousKeys.forEach(key => {
            try {
              const value = localStorage.getItem(key);
              if (value && (value.includes('<html') || value.includes('<!DOCTYPE') || value.length > 100000)) {
                localStorage.removeItem(key);
                clearedKeys++;
              }
            } catch (e) {
              // 忽略清理錯誤
            }
          });

          return {
            success: clearedKeys > 0,
            strategy: 'clear-local-storage',
            message: `已清理 ${clearedKeys} 個可能損壞的localStorage項目`,
            shouldRetry: true,
            data: { clearedKeys }
          };
        } catch (e) {
          return {
            success: false,
            strategy: 'clear-local-storage',
            message: '清理localStorage失敗',
            shouldRetry: false
          };
        }
      }
    });

    // 策略2: 重新載入認證狀態
    this.registerStrategy({
      id: 'reload-auth-state',
      name: '重新載入認證狀態',
      description: '重新初始化認證狀態',
      priority: 2,
      canApply: (error, context) => {
        return error.message.toLowerCase().includes('auth') ||
               error.message.toLowerCase().includes('token') ||
               context.componentName.toLowerCase().includes('auth');
      },
      apply: async (error, context) => {
        try {
          // 清理認證相關的狀態
          localStorage.removeItem('authToken');
          localStorage.removeItem('refreshToken');
          sessionStorage.removeItem('authState');

          // 觸發認證狀態重新初始化
          window.dispatchEvent(new CustomEvent('auth-state-reset'));

          return {
            success: true,
            strategy: 'reload-auth-state',
            message: '已重新初始化認證狀態',
            shouldRetry: true,
            fallbackMode: 'minimal'
          };
        } catch (e) {
          return {
            success: false,
            strategy: 'reload-auth-state',
            message: '認證狀態重新初始化失敗',
            shouldRetry: false
          };
        }
      }
    });

    // 策略3: 清理緩存
    this.registerStrategy({
      id: 'clear-cache',
      name: '清理緩存',
      description: '清理瀏覽器緩存和Service Worker',
      priority: 3,
      canApply: (error, context) => {
        return error.message.includes('cache') ||
               error.message.includes('fetch') ||
               context.errorCount >= 3;
      },
      apply: async (error, context) => {
        try {
          let clearedCaches = 0;

          // 清理Cache API
          if ('caches' in window) {
            const cacheNames = await caches.keys();
            for (const cacheName of cacheNames) {
              await caches.delete(cacheName);
              clearedCaches++;
            }
          }

          // 清理Service Worker
          if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            for (const registration of registrations) {
              await registration.unregister();
            }
          }

          return {
            success: clearedCaches > 0,
            strategy: 'clear-cache',
            message: `已清理 ${clearedCaches} 個緩存`,
            shouldRetry: true,
            data: { clearedCaches }
          };
        } catch (e) {
          return {
            success: false,
            strategy: 'clear-cache',
            message: '緩存清理失敗',
            shouldRetry: false
          };
        }
      }
    });

    // 策略4: 降級到靜態模式
    this.registerStrategy({
      id: 'fallback-static',
      name: '降級到靜態模式',
      description: '切換到靜態內容模式',
      priority: 4,
      canApply: (error, context) => {
        return context.retryAttempts >= 2;
      },
      apply: async (error, context) => {
        return {
          success: true,
          strategy: 'fallback-static',
          message: '已切換到靜態模式',
          shouldRetry: false,
          fallbackMode: 'static'
        };
      }
    });

    // 策略5: 降級到離線模式
    this.registerStrategy({
      id: 'fallback-offline',
      name: '降級到離線模式',
      description: '切換到離線模式',
      priority: 5,
      canApply: (error, context) => {
        return context.retryAttempts >= 3;
      },
      apply: async (error, context) => {
        return {
          success: true,
          strategy: 'fallback-offline',
          message: '已切換到離線模式',
          shouldRetry: false,
          fallbackMode: 'offline'
        };
      }
    });

    // 策略6: 頁面重新載入
    this.registerStrategy({
      id: 'page-reload',
      name: '頁面重新載入',
      description: '重新載入整個頁面',
      priority: 10,
      canApply: (error, context) => {
        return context.errorCount >= 5 && context.retryAttempts >= 4;
      },
      apply: async (error, context) => {
        // 延遲重新載入以避免無限循環
        setTimeout(() => {
          window.location.reload();
        }, 2000);

        return {
          success: true,
          strategy: 'page-reload',
          message: '將在2秒後重新載入頁面',
          shouldRetry: false
        };
      }
    });
  }

  /**
   * 註冊恢復策略
   */
  public registerStrategy(strategy: RecoveryStrategy): void {
    this.strategies.set(strategy.id, strategy);
  }

  /**
   * 移除恢復策略
   */
  public unregisterStrategy(strategyId: string): void {
    this.strategies.delete(strategyId);
  }

  /**
   * 嘗試恢復錯誤
   */
  public async attemptRecovery(
    error: Error,
    componentName: string,
    retryAttempts: number = 0,
    maxRetries: number = 3
  ): Promise<RecoveryResult> {
    const recoveryKey = `${componentName}-${error.message}`;
    
    // 防止同時進行多個恢復嘗試
    if (this.recoveryInProgress.has(recoveryKey)) {
      return {
        success: false,
        strategy: 'none',
        message: '恢復已在進行中',
        shouldRetry: false
      };
    }

    this.recoveryInProgress.add(recoveryKey);

    try {
      // 創建恢復上下文
      const context: RecoveryContext = {
        componentName,
        errorCount: this.getErrorCount(componentName),
        lastErrorTime: new Date(),
        errorHistory: this.getErrorHistory(componentName),
        userAgent: navigator.userAgent,
        url: window.location.href,
        sessionId: this.getSessionId(),
        retryAttempts,
        maxRetries
      };

      // 記錄錯誤
      this.recordError(error, componentName);

      // 報告到診斷系統
      reportComponentError(
        'render',
        `Attempting recovery for ${componentName}: ${error.message}`,
        {
          error: error.message,
          componentName,
          retryAttempts,
          context
        }
      );

      // 找到適用的恢復策略
      const applicableStrategies = Array.from(this.strategies.values())
        .filter(strategy => strategy.canApply(error, context))
        .sort((a, b) => a.priority - b.priority);

      if (applicableStrategies.length === 0) {
        return {
          success: false,
          strategy: 'none',
          message: '沒有適用的恢復策略',
          shouldRetry: retryAttempts < maxRetries
        };
      }

      // 嘗試第一個適用的策略
      const strategy = applicableStrategies[0];
      console.log(`Applying recovery strategy: ${strategy.name}`);

      const result = await strategy.apply(error, context);

      // 更新錯誤記錄
      this.updateErrorRecord(error, componentName, strategy.id, result.success);

      return result;

    } catch (recoveryError) {
      console.error('Recovery attempt failed:', recoveryError);
      
      return {
        success: false,
        strategy: 'error',
        message: `恢復嘗試失敗: ${recoveryError instanceof Error ? recoveryError.message : recoveryError}`,
        shouldRetry: false
      };
    } finally {
      this.recoveryInProgress.delete(recoveryKey);
    }
  }

  /**
   * 記錄錯誤
   */
  private recordError(error: Error, componentName: string): void {
    const errorRecord: ErrorRecord = {
      error,
      timestamp: new Date(),
      componentName,
      recoveryAttempted: false,
      recoverySuccess: false
    };

    this.errorHistory.push(errorRecord);

    // 保持錯誤歷史在合理大小
    if (this.errorHistory.length > 100) {
      this.errorHistory = this.errorHistory.slice(-50);
    }
  }

  /**
   * 更新錯誤記錄
   */
  private updateErrorRecord(
    error: Error, 
    componentName: string, 
    strategyId: string, 
    success: boolean
  ): void {
    const record = this.errorHistory
      .reverse()
      .find(r => r.error.message === error.message && r.componentName === componentName);

    if (record) {
      record.recoveryAttempted = true;
      record.recoveryStrategy = strategyId;
      record.recoverySuccess = success;
    }
  }

  /**
   * 獲取組件錯誤計數
   */
  private getErrorCount(componentName: string): number {
    return this.errorHistory.filter(record => 
      record.componentName === componentName
    ).length;
  }

  /**
   * 獲取組件錯誤歷史
   */
  private getErrorHistory(componentName: string): ErrorRecord[] {
    return this.errorHistory.filter(record => 
      record.componentName === componentName
    );
  }

  /**
   * 獲取會話ID
   */
  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('errorRecoverySessionId');
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('errorRecoverySessionId', sessionId);
    }
    return sessionId;
  }

  /**
   * 獲取錯誤統計
   */
  public getErrorStatistics(): {
    totalErrors: number;
    errorsByComponent: Record<string, number>;
    recoverySuccessRate: number;
    mostCommonErrors: Array<{ message: string; count: number }>;
  } {
    const errorsByComponent: Record<string, number> = {};
    const errorMessages: Record<string, number> = {};
    let recoveryAttempts = 0;
    let recoverySuccesses = 0;

    this.errorHistory.forEach(record => {
      // 按組件統計
      errorsByComponent[record.componentName] = 
        (errorsByComponent[record.componentName] || 0) + 1;

      // 按錯誤消息統計
      errorMessages[record.error.message] = 
        (errorMessages[record.error.message] || 0) + 1;

      // 恢復統計
      if (record.recoveryAttempted) {
        recoveryAttempts++;
        if (record.recoverySuccess) {
          recoverySuccesses++;
        }
      }
    });

    const mostCommonErrors = Object.entries(errorMessages)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([message, count]) => ({ message, count }));

    return {
      totalErrors: this.errorHistory.length,
      errorsByComponent,
      recoverySuccessRate: recoveryAttempts > 0 ? recoverySuccesses / recoveryAttempts : 0,
      mostCommonErrors
    };
  }

  /**
   * 清理錯誤歷史
   */
  public clearErrorHistory(): void {
    this.errorHistory = [];
  }

  /**
   * 檢查組件是否處於錯誤狀態
   */
  public isComponentInErrorState(componentName: string): boolean {
    const recentErrors = this.errorHistory.filter(record => 
      record.componentName === componentName &&
      Date.now() - record.timestamp.getTime() < 60000 // 最近1分鐘
    );

    return recentErrors.length >= 3;
  }

  /**
   * 獲取組件建議的降級模式
   */
  public getRecommendedFallbackMode(componentName: string): 'minimal' | 'static' | 'offline' | 'none' {
    const errorCount = this.getErrorCount(componentName);
    
    if (errorCount >= 5) {
      return 'offline';
    } else if (errorCount >= 3) {
      return 'static';
    } else if (errorCount >= 1) {
      return 'minimal';
    } else {
      return 'none';
    }
  }
}

// 導出單例實例
export const errorRecoveryManager = ErrorRecoveryManager.getInstance();

// 便利函數
export const attemptErrorRecovery = (
  error: Error,
  componentName: string,
  retryAttempts: number = 0,
  maxRetries: number = 3
): Promise<RecoveryResult> => {
  return errorRecoveryManager.attemptRecovery(error, componentName, retryAttempts, maxRetries);
};

export const isComponentInErrorState = (componentName: string): boolean => {
  return errorRecoveryManager.isComponentInErrorState(componentName);
};

export const getRecommendedFallbackMode = (componentName: string): 'minimal' | 'static' | 'offline' | 'none' => {
  return errorRecoveryManager.getRecommendedFallbackMode(componentName);
};

export default ErrorRecoveryManager;