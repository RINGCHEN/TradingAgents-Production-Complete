// AuthService - 認證服務
export type MemberTier = 'free' | 'gold' | 'diamond';

// 為了兼容性，也導出為枚舉
export const MemberTier = {
  FREE: 'free' as const,
  GOLD: 'gold' as const,
  DIAMOND: 'diamond' as const
} as const;

export interface AuthError {
  message: string;
  code?: string;
}

export interface MembershipStatus {
  tier: MemberTier;
  analysisCount: number;
  analysisLimit: number;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  tier: MemberTier;
  membershipStatus?: MembershipStatus;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthUser> => {
    // 模擬登錄
    return {
      id: '1',
      name: '測試用戶',
      email: credentials.email,
      tier: 'free'
    };
  },
  
  logout: async (): Promise<void> => {
    // 登出邏輯
  },
  
  getCurrentUser: async (): Promise<AuthUser | null> => {
    // 獲取當前用戶
    return null;
  }
};