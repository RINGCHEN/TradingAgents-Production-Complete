// API客戶端 - 自動處理認證header和錯誤重試
// 提供統一的API調用接口和認證處理

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { TokenManager } from './TokenManager';

export interface ApiError extends Error {
  status?: number;
  response?: any;
  isNetworkError?: boolean;
  isAuthError?: boolean;
}

export class ApiClient {
  private axiosInstance: AxiosInstance;
  private tokenManager: TokenManager;
  private requestQueue: Array<() => Promise<any>> = [];
  private isRefreshingToken = false;
  private requestCache = new Map<string, { data: any; timestamp: number }>();
  private readonly CACHE_TTL = 30 * 1000; // 30秒緩存
  private pendingRequests = new Map<string, Promise<any>>();

  constructor() {
    this.tokenManager = new TokenManager();
    this.axiosInstance = axios.create({
      baseURL: '/api',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      },
      // 連接池優化
      maxRedirects: 3,
      maxContentLength: 50 * 1024 * 1024, // 50MB
      maxBodyLength: 50 * 1024 * 1024,
    });

    this.setupInterceptors();
    
    // 預熱token緩存
    this.tokenManager.warmupCache();
  }

  /**
   * 設置請求和響應攔截器
   */
  private setupInterceptors(): void {
    // 請求攔截器 - 自動添加認證header
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        const token = await this.tokenManager.getValidToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: any) => {
        return Promise.reject(this.createApiError(error));
      }
    );

    // 響應攔截器 - 處理認證錯誤和自動重試
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // 處理401認證錯誤
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshingToken) {
            // 如果正在刷新token，將請求加入隊列
            return new Promise((resolve, reject) => {
              this.requestQueue.push(async () => {
                try {
                  const token = await this.tokenManager.getValidToken();
                  if (token && originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                  }
                  resolve(this.axiosInstance(originalRequest));
                } catch (err) {
                  reject(err);
                }
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshingToken = true;

          try {
            // 嘗試刷新token
            const refreshed = await this.tokenManager.refreshToken();
            
            if (refreshed) {
              // 處理隊列中的請求
              this.processRequestQueue();
              
              // 重試原始請求
              const token = await this.tokenManager.getValidToken();
              if (token && originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              return this.axiosInstance(originalRequest);
            } else {
              // 刷新失敗，觸發登出
              this.handleAuthFailure();
              throw this.createApiError(error, true);
            }
          } finally {
            this.isRefreshingToken = false;
          }
        }

        return Promise.reject(this.createApiError(error));
      }
    );
  }

  /**
   * GET請求（帶緩存和去重）
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig & { useCache?: boolean }): Promise<AxiosResponse<T>> {
    const cacheKey = `GET:${url}:${JSON.stringify(config?.params || {})}`;
    
    // 檢查緩存
    if (config?.useCache !== false) {
      const cached = this.getFromCache<T>(cacheKey);
      if (cached) {
        return cached;
      }
    }
    
    // 檢查是否有相同的請求正在進行
    if (this.pendingRequests.has(cacheKey)) {
      return this.pendingRequests.get(cacheKey);
    }
    
    // 發起請求
    const requestPromise = this.axiosInstance.get<T>(url, config);
    this.pendingRequests.set(cacheKey, requestPromise);
    
    try {
      const response = await requestPromise;
      
      // 緩存GET請求結果
      if (config?.useCache !== false && response.status === 200) {
        this.setCache(cacheKey, response);
      }
      
      return response;
    } finally {
      this.pendingRequests.delete(cacheKey);
    }
  }

  /**
   * POST請求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.post(url, data, config);
  }

  /**
   * PUT請求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.put(url, data, config);
  }

  /**
   * DELETE請求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.delete(url, config);
  }

  /**
   * PATCH請求
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.patch(url, data, config);
  }

  /**
   * 處理請求隊列
   */
  private processRequestQueue(): void {
    this.requestQueue.forEach(request => {
      request().catch(error => {
        console.error('隊列請求執行失敗:', error);
      });
    });
    this.requestQueue = [];
  }

  /**
   * 處理認證失敗
   */
  private handleAuthFailure(): void {
    // 清空請求隊列
    this.requestQueue = [];
    
    // 發送認證失敗事件
    window.dispatchEvent(new CustomEvent('auth-error', {
      detail: { type: 'token-refresh-failed' }
    }));
  }

  /**
   * 創建統一的API錯誤對象
   */
  private createApiError(error: any, isAuthError = false): ApiError {
    const apiError = new Error(error.message || '請求失敗') as ApiError;
    
    apiError.status = error.response?.status;
    apiError.response = error.response?.data;
    apiError.isNetworkError = !error.response;
    apiError.isAuthError = isAuthError || error.response?.status === 401;
    
    return apiError;
  }

  /**
   * 設置請求超時
   */
  setTimeout(timeout: number): void {
    this.axiosInstance.defaults.timeout = timeout;
  }

  /**
   * 設置基礎URL
   */
  setBaseURL(baseURL: string): void {
    this.axiosInstance.defaults.baseURL = baseURL;
  }

  /**
   * 添加請求攔截器
   */
  addRequestInterceptor(
    onFulfilled?: (config: AxiosRequestConfig) => AxiosRequestConfig | Promise<AxiosRequestConfig>,
    onRejected?: (error: any) => any
  ): number {
    return this.axiosInstance.interceptors.request.use(onFulfilled, onRejected);
  }

  /**
   * 添加響應攔截器
   */
  addResponseInterceptor(
    onFulfilled?: (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>,
    onRejected?: (error: any) => any
  ): number {
    return this.axiosInstance.interceptors.response.use(onFulfilled, onRejected);
  }

  /**
   * 移除攔截器
   */
  removeInterceptor(type: 'request' | 'response', interceptorId: number): void {
    if (type === 'request') {
      this.axiosInstance.interceptors.request.eject(interceptorId);
    } else {
      this.axiosInstance.interceptors.response.eject(interceptorId);
    }
  }

  /**
   * 批量請求處理
   */
  async batchRequests<T = any>(requests: Array<{
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    url: string;
    data?: any;
    config?: AxiosRequestConfig;
  }>): Promise<AxiosResponse<T>[]> {
    // 使用token管理器的批量操作
    return this.tokenManager.batchTokenOperations(
      requests.map(req => () => {
        switch (req.method) {
          case 'GET':
            return this.axiosInstance.get(req.url, req.config);
          case 'POST':
            return this.axiosInstance.post(req.url, req.data, req.config);
          case 'PUT':
            return this.axiosInstance.put(req.url, req.data, req.config);
          case 'DELETE':
            return this.axiosInstance.delete(req.url, req.config);
          case 'PATCH':
            return this.axiosInstance.patch(req.url, req.data, req.config);
          default:
            throw new Error(`不支持的請求方法: ${req.method}`);
        }
      })
    );
  }

  /**
   * 從緩存獲取數據
   */
  private getFromCache<T>(key: string): AxiosResponse<T> | null {
    const cached = this.requestCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data;
    }
    
    // 清除過期緩存
    if (cached) {
      this.requestCache.delete(key);
    }
    
    return null;
  }

  /**
   * 設置緩存
   */
  private setCache<T>(key: string, data: AxiosResponse<T>): void {
    this.requestCache.set(key, {
      data,
      timestamp: Date.now()
    });
    
    // 限制緩存大小
    if (this.requestCache.size > 100) {
      const oldestKey = this.requestCache.keys().next().value;
      this.requestCache.delete(oldestKey);
    }
  }

  /**
   * 清除緩存
   */
  clearCache(pattern?: string): void {
    if (pattern) {
      for (const key of this.requestCache.keys()) {
        if (key.includes(pattern)) {
          this.requestCache.delete(key);
        }
      }
    } else {
      this.requestCache.clear();
    }
  }

  /**
   * 獲取API客戶端統計信息
   */
  getStats(): {
    cacheSize: number;
    pendingRequests: number;
    queueSize: number;
    isRefreshingToken: boolean;
  } {
    return {
      cacheSize: this.requestCache.size,
      pendingRequests: this.pendingRequests.size,
      queueSize: this.requestQueue.length,
      isRefreshingToken: this.isRefreshingToken
    };
  }

  /**
   * 預加載常用數據
   */
  async preloadData(urls: string[]): Promise<void> {
    const requests = urls.map(url => ({
      method: 'GET' as const,
      url,
      config: { useCache: true }
    }));
    
    try {
      await this.batchRequests(requests);
    } catch (error) {
      console.warn('數據預加載失敗:', error);
    }
  }

  /**
   * 清理資源
   */
  cleanup(): void {
    this.requestCache.clear();
    this.pendingRequests.clear();
    this.requestQueue = [];
    this.tokenManager.cleanup();
  }
}

// 創建全局API客戶端實例
export const apiClient = new ApiClient();