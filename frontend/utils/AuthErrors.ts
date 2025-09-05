/**
 * 認證錯誤處理系統
 * 提供統一的錯誤分類、處理和用戶友好的錯誤信息
 */

export enum AuthErrorType {
  INVALID_CREDENTIALS = 'invalid_credentials',
  TOKEN_EXPIRED = 'token_expired',
  TOKEN_REFRESH_FAILED = 'token_refresh_failed',
  NETWORK_ERROR = 'network_error',
  SERVER_ERROR = 'server_error',
  PERMISSION_DENIED = 'permission_denied',
  VALIDATION_ERROR = 'validation_error',
  RATE_LIMITED = 'rate_limited',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  UNKNOWN_ERROR = 'unknown_error'
}

export interface AuthErrorDetails {
  type: AuthErrorType;
  message: string;
  originalError?: any;
  status?: number;
  timestamp: number;
  requestId?: string;
  suggestions?: string[];
}

export class AuthError extends Error {
  public readonly type: AuthErrorType;
  public readonly status?: number;
  public readonly originalError?: any;
  public readonly timestamp: number;
  public readonly requestId?: string;
  public readonly suggestions: string[];

  constructor(
    message: string,
    type: AuthErrorType = AuthErrorType.UNKNOWN_ERROR,
    options: {
      status?: number;
      originalError?: any;
      requestId?: string;
      suggestions?: string[];
    } = {}
  ) {
    super(message);
    this.name = 'AuthError';
    this.type = type;
    this.status = options.status;
    this.originalError = options.originalError;
    this.timestamp = Date.now();
    this.requestId = options.requestId;
    this.suggestions = options.suggestions || [];
  }

  /**
   * 獲取錯誤詳情
   */
  getDetails(): AuthErrorDetails {
    return {
      type: this.type,
      message: this.message,
      originalError: this.originalError,
      status: this.status,
      timestamp: this.timestamp,
      requestId: this.requestId,
      suggestions: this.suggestions
    };
  }

  /**
   * 獲取用戶友好的錯誤信息
   */
  getUserMessage(): string {
    switch (this.type) {
      case AuthErrorType.INVALID_CREDENTIALS:
        return '用戶名或密碼錯誤，請檢查後重試';
      case AuthErrorType.TOKEN_EXPIRED:
        return '登錄已過期，請重新登錄';
      case AuthErrorType.TOKEN_REFRESH_FAILED:
        return '認證更新失敗，請重新登錄';
      case AuthErrorType.NETWORK_ERROR:
        return '網絡連接失敗，請檢查網絡後重試';
      case AuthErrorType.SERVER_ERROR:
        return '服務器暫時不可用，請稍後重試';
      case AuthErrorType.PERMISSION_DENIED:
        return '權限不足，請聯繫管理員';
      case AuthErrorType.VALIDATION_ERROR:
        return '輸入信息格式錯誤，請檢查後重試';
      case AuthErrorType.RATE_LIMITED:
        return '請求過於頻繁，請稍後重試';
      case AuthErrorType.SERVICE_UNAVAILABLE:
        return '服務暫時不可用，請稍後重試';
      default:
        return this.message || '發生未知錯誤，請稍後重試';
    }
  }

  /**
   * 獲取建議操作
   */
  getSuggestions(): string[] {
    if (this.suggestions.length > 0) {
      return this.suggestions;
    }

    switch (this.type) {
      case AuthErrorType.INVALID_CREDENTIALS:
        return [
          '檢查用戶名和密碼是否正確',
          '確認大小寫是否正確',
          '如果忘記密碼，請聯繫管理員重置'
        ];
      case AuthErrorType.TOKEN_EXPIRED:
      case AuthErrorType.TOKEN_REFRESH_FAILED:
        return [
          '點擊重新登錄',
          '清除瀏覽器緩存後重試'
        ];
      case AuthErrorType.NETWORK_ERROR:
        return [
          '檢查網絡連接',
          '嘗試刷新頁面',
          '檢查防火牆設置'
        ];
      case AuthErrorType.SERVER_ERROR:
      case AuthErrorType.SERVICE_UNAVAILABLE:
        return [
          '稍後重試',
          '如果問題持續，請聯繫技術支援'
        ];
      case AuthErrorType.PERMISSION_DENIED:
        return [
          '聯繫管理員獲取權限',
          '確認使用正確的帳戶登錄'
        ];
      case AuthErrorType.RATE_LIMITED:
        return [
          '等待幾分鐘後重試',
          '避免頻繁操作'
        ];
      default:
        return [
          '刷新頁面重試',
          '如果問題持續，請聯繫技術支援'
        ];
    }
  }

  /**
   * 判斷是否可以重試
   */
  isRetryable(): boolean {
    switch (this.type) {
      case AuthErrorType.NETWORK_ERROR:
      case AuthErrorType.SERVER_ERROR:
      case AuthErrorType.SERVICE_UNAVAILABLE:
      case AuthErrorType.TOKEN_REFRESH_FAILED:
        return true;
      case AuthErrorType.RATE_LIMITED:
        return true; // 延遲後可重試
      default:
        return false;
    }
  }

  /**
   * 判斷是否需要重新登錄
   */
  requiresReauth(): boolean {
    switch (this.type) {
      case AuthErrorType.TOKEN_EXPIRED:
      case AuthErrorType.TOKEN_REFRESH_FAILED:
      case AuthErrorType.INVALID_CREDENTIALS:
        return true;
      default:
        return false;
    }
  }
}

/**
 * 錯誤處理器類
 * 提供統一的錯誤處理和轉換功能
 */
export class AuthErrorHandler {
  private static errorListeners: Set<(error: AuthError) => void> = new Set();

  /**
   * 處理和轉換錯誤
   * @param error 原始錯誤
   * @param context 錯誤上下文
   * @returns 標準化的AuthError
   */
  static handleError(error: any, context?: string): AuthError {
    let authError: AuthError;

    if (error instanceof AuthError) {
      authError = error;
    } else {
      authError = AuthErrorHandler.convertToAuthError(error, context);
    }

    // 記錄錯誤
    AuthErrorHandler.logError(authError, context);

    // 通知監聽器
    AuthErrorHandler.notifyListeners(authError);

    return authError;
  }

  /**
   * 轉換原始錯誤為AuthError
   */
  private static convertToAuthError(error: any, context?: string): AuthError {
    let type = AuthErrorType.UNKNOWN_ERROR;
    let message = '發生未知錯誤';
    let status: number | undefined;
    let suggestions: string[] = [];

    // 根據錯誤類型和狀態碼判斷
    if (error.status || error.response?.status) {
      status = error.status || error.response?.status;
      
      switch (status) {
        case 400:
          type = AuthErrorType.VALIDATION_ERROR;
          message = '請求參數錯誤';
          break;
        case 401:
          type = AuthErrorType.INVALID_CREDENTIALS;
          message = '認證失敗';
          break;
        case 403:
          type = AuthErrorType.PERMISSION_DENIED;
          message = '權限不足';
          break;
        case 408:
        case 0: // 網絡錯誤
          type = AuthErrorType.NETWORK_ERROR;
          message = '網絡連接失敗';
          break;
        case 429:
          type = AuthErrorType.RATE_LIMITED;
          message = '請求過於頻繁';
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          type = AuthErrorType.SERVER_ERROR;
          message = '服務器錯誤';
          break;
      }
    } else if (error.name === 'TypeError' || error.name === 'NetworkError') {
      type = AuthErrorType.NETWORK_ERROR;
      message = '網絡連接失敗';
    } else if (error.name === 'AbortError') {
      type = AuthErrorType.NETWORK_ERROR;
      message = '請求超時';
    }

    // 嘗試從錯誤響應中獲取詳細信息
    if (error.response?.data?.detail) {
      message = error.response.data.detail;
    } else if (error.response?.data?.message) {
      message = error.response.data.message;
    } else if (error.message) {
      message = error.message;
    }

    return new AuthError(message, type, {
      status,
      originalError: error,
      suggestions
    });
  }

  /**
   * 記錄錯誤
   */
  private static logError(error: AuthError, context?: string): void {
    const logData = {
      type: error.type,
      message: error.message,
      status: error.status,
      timestamp: error.timestamp,
      context,
      requestId: error.requestId,
      stack: error.stack
    };

    if (error.type === AuthErrorType.NETWORK_ERROR || 
        error.type === AuthErrorType.SERVER_ERROR) {
      console.error('認證錯誤:', logData);
    } else {
      console.warn('認證警告:', logData);
    }

    // 在生產環境中，這裡可以發送到錯誤監控服務
    if (process.env.NODE_ENV === 'production') {
      // 發送到錯誤監控服務（如 Sentry）
      // sentry.captureException(error, { extra: logData });
    }
  }

  /**
   * 添加錯誤監聽器
   */
  static addErrorListener(listener: (error: AuthError) => void): void {
    AuthErrorHandler.errorListeners.add(listener);
  }

  /**
   * 移除錯誤監聽器
   */
  static removeErrorListener(listener: (error: AuthError) => void): void {
    AuthErrorHandler.errorListeners.delete(listener);
  }

  /**
   * 通知所有監聽器
   */
  private static notifyListeners(error: AuthError): void {
    AuthErrorHandler.errorListeners.forEach(listener => {
      try {
        listener(error);
      } catch (listenerError) {
        console.error('錯誤監聽器執行失敗:', listenerError);
      }
    });
  }

  /**
   * 創建特定類型的錯誤
   */
  static createError(
    type: AuthErrorType, 
    message?: string, 
    options?: {
      status?: number;
      originalError?: any;
      suggestions?: string[];
    }
  ): AuthError {
    return new AuthError(
      message || AuthErrorHandler.getDefaultMessage(type),
      type,
      options
    );
  }

  /**
   * 獲取錯誤類型的默認消息
   */
  private static getDefaultMessage(type: AuthErrorType): string {
    switch (type) {
      case AuthErrorType.INVALID_CREDENTIALS:
        return '認證失敗';
      case AuthErrorType.TOKEN_EXPIRED:
        return 'Token已過期';
      case AuthErrorType.TOKEN_REFRESH_FAILED:
        return 'Token刷新失敗';
      case AuthErrorType.NETWORK_ERROR:
        return '網絡錯誤';
      case AuthErrorType.SERVER_ERROR:
        return '服務器錯誤';
      case AuthErrorType.PERMISSION_DENIED:
        return '權限不足';
      case AuthErrorType.VALIDATION_ERROR:
        return '驗證錯誤';
      case AuthErrorType.RATE_LIMITED:
        return '請求限制';
      case AuthErrorType.SERVICE_UNAVAILABLE:
        return '服務不可用';
      default:
        return '未知錯誤';
    }
  }

  /**
   * 清除所有監聽器
   */
  static clearListeners(): void {
    AuthErrorHandler.errorListeners.clear();
  }

  /**
   * 獲取錯誤統計信息
   */
  static getErrorStats(): {
    totalListeners: number;
  } {
    return {
      totalListeners: AuthErrorHandler.errorListeners.size
    };
  }
}

// 導出便捷函數
export const handleAuthError = (error: any, context?: string) => 
  AuthErrorHandler.handleError(error, context);

export const createAuthError = (
  type: AuthErrorType, 
  message?: string, 
  options?: any
) => AuthErrorHandler.createError(type, message, options);

export const addAuthErrorListener = (listener: (error: AuthError) => void) => 
  AuthErrorHandler.addErrorListener(listener);

export const removeAuthErrorListener = (listener: (error: AuthError) => void) => 
  AuthErrorHandler.removeErrorListener(listener);

// 全局錯誤處理
if (typeof window !== 'undefined') {
  // 監聽未捕獲的Promise拒絕
  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason && (
      event.reason.name === 'AuthError' || 
      event.reason.message?.includes('auth') ||
      event.reason.message?.includes('token')
    )) {
      const authError = AuthErrorHandler.handleError(event.reason, 'unhandledrejection');
      console.error('未處理的認證錯誤:', authError);
      
      // 防止默認的錯誤處理
      event.preventDefault();
    }
  });

  // 監聽全局錯誤
  window.addEventListener('error', (event) => {
    if (event.error && (
      event.error.name === 'AuthError' ||
      event.error.message?.includes('auth') ||
      event.error.message?.includes('token')
    )) {
      const authError = AuthErrorHandler.handleError(event.error, 'global-error');
      console.error('全局認證錯誤:', authError);
    }
  });
}