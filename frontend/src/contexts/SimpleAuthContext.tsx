/**
 * SimpleAuthContext - 簡化的認證上下文
 * 緊急修復版本，用於解決 Authentication context not found 錯誤
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface SimpleAuthUser {
  id: string;
  name: string;
  email: string;
  tier: 'free' | 'gold' | 'diamond';
  analysisCount?: number;
  analysisLimit?: number;
}

interface SimpleAuthContextType {
  // 基本狀態
  user: SimpleAuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;

  // 操作方法
  login: (credentials: any) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  clearError: () => void;

  // 功能檢查
  checkFeatureAccess: (feature: string) => boolean;
  checkUsageLimit: (limitType: string) => boolean;

  // 會員狀態
  membershipStatus: {
    tier: 'free' | 'gold' | 'diamond';
    analysisCount: number;
    analysisLimit: number;
    isActive: boolean;
  };

  // 訪客模式
  isGuestMode: boolean;
  switchToGuest: () => void;
}

const SimpleAuthContext = createContext<SimpleAuthContextType | undefined>(undefined);

interface SimpleAuthProviderProps {
  children: ReactNode;
}

export const SimpleAuthProvider: React.FC<SimpleAuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<SimpleAuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGuestMode, setIsGuestMode] = useState(true);

  // 初始化認證狀態
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        
        // 檢查 localStorage 中的用戶資料
        const storedUser = localStorage.getItem('user_info');
        const authToken = localStorage.getItem('auth_token');
        
        if (storedUser && authToken) {
          try {
            const parsedUser = JSON.parse(storedUser);
            setUser(parsedUser);
            setIsGuestMode(false);
            console.log('Auto-login successful:', parsedUser.name);
          } catch (parseError) {
            console.error('Failed to parse stored user data:', parseError);
            localStorage.removeItem('user_info');
            localStorage.removeItem('auth_token');
          }
        }
        
        setIsInitialized(true);
        setIsLoading(false);
        console.log('SimpleAuth initialized successfully');
      } catch (error) {
        console.error('Auth initialization error:', error);
        setError('認證系統初始化失敗');
        setIsInitialized(true);
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  // 登入
  const login = async (credentials: any): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      setError(null);

      // 模擬登入延遲
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockUser: SimpleAuthUser = {
        id: Date.now().toString(),
        name: credentials.name || '測試用戶',
        email: credentials.email || 'test@example.com',
        tier: 'free',
        analysisCount: 0,
        analysisLimit: 5
      };

      // 儲存用戶資料
      localStorage.setItem('user_info', JSON.stringify(mockUser));
      localStorage.setItem('auth_token', `simple_token_${Date.now()}`);
      localStorage.setItem('auth_method', 'email');

      setUser(mockUser);
      setIsGuestMode(false);
      setIsLoading(false);

      console.log('Login successful:', mockUser.name);
      return { success: true };

    } catch (error) {
      setIsLoading(false);
      const errorMessage = error instanceof Error ? error.message : '登入失敗';
      setError(errorMessage);
      
      return { success: false, error: errorMessage };
    }
  };

  // 登出
  const logout = async (): Promise<void> => {
    try {
      // 清除儲存的資料
      localStorage.removeItem('user_info');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_method');
      localStorage.removeItem('user_email');

      setUser(null);
      setIsGuestMode(true);
      setError(null);

      console.log('Logout successful');
    } catch (error) {
      console.error('Logout error:', error);
      setError('登出失敗');
    }
  };

  // 清除錯誤
  const clearError = () => {
    setError(null);
  };

  // 檢查功能存取權限
  const checkFeatureAccess = (feature: string): boolean => {
    if (!user) {
      // 訪客模式下的功能限制
      const guestAllowedFeatures = ['view-basic-info', 'personality-test', 'help'];
      return guestAllowedFeatures.includes(feature);
    }

    // 根據會員等級檢查功能權限
    switch (feature) {
      case 'stock-analysis':
        return true; // 所有會員都可以使用
      case 'advanced-analysis':
        return user.tier === 'gold' || user.tier === 'diamond';
      case 'portfolio-management':
        return user.tier === 'gold' || user.tier === 'diamond';
      case 'real-time-alerts':
        return user.tier === 'diamond';
      case 'api-access':
        return user.tier === 'diamond';
      default:
        return true;
    }
  };

  // 檢查使用限制
  const checkUsageLimit = (limitType: string): boolean => {
    if (!user) return false;

    switch (limitType) {
      case 'analysis':
        return (user.analysisCount || 0) < (user.analysisLimit || 0);
      default:
        return true;
    }
  };

  // 切換到訪客模式
  const switchToGuest = () => {
    logout();
  };

  // 計算會員狀態
  const membershipStatus = {
    tier: user?.tier || 'free',
    analysisCount: user?.analysisCount || 0,
    analysisLimit: user?.analysisLimit || 5,
    isActive: !!user
  };

  const contextValue: SimpleAuthContextType = {
    // 基本狀態
    user,
    isAuthenticated: !!user,
    isLoading,
    isInitialized,
    error,

    // 操作方法
    login,
    logout,
    clearError,

    // 功能檢查
    checkFeatureAccess,
    checkUsageLimit,

    // 會員狀態
    membershipStatus,

    // 訪客模式
    isGuestMode,
    switchToGuest
  };

  return (
    <SimpleAuthContext.Provider value={contextValue}>
      <div data-auth-context="simple-auth">
        {children}
      </div>
    </SimpleAuthContext.Provider>
  );
};

// Hook for using simple auth context
export const useSimpleAuth = (): SimpleAuthContextType => {
  const context = useContext(SimpleAuthContext);
  if (context === undefined) {
    throw new Error('useSimpleAuth must be used within a SimpleAuthProvider');
  }
  return context;
};

// 兼容性 Hook - 與 EnhancedAuthContext 保持一致的介面
export const useAuth = () => {
  const simpleAuth = useSimpleAuth();
  
  return {
    user: simpleAuth.user,
    isAuthenticated: simpleAuth.isAuthenticated,
    isLoading: simpleAuth.isLoading,
    login: simpleAuth.login,
    logout: simpleAuth.logout,
    checkFeatureAccess: simpleAuth.checkFeatureAccess,
    checkUsageLimit: simpleAuth.checkUsageLimit
  };
};

// 兼容性別名
export const useAuthContext = useAuth;

// 會員狀態Hook
export const useMembershipStatus = () => {
  const { membershipStatus, isAuthenticated } = useSimpleAuth();
  
  return {
    ...membershipStatus,
    isAuthenticated
  };
};

// 功能存取Hook
export const useFeatureAccess = () => {
  const { checkFeatureAccess, checkUsageLimit } = useSimpleAuth();
  
  return {
    checkFeatureAccess,
    checkUsageLimit
  };
};

export default SimpleAuthProvider;