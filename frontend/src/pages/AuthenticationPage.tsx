import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
// import { useEnhancedAuth } from '../contexts/EnhancedAuthContext';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import googleAuthService from '../services/GoogleAuthService';
import { crossProjectAuthService } from '../services/CrossProjectAuthService';
import GoogleAuthButton from '../components/GoogleAuthButton';
import './AuthenticationPage.css';

type MemberTier = 'free' | 'gold' | 'diamond';

// 用戶認證頁面 - 整合登入、註冊和訪客模式
// Phase 1.1 - 用戶認證流程整合

interface AuthenticationPageProps {
  initialMode?: 'login' | 'register' | 'guest';
}

interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface RegisterFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  agreeToTerms: boolean;
  selectedTier: MemberTier;
  phone?: string;
  referralCode?: string;
}

interface AuthResponse {
  success: boolean;
  user?: {
    id: string;
    name: string;
    email: string;
    tier: MemberTier;
  };
  token?: string;
  error?: string;
  message?: string;
}

const AuthenticationPage: React.FC<AuthenticationPageProps> = ({ 
  initialMode = 'login' 
}) => {
  const [mode, setMode] = useState<'login' | 'register' | 'guest' | 'forgot'>(initialMode);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { error: authError } = useSimpleAuth();
  
  // 登入表單狀態
  const [loginForm, setLoginForm] = useState<LoginFormData>({
    email: '',
    password: '',
    rememberMe: false
  });
  
  // 註冊表單狀態
  const [registerForm, setRegisterForm] = useState<RegisterFormData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreeToTerms: false,
    selectedTier: 'free'
  });
  
  // 密碼強度檢查狀態
  const [passwordStrength, setPasswordStrength] = useState({
    hasMinLength: false,
    hasLowerCase: false,
    hasUpperCase: false,
    hasNumber: false,
    isValid: false
  });
  
  // 忘記密碼表單狀態
  const [forgotEmail, setForgotEmail] = useState('');

  // 檢查密碼強度
  const checkPasswordStrength = (password: string) => {
    const hasMinLength = password.length >= 8;
    const hasLowerCase = /[a-z]/.test(password);
    const hasUpperCase = /[A-Z]/.test(password);
    const hasNumber = /\d/.test(password);
    const isValid = hasMinLength && hasLowerCase && hasUpperCase && hasNumber;
    
    setPasswordStrength({
      hasMinLength,
      hasLowerCase,
      hasUpperCase,
      hasNumber,
      isValid
    });
    
    return isValid;
  };

  // 表單驗證
  const validateForm = (): string | null => {
    if (mode === 'register') {
      if (registerForm.password !== registerForm.confirmPassword) {
        return '密碼確認不一致';
      }
      
      if (registerForm.password.length < 8) {
        return '密碼至少需要8個字符';
      }
      
      if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(registerForm.password)) {
        return '密碼需包含大小寫字母和數字';
      }
      
      if (!registerForm.agreeToTerms) {
        return '請同意服務條款和隱私政策';
      }
      
      if (registerForm.phone && !/^[0-9+\-\s]+$/.test(registerForm.phone)) {
        return '請輸入有效的電話號碼';
      }
    }
    
    return null;
  };
  
  // 處理會員等級選擇
  const handleTierSelection = (selectedTier: MemberTier) => {
    setRegisterForm({ ...registerForm, selectedTier });
    setMode('register');
  };
  
  // 處理 Line 登入
  const handleLineLogin = async () => {
    setLoading(true);
    try {
      window.location.href = '/api/auth/line';
    } catch (err) {
      setError('Line 登入失敗');
      setLoading(false);
    }
  };
  
  // 處理 Apple 登入
  const handleAppleLogin = async () => {
    setLoading(true);
    try {
      window.location.href = '/api/auth/apple';
    } catch (err) {
      setError('Apple 登入失敗');
      setLoading(false);
    }
  };

  useEffect(() => {
    // 檢查跨專案認證狀態
    const crossProjectAuth = crossProjectAuthService.getAuthFromProjects();
    if (crossProjectAuth) {
      console.log('發現跨專案認證狀態，自動登入:', crossProjectAuth.user.name);
      // 自動設置認證狀態
      localStorage.setItem('user_info', JSON.stringify(crossProjectAuth.user));
      localStorage.setItem('auth_token', crossProjectAuth.token);
      localStorage.setItem('auth_method', crossProjectAuth.user.authMethod);
      localStorage.setItem('user_email', crossProjectAuth.user.email);
      
      setSuccess(`🎉 歡迎回來，${crossProjectAuth.user.name}！自動登入成功`);
      setTimeout(() => {
        navigate('/dashboard?cross_project=true');
      }, 1500);
      return;
    }
    
    // 處理從 URL 參數中的認證信息
    if (crossProjectAuthService.handleAuthFromUrl()) {
      return;
    }
    
    // 檢查 URL 參數決定顯示模式
    const params = new URLSearchParams(location.search);
    const modeParam = params.get('mode');
    if (modeParam && ['login', 'register', 'guest', 'tier-selection'].includes(modeParam)) {
      setMode(modeParam as any);
    }
    
    // 檢查是否有OAuth回調
    const oauthSuccess = params.get('oauth_success');
    const oauthError = params.get('oauth_error');
    
    if (oauthSuccess === 'true') {
      setSuccess('第三方登入成功！');
      // 稍後跳轉
      setTimeout(() => {
        const redirectTo = params.get('redirect') || '/dashboard';
        navigate(redirectTo);
      }, 1500);
    } else if (oauthError) {
      setError(decodeURIComponent(oauthError));
    }
    
    // 清除認證錯誤
    if (authError) {
      setError(authError.message);
    }
  }, [location, authError, navigate]);
  
  // 清除錯誤
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // 處理登入
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // 模擬登入延遲
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 從 localStorage 中查找已註冊的用戶
      const registeredUsers = JSON.parse(localStorage.getItem('registered_users') || '[]');
      const foundUser = registeredUsers.find((user: any) => 
        user.email === loginForm.email && user.authMethod === 'email'
      );
      
      if (foundUser) {
        // 找到用戶，模擬密碼驗證（實際上應該有密碼哈希驗證）
        // 在模擬環境中，我們假設密碼正確
        
        // 更新用戶的最後登入時間
        foundUser.lastLoginAt = new Date().toISOString();
        
        // 更新 localStorage 中的用戶資料
        const updatedUsers = registeredUsers.map((user: any) => 
          user.email === foundUser.email && user.authMethod === 'email' ? foundUser : user
        );
        localStorage.setItem('registered_users', JSON.stringify(updatedUsers));
        
        // 儲存當前用戶資訊和認證資料
        localStorage.setItem('user_info', JSON.stringify(foundUser));
        localStorage.setItem('auth_token', `email_token_${Date.now()}`);
        localStorage.setItem('auth_method', 'email');
        localStorage.setItem('user_email', foundUser.email);
        
        setSuccess(`🎉 歡迎回來，${foundUser.name}！登入成功，正在跳轉...`);
        
        // 跳轉到儀表板
        setTimeout(() => {
          const redirectTo = new URLSearchParams(location.search).get('redirect') || '/dashboard';
          navigate(`${redirectTo}?welcome=true`);
        }, 1500);
        
      } else {
        setError('帳號或密碼錯誤，請檢查您的登入資訊或先進行註冊');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('登入過程中發生錯誤，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 處理註冊
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      setLoading(false);
      return;
    }
    
    try {
      // 模擬註冊延遲（更真實的用戶體驗）
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // 檢查是否已有相同email的用戶（簡單的本地檢查）
      const existingUsers = JSON.parse(localStorage.getItem('registered_users') || '[]');
      const emailExists = existingUsers.some((user: any) => user.email === registerForm.email);
      
      if (emailExists) {
        setError('此電子郵件已被註冊，請使用其他郵件地址或嘗試登入');
        setLoading(false);
        return;
      }
      
      // 創建新用戶
      const newUser = {
        id: Date.now().toString(),
        name: registerForm.name,
        email: registerForm.email,
        tier: registerForm.selectedTier || 'free',
        analysisCount: 0,
        analysisLimit: registerForm.selectedTier === 'free' ? 5 : registerForm.selectedTier === 'gold' ? 50 : 999,
        registeredAt: new Date().toISOString(),
        authMethod: 'email'
      };

      // 儲存到註冊用戶列表
      existingUsers.push(newUser);
      localStorage.setItem('registered_users', JSON.stringify(existingUsers));
      
      // 儲存當前用戶資訊
      localStorage.setItem('user_info', JSON.stringify(newUser));
      localStorage.setItem('auth_token', `local_token_${Date.now()}`);
      localStorage.setItem('auth_method', 'email');
      localStorage.setItem('user_email', registerForm.email);
      
      // 同步認證狀態到其他專案
      const crossProjectAuth = crossProjectAuthService.createCrossProjectAuth(newUser, 'email');
      crossProjectAuthService.syncAuthToProjects(crossProjectAuth);
      
      setSuccess('🎉 註冊成功！歡迎加入 TradingAgents！正在為您準備個人化體驗...');
      
      // 跳轉到儀表板
      setTimeout(() => {
        navigate('/dashboard?welcome=true&new_user=true');
      }, 2000);
      
    } catch (err) {
      console.error('Registration error:', err);
      setError('註冊過程中發生錯誤，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 處理 Google 登入
  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);
    
    try {
      setSuccess('正在連接 Google 帳戶服務...');
      
      // 初始化Google認證服務並設置回調
      await googleAuthService.initialize();
      
      // 設置登入成功回調
      googleAuthService.onSignIn((googleUser: any) => {
        console.log('✅ Google 登入成功回調觸發:', googleUser);
        
        // 創建用戶資料（使用真實的 Google 資料）
        const userProfile = {
          id: `google_${googleUser.id}`,
          name: googleUser.name,
          email: googleUser.email,
          tier: 'free' as const,
          analysisCount: 0,
          analysisLimit: 5,
          totalValue: 0,
          monthlyReturn: 0,
          successRate: 0,
          premiumFeatures: [],
          registeredAt: new Date().toISOString(),
          authMethod: 'google',
          picture: googleUser.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(googleUser.name)}&background=4285f4&color=fff&size=150`,
          joinDate: new Date().toISOString(),
          lastLoginAt: new Date().toISOString()
        };

        setSuccess(`正在驗證 ${googleUser.name} 的 Google 帳戶...`);
        processGoogleUserProfile(userProfile);
      });
      
      // 嘗試觸發登入
      const googleUser = await googleAuthService.signIn();
      
      if (!googleUser) {
        setError('Google 登入被取消或失敗');
        setLoading(false);
        return;
      }
      
    } catch (err) {
      console.error('Google login error:', err);
      if (err instanceof Error && err.message.includes('Client ID')) {
        setError('Google OAuth 未正確配置，請聯繫系統管理員設定 Client ID');
      } else {
        setError('Google 服務暫時無法使用，請稍後再試或使用其他登入方式');
      }
    } finally {
      setLoading(false);
    }
  };

  // 處理 Google 用戶資料的共用邏輯
  const processGoogleUserProfile = async (userProfile: any) => {
    // 檢查是否已註冊
    const existingUsers = JSON.parse(localStorage.getItem('registered_users') || '[]');
    let existingUser = existingUsers.find((user: any) => 
      user.email === userProfile.email && user.authMethod === 'google'
    );
    
    if (existingUser) {
      // 更新現有用戶
      existingUser.lastLoginAt = new Date().toISOString();
      existingUser.name = userProfile.name; // 更新姓名以防變更
      if (userProfile.picture) {
        existingUser.picture = userProfile.picture;
      }
      
      const updatedUsers = existingUsers.map((user: any) => 
        user.email === userProfile.email && user.authMethod === 'google' ? existingUser : user
      );
      localStorage.setItem('registered_users', JSON.stringify(updatedUsers));
      
      // 使用現有用戶資料
      userProfile.analysisCount = existingUser.analysisCount;
      userProfile.totalValue = existingUser.totalValue;
      userProfile.monthlyReturn = existingUser.monthlyReturn;
      userProfile.successRate = existingUser.successRate;
      userProfile.tier = existingUser.tier;
      userProfile.registeredAt = existingUser.registeredAt;
      userProfile.joinDate = existingUser.joinDate;
    } else {
      // 新用戶，添加到註冊列表
      existingUsers.push(userProfile);
      localStorage.setItem('registered_users', JSON.stringify(existingUsers));
    }

    // 儲存當前用戶資訊
    localStorage.setItem('user_info', JSON.stringify(userProfile));
    localStorage.setItem('auth_token', `google_token_${Date.now()}`);
    localStorage.setItem('auth_method', 'google');
    localStorage.setItem('user_email', userProfile.email);
    
    // 同步認證狀態到其他專案
    const crossProjectAuth = crossProjectAuthService.createCrossProjectAuth(userProfile, 'google');
    crossProjectAuthService.syncAuthToProjects(crossProjectAuth);
    
    setSuccess(`🎉 歡迎 ${userProfile.name}！Google 登入成功，正在跳轉...`);
    
    // 跳轉到儀表板
    setTimeout(() => {
      const redirectTo = new URLSearchParams(location.search).get('redirect') || '/dashboard';
      navigate(`${redirectTo}?welcome=true${!existingUser ? '&new_user=true' : ''}`);
    }, 1500);
  };

  // 處理訪客模式
  const handleGuestMode = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/auth/guest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 儲存訪客 session
        localStorage.setItem('guest_session', data.session_id);
        navigate('/dashboard?mode=guest');
      } else {
        setError('訪客模式啟動失敗');
      }
    } catch (err) {
      setError('網路錯誤，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 處理忘記密碼
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: forgotEmail }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSuccess('密碼重置連結已發送到您的信箱');
        setMode('login');
      } else {
        setError(data.error || '發送失敗，請稍後再試');
      }
    } catch (err) {
      setError('網路錯誤，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 渲染登入表單
  const renderLoginForm = () => (
    <div className="auth-form">
      <div className="auth-header">
        <h1>歡迎回來</h1>
        <p>登入您的 TradingAgents 帳戶</p>
      </div>
      
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label htmlFor="email">電子郵件</label>
          <input
            type="email"
            id="email"
            value={loginForm.email}
            onChange={(e: any) => setLoginForm({ ...loginForm, email: e.target.value })}
            placeholder="請輸入您的電子郵件"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">密碼</label>
          <input
            type="password"
            id="password"
            value={loginForm.password}
            onChange={(e: any) => setLoginForm({ ...loginForm, password: e.target.value })}
            placeholder="請輸入您的密碼"
            required
          />
        </div>
        
        <div className="form-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={loginForm.rememberMe}
              onChange={(e: any) => setLoginForm({ ...loginForm, rememberMe: e.target.checked })}
            />
            記住我
          </label>
          
          <button
            type="button"
            className="link-button"
            onClick={() => setMode('forgot')}
          >
            忘記密碼？
          </button>
        </div>
        
        <button type="submit" className="auth-button primary" disabled={loading}>
          {loading ? '登入中...' : '登入'}
        </button>
      </form>
      
      <div className="auth-divider">
        <span>或</span>
      </div>
      
      <div className="social-login-section">
        <GoogleAuthButton
          onSignIn={(googleUser) => {
            console.log('✅ Google 登入成功:', googleUser);
            
            // 創建用戶資料
            const userProfile = {
              id: `google_${googleUser.id}`,
              name: googleUser.name,
              email: googleUser.email,
              tier: 'free' as const,
              analysisCount: 0,
              analysisLimit: 5,
              totalValue: 0,
              monthlyReturn: 0,
              successRate: 0,
              premiumFeatures: [],
              registeredAt: new Date().toISOString(),
              authMethod: 'google',
              picture: googleUser.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(googleUser.name)}&background=4285f4&color=fff&size=150`,
              joinDate: new Date().toISOString(),
              lastLoginAt: new Date().toISOString()
            };

            setSuccess(`正在驗證 ${googleUser.name} 的 Google 帳戶...`);
            processGoogleUserProfile(userProfile);
          }}
          onError={(error) => {
            console.error('❌ Google 登入錯誤:', error);
            setError(error.message || 'Google 登入失敗');
          }}
          theme="outline"
          size="large"
          text="signin_with"
          disabled={loading}
        />
        
        <button
          type="button"
          className="auth-button line"
          onClick={handleLineLogin}
          disabled={loading}
        >
          <span className="line-icon">📱</span>
          使用 Line 登入
        </button>
        
        <button
          type="button"
          className="auth-button apple"
          onClick={handleAppleLogin}
          disabled={loading}
        >
          <span className="apple-icon">🍎</span>
          使用 Apple 登入
        </button>
      </div>
      
      <button
        type="button"
        className="auth-button guest"
        onClick={handleGuestMode}
        disabled={loading}
      >
        訪客體驗（3次免費分析）
      </button>
      
      <div className="auth-footer">
        <p>
          還沒有帳戶？
          <button
            type="button"
            className="link-button"
            onClick={() => setMode('tier-selection')}
          >
            選擇方案註冊
          </button>
        </p>
      </div>
    </div>
  );

  // 渲染註冊表單
  const renderRegisterForm = () => (
    <div className="auth-form">
      <div className="auth-header">
        <h1>加入 TradingAgents</h1>
        <p>開始您的智能投資分析之旅</p>
      </div>
      
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label htmlFor="name">姓名</label>
          <input
            type="text"
            id="name"
            value={registerForm.name}
            onChange={(e: any) => setRegisterForm({ ...registerForm, name: e.target.value })}
            placeholder="請輸入您的姓名"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="reg-email">電子郵件</label>
          <input
            type="email"
            id="reg-email"
            value={registerForm.email}
            onChange={(e: any) => setRegisterForm({ ...registerForm, email: e.target.value })}
            placeholder="請輸入您的電子郵件"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="reg-password">密碼</label>
          <input
            type="password"
            id="reg-password"
            value={registerForm.password}
            onChange={(e: any) => {
              const newPassword = e.target.value;
              setRegisterForm({ ...registerForm, password: newPassword });
              checkPasswordStrength(newPassword);
            }}
            placeholder="請輸入安全密碼"
            required
          />
          
          {registerForm.password && (
            <div className="password-strength">
              <div className="password-requirements">
                <div className={`requirement ${passwordStrength.hasMinLength ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordStrength.hasMinLength ? '✓' : '○'}</span>
                  至少8個字符
                </div>
                <div className={`requirement ${passwordStrength.hasLowerCase ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordStrength.hasLowerCase ? '✓' : '○'}</span>
                  包含小寫字母 (a-z)
                </div>
                <div className={`requirement ${passwordStrength.hasUpperCase ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordStrength.hasUpperCase ? '✓' : '○'}</span>
                  包含大寫字母 (A-Z)
                </div>
                <div className={`requirement ${passwordStrength.hasNumber ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordStrength.hasNumber ? '✓' : '○'}</span>
                  包含數字 (0-9)
                </div>
              </div>
              
              <div className="password-strength-bar">
                <div className={`strength-indicator ${passwordStrength.isValid ? 'strong' : 'weak'}`}>
                  {passwordStrength.isValid ? '密碼強度：強' : '密碼強度：弱'}
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="form-group">
          <label htmlFor="confirm-password">確認密碼</label>
          <input
            type="password"
            id="confirm-password"
            value={registerForm.confirmPassword}
            onChange={(e: any) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
            placeholder="請再次輸入密碼"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={registerForm.agreeToTerms}
              onChange={(e: any) => setRegisterForm({ ...registerForm, agreeToTerms: e.target.checked })}
              required
            />
            我同意
            <a href="/terms" target="_blank" rel="noopener noreferrer">服務條款</a>
            和
            <a href="/privacy" target="_blank" rel="noopener noreferrer">隱私政策</a>
          </label>
        </div>
        
        <button type="submit" className="auth-button primary" disabled={loading}>
          {loading ? '註冊中...' : '創建帳戶'}
        </button>
      </form>
      
      <div className="auth-divider">
        <span>或</span>
      </div>
      
      <button
        type="button"
        className="auth-button google"
        onClick={handleGoogleLogin}
        disabled={loading}
      >
        <span className="google-icon">G</span>
        使用 Google 註冊
      </button>
      
      <div className="auth-footer">
        <p>
          已有帳戶？
          <button
            type="button"
            className="link-button"
            onClick={() => setMode('login')}
          >
            立即登入
          </button>
        </p>
      </div>
    </div>
  );

  // 渲染忘記密碼表單
  const renderForgotPasswordForm = () => (
    <div className="auth-form">
      <div className="auth-header">
        <h1>重置密碼</h1>
        <p>輸入您的電子郵件，我們將發送重置連結</p>
      </div>
      
      <form onSubmit={handleForgotPassword}>
        <div className="form-group">
          <label htmlFor="forgot-email">電子郵件</label>
          <input
            type="email"
            id="forgot-email"
            value={forgotEmail}
            onChange={(e: any) => setForgotEmail(e.target.value)}
            placeholder="請輸入您的電子郵件"
            required
          />
        </div>
        
        <button type="submit" className="auth-button primary" disabled={loading}>
          {loading ? '發送中...' : '發送重置連結'}
        </button>
      </form>
      
      <div className="auth-footer">
        <p>
          記起密碼了？
          <button
            type="button"
            className="link-button"
            onClick={() => setMode('login')}
          >
            返回登入
          </button>
        </p>
      </div>
    </div>
  );

  // 渲染會員等級選擇頁面
  const renderTierSelectionForm = () => (
    <div className="auth-form tier-selection">
      <div className="auth-header">
        <h1>歡迎加入 TradingAgents</h1>
        <p>選擇最適合您的投資分析方案，隨時可以升級</p>
      </div>
      
      <div className="tier-options">
        <div 
          className={`tier-card free ${registerForm.selectedTier === 'free' ? 'selected' : ''}`}
          onClick={() => handleTierSelection('free')}
        >
          <div className="tier-badge free-badge">🆓 推薦新手</div>
          <div className="tier-header">
            <h3>免費體驗</h3>
            <div className="tier-price">
              <span className="price">NT$ 0</span>
              <span className="period">/永久</span>
            </div>
          </div>
          <div className="tier-features">
            <ul>
              <li><span className="icon">✅</span> 每日5次AI分析</li>
              <li><span className="icon">✅</span> 基礎股票資訊</li>
              <li><span className="icon">✅</span> 投資人格測試</li>
              <li><span className="icon">✅</span> 基礎市場數據</li>
              <li><span className="icon">💎</span> 升級享受更多功能</li>
            </ul>
          </div>
          <button 
            type="button" 
            className="tier-select-btn free-btn"
            onClick={() => handleTierSelection('free')}
          >
            免費開始體驗
          </button>
        </div>

        <div 
          className={`tier-card gold popular ${registerForm.selectedTier === 'gold' ? 'selected' : ''}`}
          onClick={() => handleTierSelection('gold')}
        >
          <div className="tier-badge popular-badge">🔥 最受歡迎</div>
          <div className="tier-header">
            <h3>進階會員</h3>
            <div className="tier-price">
              <span className="price">NT$ 999</span>
              <span className="period">/月</span>
            </div>
            <div className="tier-save">🎯 適合活躍投資者</div>
          </div>
          <div className="tier-features">
            <ul>
              <li><span className="icon">🚀</span> 每日50次AI分析</li>
              <li><span className="icon">📊</span> 7位專業AI分析師</li>
              <li><span className="icon">⚡</span> 實時市場數據</li>
              <li><span className="icon">📈</span> 投資組合追蹤</li>
              <li><span className="icon">🎯</span> 智能投資建議</li>
              <li><span className="icon">🔔</span> 即時價格警報</li>
              <li><span className="icon">📋</span> 數據匯出功能</li>
            </ul>
          </div>
          <button 
            type="button" 
            className="tier-select-btn gold-btn"
            onClick={() => handleTierSelection('gold')}
          >
            開始進階體驗
          </button>
        </div>

        <div 
          className={`tier-card diamond ${registerForm.selectedTier === 'diamond' ? 'selected' : ''}`}
          onClick={() => handleTierSelection('diamond')}
        >
          <div className="tier-badge diamond-badge">💎 專業版</div>
          <div className="tier-header">
            <h3>專業會員</h3>
            <div className="tier-price">
              <span className="price">NT$ 1,999</span>
              <span className="period">/月</span>
            </div>
            <div className="tier-save">🏆 專業投資者首選</div>
          </div>
          <div className="tier-features">
            <ul>
              <li><span className="icon">♾️</span> 無限次AI分析</li>
              <li><span className="icon">🎯</span> 所有進階功能</li>
              <li><span className="icon">⚡</span> 即時數據推送</li>
              <li><span className="icon">📊</span> 高級圖表工具</li>
              <li><span className="icon">🤖</span> 個人專屬AI顧問</li>
              <li><span className="icon">⭐</span> 優先客服支援</li>
              <li><span className="icon">🔔</span> 智能多元警報</li>
              <li><span className="icon">📈</span> 深度市場分析</li>
              <li><span className="icon">👨‍💼</span> 專屬分析師諮詢</li>
            </ul>
          </div>
          <button 
            type="button" 
            className="tier-select-btn diamond-btn"
            onClick={() => handleTierSelection('diamond')}
          >
            unlock專業功能
          </button>
        </div>
      </div>
      
      <div className="auth-footer">
        <p>
          已有帳戶？
          <button
            type="button"
            className="link-button"
            onClick={() => setMode('login')}
          >
            立即登入
          </button>
        </p>
      </div>
    </div>
  );

  return (
    <div className="authentication-page">
      <div className="auth-container">
        <div className="auth-left">
          <div className="auth-brand">
            <div className="brand-logo">
              <span className="logo-icon">🤖</span>
              <span className="logo-text">TradingAgents</span>
            </div>
            <h2>AI 驅動的智能投資分析</h2>
            <ul className="feature-list">
              <li>🌍 台股與國際市場同業比較</li>
              <li>🤖 7位專業AI分析師團隊</li>
              <li>📊 機構級數據分析工具</li>
              <li>💡 個人化投資建議</li>
              <li>🔒 銀行級安全保護</li>
            </ul>
          </div>
        </div>
        
        <div className="auth-right">
          {error && (
            <div className="alert alert-error">
              <span className="alert-icon">⚠️</span>
              {error}
            </div>
          )}
          
          {success && (
            <div className="alert alert-success">
              <span className="alert-icon">✅</span>
              {success}
            </div>
          )}
          
          {mode === 'login' && renderLoginForm()}
          {mode === 'register' && renderRegisterForm()}
          {mode === 'forgot' && renderForgotPasswordForm()}
          {mode === 'tier-selection' && renderTierSelectionForm()}
        </div>
      </div>
    </div>
  );
};

export default AuthenticationPage;