/**
 * 認證守衛組件
 * 保護需要認證的路由和組件
 */
import React, { useEffect, useState } from 'react';
import { adminApiService } from '../../services/AdminApiService_Fixed';
import { useNotifications } from '../../hooks/useAdminHooks';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  fallback?: React.ReactNode;
}

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requiredPermissions = [],
  fallback
}) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
    error: null
  });
  const { showError, showWarning } = useNotifications();

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      if (!token) {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: '未找到認證令牌'
        });
        return;
      }

      // 驗證token有效性
      const response = await adminApiService.get('/admin/auth/verify');
      if (response.success && response.data) {
        const user = response.data.user;
        // 檢查權限
        if (requiredPermissions.length > 0) {
          const hasPermission = requiredPermissions.every(permission =>
            user.permissions.includes(permission) || user.role === 'admin'
          );
          if (!hasPermission) {
            setAuthState({
              isAuthenticated: true,
              user,
              loading: false,
              error: '權限不足'
            });
            showWarning('權限不足', '您沒有訪問此功能的權限');
            return;
          }
        }
        setAuthState({
          isAuthenticated: true,
          user,
          loading: false,
          error: null
        });
      } else {
        // Token無效，嘗試刷新
        await refreshToken();
      }
    } catch (error) {
      console.error('認證檢查失敗:', error);
      await refreshToken();
    }
  };

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('admin_refresh_token');
      if (!refreshToken) {
        handleAuthFailure('未找到刷新令牌');
        return;
      }

      const response = await adminApiService.post('/admin/auth/refresh', {
        refreshToken
      });

      if (response.success && response.data) {
        const { token, refreshToken: newRefreshToken, user } = response.data;
        // 更新本地存儲的token
        localStorage.setItem('admin_token', token);
        localStorage.setItem('admin_refresh_token', newRefreshToken);
        // 更新API服務的token
        adminApiService.setAuthToken(token);
        setAuthState({
          isAuthenticated: true,
          user,
          loading: false,
          error: null
        });
      } else {
        handleAuthFailure('Token刷新失敗');
      }
    } catch (error) {
      console.error('Token刷新失敗:', error);
      handleAuthFailure('認證已過期，請重新登入');
    }
  };

  const handleAuthFailure = (errorMessage: string) => {
    // 清除本地存儲的認證信息
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_refresh_token');
    setAuthState({
      isAuthenticated: false,
      user: null,
      loading: false,
      error: errorMessage
    });
    showError('認證失敗', errorMessage);
    // 重定向到登入頁面
    setTimeout(() => {
      window.location.href = '/admin/login';
    }, 2000);
  };

  // 載入中狀態
  if (authState.loading) {
    return (
      <div className="auth-loading">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
          <div className="text-center">
            <div className="spinner-border text-primary mb-3" role="status">
              <span className="visually-hidden">驗證中...</span>
            </div>
            <p className="text-muted">正在驗證您的身份...</p>
          </div>
        </div>
      </div>
    );
  }

  // 認證失敗狀態
  if (!authState.isAuthenticated || authState.error) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return (
      <div className="auth-error">
        <div className="container-fluid">
          <div className="row justify-content-center">
            <div className="col-md-6">
              <div className="card shadow mt-5">
                <div className="card-body text-center">
                  <div className="mb-4">
                    <i className="fas fa-lock fa-3x text-warning"></i>
                  </div>
                  <h4 className="card-title">認證失敗</h4>
                  <p className="card-text text-muted">
                    {authState.error || '您需要登入才能訪問此頁面'}
                  </p>
                  <div className="mt-4">
                    <button
                      type="button"
                      className="btn btn-primary me-2"
                      onClick={() => window.location.href = '/admin/login'}
                    >
                      前往登入
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={checkAuthentication}
                    >
                      重新驗證
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 認證成功，渲染子組件
  return <>{children}</>;
};

// Hook版本，用於在組件中獲取認證狀態
export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
    error: null
  });

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      if (!token) {
        setAuthState(prev => ({ ...prev, loading: false }));
        return;
      }

      const response = await adminApiService.get('/admin/auth/verify');
      if (response.success && response.data) {
        setAuthState({
          isAuthenticated: true,
          user: response.data.user,
          loading: false,
          error: null
        });
      } else {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: 'Token無效'
        });
      }
    } catch (error) {
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: '認證檢查失敗'
      });
    }
  };

  const logout = async () => {
    try {
      await adminApiService.post('/admin/auth/logout');
    } catch (error) {
      console.error('登出API調用失敗:', error);
    } finally {
      // 清除本地存儲
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_refresh_token');
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null
      });
      // 重定向到登入頁面
      window.location.href = '/admin/login';
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!authState.user) return false;
    return authState.user.permissions.includes(permission) || authState.user.role === 'admin';
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some(permission => hasPermission(permission));
  };

  return {
    ...authState,
    logout,
    hasPermission,
    hasAnyPermission,
    refreshAuth: checkAuth
  };
};

export default AuthGuard;