import React, { ReactNode, useState, useEffect } from 'react';

export interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 支援前端模式和後端模式的認證檢查
    const checkAuth = () => {
      console.log('🔍 ProtectedRoute 認證檢查');
      
      // 後端模式認證
      const token = localStorage.getItem('auth_token');
      
      // 前端模式認證
      const frontendAuth = localStorage.getItem('frontend_google_auth');
      const frontendEmail = localStorage.getItem('frontend_user_email');
      
      const isBackendAuth = !!token;
      const isFrontendAuth = frontendAuth === 'true' && !!frontendEmail;
      
      console.log('🔍 認證狀態:', {
        hasAuthToken: isBackendAuth,
        hasFrontendAuth: isFrontendAuth,
        frontendEmail: localStorage.getItem('frontend_user_email')
      });
      
      const authenticated = isBackendAuth || isFrontendAuth;
      setIsAuthenticated(authenticated);
      setIsLoading(false);
      
      console.log(`✅ ProtectedRoute 認證結果: ${authenticated ? '已認證' : '未認證'}`);
    };

    checkAuth();
  }, []);

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column'
      }}>
        <div style={{
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #3498db',
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          animation: 'spin 2s linear infinite'
        }}></div>
        <p style={{ marginTop: '20px' }}>正在驗證訪問權限...</p>
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔒</div>
        <h2>需要登錄</h2>
        <p>請先登錄以訪問此頁面</p>
        <button 
          style={{
            padding: '10px 20px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
          onClick={() => window.location.href = '/auth'}
        >
          立即登錄
        </button>
      </div>
    );
  }

  return <>{children}</>;
};

export const MembershipRoute: React.FC<ProtectedRouteProps> = ({
  children
}) => {
  return (
    <ProtectedRoute requireAuth={true}>
      {children}
    </ProtectedRoute>
  );
};

export default ProtectedRoute;