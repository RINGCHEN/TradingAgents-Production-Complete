import React, { useEffect, useRef, useState } from 'react';
import googleAuthService, { GoogleUser, GoogleAuthError } from '../services/GoogleAuthService';

interface GoogleAuthButtonProps {
  onSignIn?: (user: GoogleUser) => void;
  onSignOut?: () => void;
  onError?: (error: GoogleAuthError) => void;
  theme?: 'outline' | 'filled_blue' | 'filled_black';
  size?: 'large' | 'medium' | 'small';
  text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin';
  shape?: 'rectangular' | 'pill' | 'circle' | 'square';
  width?: number;
  className?: string;
  disabled?: boolean;
}

const GoogleAuthButton: React.FC<GoogleAuthButtonProps> = ({
  onSignIn,
  onSignOut,
  onError,
  theme = 'outline',
  size = 'large',
  text = 'signin_with',
  shape = 'rectangular',
  width = 250,
  className = '',
  disabled = false
}) => {
  const buttonRef = useRef<HTMLDivElement>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<GoogleUser | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeGoogleAuth();
    
    // 監聽 Google Auth 錯誤事件
    const handleAuthError = (event: CustomEvent<GoogleAuthError>) => {
      const authError = event.detail;
      setError(authError.message);
      if (onError) {
        onError(authError);
      }
    };

    window.addEventListener('google-auth-error', handleAuthError as EventListener);

    return () => {
      window.removeEventListener('google-auth-error', handleAuthError as EventListener);
    };
  }, []);

  useEffect(() => {
    if (isInitialized && buttonRef.current && !disabled) {
      renderButton();
    }
  }, [isInitialized, theme, size, text, shape, width, disabled]);

  const initializeGoogleAuth = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 設定回調函數
      googleAuthService.onSignIn((user: GoogleUser) => {
        setCurrentUser(user);
        if (onSignIn) {
          onSignIn(user);
        }
      });

      googleAuthService.onSignOut(() => {
        setCurrentUser(null);
        if (onSignOut) {
          onSignOut();
        }
      });

      // 初始化服務
      await googleAuthService.initialize();
      
      // 嘗試恢復認證狀態
      const restoredUser = await googleAuthService.restoreAuthState();
      if (restoredUser) {
        setCurrentUser(restoredUser);
        if (onSignIn) {
          onSignIn(restoredUser);
        }
      }

      setIsInitialized(true);
    } catch (error) {
      console.error('Google Auth 初始化失敗:', error);
      setError(error instanceof Error ? error.message : '初始化失敗');
    } finally {
      setIsLoading(false);
    }
  };

  const renderButton = () => {
    if (!buttonRef.current || !isInitialized) return;

    try {
      // 清空現有內容
      buttonRef.current.innerHTML = '';

      // 渲染 Google 登入按鈕
      googleAuthService.renderSignInButton(buttonRef.current, {
        theme,
        size,
        text,
        shape,
        width,
        locale: 'zh_TW'
      });
    } catch (error) {
      console.error('渲染 Google 按鈕失敗:', error);
      setError('渲染按鈕失敗');
    }
  };

  const handleSignOut = async () => {
    try {
      await googleAuthService.signOut();
    } catch (error) {
      console.error('登出失敗:', error);
      setError(error instanceof Error ? error.message : '登出失敗');
    }
  };

  const handleManualSignIn = async () => {
    try {
      setError(null);
      const user = await googleAuthService.signIn();
      if (user) {
        setCurrentUser(user);
        if (onSignIn) {
          onSignIn(user);
        }
      }
    } catch (error) {
      console.error('手動登入失敗:', error);
      setError(error instanceof Error ? error.message : '登入失敗');
    }
  };

  if (isLoading) {
    return (
      <div className={`google-auth-loading ${className}`}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          padding: '12px 24px',
          border: '1px solid #dadce0',
          borderRadius: '4px',
          backgroundColor: '#f8f9fa',
          color: '#5f6368',
          fontSize: '14px'
        }}>
          <div style={{ 
            width: '16px', 
            height: '16px', 
            border: '2px solid #dadce0',
            borderTop: '2px solid #1a73e8',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginRight: '8px'
          }}></div>
          載入中...
        </div>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`google-auth-error ${className}`}>
        <div style={{
          padding: '12px 16px',
          border: '1px solid #ea4335',
          borderRadius: '4px',
          backgroundColor: '#fce8e6',
          color: '#d93025',
          fontSize: '14px',
          marginBottom: '8px'
        }}>
          ❌ {error}
        </div>
        <button
          onClick={initializeGoogleAuth}
          style={{
            padding: '8px 16px',
            border: '1px solid #dadce0',
            borderRadius: '4px',
            backgroundColor: '#fff',
            color: '#1a73e8',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          重試
        </button>
      </div>
    );
  }

  if (currentUser) {
    return (
      <div className={`google-auth-signed-in ${className}`}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '12px 16px',
          border: '1px solid #34a853',
          borderRadius: '4px',
          backgroundColor: '#e6f4ea',
          marginBottom: '8px'
        }}>
          <img
            src={currentUser.picture}
            alt={currentUser.name}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              marginRight: '12px'
            }}
          />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 'bold', fontSize: '14px', color: '#137333' }}>
              {currentUser.name}
            </div>
            <div style={{ fontSize: '12px', color: '#5f6368' }}>
              {currentUser.email}
            </div>
          </div>
        </div>
        <button
          onClick={handleSignOut}
          style={{
            padding: '8px 16px',
            border: '1px solid #dadce0',
            borderRadius: '4px',
            backgroundColor: '#fff',
            color: '#5f6368',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          登出
        </button>
      </div>
    );
  }

  return (
    <div className={`google-auth-button ${className}`}>
      {disabled ? (
        <div style={{
          padding: '12px 24px',
          border: '1px solid #dadce0',
          borderRadius: '4px',
          backgroundColor: '#f8f9fa',
          color: '#9aa0a6',
          fontSize: '14px',
          textAlign: 'center'
        }}>
          Google 登入已禁用
        </div>
      ) : (
        <>
          <div ref={buttonRef} />
          <div style={{ marginTop: '8px', textAlign: 'center' }}>
            <button
              onClick={handleManualSignIn}
              style={{
                padding: '6px 12px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: 'transparent',
                color: '#1a73e8',
                cursor: 'pointer',
                fontSize: '12px',
                textDecoration: 'underline'
              }}
            >
              或點擊這裡登入
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default GoogleAuthButton;