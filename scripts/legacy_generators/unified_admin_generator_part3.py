#!/usr/bin/env python3
"""
統一管理後台架構生成器 - 第三部分
服務層和API客戶端
"""

class ServicesGenerator:
    """服務層生成器"""
    
    def __init__(self, base_path: str):
        self.services_path = f"{base_path}/admin/services"
    
    def generate_admin_api_service(self) -> str:
        """生成管理後台API服務"""
        return '''/**
 * 管理後台統一API服務
 * 基於486個API端點分析結果
 */

import { ApiClient, ApiResponse } from '../../services/ApiClient';
import { 
  User, 
  SystemStatus, 
  PaginatedResponse, 
  PaginationParams 
} from '../types/AdminTypes';

export class AdminApiService extends ApiClient {
  constructor() {
    super('/api');
    this.setupAdminInterceptors();
  }

  private setupAdminInterceptors(): void {
    // 添加管理後台專用的請求攔截器
    this.addRequestInterceptor((config) => {
      // 添加管理後台認證頭
      const adminToken = localStorage.getItem('admin_token');
      if (adminToken) {
        config.headers = {
          ...config.headers,
          'X-Admin-Token': adminToken
        };
      }
      return config;
    });

    // 添加響應攔截器處理管理後台特定錯誤
    this.addResponseInterceptor((response) => {
      if (response.status === 403) {
        // 管理權限不足，跳轉到登入頁
        window.location.href = '/admin/login';
      }
      return response;
    });
  }

  // 系統管理API
  async getSystemStatus(): Promise<ApiResponse<SystemStatus>> {
    return this.get<SystemStatus>('/admin/system/status');
  }

  async getSystemHealth(): Promise<ApiResponse<any>> {
    return this.get('/health');
  }

  // 用戶管理API
  async getUsers(params?: PaginationParams): Promise<ApiResponse<PaginatedResponse<User>>> {
    return this.get<PaginatedResponse<User>>('/admin/users', params);
  }

  async createUser(userData: Partial<User>): Promise<ApiResponse<User>> {
    return this.post<User>('/users', userData);
  }

  async updateUser(userId: string, userData: Partial<User>): Promise<ApiResponse<User>> {
    return this.put<User>(`/users/${userId}`, userData);
  }

  async deleteUser(userId: string): Promise<ApiResponse<void>> {
    return this.delete(`/users/${userId}`);
  }

  // 數據分析API
  async getDashboardData(): Promise<ApiResponse<any>> {
    return this.get('/admin/analytics/dashboard');
  }

  async getReports(params?: any): Promise<ApiResponse<any>> {
    return this.get('/admin/reports', params);
  }

  async generateReport(reportConfig: any): Promise<ApiResponse<any>> {
    return this.post('/admin/reports/generate', reportConfig);
  }

  // 內容管理API
  async getContent(params?: any): Promise<ApiResponse<any>> {
    return this.get('/admin/content', params);
  }

  // 財務管理API
  async getFinancialMetrics(): Promise<ApiResponse<any>> {
    return this.get('/admin/financial/metrics');
  }
}

// 創建單例實例
export const adminApiService = new AdminApiService();'''
    
    def generate_notification_service(self) -> str:
        """生成通知服務"""
        return '''/**
 * 通知服務
 * 統一管理所有用戶通知
 */

export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
  timestamp: Date;
}

class NotificationService {
  private notifications: Notification[] = [];
  private listeners: ((notifications: Notification[]) => void)[] = [];

  show(notification: Omit<Notification, 'id' | 'timestamp'>): string {
    const id = Date.now().toString();
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      duration: notification.duration || 5000
    };

    this.notifications.push(newNotification);
    this.notifyListeners();

    // 自動移除通知
    if (newNotification.duration > 0) {
      setTimeout(() => {
        this.remove(id);
      }, newNotification.duration);
    }

    return id;
  }

  remove(id: string): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notifyListeners();
  }

  clear(): void {
    this.notifications = [];
    this.notifyListeners();
  }

  subscribe(listener: (notifications: Notification[]) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener([...this.notifications]));
  }

  // 便捷方法
  success(title: string, message: string): string {
    return this.show({ type: NotificationType.SUCCESS, title, message });
  }

  error(title: string, message: string): string {
    return this.show({ type: NotificationType.ERROR, title, message, duration: 0 });
  }

  warning(title: string, message: string): string {
    return this.show({ type: NotificationType.WARNING, title, message });
  }

  info(title: string, message: string): string {
    return this.show({ type: NotificationType.INFO, title, message });
  }
}

export const notificationService = new NotificationService();'''