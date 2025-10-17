/**
 * 管理後台 API 服務 - 修復版
 * 為舊組件提供基本的 API 服務存根
 */

import { ApiResponse, PaginationParams } from '../types/AdminTypes';

export class AdminApiService {
  private static instance: AdminApiService;
  // Base URL for API calls (currently using mock responses)
  // private _baseUrl = process.env.NODE_ENV === 'production' 
  //   ? 'https://twshocks-app-79rsx.ondigitalocean.app/api/v1'
  //   : 'http://localhost:8000/api/v1';

  public static getInstance(): AdminApiService {
    if (!AdminApiService.instance) {
      AdminApiService.instance = new AdminApiService();
    }
    return AdminApiService.instance;
  }

  // 基本 HTTP 方法
  async get<T>(_endpoint: string, _params?: any): Promise<ApiResponse<T>> {
    // TODO: 實現實際的 API 調用
    return {
      data: {} as T,
      status: 200,
      success: true,
      message: 'Mock response from AdminApiService_Fixed'
    };
  }

  async post<T>(_endpoint: string, _data?: any): Promise<ApiResponse<T>> {
    // TODO: 實現實際的 API 調用
    return {
      data: {} as T,
      status: 200,
      success: true,
      message: 'Mock response from AdminApiService_Fixed'
    };
  }

  async put<T>(_endpoint: string, _data?: any): Promise<ApiResponse<T>> {
    // TODO: 實現實際的 API 調用
    return {
      data: {} as T,
      status: 200,
      success: true,
      message: 'Mock response from AdminApiService_Fixed'
    };
  }

  async delete<T>(_endpoint: string): Promise<ApiResponse<T>> {
    // TODO: 實現實際的 API 調用
    return {
      data: {} as T,
      status: 200,
      success: true,
      message: 'Mock response from AdminApiService_Fixed'
    };
  }

  async patch<T>(_endpoint: string, _data?: any): Promise<ApiResponse<T>> {
    // TODO: 實現實際的 API 調用
    return {
      data: {} as T,
      status: 200,
      success: true,
      message: 'Mock response from AdminApiService_Fixed'
    };
  }

  // 認證相關
  setAuthToken(_token: string): void {
    // TODO: 實現實際的 token 設置
    // 通常會設置到 axios headers 或其他 HTTP 客戶端
  }

  // 分頁查詢
  async getPaginated<T>(_endpoint: string, params: PaginationParams): Promise<ApiResponse<{
    items: T[];
    total: number;
    page: number;
    limit: number;
  }>> {
    return {
      data: {
        items: [],
        total: 0,
        page: params.page,
        limit: params.limit
      },
      status: 200,
      success: true,
      message: 'Mock paginated response'
    };
  }

  // 用戶管理相關
  async getUsers(params?: PaginationParams) {
    return this.getPaginated('/admin/users', params || { page: 1, limit: 10 });
  }

  async exportUsers() {
    return this.get('/admin/users/export');
  }

  async getSystemStats() {
    return this.get('/admin/stats');
  }

  async getDashboardData() {
    return this.get('/admin/dashboard');
  }

  async getAnalytics(params?: any) {
    return this.get('/admin/analytics', params);
  }

  // 權限管理
  async getPermissions() {
    return this.get('/admin/permissions');
  }

  async updatePermissions(userId: string, permissions: any) {
    return this.put(`/admin/users/${userId}/permissions`, permissions);
  }

  // 財務管理
  async getFinancialData(params?: any) {
    return this.get('/admin/financial', params);
  }

  // 訂閱管理
  async getSubscriptions(params?: PaginationParams) {
    return this.getPaginated('/admin/subscriptions', params || { page: 1, limit: 10 });
  }

  // 內容管理
  async getContent(params?: PaginationParams) {
    return this.getPaginated('/admin/content', params || { page: 1, limit: 10 });
  }

  // 系統監控
  async getSystemHealth() {
    return this.get('/admin/health');
  }

  async getSystemLogs(params?: any) {
    return this.get('/admin/logs', params);
  }
}

// 導出默認實例
const adminApiService = AdminApiService.getInstance();
export default adminApiService;

// 導出命名實例 (為了向後兼容)
export { adminApiService };

// 導出類型
export * from '../types/AdminTypes';