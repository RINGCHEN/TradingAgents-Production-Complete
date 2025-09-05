/**
 * 認證Hook工具集
 * 提供便捷的認證狀態訪問和操作的React Hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthContext, useAuthState, useAuthActions, useAuthCheck } from '../contexts/AuthContext';
import { AuthUser, LoginCredentials, AuthError } from '../services/AuthService';
import { authService } from '../services/AuthService';

/**
 * 主要認證Hook
 * 提供完整的認證功能訪問
 */
export const useAuth = () => {
  return useAuthContext();
};

/**
 * 登錄Hook
 * 提供登錄功能和狀態管理
 */
export const useLogin = () => {
  const { login: contextLogin, clearError } = useAuthActions();
  const { error, isLoading } = useAuthState();
  const [loginError, setLoginError] = useState<AuthError | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      setIsSubmitting(true);
      setLoginError(null);
      clearError();
      
      await contextLogin(credentials);
      console.log('登錄Hook：登錄成功');
    } catch (error) {
      console.error('登錄Hook：登錄失敗', error);
      setLoginError(error as AuthError);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  }, [contextLogin, clearError]);

  const clearLoginError = useCallback(() => {
    setLoginError(null);
    clearError();
  }, [clearError]);

  return {
    login,
    isLoading: isLoading || isSubmitting,
    error: loginError || error,
    clearError: clearLoginError
  };
};

/**
 * 登出Hook
 * 提供登出功能和狀態管理
 */
export const useLogout = () => {
  const { logout: contextLogout } = useAuthActions();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<AuthError | null>(null);

  const logout = useCallback(async () => {
    try {
      setIsLoggingOut(true);
      setLogoutError(null);
      
      await contextLogout();
      console.log('登出Hook：登出成功');
    } catch (error) {
      console.error('登出Hook：登出失敗', error);
      setLogoutError(error as AuthError);
    } finally {
      setIsLoggingOut(false);
    }
  }, [contextLogout]);

  const clearLogoutError = useCallback(() => {
    setLogoutError(null);
  }, []);

  return {
    logout,
    isLoggingOut,
    error: logoutError,
    clearError: clearLogoutError
  };
};

/**
 * 用戶信息Hook
 * 提供用戶信息訪問和刷新功能
 */
export const useUser = () => {
  const { user, isAuthenticated } = useAuthState();
  const { refreshUser } = useAuthActions();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<AuthError | null>(null);

  const refresh = useCallback(async () => {
    try {
      setIsRefreshing(true);
      setRefreshError(null);
      
      await refreshUser();
      console.log('用戶Hook：用戶信息刷新成功');
    } catch (error) {
      console.error('用戶Hook：用戶信息刷新失敗', error);
      setRefreshError(error as AuthError);
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshUser]);

  const clearRefreshError = useCallback(() => {
    setRefreshError(null);
  }, []);

  return {
    user,
    isAuthenticated,
    refresh,
    isRefreshing,
    error: refreshError,
    clearError: clearRefreshError
  };
};

/**
 * 認證狀態檢查Hook
 * 提供認證狀態的實時檢查
 */
export const useAuthStatus = () => {
  const { isAuthenticated, isLoading, isInitialized } = useAuthCheck();
  const { checkAuthStatus } = useAuthActions();
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const checkStatus = useCallback(async () => {
    await checkAuthStatus();
    setLastCheck(new Date());
  }, [checkAuthStatus]);

  return {
    isAuthenticated,
    isLoading,
    isInitialized,
    isReady: isInitialized && !isLoading,
    lastCheck,
    checkStatus
  };
};

/**
 * 權限檢查Hook
 * 提供基於用戶權限的檢查功能
 */
export const usePermissions = () => {
  const { user, isAuthenticated } = useAuthState();

  const hasPermission = useCallback((permission: string): boolean => {
    if (!isAuthenticated || !user) {
      return false;
    }
    
    return user.permissions?.includes(permission) || false;
  }, [isAuthenticated, user]);

  const hasAnyPermission = useCallback((permissions: string[]): boolean => {
    if (!isAuthenticated || !user) {
      return false;
    }
    
    return permissions.some(permission => 
      user.permissions?.includes(permission) || false
    );
  }, [isAuthenticated, user]);

  const hasAllPermissions = useCallback((permissions: string[]): boolean => {
    if (!isAuthenticated || !user) {
      return false;
    }
    
    return permissions.every(permission => 
      user.permissions?.includes(permission) || false
    );
  }, [isAuthenticated, user]);

  const hasRole = useCallback((role: string): boolean => {
    if (!isAuthenticated || !user) {
      return false;
    }
    
    return user.role === role;
  }, [isAuthenticated, user]);

  const isAdmin = useCallback((): boolean => {
    return hasRole('admin') || hasRole('super_admin');
  }, [hasRole]);

  return {
    permissions: user?.permissions || [],
    role: user?.role,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    isAdmin
  };
};

/**
 * 認證錯誤處理Hook
 * 提供統一的錯誤處理和恢復機制
 */
export const useAuthError = () => {
  const { error, clearError } = useAuthState();
  const { checkAuthStatus } = useAuthActions();
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  const retry = useCallback(async () => {
    if (retryCount >= maxRetries) {
      console.warn('認證錯誤重試次數已達上限');
      return false;
    }

    try {
      setRetryCount(prev => prev + 1);
      clearError();
      
      await checkAuthStatus();
      console.log('認證錯誤重試成功');
      setRetryCount(0);
      return true;
    } catch (error) {
      console.error('認證錯誤重試失敗', error);
      return false;
    }
  }, [retryCount, maxRetries, clearError, checkAuthStatus]);

  const reset = useCallback(() => {
    setRetryCount(0);
    clearError();
  }, [clearError]);

  const canRetry = retryCount < maxRetries && error?.isRetryable();

  return {
    error,
    retryCount,
    maxRetries,
    canRetry,
    retry,
    reset,
    clearError
  };
};

/**
 * 會話管理Hook
 * 提供會話狀態監控和管理
 */
export const useSession = () => {
  const { isAuthenticated, user } = useAuthState();
  const { checkAuthStatus } = useAuthActions();
  const [sessionExpiry, setSessionExpiry] = useState<Date | null>(null);
  const [timeUntilExpiry, setTimeUntilExpiry] = useState<number | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 更新會話過期時間
  const updateSessionExpiry = useCallback(async () => {
    try {
      const token = await authService.getValidToken();
      if (token) {
        // 這裡應該從token中解析過期時間
        // 暫時使用估算值
        const expiry = new Date(Date.now() + 60 * 60 * 1000); // 1小時後
        setSessionExpiry(expiry);
      } else {
        setSessionExpiry(null);
      }
    } catch (error) {
      console.error('更新會話過期時間失敗:', error);
      setSessionExpiry(null);
    }
  }, []);

  // 計算剩餘時間
  useEffect(() => {
    if (!sessionExpiry) {
      setTimeUntilExpiry(null);
      return;
    }

    const updateTimeUntilExpiry = () => {
      const now = new Date();
      const remaining = sessionExpiry.getTime() - now.getTime();
      setTimeUntilExpiry(Math.max(0, remaining));
    };

    updateTimeUntilExpiry();
    intervalRef.current = setInterval(updateTimeUntilExpiry, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [sessionExpiry]);

  // 會話即將過期警告
  const isSessionExpiringSoon = timeUntilExpiry !== null && timeUntilExpiry < 5 * 60 * 1000; // 5分鐘

  // 延長會話
  const extendSession = useCallback(async () => {
    try {
      await checkAuthStatus();
      await updateSessionExpiry();
      console.log('會話延長成功');
    } catch (error) {
      console.error('會話延長失敗:', error);
    }
  }, [checkAuthStatus, updateSessionExpiry]);

  // 初始化會話信息
  useEffect(() => {
    if (isAuthenticated) {
      updateSessionExpiry();
    } else {
      setSessionExpiry(null);
      setTimeUntilExpiry(null);
    }
  }, [isAuthenticated, updateSessionExpiry]);

  return {
    isAuthenticated,
    user,
    sessionExpiry,
    timeUntilExpiry,
    isSessionExpiringSoon,
    extendSession,
    updateSessionExpiry
  };
};

/**
 * 自動登出Hook
 * 提供自動登出功能（基於不活動時間）
 */
export const useAutoLogout = (inactivityTimeout: number = 30 * 60 * 1000) => { // 默認30分鐘
  const { isAuthenticated } = useAuthState();
  const { logout } = useAuthActions();
  const [lastActivity, setLastActivity] = useState<Date>(new Date());
  const [isInactive, setIsInactive] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 重置活動時間
  const resetActivity = useCallback(() => {
    setLastActivity(new Date());
    setIsInactive(false);
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    if (isAuthenticated) {
      timeoutRef.current = setTimeout(() => {
        setIsInactive(true);
        console.log('用戶不活動超時，自動登出');
        logout();
      }, inactivityTimeout);
    }
  }, [isAuthenticated, logout, inactivityTimeout]);

  // 監聽用戶活動
  useEffect(() => {
    if (!isAuthenticated) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      return;
    }

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    const handleActivity = () => {
      resetActivity();
    };

    events.forEach(event => {
      document.addEventListener(event, handleActivity, true);
    });

    // 初始設置超時
    resetActivity();

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity, true);
      });
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isAuthenticated, resetActivity]);

  const timeUntilLogout = isAuthenticated && !isInactive 
    ? Math.max(0, inactivityTimeout - (Date.now() - lastActivity.getTime()))
    : 0;

  return {
    lastActivity,
    isInactive,
    timeUntilLogout,
    resetActivity
  };
};

// 導出所有Hook
export {
  useAuthState,
  useAuthActions,
  useAuthCheck
} from '../contexts/AuthContext';