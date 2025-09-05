// Token管理器 - 處理token的存儲、刷新和生命週期管理
// 提供安全的token存儲和自動刷新機制

import { SecureStorage } from '../utils/SecureStorage';
import type { AuthTokens } from './AuthService';

export class TokenManager {
  private static readonly TOKEN_KEY = 'admin_auth_tokens';
  private static readonly REFRESH_THRESHOLD = 5 * 60 * 1000; // 5分鐘
  private static readonly PROACTIVE_REFRESH_THRESHOLD = 10 * 60 * 1000; // 10分鐘
  
  private refreshListeners: Set<(success: boolean) => void> = new Set();
  private isRefreshing = false;
  private refreshPromise: Promise<boolean> | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;
  private tokenCache: { token: string; expiresAt: number } | null = null;

  /**
   * 設置tokens
   */
  async setTokens(tokens: AuthTokens): Promise<void> {
    const tokenData = {
      ...tokens,
      expires_at: tokens.expires_at || (Date.now() + (tokens.expires_in * 1000))
    };

    try {
      await SecureStorage.setItem(TokenManager.TOKEN_KEY, tokenData);
      
      // 更新內存緩存
      this.tokenCache = {
        token: tokenData.access_token,
        expiresAt: tokenData.expires_at
      };
      
      // 設置主動刷新定時器
      this.scheduleProactiveRefresh(tokenData.expires_at);
    } catch (error) {
      console.error('Token存儲失敗:', error);
      throw new Error('Token存儲失敗');
    }
  }

  /**
   * 獲取有效的token，如果需要會自動刷新
   */
  async getValidToken(): Promise<string | null> {
    // 優先使用內存緩存
    if (this.tokenCache && this.tokenCache.expiresAt > Date.now() + TokenManager.REFRESH_THRESHOLD) {
      return this.tokenCache.token;
    }

    const tokens = await this.getTokens();
    if (!tokens) return null;

    // 檢查是否需要刷新
    if (this.shouldRefreshToken(tokens)) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        const newTokens = await this.getTokens();
        return newTokens?.access_token || null;
      } else {
        return null;
      }
    }

    // 更新內存緩存
    this.tokenCache = {
      token: tokens.access_token,
      expiresAt: tokens.expires_at
    };

    return tokens.access_token;
  }

  /**
   * 刷新token
   */
  async refreshToken(): Promise<boolean> {
    // 如果正在刷新，返回現有的Promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * 執行token刷新
   */
  private async performTokenRefresh(): Promise<boolean> {
    const tokens = await this.getTokens();
    if (!tokens?.refresh_token) {
      this.notifyRefreshListeners(false);
      return false;
    }

    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: tokens.refresh_token
        })
      });

      if (response.ok) {
        const newTokens = await response.json();
        const tokenData: AuthTokens = {
          ...newTokens,
          expires_at: Date.now() + (newTokens.expires_in * 1000)
        };
        
        await this.setTokens(tokenData);
        this.notifyRefreshListeners(true);
        return true;
      } else {
        console.warn('Token刷新失敗:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Token刷新請求失敗:', error);
    }

    // 刷新失敗，清除token
    await this.clearTokens();
    this.notifyRefreshListeners(false);
    return false;
  }

  /**
   * 清除所有tokens
   */
  async clearTokens(): Promise<void> {
    try {
      await SecureStorage.removeItem(TokenManager.TOKEN_KEY);
      
      // 清除內存緩存
      this.tokenCache = null;
      
      // 清除定時器
      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
        this.refreshTimer = null;
      }
    } catch (error) {
      console.error('清除Token失敗:', error);
    }
  }

  /**
   * 檢查是否有有效token（同步方法，用於快速檢查）
   */
  hasValidToken(): boolean {
    try {
      const tokens = SecureStorage.getItemSync<AuthTokens>(TokenManager.TOKEN_KEY);
      return tokens && tokens.expires_at > Date.now();
    } catch (error) {
      return false;
    }
  }

  /**
   * 添加token刷新監聽器
   */
  onTokenRefresh(listener: (success: boolean) => void): () => void {
    this.refreshListeners.add(listener);
    
    return () => {
      this.refreshListeners.delete(listener);
    };
  }

  /**
   * 獲取存儲的tokens
   */
  private async getTokens(): Promise<AuthTokens | null> {
    try {
      return await SecureStorage.getItem<AuthTokens>(TokenManager.TOKEN_KEY);
    } catch (error) {
      console.error('讀取Token失敗:', error);
      return null;
    }
  }

  /**
   * 檢查是否需要刷新token
   */
  private shouldRefreshToken(tokens: AuthTokens): boolean {
    const timeUntilExpiry = tokens.expires_at - Date.now();
    return timeUntilExpiry < TokenManager.REFRESH_THRESHOLD;
  }

  /**
   * 通知刷新監聽器
   */
  private notifyRefreshListeners(success: boolean): void {
    this.refreshListeners.forEach(listener => {
      try {
        listener(success);
      } catch (error) {
        console.error('Token刷新監聽器執行失敗:', error);
      }
    });
  }

  /**
   * 獲取token剩餘時間（毫秒）
   */
  async getTokenTimeRemaining(): Promise<number> {
    const tokens = await this.getTokens();
    if (!tokens) return 0;
    
    return Math.max(0, tokens.expires_at - Date.now());
  }

  /**
   * 檢查token是否即將過期
   */
  async isTokenExpiringSoon(): Promise<boolean> {
    const timeRemaining = await this.getTokenTimeRemaining();
    return timeRemaining < TokenManager.REFRESH_THRESHOLD;
  }

  /**
   * 設置主動刷新定時器
   */
  private scheduleProactiveRefresh(expiresAt: number): void {
    // 清除現有定時器
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    // 計算刷新時間點（過期前10分鐘）
    const refreshTime = expiresAt - TokenManager.PROACTIVE_REFRESH_THRESHOLD;
    const delay = Math.max(0, refreshTime - Date.now());

    // 設置定時器
    this.refreshTimer = setTimeout(async () => {
      try {
        await this.refreshToken();
      } catch (error) {
        console.error('主動刷新token失敗:', error);
      }
    }, delay);
  }

  /**
   * 批量處理token操作（性能優化）
   */
  async batchTokenOperations<T>(operations: Array<() => Promise<T>>): Promise<T[]> {
    // 確保token有效
    const token = await this.getValidToken();
    if (!token) {
      throw new Error('無有效token');
    }

    // 並行執行操作
    return Promise.all(operations.map(op => op()));
  }

  /**
   * 預熱token緩存
   */
  async warmupCache(): Promise<void> {
    try {
      const tokens = await this.getTokens();
      if (tokens && tokens.expires_at > Date.now()) {
        this.tokenCache = {
          token: tokens.access_token,
          expiresAt: tokens.expires_at
        };
        this.scheduleProactiveRefresh(tokens.expires_at);
      }
    } catch (error) {
      console.error('Token緩存預熱失敗:', error);
    }
  }

  /**
   * 獲取token統計信息（用於性能監控）
   */
  getTokenStats(): {
    hasCache: boolean;
    cacheExpiresIn: number;
    isRefreshing: boolean;
    refreshListenerCount: number;
  } {
    return {
      hasCache: !!this.tokenCache,
      cacheExpiresIn: this.tokenCache ? Math.max(0, this.tokenCache.expiresAt - Date.now()) : 0,
      isRefreshing: this.isRefreshing,
      refreshListenerCount: this.refreshListeners.size
    };
  }

  /**
   * 清理資源（組件卸載時調用）
   */
  cleanup(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    this.refreshListeners.clear();
    this.tokenCache = null;
  }
}