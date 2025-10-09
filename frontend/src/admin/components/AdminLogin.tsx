/**
 * 管理員登入組件
 * 提供安全的管理員身份認證
 */

import React, { useState } from 'react';
import { useToast } from './common/SimpleToast';

interface AdminLoginProps {
  onLogin: (adminData: AdminData) => void;
}

interface AdminData {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  token: string;
}

interface AuthResponse {
  success: boolean;
  adminData?: AdminData;
  token?: string;
  requiresTwoFactor?: boolean;
}

interface LoginCredentials {
  username: string;
  password: string;
  twoFactorCode?: string;
}

export const AdminLogin: React.FC<AdminLoginProps> = ({ onLogin }) => {
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
    twoFactorCode: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [showTwoFactor, setShowTwoFactor] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [lockoutTime, setLockoutTime] = useState<Date | null>(null);

  const { showSuccess, showError, showWarning } = useToast();

  // 檢查是否被鎖定
  const isLockedOut = lockoutTime && new Date() < lockoutTime;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLockedOut) {
      showError('登入被鎖定', '請等待解鎖後再試');
      return;
    }

    if (!credentials.username || !credentials.password) {
      showError('請填寫完整資訊', '用戶名和密碼不能為空');
      return;
    }

    setIsLoading(true);

    try {
      // 模擬管理員登入API調用
      const response = await authenticateAdmin(credentials);
      
      if (response.requiresTwoFactor) {
        setShowTwoFactor(true);
        showWarning('需要雙重驗證', '請輸入您的驗證碼');
        return;
      }

      if (response.success && response.adminData && response.token) {
        // 重置登入嘗試
        setLoginAttempts(0);
        setLockoutTime(null);
        
        // 儲存管理員token
        localStorage.setItem('admin_token', response.token);
        localStorage.setItem('admin_user', JSON.stringify(response.adminData));
        
        showSuccess('登入成功', `歡迎回來，${response.adminData.username}！`);
        onLogin(response.adminData);
      } else {
        handleFailedLogin();
      }
    } catch (error) {
      console.error('登入錯誤:', error);
      handleFailedLogin();
    } finally {
      setIsLoading(false);
    }
  };

  const handleFailedLogin = () => {
    const newAttempts = loginAttempts + 1;
    setLoginAttempts(newAttempts);

    if (newAttempts >= 5) {
      // 鎖定15分鐘
      const lockout = new Date();
      lockout.setMinutes(lockout.getMinutes() + 15);
      setLockoutTime(lockout);
      
      showError('登入失敗次數過多', '帳戶已被鎖定15分鐘');
    } else {
      showError('登入失敗', `用戶名或密碼錯誤 (${newAttempts}/5)`);
    }
  };

  const authenticateAdmin = async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      // 調用現有認證API - 使用模擬管理員帳戶
      const response = await fetch('https://twshocks-app-79rsx.ondigitalocean.app/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: credentials.username === 'admin' ? 'admin@example.com' : `${credentials.username}@example.com`,
          password: credentials.password
        }),
      });

      const result = await response.json();

      if (response.ok && result.access_token) {
        // 現有API使用access_token格式
        const adminData = {
          id: 'admin_001',
          username: credentials.username,
          email: credentials.username === 'admin' ? 'admin@example.com' : `${credentials.username}@example.com`,
          role: 'admin',
          permissions: ['*'],
          token: result.access_token
        };

        // 儲存管理員Token到localStorage
        localStorage.setItem('admin_token', result.access_token);
        localStorage.setItem('admin_user', JSON.stringify(adminData));

        return {
          success: true,
          adminData: adminData,
          token: result.access_token,
          requiresTwoFactor: false
        };
      } else {
        return {
          success: false,
          requiresTwoFactor: false
        };
      }
    } catch (error) {
      console.error('Admin authentication error:', error);
      return { success: false };
    }

    // 備用模擬管理員帳戶 (如果API失敗)
    const adminAccounts = [
      {
        username: 'admin',
        password: 'admin123',
        adminData: {
          id: '1',
          username: 'admin',
          email: 'admin@tradingagents.com',
          role: 'super_admin',
          permissions: ['*'],
          token: 'admin-token-' + Date.now()
        }
      },
      {
        username: 'manager',
        password: 'manager123',
        adminData: {
          id: '2',
          username: 'manager',
          email: 'manager@tradingagents.com', 
          role: 'manager',
          permissions: ['user_management', 'subscription_management', 'analytics'],
          token: 'manager-token-' + Date.now()
        }
      }
    ];

    const account = adminAccounts.find(
      acc => acc.username === credentials.username && acc.password === credentials.password
    );

    if (account) {
      return {
        success: true,
        adminData: account.adminData,
        token: account.adminData.token,
        requiresTwoFactor: false
      };
    }

    return { success: false };
  };

  const handleDemoLogin = (role: 'admin' | 'manager') => {
    if (role === 'admin') {
      setCredentials({ username: 'admin', password: 'admin123' });
    } else {
      setCredentials({ username: 'manager', password: 'manager123' });
    }
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-card">
        <div className="login-header">
          <div className="login-logo">
            <div className="logo-icon">🤖</div>
            <h1>TradingAgents</h1>
            <p>管理後台登入</p>
          </div>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="username">管理員帳戶</label>
            <input
              type="text"
              id="username"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              placeholder="請輸入管理員用戶名"
              disabled={isLoading || Boolean(isLockedOut)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">密碼</label>
            <input
              type="password"
              id="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              placeholder="請輸入密碼"
              disabled={isLoading || Boolean(isLockedOut)}
              required
            />
          </div>

          {showTwoFactor && (
            <div className="form-group">
              <label htmlFor="twoFactorCode">雙重驗證碼</label>
              <input
                type="text"
                id="twoFactorCode"
                value={credentials.twoFactorCode || ''}
                onChange={(e) => setCredentials({...credentials, twoFactorCode: e.target.value})}
                placeholder="請輸入6位驗證碼"
                disabled={isLoading}
                maxLength={6}
              />
            </div>
          )}

          {isLockedOut && (
            <div className="lockout-notice">
              <span className="lockout-icon">🔒</span>
              <p>帳戶已被鎖定，解鎖時間：{lockoutTime?.toLocaleTimeString()}</p>
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={isLoading || Boolean(isLockedOut)}
          >
            {isLoading ? (
              <>
                <span className="loading-spinner"></span>
                登入中...
              </>
            ) : (
              '登入管理後台'
            )}
          </button>

          {loginAttempts > 0 && loginAttempts < 5 && (
            <div className="login-attempts">
              <span className="warning-icon">⚠️</span>
              登入失敗次數：{loginAttempts}/5
            </div>
          )}
        </form>

        {/* 示範帳戶 - 僅開發環境顯示 */}
        {process.env.NODE_ENV === 'development' && (
          <div className="demo-accounts">
            <h3>示範帳戶 (僅開發環境)</h3>
            <div className="demo-buttons">
              <button
                onClick={() => handleDemoLogin('admin')}
                className="demo-btn admin-demo"
                disabled={isLoading}
              >
                👑 超級管理員
                <small>admin / admin123 (admin@example.com)</small>
              </button>
              <button
                onClick={() => handleDemoLogin('manager')}
                className="demo-btn manager-demo"
                disabled={isLoading}
              >
                🎯 經理
                <small>manager / manager123</small>
              </button>
            </div>
          </div>
        )}

        <div className="login-footer">
          <div className="security-features">
            <span className="feature-item">🛡️ 安全登入</span>
            <span className="feature-item">🔒 資料加密</span>
            <span className="feature-item">⏰ 會話管理</span>
          </div>
          <p className="copyright">© 2025 TradingAgents. 保留所有權利。</p>
        </div>
      </div>

      <style>{`
        .admin-login-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
        }

        .admin-login-card {
          background: white;
          border-radius: 16px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          padding: 40px;
          width: 100%;
          max-width: 440px;
        }

        .login-header {
          text-align: center;
          margin-bottom: 32px;
        }

        .login-logo .logo-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }

        .login-logo h1 {
          font-size: 24px;
          font-weight: 700;
          color: #2d3748;
          margin-bottom: 8px;
        }

        .login-logo p {
          color: #718096;
          font-size: 14px;
        }

        .login-form {
          margin-bottom: 24px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: 600;
          color: #2d3748;
          font-size: 14px;
        }

        .form-group input {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          font-size: 14px;
          transition: all 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: #4299e1;
          box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }

        .form-group input:disabled {
          background-color: #f7fafc;
          cursor: not-allowed;
        }

        .lockout-notice {
          text-align: center;
          padding: 12px;
          background-color: #fed7d7;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .lockout-notice .lockout-icon {
          font-size: 20px;
          margin-bottom: 8px;
          display: block;
        }

        .lockout-notice p {
          margin: 0;
          color: #c53030;
          font-size: 14px;
        }

        .login-button {
          width: 100%;
          padding: 12px;
          background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .login-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
        }

        .login-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .loading-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .login-attempts {
          text-align: center;
          margin-top: 12px;
          padding: 8px;
          background-color: #fef5e7;
          border-radius: 6px;
          color: #d69e2e;
          font-size: 14px;
        }

        .warning-icon {
          margin-right: 4px;
        }

        .demo-accounts {
          margin-bottom: 24px;
          padding-top: 20px;
          border-top: 1px solid #e2e8f0;
        }

        .demo-accounts h3 {
          text-align: center;
          font-size: 16px;
          color: #4a5568;
          margin-bottom: 16px;
        }

        .demo-buttons {
          display: grid;
          gap: 8px;
        }

        .demo-btn {
          padding: 12px 16px;
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
        }

        .demo-btn:hover:not(:disabled) {
          border-color: #4299e1;
          background-color: #f7fafc;
        }

        .demo-btn small {
          display: block;
          color: #718096;
          font-size: 12px;
          margin-top: 2px;
        }

        .admin-demo {
          border-color: #f6ad55;
        }

        .manager-demo {
          border-color: #68d391;
        }

        .login-footer {
          text-align: center;
          padding-top: 20px;
          border-top: 1px solid #e2e8f0;
        }

        .security-features {
          display: flex;
          justify-content: center;
          gap: 16px;
          margin-bottom: 12px;
          flex-wrap: wrap;
        }

        .feature-item {
          font-size: 12px;
          color: #718096;
        }

        .copyright {
          font-size: 12px;
          color: #a0aec0;
          margin: 0;
        }
      `}</style>
    </div>
  );
};

export default AdminLogin;