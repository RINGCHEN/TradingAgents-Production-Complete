import { env } from '../utils/env';

/**
 * ApiClient - ?�用API客戶�?
 * 專�??��?API請�??�響?��?證�?確�?返�?JSON?��?HTML
 * 實施API?�誤?��??��??��???
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
   * ?�送API請�?並�?證響?�格�?
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
    
    // 準�?請�??�置
    const requestConfig: RequestInit = {
      method,
      headers: requestHeaders,
      mode: 'cors', // ?�確設置CORS模�?
      credentials: 'include' // ?�含認�?信息
    };

    if (body && method !== 'GET') {
      requestConfig.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    // ?��?請�?（帶?�試機制�?
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
          // 等�?後�?�?
          await this.delay(retryDelay * attempt);
        } else {
          // 不可?�試?�錯誤�??�接返�?
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

    // ?�裡不�?該到??
    throw new Error('Unexpected error in request execution');
  }

  /**
   * ?��?帶�??��?HTTP請�?
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
   * ?��??��?證響??
   */
  private async processAndValidateResponse<T>(
    response: Response,
    endpoint: string,
    validateJsonResponse: boolean,
    expectJson: boolean
  ): Promise<ApiResponse<T>> {
    const contentType = response.headers.get('content-type') || '';
    const responseHeaders = this.extractHeaders(response.headers);
    
    // 檢查?�否返�?了HTML?��??�JSON
    const isHtmlResponse = contentType.includes('text/html');
    
    if (validateJsonResponse && expectJson && isHtmlResponse) {
      const apiError: ApiError = {
        type: 'format',
        status: response.status,
        message: `API端�?返�?HTML?��?JSON: ${endpoint}`,
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

    // ?��?404?�誤
    if (response.status === 404) {
      const apiError: ApiError = {
        type: 'not_found',
        status: 404,
        message: `API端�?不�??? ${endpoint}`,
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

    // ?��??��??�錯誤�?5xx�?
    if (response.status >= 500) {
      const errorText = await this.safeGetResponseText(response);
      const apiError: ApiError = {
        type: 'server',
        status: response.status,
        message: `?��??�錯�?${response.status}: ${response.statusText}`,
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

    // ?��?客戶端錯誤�?4xx，除�?04�?
    if (response.status >= 400 && response.status < 500) {
      const errorText = await this.safeGetResponseText(response);
      const apiError: ApiError = {
        type: 'client',
        status: response.status,
        message: `客戶端錯�?${response.status}: ${response.statusText}`,
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

    // �???��??��?
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
              message: `JSON�??失�?: ${endpoint}`,
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
        // ?��?JSON但收?�其他格�?
        const apiError: ApiError = {
          type: 'format',
          status: response.status,
          message: `?��?JSON?��?但收??${contentType}: ${endpoint}`,
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
        // ?�JSON?��?，直?��??��???
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
        message: `?��??��?失�?: ${endpoint}`,
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
   * ?��??�誤類�?
   */
  private categorizeError(error: any, endpoint: string, method: string): ApiError {
    if (error instanceof Error) {
      // 超�??�誤
      if (error.message.includes('timeout') || error.message.includes('Request timeout')) {
        return {
          type: 'timeout',
          message: `請�?超�?: ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message },
          isRetryable: true
        };
      }
      
      // 網路?�誤
      if (error.message.includes('Failed to fetch') || 
          error.message.includes('NetworkError') ||
          error.message.includes('ERR_NETWORK') ||
          error.message.includes('fetch')) {
        return {
          type: 'network',
          message: `網路?�誤: ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message },
          isRetryable: true
        };
      }

      // CORS?�誤
      if (error.message.includes('CORS') || 
          error.message.includes('Cross-Origin') ||
          error.message.includes('blocked by CORS policy')) {
        return {
          type: 'cors',
          message: `CORS?�誤: ${method} ${endpoint}`,
          endpoint,
          timestamp: new Date(),
          details: { originalError: error.message },
          isRetryable: false
        };
      }
    }

    return {
      type: 'client',
      message: `請�?失�?: ${method} ${endpoint}: ${error?.message || error}`,
      endpoint,
      timestamp: new Date(),
      details: { originalError: error },
      isRetryable: false
    };
  }

  /**
   * ?�斷?�否?�該?�試
   */
  private shouldRetry(error: any): boolean {
    if (error instanceof Error) {
      // 不�?試CORS?�誤?�解?�錯�?
      if (error.message.includes('CORS') || 
          error.message.includes('JSON') ||
          error.message.includes('SyntaxError')) {
        return false;
      }
      
      // ?�試網路?��??�錯�?
      if (error.message.includes('timeout') || 
          error.message.includes('Failed to fetch') ||
          error.message.includes('NetworkError')) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * 安全?��??��??�本
   */
  private async safeGetResponseText(response: Response): Promise<string | null> {
    try {
      return await response.text();
    } catch (error) {
      return null;
    }
  }

  /**
   * ?��??��???
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
   * 延遲?�數
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 便捷?��?

  /**
   * GET請�?
   */
  async get<T = any>(endpoint: string, config: Omit<ApiRequestConfig, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST請�?
   */
  async post<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body: data });
  }

  /**
   * PUT請�?
   */
  async put<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body: data });
  }

  /**
   * DELETE請�?
   */
  async delete<T = any>(endpoint: string, config: Omit<ApiRequestConfig, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * PATCH請�?
   */
  async patch<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body: data });
  }

  /**
   * ?�康檢查 - ?��?端�??�優??
   */
  async healthCheck(): Promise<boolean> {
    try {
      // 對於純�?端�??��??�們檢?�基?��??�而�??�API端�?
      return navigator.onLine && 
             document.readyState === 'complete' && 
             !!document.getElementById('root');
    } catch (error) {
      return false;
    }
  }

  /**
   * 檢查CORS?�置
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

// 配置
const getApiBaseUrl = (): string => {
  // 開發環境中，使用 Vite 代理，使用空字符串相對路徑
  if (env.isDev) {
    return ''; // Vite 會代理 api 路徑
  }

  // 生產環境使用環境變量或默認值
  return env.apiBaseUrl;
};

const getApiTimeout = (): number => {
  return env.apiTimeout;
};

// ?�建默�?實�?
export const apiClient = new ApiClient(
  getApiBaseUrl(),
  getApiTimeout(),
  {
    'X-Client-Version': '2.0.0',
    'X-Environment': env.environment
  }
);

// ?�建專�??�於API測試?�實�?
export const testApiClient = new ApiClient(
  getApiBaseUrl(), 
  5000, 
  {
    'X-Test-Client': 'true',
    'X-Client-Version': '2.0.0',
    'X-Environment': env.environment
  }
);

export default ApiClient;
