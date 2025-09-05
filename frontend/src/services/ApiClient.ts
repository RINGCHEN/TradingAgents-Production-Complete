/**
 * ApiClient - 通用API客戶端
 * 專門處理API請求和響應驗證，確保返回JSON而非HTML
 * 實施API錯誤分類和處理機制
 */

export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  success: boolean;
  status: number;
  headers: Record<string, string>;
  isHtml?: boolean;
  isCorsError?: boolean;
}

export interface ApiError {
  type: 'network' | 'server' | 'client' | 'format' | 'timeout' | 'cors' | 'not_found';
  status?: number;
  message: string;
  endpoint: string;
  timestamp: Date;
  details?: any;
  isRetryable?: boolean;
}

export interface ApiRequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  validateJsonResponse?: boolean;
  expectJson?: boolean;
}

export class ApiClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private defaultHeaders: Record<string, string>;

  constructor(
    baseUrl: string = '',
    defaultTimeout: number = 10000,
    defaultHeaders: Record<string, string> = {}
  ) {
    this.baseUrl = baseUrl;
    this.defaultTimeout = defaultTimeout;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...defaultHeaders
    };
  }

  /**
   * 發送API請求並驗證響應格式
   */
  async request<T = any>(endpoint: string, config: ApiRequestConfig = {}): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      retryAttempts = 3,
      retryDelay = 1000,
      validateJsonResponse = true,
      expectJson = true
    } = config;

    const url = this.buildUrl(endpoint);
    const requestHeaders = { ...this.defaultHeaders, ...headers };
    
    // 準備請求配置
    const requestConfig: RequestInit = {
      method,
      headers: requestHeaders,
      mode: 'cors', // 明確設置CORS模式
      credentials: 'include' // 包含認證信息
    };

    if (body && method !== 'GET') {
      requestConfig.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    // 執行請求（帶重試機制）
    for (let attempt = 1; attempt <= retryAttempts; attempt++) {
      try {
        const response = await this.executeRequestWithTimeout(url, requestConfig, timeout);
        const apiResponse = await this.processAndValidateResponse<T>(
          response, 
          endpoint, 
          validateJsonResponse,
          expectJson
        );
        
        return apiResponse;

      } catch (error) {
        const isLastAttempt = attempt === retryAttempts;
        
        if (isLastAttempt) {
          const apiError = this.categorizeError(error, endpoint, method);
          return {
            success: false,
            status: 0,
            error: apiError,
            headers: {},
            isCorsError: apiError.type === 'cors'
          };
        } else if (this.shouldRetry(error)) {
          // 等待後重試
          await this.delay(retryDelay * attempt);
        } else {
          // 不可重試的錯誤，直接返回
          const apiError = this.categorizeError(error, endpoint, method);
          return {
            success: false,
            status: 0,
            error: apiError,
            headers: {},
            isCorsError: apiError.type === 'cors'
          };
        }
      }
    }

    // 這裡不應該到達
    throw new Error('Unexpected error in request execution');
  }

  /**
   * 執行帶超時的HTTP請求
   */
  private async executeRequestWithTimeout(
    url: string, 
    config: RequestInit, 
    timeout: number
  ): Promise<Response> {
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
   * 處理和驗證響應
   */
  private async processAndValidateResponse<T>(
    response: Response,
    endpoint: string,
    validateJsonResponse: boolean,
    expectJson: boolean
  ): Promise<ApiResponse<T>> {
    const contentType = response.headers.get('content-type') || '';
    const responseHeaders = this.extractHeaders(response.headers);
    
    // 檢查是否返回了HTML而不是JSON
    const isHtmlResponse = contentType.includes('text/html');
    
    if (validateJsonResponse && expectJson && isHtmlResponse) {
      const apiError: ApiError = {
        type: 'format',
        status: response.status,
        message: `API端點返回HTML而非JSON: ${endpoint}`,
        endpoint,
        timestamp: new Date(),
        details: {
          contentType,
          expectedType: 'application/json',
          responseUrl: response.url,
          statusText: response.statusText
        },
        isRetryable: false
      };
      
      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: responseHeaders,
        isHtml: true
      };
    }

    // 處理404錯誤
    if (response.status === 404) {
      const apiError: ApiError = {
        type: 'not_found',
        status: 404,
        message: `API端點不存在: ${endpoint}`,
        endpoint,
        timestamp: new Date(),
        details: {
          statusText: response.statusText,
          responseUrl: response.url
        },
        isRetryable: false
      };

      return {
        success: false,
        status: 404,
        error: apiError,
        headers: responseHeaders
      };
    }

    // 處理服務器錯誤（5xx）
    if (response.status >= 500) {
      const errorText = await this.safeGetResponseText(response);
      const apiError: ApiError = {
        type: 'server',
        status: response.status,
        message: `服務器錯誤 ${response.status}: ${response.statusText}`,
        endpoint,
        timestamp: new Date(),
        details: {
          statusText: response.statusText,
          responseText: errorText?.substring(0, 500),
          responseUrl: response.url
        },
        isRetryable: true
      };

      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: responseHeaders
      };
    }

    // 處理客戶端錯誤（4xx，除了404）
    if (response.status >= 400 && response.status < 500) {
      const errorText = await this.safeGetResponseText(response);
      const apiError: ApiError = {
        type: 'client',
        status: response.status,
        message: `客戶端錯誤 ${response.status}: ${response.statusText}`,
        endpoint,
        timestamp: new Date(),
        details: {
          statusText: response.statusText,
          responseText: errorText?.substring(0, 500),
          responseUrl: response.url
        },
        isRetryable: false
      };

      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: responseHeaders
      };
    }

    // 解析成功響應
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
            const apiError: ApiError = {
              type: 'format',
              status: response.status,
              message: `JSON解析失敗: ${endpoint}`,
              endpoint,
              timestamp: new Date(),
              details: {
                parseError: parseError instanceof Error ? parseError.message : parseError,
                responseText: responseText.substring(0, 200)
              },
              isRetryable: false
            };
            
            return {
              success: false,
              status: response.status,
              error: apiError,
              headers: responseHeaders
            };
          }
        }
      } else if (expectJson) {
        // 期望JSON但收到其他格式
        const apiError: ApiError = {
          type: 'format',
          status: response.status,
          message: `期望JSON響應但收到 ${contentType}: ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: {
            contentType,
            expectedType: 'application/json'
          },
          isRetryable: false
        };
        
        return {
          success: false,
          status: response.status,
          error: apiError,
          headers: responseHeaders
        };
      } else {
        // 非JSON響應，直接返回文本
        data = await response.text() as T;
      }

      return {
        success: true,
        status: response.status,
        data,
        headers: responseHeaders,
        isHtml: isHtmlResponse
      };

    } catch (error) {
      const apiError: ApiError = {
        type: 'format',
        status: response.status,
        message: `響應處理失敗: ${endpoint}`,
        endpoint,
        timestamp: new Date(),
        details: {
          error: error instanceof Error ? error.message : error
        },
        isRetryable: false
      };
      
      return {
        success: false,
        status: response.status,
        error: apiError,
        headers: responseHeaders
      };
    }
  }

  /**
   * 分類錯誤類型
   */
  private categorizeError(error: any, endpoint: string, method: string): ApiError {
    if (error instanceof Error) {
      // 超時錯誤
      if (error.message.includes('timeout') || error.message.includes('Request timeout')) {
        return {
          type: 'timeout',
          message: `請求超時: ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message },
          isRetryable: true
        };
      }
      
      // 網路錯誤
      if (error.message.includes('Failed to fetch') || 
          error.message.includes('NetworkError') ||
          error.message.includes('ERR_NETWORK') ||
          error.message.includes('fetch')) {
        return {
          type: 'network',
          message: `網路錯誤: ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message },
          isRetryable: true
        };
      }

      // CORS錯誤
      if (error.message.includes('CORS') || 
          error.message.includes('Cross-Origin') ||
          error.message.includes('blocked by CORS policy')) {
        return {
          type: 'cors',
          message: `CORS錯誤: ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message },
          isRetryable: false
        };
      }
    }

    return {
      type: 'client',
      message: `請求失敗: ${method} ${endpoint}: ${error?.message || error}`,
      endpoint,
      timestamp: new Date(),
      details: { originalError: error },
      isRetryable: false
    };
  }

  /**
   * 判斷是否應該重試
   */
  private shouldRetry(error: any): boolean {
    if (error instanceof Error) {
      // 不重試CORS錯誤和解析錯誤
      if (error.message.includes('CORS') || 
          error.message.includes('JSON') ||
          error.message.includes('SyntaxError')) {
        return false;
      }
      
      // 重試網路和超時錯誤
      if (error.message.includes('timeout') || 
          error.message.includes('Failed to fetch') ||
          error.message.includes('NetworkError')) {
        return true;
      }
    }
    
    return false;
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
   * 提取響應頭
   */
  private extractHeaders(headers: Headers): Record<string, string> {
    const result: Record<string, string> = {};
    headers.forEach((value, key) => {
      result[key] = value;
    });
    return result;
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

  // 便捷方法

  /**
   * GET請求
   */
  async get<T = any>(endpoint: string, config: Omit<ApiRequestConfig, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST請求
   */
  async post<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body: data });
  }

  /**
   * PUT請求
   */
  async put<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body: data });
  }

  /**
   * DELETE請求
   */
  async delete<T = any>(endpoint: string, config: Omit<ApiRequestConfig, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * PATCH請求
   */
  async patch<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body: data });
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

  /**
   * 檢查CORS配置
   */
  async checkCorsConfiguration(): Promise<{ success: boolean; details?: any }> {
    try {
      const response = await this.get('/api/cors-test', {
        timeout: 5000,
        retryAttempts: 1,
        expectJson: false
      });

      return {
        success: response.success,
        details: {
          status: response.status,
          headers: response.headers,
          corsError: response.isCorsError
        }
      };
    } catch (error) {
      return {
        success: false,
        details: { 
          error: error instanceof Error ? error.message : error 
        }
      };
    }
  }
}

// 環境配置
const getApiBaseUrl = (): string => {
  // 在開發環境中，如果有Vite代理，使用空字符串（相對路徑）
  if (import.meta.env.DEV) {
    return ''; // Vite代理會處理/api路徑
  }
  
  // 生產環境使用環境變量或默認值
  return import.meta.env.VITE_API_BASE_URL || '';
};

const getApiTimeout = (): number => {
  return parseInt(import.meta.env.VITE_API_TIMEOUT || '10000', 10);
};

// 創建默認實例
export const apiClient = new ApiClient(
  getApiBaseUrl(),
  getApiTimeout(),
  {
    'X-Client-Version': '2.0.0',
    'X-Environment': import.meta.env.VITE_ENVIRONMENT || 'development'
  }
);

// 創建專門用於API測試的實例
export const testApiClient = new ApiClient(
  getApiBaseUrl(), 
  5000, 
  {
    'X-Test-Client': 'true',
    'X-Client-Version': '2.0.0',
    'X-Environment': import.meta.env.VITE_ENVIRONMENT || 'development'
  }
);

export default ApiClient;