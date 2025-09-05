/**
 * 管理後台API客戶端
 * 專門用於管理後台API調用的認證客戶端
 */

import { TokenManager } from './TokenManager';

export interface AdminApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
}

export interface AdminApiError extends Error {
  status?: number;
  response?: any;
  isNetworkError?: boolean;
  isAuthError?: boolean;
}

export class AdminApiClient {
  private tokenManager: TokenManager;
  private baseURL: string;

  constructor(baseURL: string = '/admin') {
    this.tokenManager = new TokenManager();
    this.baseURL = baseURL;
  }

  /**
   * 執行認證的HTTP請求
   */
  private async makeAuthenticatedRequest<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<AdminApiResponse<T>> {
    const token = await this.tokenManager.getValidToken();
    
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // 添加認證header
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // 處理認證錯誤
      if (response.status === 401) {
        // 嘗試刷新token
        const refreshed = await this.tokenManager.refreshToken();
        if (refreshed) {
          // 重試請求
          const newToken = await this.tokenManager.getValidToken();
          if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`;
            const retryResponse = await fetch(url, {
              ...options,
              headers,
            });
            
            if (retryResponse.ok) {
              const data = await retryResponse.json();
              return {
                data,
                status: retryResponse.status,
                statusText: retryResponse.statusText,
              };
            }
          }
        }
        
        // 刷新失敗或重試失敗，拋出認證錯誤
        const error = new Error('Authentication failed') as AdminApiError;
        error.status = 401;
        error.isAuthError = true;
        throw error;
      }

      // 處理其他HTTP錯誤
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.detail || `HTTP ${response.status}`) as AdminApiError;
        error.status = response.status;
        error.response = errorData;
        throw error;
      }

      // 解析響應數據
      const data = await response.json();
      return {
        data,
        status: response.status,
        statusText: response.statusText,
      };

    } catch (error) {
      if (error instanceof Error && !error.hasOwnProperty('status')) {
        // 網絡錯誤
        const networkError = error as AdminApiError;
        networkError.isNetworkError = true;
      }
      throw error;
    }
  }

  /**
   * GET請求
   */
  async get<T = any>(endpoint: string): Promise<AdminApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>(endpoint, {
      method: 'GET',
    });
  }

  /**
   * POST請求
   */
  async post<T = any>(endpoint: string, data?: any): Promise<AdminApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT請求
   */
  async put<T = any>(endpoint: string, data?: any): Promise<AdminApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE請求
   */
  async delete<T = any>(endpoint: string): Promise<AdminApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>(endpoint, {
      method: 'DELETE',
    });
  }

  /**
   * PATCH請求
   */
  async patch<T = any>(endpoint: string, data?: any): Promise<AdminApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * 獲取系統健康狀態
   */
  async getSystemHealth() {
    return this.get('/system/health');
  }

  /**
   * 獲取用戶列表
   */
  async getUsers(params?: { page?: number; limit?: number; search?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    
    const query = queryParams.toString();
    return this.get(`/users${query ? `?${query}` : ''}`);
  }

  /**
   * 獲取用戶詳情
   */
  async getUser(userId: string) {
    return this.get(`/users/${userId}`);
  }

  /**
   * 更新用戶
   */
  async updateUser(userId: string, userData: any) {
    return this.put(`/users/${userId}`, userData);
  }

  /**
   * 刪除用戶
   */
  async deleteUser(userId: string) {
    return this.delete(`/users/${userId}`);
  }

  /**
   * 獲取系統配置
   */
  async getSystemConfig() {
    return this.get('/config');
  }

  /**
   * 更新系統配置
   */
  async updateSystemConfig(config: any) {
    return this.put('/config', config);
  }

  /**
   * 獲取系統統計
   */
  async getSystemStats() {
    return this.get('/stats');
  }

  /**
   * 獲取系統日誌
   */
  async getSystemLogs(params?: { level?: string; limit?: number; offset?: number }) {
    const queryParams = new URLSearchParams();
    if (params?.level) queryParams.append('level', params.level);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const query = queryParams.toString();
    return this.get(`/logs${query ? `?${query}` : ''}`);
  }

  /**
   * 執行系統操作
   */
  async executeSystemAction(action: string, params?: any) {
    return this.post(`/actions/${action}`, params);
  }

  /**
   * 設置請求超時
   */
  setTimeout(timeout: number): void {
    // 在實際實現中，可以設置fetch的AbortController超時
    console.log(`設置請求超時: ${timeout}ms`);
  }

  /**
   * 設置基礎URL
   */
  setBaseURL(baseURL: string): void {
    this.baseURL = baseURL;
  }

  /**
   * 檢查認證狀態
   */
  async checkAuthStatus(): Promise<boolean> {
    try {
      const token = await this.tokenManager.getValidToken();
      return !!token;
    } catch (error) {
      return false;
    }
  }

  /**
   * 手動刷新token
   */
  async refreshToken(): Promise<boolean> {
    return this.tokenManager.refreshToken();
  }
}

// 創建全局管理後台API客戶端實例
export const adminApiClient = new AdminApiClient();

// 導出類型
export type { AdminApiResponse, AdminApiError };