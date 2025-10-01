/**
 * 管理員認證管理器
 * Phase 1 Day 2新增 - 處理Token刷新和認證狀態
 *
 * 核心功能：
 * 1. 自動處理401錯誤（Token過期）
 * 2. 防止併發刷新請求
 * 3. 刷新失敗自動導向登入
 * 4. 友好的403權限錯誤提示
 */

import { RealAdminApiService } from './RealAdminApiService';
import { ApiError } from '../../services/ApiClient';

export class AdminAuthManager {
  private refreshPromise: Promise<boolean> | null = null;
  private apiService: RealAdminApiService;

  constructor(apiService: RealAdminApiService) {
    this.apiService = apiService;
    console.log('✅ AdminAuthManager 初始化完成');
  }

  /**
   * 處理API錯誤，自動刷新401錯誤
   * @param error API錯誤對象
   * @returns true表示錯誤已處理且token已刷新，false表示無法處理
   */
  async handleApiError(error: ApiError): Promise<boolean> {
    console.log(`🔍 AdminAuthManager處理錯誤: ${error.status} - ${error.message}`);

    // 如果是401錯誤，嘗試刷新token
    if (error.status === 401) {
      console.log('🔄 檢測到401錯誤，嘗試刷新token...');
      const refreshed = await this.refreshTokenIfNeeded();

      if (refreshed) {
        console.log('✅ Token刷新成功，可以重試請求');
      } else {
        console.log('❌ Token刷新失敗，將導向登入頁面');
      }

      return refreshed;
    }

    // 如果是403錯誤，顯示權限不足訊息
    if (error.status === 403) {
      console.log('⚠️ 檢測到403錯誤，顯示權限不足訊息');
      this.showPermissionDeniedMessage(error);
      return false;
    }

    // 其他錯誤不處理
    return false;
  }

  /**
   * 刷新Token（防止併發）
   * 如果已經有刷新請求在進行中，等待它完成而不是發起新請求
   * @private
   */
  private async refreshTokenIfNeeded(): Promise<boolean> {
    // 如果已經有刷新請求在進行中，等待它完成
    if (this.refreshPromise) {
      console.log('⏳ 已有刷新請求進行中，等待完成...');
      return await this.refreshPromise;
    }

    console.log('🚀 發起新的token刷新請求');

    // 創建新的刷新請求
    this.refreshPromise = this.apiService.refreshAccessToken()
      .finally(() => {
        console.log('🏁 Token刷新請求完成，清除刷新狀態');
        this.refreshPromise = null;
      });

    const success = await this.refreshPromise;

    if (!success) {
      // 刷新失敗，導向登入頁面
      console.log('💥 Token刷新失敗，清除認證並導向登入');
      this.redirectToLogin();
    }

    return success;
  }

  /**
   * 導向登入頁面
   * 清除所有認證信息並重新載入頁面
   * @private
   */
  private redirectToLogin() {
    console.log('🚪 清除認證信息並重新載入頁面');

    // 清除所有認證相關的localStorage
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    localStorage.removeItem('refresh_token');

    // 重新載入頁面，AdminApp會檢測無token並顯示登入頁面
    window.location.reload();
  }

  /**
   * 顯示權限不足訊息
   * @param error API錯誤對象
   * @private
   */
  private showPermissionDeniedMessage(error: ApiError) {
    const message = `權限不足：您沒有權限執行此操作 (${error.endpoint})`;

    console.warn('⚠️', message);

    // TODO: 整合到AdminApp的Toast系統
    // 臨時使用alert（生產環境應替換為專業的Toast組件）
    if (typeof window !== 'undefined') {
      // 使用setTimeout避免阻塞
      setTimeout(() => {
        alert(`⚠️ ${message}`);
      }, 100);
    }
  }

  /**
   * 手動觸發token刷新
   * 可供外部組件主動呼叫（例如定時刷新）
   */
  async manualRefresh(): Promise<boolean> {
    console.log('🔧 手動觸發token刷新');
    return await this.refreshTokenIfNeeded();
  }

  /**
   * 檢查當前是否有刷新請求進行中
   */
  isRefreshing(): boolean {
    return this.refreshPromise !== null;
  }

  /**
   * 檢查是否已登入（有token）
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('admin_token');
    const hasToken = !!token;
    console.log(`🔐 認證檢查: ${hasToken ? '已登入' : '未登入'}`);
    return hasToken;
  }

  /**
   * 取得當前用戶角色
   * 用於前端UI權限控制
   */
  getUserRole(): 'admin' | 'readonly' | 'finance' | null {
    const roleStr = localStorage.getItem('admin_user_role');

    if (roleStr === 'admin' || roleStr === 'readonly' || roleStr === 'finance') {
      return roleStr;
    }

    // 如果沒有角色信息但有token，默認為readonly（最安全）
    if (this.isAuthenticated()) {
      console.warn('⚠️ 未找到角色信息，默認為readonly');
      return 'readonly';
    }

    return null;
  }

  /**
   * 設置用戶角色
   * 登入成功後應該調用此方法設置角色
   */
  setUserRole(role: 'admin' | 'readonly' | 'finance') {
    localStorage.setItem('admin_user_role', role);
    console.log(`✅ 用戶角色已設置: ${role}`);
  }
}