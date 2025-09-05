/**
 * EnhancedAuthContext - 增強的認證上下文
 * 整合AuthStateManager，提供安全的認證狀態管理和錯誤處理
 * 支援訪客模式降級和自動恢復機制
 */

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { AuthState, AuthUser, AuthError, authStateManager } from '../utils/AuthStateManager';
import { useErrorState } from './ErrorStateContext';

interface EnhancedAuthContextType {
  // 基本狀態
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: AuthError | null;
  mode: 'authenticated' | 'guest' | 'error' | 'initializing';

  // 操作方法
  login: (credentials: any) => Promise<{ success: boolean; error?: AuthError }>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  clearError: () => void;

  // 功能檢查
  checkFeatureAccess: (feature: string) => boolean;
  checkUsageLimit: (limitType: string) => boolean;
  canAccessFeature: (feature: string) => { allowed: boolean; reason?: string };

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
  
  // 錯誤恢復
  retryInitialization: () => Promise<void>;
  hasRecoverableError: boolean;
}

const EnhancedAuthContext = createContext<EnhancedAuthContextType | undefined>(undefined);

interface EnhancedAuthProviderProps {
  children: ReactNode;
  enableGuestMode?: boolean;
  onAuthStateChange?: (state: AuthState) => void;
  onError?: (error: AuthError) => void;
}

export const EnhancedAuthProvider: React.FC<EnhancedAuthProviderProps> = ({
  children,
  enableGuestMode = true,
  onAuthStateChange,
  onError
}) => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    try {
      return authStateManager.getState();
    } catch (error) {
      console.error('Failed to get initial auth state:', error);
      return {
        isInitialized: false,
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null,
        mode: 'initializing',
        lastInitAttempt: null,
        initAttempts: 0
      };
    }
  });
  const { addError } = useErrorState();

  // 初始化認證狀態
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        await authStateManager.initialize();
      } catch (error) {
        console.error('Auth initialization failed:', error);
        addError('auth', new Error('Authentication initialization failed'), 'high');
      }
    };

    initializeAuth();
  }, [addError]);

  // 監聽認證狀態變化
  useEffect(() => {
    const handleAuthStateChange = (event: CustomEvent<AuthState>) => {
      const newState = event.detail;
      setAuthState(newState);
      
      // 調用外部回調
      if (onAuthStateChange) {
        onAuthStateChange(newState);
      }

      // 報告錯誤
      if (newState.error && onError) {
        onError(newState.error);
      }

      // 報告到錯誤診斷系統
      if (newState.error) {
        addError('auth', new Error(newState.error.message), 
          newState.error.type === 'initialization' ? 'critical' : 'medium');
      }
    };

    window.addEventListener('auth-state-change', handleAuthStateChange as EventListener);
    
    return () => {
      window.removeEventListener('auth-state-change', handleAuthStateChange as EventListener);
    };
  }, [onAuthStateChange, onError, addError]);

  // 登錄方法
  const login = useCallback(async (credentials: any) => {
    try {
      const result = await authStateManager.login(credentials);
      
      if (!result.success && result.error) {
        addError('auth', new Error(`Login failed: ${result.error.message}`), 'medium');
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      addError('auth', new Error(errorMessage), 'high');
      
      return {
        success: false,
        error: {
          type: 'unknown' as const,
          message: errorMessage,
          timestamp: new Date(),
          recoverable: false
        }
      };
    }
  }, [addError]);

  // 登出方法
  const logout = useCallback(async () => {
    try {
      await authStateManager.logout();
    } catch (error) {
      console.error('Logout failed:', error);
      addError('auth', new Error('Logout failed'), 'medium');
    }
  }, [addError]);

  // 刷新認證狀態
  const refresh = useCallback(async () => {
    try {
      await authStateManager.forceReinitialize();
    } catch (error) {
      console.error('Auth refresh failed:', error);
      addError('auth', new Error('Auth refresh failed'), 'medium');
    }
  }, [addError]);

  // 清除錯誤
  const clearError = useCallback(() => {
    // 這裡可以實現清除錯誤的邏輯
    console.log('Clearing auth error');
  }, []);

  // 檢查功能訪問權限
  const checkFeatureAccess = useCallback((feature: string): boolean => {
    if (!authState.isAuthenticated) {
      // 訪客模式下的功能限制
      const guestAllowedFeatures = ['view-basic-info', 'personality-test', 'help'];
      return guestAllowedFeatures.includes(feature);
    }

    const user = authState.user;
    if (!user) return false;

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
  }, [authState]);

  // 檢查使用限制
  const checkUsageLimit = useCallback((limitType: string): boolean => {
    if (!authState.isAuthenticated || !authState.user) {
      return false;
    }

    const user = authState.user;
    
    switch (limitType) {
      case 'analysis':
        return (user.analysisCount || 0) < (user.analysisLimit || 0);
      case 'portfolio-items':
        // 這裡需要實際的組合項目計數
        return true;
      default:
        return true;
    }
  }, [authState]);

  // 更詳細的功能訪問檢查
  const canAccessFeature = useCallback((feature: string): { allowed: boolean; reason?: string } => {
    if (!authState.isInitialized) {
      return { allowed: false, reason: '系統正在初始化，請稍候' };
    }

    if (authState.mode === 'error') {
      return { allowed: false, reason: '認證系統發生錯誤，請重試' };
    }

    if (!authState.isAuthenticated) {
      if (authState.mode === 'guest' && enableGuestMode) {
        const guestAllowed = checkFeatureAccess(feature);
        return {
          allowed: guestAllowed,
          reason: guestAllowed ? undefined : '此功能需要登錄後使用'
        };
      }
      return { allowed: false, reason: '請先登錄' };
    }

    const hasAccess = checkFeatureAccess(feature);
    if (!hasAccess) {
      return { allowed: false, reason: '您的會員等級無法使用此功能' };
    }

    // 檢查使用限制
    if (feature === 'stock-analysis' && !checkUsageLimit('analysis')) {
      return { allowed: false, reason: '您已達到分析次數限制' };
    }

    return { allowed: true };
  }, [authState, enableGuestMode, checkFeatureAccess, checkUsageLimit]);

  // 切換到訪客模式
  const switchToGuest = useCallback(() => {
    if (enableGuestMode) {
      logout();
    }
  }, [enableGuestMode, logout]);

  // 重試初始化
  const retryInitialization = useCallback(async () => {
    try {
      await authStateManager.forceReinitialize();
    } catch (error) {
      console.error('Retry initialization failed:', error);
      addError('auth', new Error('Retry initialization failed'), 'high');
    }
  }, [addError]);

  // 計算會員狀態
  const membershipStatus = {
    tier: authState?.user?.tier || 'free',
    analysisCount: authState?.user?.analysisCount || 0,
    analysisLimit: authState?.user?.analysisLimit || 5,
    isActive: authState?.isAuthenticated || false
  };

  const contextValue: EnhancedAuthContextType = {
    // 基本狀態
    user: authState?.user || null,
    isAuthenticated: authState?.isAuthenticated || false,
    isLoading: authState?.isLoading || false,
    isInitialized: authState?.isInitialized || false,
    error: authState?.error || null,
    mode: authState?.mode || 'initializing',

    // 操作方法
    login,
    logout,
    refresh,
    clearError,

    // 功能檢查
    checkFeatureAccess,
    checkUsageLimit,
    canAccessFeature,

    // 會員狀態
    membershipStatus,

    // 訪客模式
    isGuestMode: authState?.mode === 'guest',
    switchToGuest,

    // 錯誤恢復
    retryInitialization,
    hasRecoverableError: authState?.error?.recoverable || false
  };

  return (
    <EnhancedAuthContext.Provider value={contextValue}>
      {children}
    </EnhancedAuthContext.Provider>
  );
};

// Hook for using enhanced auth context
export const useEnhancedAuth = (): EnhancedAuthContextType => {
  const context = useContext(EnhancedAuthContext);
  if (context === undefined) {
    throw new Error('useEnhancedAuth must be used within an EnhancedAuthProvider');
  }
  return context;
};

// 兼容性Hook - 保持與原有AuthContext的兼容性
export const useAuth = () => {
  const enhancedAuth = useEnhancedAuth();
  
  return {
    user: enhancedAuth.user,
    isAuthenticated: enhancedAuth.isAuthenticated,
    isLoading: enhancedAuth.isLoading,
    login: enhancedAuth.login,
    logout: enhancedAuth.logout,
    checkFeatureAccess: enhancedAuth.checkFeatureAccess,
    checkUsageLimit: enhancedAuth.checkUsageLimit
  };
};

// 別名導出以保持兼容性
export const useAuthContext = useAuth;

// 會員狀態Hook
export const useMembershipStatus = () => {
  const { membershipStatus, isAuthenticated } = useEnhancedAuth();
  
  return {
    ...membershipStatus,
    isAuthenticated
  };
};

// 會員升級Hook
export const useMembershipUpgrade = () => {
  const upgradeMembership = async (targetTier: string) => {
    // 模擬升級邏輯
    console.log('Upgrading to:', targetTier);
    return Promise.resolve();
  };

  return { upgradeMembership };
};

// 訪客模式Hook
export const useGuestMode = () => {
  const { isGuestMode, switchToGuest, canAccessFeature } = useEnhancedAuth();
  
  return {
    isGuestMode,
    switchToGuest,
    canAccessFeature
  };
};

// 認證錯誤Hook
export const useAuthError = () => {
  const { error, clearError, retryInitialization, hasRecoverableError } = useEnhancedAuth();
  
  return {
    error,
    clearError,
    retryInitialization,
    hasRecoverableError
  };
};

export default EnhancedAuthProvider;