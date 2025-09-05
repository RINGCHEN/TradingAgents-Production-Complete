/**
 * AuthErrors - 認證錯誤處理工具
 * 提供認證錯誤的分類、處理和恢復建議
 */

export interface AuthErrorInfo {
  type: 'network' | 'token' | 'server' | 'validation' | 'initialization' | 'unknown';
  message: string;
  code?: string;
  timestamp: Date;
  recoverable: boolean;
  userMessage: string;
  suggestedAction: string;
}

export class AuthErrorHandler {
  /**
   * 處理認證錯誤
   */
  static handleAuthError(error: any): AuthErrorInfo {
    const errorInfo = this.categorizeError(error);
    
    // 記錄錯誤
    console.error('認證錯誤:', {
      type: errorInfo.type,
      message: errorInfo.message,
      code: errorInfo.code,
      timestamp: errorInfo.timestamp
    });

    return errorInfo;
  }

  /**
   * 分類錯誤
   */
  private static categorizeError(error: any): AuthErrorInfo {
    const timestamp = new Date();
    
    // 網路錯誤
    if (this.isNetworkError(error)) {
      return {
        type: 'network',
        message: error?.message || 'Network connection failed',
        timestamp,
        recoverable: true,
        userMessage: '網路連線異常，請檢查網路連線',
        suggestedAction: '請檢查網路連線後重試'
      };
    }

    // Token錯誤
    if (this.isTokenError(error)) {
      return {
        type: 'token',
        message: error?.message || 'Authentication token invalid',
        code: error?.code,
        timestamp,
        recoverable: false,
        userMessage: '登錄狀態已過期',
        suggestedAction: '請重新登錄'
      };
    }

    // 服務器錯誤
    if (this.isServerError(error)) {
      return {
        type: 'server',
        message: error?.message || 'Server error occurred',
        code: error?.status?.toString(),
        timestamp,
        recoverable: true,
        userMessage: '服務器暫時無法響應',
        suggestedAction: '請稍後重試'
      };
    }

    // 驗證錯誤
    if (this.isValidationError(error)) {
      return {
        type: 'validation',
        message: error?.message || 'Validation failed',
        code: error?.code,
        timestamp,
        recoverable: false,
        userMessage: '輸入的資訊有誤',
        suggestedAction: '請檢查輸入資訊'
      };
    }

    // 初始化錯誤
    if (this.isInitializationError(error)) {
      return {
        type: 'initialization',
        message: error?.message || 'Authentication initialization failed',
        timestamp,
        recoverable: true,
        userMessage: '認證系統初始化失敗',
        suggestedAction: '請刷新頁面重試'
      };
    }

    // 未知錯誤
    return {
      type: 'unknown',
      message: error?.message || 'Unknown authentication error',
      timestamp,
      recoverable: false,
      userMessage: '發生未知錯誤',
      suggestedAction: '請聯繫客服'
    };
  }

  /**
   * 判斷是否為網路錯誤
   */
  private static isNetworkError(error: any): boolean {
    const message = error?.message?.toLowerCase() || '';
    return (
      message.includes('network') ||
      message.includes('fetch') ||
      message.includes('timeout') ||
      message.includes('connection') ||
      error?.name === 'NetworkError' ||
      error?.code === 'NETWORK_ERROR'
    );
  }

  /**
   * 判斷是否為Token錯誤
   */
  private static isTokenError(error: any): boolean {
    return (
      error?.message?.includes('token') ||
      error?.message?.includes('jwt') ||
      error?.message?.includes('unauthorized') ||
      error?.status === 401 ||
      error?.code === 'TOKEN_EXPIRED' ||
      error?.code === 'INVALID_TOKEN'
    );
  }

  /**
   * 判斷是否為服務器錯誤
   */
  private static isServerError(error: any): boolean {
    return (
      error?.status >= 500 ||
      error?.message?.includes('server') ||
      error?.message?.includes('internal') ||
      error?.code === 'SERVER_ERROR'
    );
  }

  /**
   * 判斷是否為驗證錯誤
   */
  private static isValidationError(error: any): boolean {
    const message = error?.message?.toLowerCase() || '';
    return (
      error?.status === 400 ||
      error?.status === 422 ||
      message.includes('validation') ||
      message.includes('invalid') ||
      message.includes('credentials') ||
      message.includes('required') ||
      error?.code === 'VALIDATION_ERROR'
    );
  }

  /**
   * 判斷是否為初始化錯誤
   */
  private static isInitializationError(error: any): boolean {
    return (
      error?.message?.includes('initialization') ||
      error?.message?.includes('init') ||
      error?.code === 'INIT_ERROR'
    );
  }

  /**
   * 獲取錯誤恢復建議
   */
  static getRecoveryStrategy(errorInfo: AuthErrorInfo): {
    canAutoRecover: boolean;
    retryDelay: number;
    maxRetries: number;
    fallbackAction: string;
  } {
    switch (errorInfo.type) {
      case 'network':
        return {
          canAutoRecover: true,
          retryDelay: 2000,
          maxRetries: 3,
          fallbackAction: 'switch-to-guest'
        };

      case 'server':
        return {
          canAutoRecover: true,
          retryDelay: 5000,
          maxRetries: 2,
          fallbackAction: 'switch-to-guest'
        };

      case 'initialization':
        return {
          canAutoRecover: true,
          retryDelay: 1000,
          maxRetries: 3,
          fallbackAction: 'switch-to-guest'
        };

      case 'token':
        return {
          canAutoRecover: false,
          retryDelay: 0,
          maxRetries: 0,
          fallbackAction: 'force-logout'
        };

      case 'validation':
        return {
          canAutoRecover: false,
          retryDelay: 0,
          maxRetries: 0,
          fallbackAction: 'show-error'
        };

      default:
        return {
          canAutoRecover: false,
          retryDelay: 0,
          maxRetries: 0,
          fallbackAction: 'switch-to-guest'
        };
    }
  }

  /**
   * 格式化錯誤消息供用戶顯示
   */
  static formatUserMessage(errorInfo: AuthErrorInfo): {
    title: string;
    message: string;
    action: string;
    severity: 'info' | 'warning' | 'error';
  } {
    switch (errorInfo.type) {
      case 'network':
        return {
          title: '網路連線問題',
          message: errorInfo.userMessage,
          action: errorInfo.suggestedAction,
          severity: 'warning'
        };

      case 'token':
        return {
          title: '登錄已過期',
          message: errorInfo.userMessage,
          action: errorInfo.suggestedAction,
          severity: 'info'
        };

      case 'server':
        return {
          title: '服務暫時不可用',
          message: errorInfo.userMessage,
          action: errorInfo.suggestedAction,
          severity: 'warning'
        };

      case 'initialization':
        return {
          title: '系統初始化失敗',
          message: errorInfo.userMessage,
          action: errorInfo.suggestedAction,
          severity: 'error'
        };

      default:
        return {
          title: '認證錯誤',
          message: errorInfo.userMessage,
          action: errorInfo.suggestedAction,
          severity: 'error'
        };
    }
  }
}

// 便利函數
export const handleAuthError = (error: any): AuthErrorInfo => {
  return AuthErrorHandler.handleAuthError(error);
};

export const getAuthErrorRecovery = (errorInfo: AuthErrorInfo) => {
  return AuthErrorHandler.getRecoveryStrategy(errorInfo);
};

export const formatAuthErrorMessage = (errorInfo: AuthErrorInfo) => {
  return AuthErrorHandler.formatUserMessage(errorInfo);
};

// 常見錯誤類型
export const AUTH_ERROR_TYPES = {
  NETWORK: 'network',
  TOKEN: 'token', 
  SERVER: 'server',
  VALIDATION: 'validation',
  INITIALIZATION: 'initialization',
  UNKNOWN: 'unknown'
} as const;

// 錯誤代碼
export const AUTH_ERROR_CODES = {
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  NETWORK_ERROR: 'NETWORK_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INIT_ERROR: 'INIT_ERROR'
} as const;