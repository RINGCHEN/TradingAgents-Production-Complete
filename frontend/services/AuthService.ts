// 認證服務 - 統一管理所有認證相關操作
// 基於現有的AdminLogin和AdminDashboard組件進行整合

import { TokenManager } from './TokenManager';
import { ApiClient } from './ApiClient';

export interface LoginCredentials {
  email: string;
  password: string;
}

// 會員等級枚舉
export enum MemberTier {
  FREE = 'FREE',
  GOLD = 'GOLD',
  DIAMOND = 'DIAMOND'
}

// 會員權益配置
export interface MemberBenefits {
  dailyAnalysisLimit: number;
  advancedAnalysis: boolean;
  realtimeData: boolean;
  portfolioTracking: boolean;
  aiRecommendations: boolean;
  prioritySupport: boolean;
  customAlerts: boolean;
  exportData: boolean;
}

// 會員狀態
export interface MembershipStatus {
  tier: MemberTier;
  benefits: MemberBenefits;
  subscriptionStartDate?: Date;
  subscriptionEndDate?: Date;
  isActive: boolean;
  paymentStatus: 'active' | 'pending' | 'failed' | 'cancelled';
  usageStats: {
    dailyAnalysisUsed: number;
    monthlyAnalysisUsed: number;
    lastAnalysisDate?: Date;
  };
}

// 用戶接口 - 增強版本
export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  is_admin: boolean;
  is_active: boolean;
  // 新增會員相關字段
  membershipStatus: MembershipStatus;
  profile: {
    displayName?: string;
    avatar?: string;
    phone?: string;
    preferences: {
      language: string;
      timezone: string;
      notifications: {
        email: boolean;
        sms: boolean;
        push: boolean;
      };
    };
  };
  // 安全設置
  security: {
    twoFactorEnabled: boolean;
    lastLoginDate?: Date;
    lastLoginIP?: string;
    passwordChangedDate?: Date;
  };
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  expires_at: number;
}

export class AuthError extends Error {
  constructor(message: string, public originalError?: any) {
    super(message);
    this.name = 'AuthError';
  }

  /**
   * 獲取用戶友好的錯誤信息
   */
  getUserMessage(): string {
    return this.message;
  }

  /**
   * 獲取錯誤建議
   */
  getSuggestions(): string[] {
    if (this.message.includes('用戶名或密碼錯誤')) {
      return [
        '檢查用戶名和密碼是否正確',
        '確認大小寫是否正確',
        '如果忘記密碼，請聯繫管理員重置'
      ];
    } else if (this.message.includes('網絡')) {
      return [
        '檢查網絡連接',
        '嘗試刷新頁面',
        '檢查防火牆設置'
      ];
    } else if (this.message.includes('服務器')) {
      return [
        '稍後重試',
        '如果問題持續，請聯繫技術支援'
      ];
    }
    
    return [
      '刷新頁面重試',
      '如果問題持續，請聯繫技術支援'
    ];
  }

  /**
   * 判斷是否可以重試
   */
  isRetryable(): boolean {
    return this.message.includes('網絡') || this.message.includes('服務器');
  }
}

export class AuthService {
  private tokenManager: TokenManager;
  private apiClient: ApiClient;
  private authStateListeners: Set<(user: AuthUser | null) => void> = new Set();
  private membershipListeners: Set<(membership: MembershipStatus) => void> = new Set();

  constructor() {
    this.tokenManager = new TokenManager();
    this.apiClient = new ApiClient();
    
    // 監聽token刷新事件
    this.tokenManager.onTokenRefresh((success) => {
      if (!success) {
        this.notifyAuthStateChange(null);
      }
    });
  }

  /**
   * 用戶登錄
   */
  async login(credentials: LoginCredentials): Promise<AuthUser> {
    try {
      // 調用登錄API - 使用完整路徑因為auth端點不在/api下
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.access_token) {
        throw new AuthError('登錄響應格式錯誤');
      }

      // 計算token過期時間
      const expiresAt = Date.now() + (data.expires_in * 1000);
      const tokens: AuthTokens = {
        ...data,
        expires_at: expiresAt
      };

      // 存儲token
      await this.tokenManager.setTokens(tokens);
      
      // 獲取用戶信息
      const userInfo = await this.getCurrentUser();
      if (!userInfo) {
        throw new AuthError('無法獲取用戶信息');
      }
      
      // 觸發認證狀態更新
      this.notifyAuthStateChange(userInfo);
      
      return userInfo;
    } catch (error) {
      console.error('登錄失敗:', error);
      if (error instanceof AuthError) {
        throw error;
      }
      
      // 處理HTTP錯誤
      if (error.message?.includes('401') || error.message?.includes('Unauthorized')) {
        throw new AuthError('用戶名或密碼錯誤');
      } else if (error.message?.includes('500') || error.message?.includes('502') || error.message?.includes('503')) {
        throw new AuthError('服務器錯誤，請稍後重試');
      } else if (!navigator.onLine) {
        throw new AuthError('網絡連接失敗，請檢查網絡設置');
      }
      
      throw new AuthError('登錄失敗，請稍後重試', error);
    }
  }

  /**
   * 用戶登出
   */
  async logout(): Promise<void> {
    try {
      // 嘗試調用登出API
      const token = await this.tokenManager.getValidToken();
      if (token) {
        await fetch('/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
    } catch (error) {
      // 即使API調用失敗也要清除本地狀態
      console.warn('登出API調用失敗，但將清除本地狀態', error);
    } finally {
      // 清除本地認證狀態
      await this.tokenManager.clearTokens();
      this.notifyAuthStateChange(null);
    }
  }

  /**
   * 獲取當前用戶信息
   */
  async getCurrentUser(): Promise<AuthUser | null> {
    const token = await this.tokenManager.getValidToken();
    if (!token) return null;

    try {
      const response = await fetch('/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token無效，清除認證狀態
          await this.logout();
        }
        return null;
      }

      const data = await response.json();
      return this.normalizeUserData(data);
    } catch (error) {
      console.error('獲取用戶信息失敗:', error);
      return null;
    }
  }

  /**
   * 獲取有效的token
   */
  async getValidToken(): Promise<string | null> {
    return await this.tokenManager.getValidToken();
  }

  /**
   * 刷新認證token
   */
  async refreshToken(): Promise<boolean> {
    return await this.tokenManager.refreshToken();
  }

  /**
   * 檢查是否已認證
   */
  isAuthenticated(): boolean {
    return this.tokenManager.hasValidToken();
  }

  /**
   * 添加認證狀態監聽器
   */
  onAuthStateChange(listener: (user: AuthUser | null) => void): () => void {
    this.authStateListeners.add(listener);
    
    // 返回取消監聽的函數
    return () => {
      this.authStateListeners.delete(listener);
    };
  }

  /**
   * 初始化認證狀態
   */
  async initializeAuth(): Promise<AuthUser | null> {
    try {
      if (this.isAuthenticated()) {
        const user = await this.getCurrentUser();
        if (user) {
          this.notifyAuthStateChange(user);
          return user;
        }
      }
    } catch (error) {
      console.error('認證初始化失敗:', error);
    }
    
    return null;
  }

  /**
   * 通知認證狀態變化
   */
  private notifyAuthStateChange(user: AuthUser | null): void {
    // 通知所有監聽器
    this.authStateListeners.forEach(listener => {
      try {
        listener(user);
      } catch (error) {
        console.error('認證狀態監聽器執行失敗:', error);
      }
    });

    // 發送全局事件（用於跨組件通信）
    window.dispatchEvent(new CustomEvent('auth-state-change', { 
      detail: { user } 
    }));
  }

  /**
   * 標準化用戶數據格式
   */
  private normalizeUserData(userData: any): AuthUser {
    // 獲取會員權益配置
    const memberBenefits = this.getMemberBenefits(userData.membershipStatus?.tier || MemberTier.FREE);
    
    return {
      id: userData.id,
      username: userData.username,
      email: userData.email || '',
      role: userData.role || 'user',
      permissions: userData.permissions || [],
      is_admin: userData.is_admin || false,
      is_active: userData.is_active !== false,
      
      // 會員狀態
      membershipStatus: {
        tier: userData.membershipStatus?.tier || MemberTier.FREE,
        benefits: memberBenefits,
        subscriptionStartDate: userData.membershipStatus?.subscriptionStartDate 
          ? new Date(userData.membershipStatus.subscriptionStartDate) 
          : undefined,
        subscriptionEndDate: userData.membershipStatus?.subscriptionEndDate 
          ? new Date(userData.membershipStatus.subscriptionEndDate) 
          : undefined,
        isActive: userData.membershipStatus?.isActive !== false,
        paymentStatus: userData.membershipStatus?.paymentStatus || 'active',
        usageStats: {
          dailyAnalysisUsed: userData.membershipStatus?.usageStats?.dailyAnalysisUsed || 0,
          monthlyAnalysisUsed: userData.membershipStatus?.usageStats?.monthlyAnalysisUsed || 0,
          lastAnalysisDate: userData.membershipStatus?.usageStats?.lastAnalysisDate 
            ? new Date(userData.membershipStatus.usageStats.lastAnalysisDate) 
            : undefined
        }
      },
      
      // 用戶資料
      profile: {
        displayName: userData.profile?.displayName || userData.username,
        avatar: userData.profile?.avatar,
        phone: userData.profile?.phone,
        preferences: {
          language: userData.profile?.preferences?.language || 'zh-TW',
          timezone: userData.profile?.preferences?.timezone || 'Asia/Taipei',
          notifications: {
            email: userData.profile?.preferences?.notifications?.email !== false,
            sms: userData.profile?.preferences?.notifications?.sms !== false,
            push: userData.profile?.preferences?.notifications?.push !== false
          }
        }
      },
      
      // 安全設置
      security: {
        twoFactorEnabled: userData.security?.twoFactorEnabled || false,
        lastLoginDate: userData.security?.lastLoginDate 
          ? new Date(userData.security.lastLoginDate) 
          : undefined,
        lastLoginIP: userData.security?.lastLoginIP,
        passwordChangedDate: userData.security?.passwordChangedDate 
          ? new Date(userData.security.passwordChangedDate) 
          : undefined
      }
    };
  }
  
  /**
   * 獲取會員權益配置
   */
  private getMemberBenefits(tier: MemberTier): MemberBenefits {
    switch (tier) {
      case MemberTier.FREE:
        return {
          dailyAnalysisLimit: 3,
          advancedAnalysis: false,
          realtimeData: false,
          portfolioTracking: false,
          aiRecommendations: false,
          prioritySupport: false,
          customAlerts: false,
          exportData: false
        };
        
      case MemberTier.GOLD:
        return {
          dailyAnalysisLimit: 20,
          advancedAnalysis: true,
          realtimeData: true,
          portfolioTracking: true,
          aiRecommendations: true,
          prioritySupport: false,
          customAlerts: true,
          exportData: true
        };
        
      case MemberTier.DIAMOND:
        return {
          dailyAnalysisLimit: -1, // 無限制
          advancedAnalysis: true,
          realtimeData: true,
          portfolioTracking: true,
          aiRecommendations: true,
          prioritySupport: true,
          customAlerts: true,
          exportData: true
        };
        
      default:
        return this.getMemberBenefits(MemberTier.FREE);
    }
  }
  
  /**
   * 檢查用戶是否有使用權限
   */
  checkFeatureAccess(user: AuthUser, feature: keyof MemberBenefits): boolean {
    return user.membershipStatus.benefits[feature] === true;
  }
  
  /**
   * 檢查用戶是否達到使用限制
   */
  checkUsageLimit(user: AuthUser, limitType: 'dailyAnalysis' | 'monthlyAnalysis'): boolean {
    const { benefits, usageStats } = user.membershipStatus;
    
    switch (limitType) {
      case 'dailyAnalysis':
        if (benefits.dailyAnalysisLimit === -1) return false; // 無限制
        return usageStats.dailyAnalysisUsed >= benefits.dailyAnalysisLimit;
        
      default:
        return false;
    }
  }
  
  /**
   * 更新用戶使用統計
   */
  async updateUsageStats(type: 'analysis'): Promise<void> {
    try {
      const token = await this.getValidToken();
      if (!token) return;
      
      await fetch('/api/members/usage/update', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type })
      });
    } catch (error) {
      console.error('更新使用統計失敗:', error);
    }
  }
  
  /**
   * 獲取會員升級建議
   */
  getMembershipUpgradeRecommendation(user: AuthUser): {
    shouldUpgrade: boolean;
    recommendedTier?: MemberTier;
    reason?: string;
  } {
    const { tier, usageStats } = user.membershipStatus;
    
    if (tier === MemberTier.FREE) {
      if (usageStats.dailyAnalysisUsed >= 3) {
        return {
          shouldUpgrade: true,
          recommendedTier: MemberTier.GOLD,
          reason: '您今日的分析次數已達上限，升級至Gold會員享有更多分析次數和進階功能！'
        };
      }
    }
    
    if (tier === MemberTier.GOLD) {
      if (usageStats.dailyAnalysisUsed >= 20) {
        return {
          shouldUpgrade: true,
          recommendedTier: MemberTier.DIAMOND,
          reason: '升級至Diamond會員享有無限分析次數和專屬客服支援！'
        };
      }
    }
    
    return { shouldUpgrade: false };
  }
}

// 創建全局認證服務實例
export const authService = new AuthService();