/**
 * DiagnosticApiClient - 診斷式API客戶端
 * 整合錯誤診斷系統的API客戶端，自動檢測和報告API響應格式問題
 */

import { reportComponentError } from '../utils/ErrorDiagnostics';

export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  success: boolean;
  status: number;
  headers: Headers;
}

export interface ApiError {
  type: 'network' | 'server' | 'client' | 'format' | 'timeout';
  status?: number;
  message: string;
  endpoint: string;
  timestamp: Date;
  details?: any;
}

export interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  validateJson?: boolean;
}

export class DiagnosticApiClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private defaultRetryAttempts: number;

  constructor(baseUrl: string = '', defaultTimeout: number = 10000) {
    this.baseUrl = baseUrl;
    this.defaultTimeout = defaultTimeout;
    this.defaultRetryAttempts = 3;
  }

  /**
   * 發送API請求
   */
  async request<T = any>(endpoint: string, options: ApiRequestOptions = {}): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      retryAttempts = this.defaultRetryAttempts,
      retryDelay = 1000,
      validateJson = true
    } = options;

    const url = this.buildUrl(endpoint);
    const startTime = Date.now();

    // 準備請求配置
    const requestConfig: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    if (body && method !== 'GET') {
      requestConfig.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    // 執行請求（帶重試機制）
    for (let attempt = 1; attempt <= retryAttempts; attempt++) {
      try {
        const response = await this.executeRequest(url, requestConfig, timeout);
        const apiResponse = await this.processResponse<T>(response, endpoint, validateJson);
        
        // 記錄成功的請求
        this.logRequest(endpoint, method, Date.now() - startTime, response.status, true);
        
        return apiResponse;

      } catch (error) {
        const isLastAttempt = attempt === retryAttempts;
        
        if (isLastAttempt) {
          // 最後一次嘗試失敗，報告錯誤
          const apiError = this.createApiError(error, endpoint, method);
          this.reportApiError(apiError);
          this.logRequest(endpoint, method, Date.now() - startTime, 0, false, apiError);
          
          return {
            success: false,
            status: 0,
            error: apiError,
            headers: new Headers()
          };
        } else {
          // 等待後重試
          await this.delay(retryDelay * attempt);
        }
      }
    }

    // 這裡不應該到達，但為了類型安全
    throw new Error('Unexpected error in request execution');
  }

  /**
   * 執行HTTP請求
   */
  private async executeRequest(url: string, config: RequestInit, timeout: number): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Request timeout after ${timeout}ms`);
      }
      
      throw error;
    }
  }

  /**
   * 處理響應
   */
  private async processResponse<T>(
    response: Response, 
    endpoint: string, 
    validateJson: boolean
  ): Promise<ApiResponse<T>> {
    const contentType = response.headers.get('content-type') || '';
    
    // 檢查響應格式問題
    if (validateJson && endpoint.includes('/api/') && contentType.includes('text/html')) {
      const apiError: ApiError = {
        type: 'format',
        status: response.status,
        message: `API endpoint returned HTML instead of JSON: ${endpoint}`,
        endpoint,
        timestamp: new Date(),
        details: {
          contentType,
          expectedType: 'application/json',
          responseUrl: response.url
        }
      };
      
      this.reportApiError(apiError);
      
      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: response.headers
      };
    }

    // 檢查HTTP狀態
    if (!response.ok) {
      const errorText = await this.safeGetResponseText(response);
      const apiError: ApiError = {
        type: response.status >= 500 ? 'server' : 'client',
        status: response.status,
        message: `HTTP ${response.status}: ${response.statusText}`,
        endpoint,
        timestamp: new Date(),
        details: {
          statusText: response.statusText,
          responseText: errorText?.substring(0, 500)
        }
      };
      
      this.reportApiError(apiError);
      
      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: response.headers
      };
    }

    // 嘗試解析響應數據
    try {
      let data: T;
      
      if (contentType.includes('application/json')) {
        const responseText = await response.text();
        
        if (!responseText.trim()) {
          data = null as T;
        } else {
          try {
            data = JSON.parse(responseText);
          } catch (parseError) {
            // JSON解析失敗，可能是格式問題
            const apiError: ApiError = {
              type: 'format',
              status: response.status,
              message: `Failed to parse JSON response from ${endpoint}`,
              endpoint,
              timestamp: new Date(),
              details: {
                parseError: parseError instanceof Error ? parseError.message : parseError,
                responseText: responseText.substring(0, 200)
              }
            };
            
            this.reportApiError(apiError);
            
            return {
              success: false,
              status: response.status,
              error: apiError,
              headers: response.headers
            };
          }
        }
      } else {
        // 非JSON響應
        data = await response.text() as T;
      }

      return {
        success: true,
        status: response.status,
        data,
        headers: response.headers
      };

    } catch (error) {
      const apiError: ApiError = {
        type: 'format',
        status: response.status,
        message: `Error processing response from ${endpoint}`,
        endpoint,
        timestamp: new Date(),
        details: {
          error: error instanceof Error ? error.message : error
        }
      };
      
      this.reportApiError(apiError);
      
      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: response.headers
      };
    }
  }

  /**
   * 安全獲取響應文本
   */
  private async safeGetResponseText(response: Response): Promise<string | null> {
    try {
      return await response.text();
    } catch (error) {
      return null;
    }
  }

  /**
   * 創建API錯誤對象
   */
  private createApiError(error: any, endpoint: string, method: string): ApiError {
    if (error instanceof Error) {
      if (error.message.includes('timeout')) {
        return {
          type: 'timeout',
          message: `Request timeout for ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message }
        };
      }
      
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return {
          type: 'network',
          message: `Network error for ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message }
        };
      }
    }

    return {
      type: 'client',
      message: `Request failed for ${method} ${endpoint}: ${error?.message || error}`,
      endpoint,
      timestamp: new Date(),
      details: { originalError: error }
    };
  }

  /**
   * 報告API錯誤到診斷系統
   */
  private reportApiError(apiError: ApiError): void {
    const category = apiError.type === 'network' ? 'network' : 'api';
    
    reportComponentError(
      category,
      apiError.message,
      {
        apiError,
        endpoint: apiError.endpoint,
        type: apiError.type,
        status: apiError.status
      }
    );
  }

  /**
   * 記錄請求日誌
   */
  private logRequest(
    endpoint: string, 
    method: string, 
    duration: number, 
    status: number, 
    success: boolean,
    error?: ApiError
  ): void {
    const logData = {
      endpoint,
      method,
      duration,
      status,
      success,
      timestamp: new Date().toISOString()
    };

    if (process.env.NODE_ENV === 'development') {
      if (success) {
        console.log(`✅ API ${method} ${endpoint} - ${status} (${duration}ms)`, logData);
      } else {
        console.error(`❌ API ${method} ${endpoint} - Failed (${duration}ms)`, logData, error);
      }
    }
  }

  /**
   * 構建完整URL
   */
  private buildUrl(endpoint: string): string {
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      return endpoint;
    }
    
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${this.baseUrl}${cleanEndpoint}`;
  }

  /**
   * 延遲函數
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * GET請求
   */
  async get<T = any>(endpoint: string, options: Omit<ApiRequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST請求
   */
  async post<T = any>(endpoint: string, data?: any, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body: data });
  }

  /**
   * PUT請求
   */
  async put<T = any>(endpoint: string, data?: any, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body: data });
  }

  /**
   * DELETE請求
   */
  async delete<T = any>(endpoint: string, options: Omit<ApiRequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * 健康檢查 - 為前端應用優化
   */
  async healthCheck(): Promise<boolean> {
    try {
      // 對於純前端應用，我們檢查基本功能而不是API端點
      return navigator.onLine && 
             document.readyState === 'complete' && 
             !!document.getElementById('root');
    } catch (error) {
      return false;
    }
  }
}

// 創建默認實例
export const apiClient = new DiagnosticApiClient();

// 專門用於優惠券API的客戶端（針對已知問題）
export const couponApiClient = new DiagnosticApiClient();

// 優惠券API專用方法
export const loadCouponsWithDiagnostics = async () => {
  try {
    const response = await couponApiClient.get('/api/coupons', {
      validateJson: true,
      retryAttempts: 2,
      timeout: 8000
    });

    if (!response.success && response.error?.type === 'format') {
      // 特別處理優惠券API格式錯誤
      reportComponentError('coupon', 'Coupon API returned invalid format - likely HTML instead of JSON', {
        endpoint: '/api/coupons',
        error: response.error,
        suggestion: 'Check coupon API routing and ensure it returns JSON'
      });
      
      // 返回空的優惠券列表作為降級
      return {
        success: true,
        data: [],
        fallback: true
      };
    }

    return response;
  } catch (error) {
    reportComponentError('coupon', 'Failed to load coupons', { error });
    return {
      success: false,
      error,
      fallback: true
    };
  }
};

export default DiagnosticApiClient;