/**
 * AuthStateManager - 認證狀態管理器
 * 安全處理認證狀態初始化，實施認證錯誤容錯處理和訪客模式降級
 * 修復認證狀態初始化時的JavaScript錯誤
 */

import { reportComponentError } from './ErrorDiagnostics';
import { AuthErrorHandler, AUTH_ERROR_TYPES } from './AuthErrors';

export interface AuthState {
  isInitialized: boolean;
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
  error: AuthError | null;
  mode: 'authenticated' | 'guest' | 'error' | 'initializing';
  lastInitAttempt: Date | null;
  initAttempts: number;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  tier: 'free' | 'gold' | 'diamond';
  membershipStatus?: MembershipStatus;
  analysisCount?: number;
  analysisLimit?: number;
}

export interface MembershipStatus {
  tier: 'free' | 'gold' | 'diamond';
  analysisCount: number;
  analysisLimit: number;
  expiresAt?: Date;
  isActive: boolean;
}

export interface AuthError {
  type: 'network' | 'token' | 'server' | 'validation' | 'initialization' | 'unknown';
  message: string;
  code?: string;
  timestamp: Date;
  recoverable: boolean;
}

export interface AuthInitOptions {
  enableGuestMode: boolean;
  maxInitAttempts: number;
  initTimeout: number;
  enableAutoRecovery: boolean;
  fallbackToGuest: boolean;
  persistState: boolean;
}

export class AuthStateManager {
  private static instance: AuthStateManager;
  private state: AuthState;
  private options: AuthInitOptions;
  private initPromise: Promise<void> | null = null;
  private recoveryTimeoutId: NodeJS.Timeout | null = null;

  private constructor(options: Partial<AuthInitOptions> = {}) {
    this.options = {
      enableGuestMode: true,
      maxInitAttempts: 3,
      initTimeout: 10000,
      enableAutoRecovery: true,
      fallbackToGuest: true,
      persistState: true,
      ...options
    };

    this.state = {
      isInitialized: false,
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,
      mode: 'initializing',
      lastInitAttempt: null,
      initAttempts: 0
    };

    this.initializeEventListeners();
  }

  public static getInstance(options?: Partial<AuthInitOptions>): AuthStateManager {
    if (!AuthStateManager.instance) {
      AuthStateManager.instance = new AuthStateManager(options);
    }
    return AuthStateManager.instance;
  }

  /**
   * 初始化認證狀態
   */
  public async initialize(): Promise<AuthState> {
    // 防止重複初始化
    if (this.initPromise) {
      await this.initPromise;
      return this.state;
    }

    this.initPromise = this.performInitialization();
    
    try {
      await this.initPromise;
    } catch (error) {
      console.error('Auth initialization failed:', error);
    } finally {
      this.initPromise = null;
    }

    return this.state;
  }

  /**
   * 執行初始化邏輯
   */
  private async performInitialization(): Promise<void> {
    this.updateState({
      isLoading: true,
      mode: 'initializing',
      lastInitAttempt: new Date(),
      initAttempts: this.state.initAttempts + 1
    });

    try {
      // 步驟1: 檢查localStorage中的認證數據
      const storedAuth = await this.loadStoredAuthState();
      
      // 步驟2: 驗證存儲的認證數據
      if (storedAuth) {
        const validationResult = await this.validateStoredAuth(storedAuth);
        if (validationResult.isValid) {
          await this.setAuthenticatedState(validationResult.user!);
          return;
        }
      }

      // 步驟3: 嘗試自動登錄（如果有refresh token）
      const autoLoginResult = await this.attemptAutoLogin();
      if (autoLoginResult.success) {
        await this.setAuthenticatedState(autoLoginResult.user!);
        return;
      }

      // 步驟4: 降級到訪客模式
      if (this.options.fallbackToGuest) {
        await this.setGuestMode();
      } else {
        throw new Error('Authentication required but fallback to guest mode is disabled');
      }

    } catch (error) {
      await this.handleInitializationError(error);
    }
  }

  /**
   * 載入存儲的認證狀態
   */
  private async loadStoredAuthState(): Promise<any | null> {
    try {
      if (!this.options.persistState) {
        return null;
      }

      const authToken = this.safeGetLocalStorage('authToken');
      const userInfo = this.safeGetLocalStorage('userInfo');
      const refreshToken = this.safeGetLocalStorage('refreshToken');

      if (!authToken && !refreshToken) {
        return null;
      }

      // 檢查數據完整性
      if (authToken && this.isValidToken(authToken)) {
        return {
          token: authToken,
          user: userInfo ? this.safeParseJSON(userInfo) : null,
          refreshToken
        };
      }

      return null;
    } catch (error) {
      this.reportError('initialization', 'Failed to load stored auth state', error);
      return null;
    }
  }

  /**
   * 安全獲取localStorage數據
   */
  private safeGetLocalStorage(key: string): string | null {
    try {
      const value = localStorage.getItem(key);
      
      // 檢查是否是HTML內容（常見的錯誤情況）
      if (value && (value.includes('<html') || value.includes('<!DOCTYPE'))) {
        console.warn(`Corrupted localStorage detected for key: ${key}`);
        localStorage.removeItem(key);
        return null;
      }

      return value;
    } catch (error) {
      console.error(`Error accessing localStorage for key ${key}:`, error);
      return null;
    }
  }

  /**
   * 安全解析JSON
   */
  private safeParseJSON(jsonString: string): any | null {
    try {
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Failed to parse JSON:', error);
      return null;
    }
  }

  /**
   * 驗證token有效性
   */
  private isValidToken(token: string): boolean {
    try {
      // 基本格式檢查
      if (!token || typeof token !== 'string') {
        return false;
      }

      // 檢查是否是JWT格式
      const parts = token.split('.');
      if (parts.length !== 3) {
        return false;
      }

      // 檢查是否過期（簡單檢查）
      const payload = this.safeParseJSON(atob(parts[1]));
      if (payload && payload.exp) {
        const now = Math.floor(Date.now() / 1000);
        return payload.exp > now;
      }

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 驗證存儲的認證數據
   */
  private async validateStoredAuth(storedAuth: any): Promise<{ isValid: boolean; user?: AuthUser }> {
    try {
      // 驗證token
      if (!this.isValidToken(storedAuth.token)) {
        return { isValid: false };
      }

      // 驗證用戶信息
      if (!storedAuth.user || !storedAuth.user.id) {
        return { isValid: false };
      }

      // 可以在這裡添加服務器端驗證
      // const serverValidation = await this.validateWithServer(storedAuth.token);

      return {
        isValid: true,
        user: this.normalizeUser(storedAuth.user)
      };
    } catch (error) {
      this.reportError('validation', 'Failed to validate stored auth', error);
      return { isValid: false };
    }
  }

  /**
   * 嘗試自動登錄
   */
  private async attemptAutoLogin(): Promise<{ success: boolean; user?: AuthUser }> {
    try {
      const refreshToken = this.safeGetLocalStorage('refreshToken');
      if (!refreshToken) {
        return { success: false };
      }

      // 這裡應該調用實際的refresh token API
      // const response = await authAPI.refreshToken(refreshToken);
      
      // 模擬自動登錄邏輯
      console.log('Attempting auto-login with refresh token...');
      
      // 暫時返回失敗，實際實現時需要調用API
      return { success: false };
    } catch (error) {
      this.reportError('token', 'Auto-login failed', error);
      return { success: false };
    }
  }

  /**
   * 設置認證狀態
   */
  private async setAuthenticatedState(user: AuthUser): Promise<void> {
    const normalizedUser = this.normalizeUser(user);
    
    this.updateState({
      isInitialized: true,
      isAuthenticated: true,
      isLoading: false,
      user: normalizedUser,
      error: null,
      mode: 'authenticated'
    });

    // 持久化狀態
    if (this.options.persistState) {
      this.persistAuthState(normalizedUser);
    }

    console.log('Authentication state set successfully');
  }

  /**
   * 設置訪客模式
   */
  private async setGuestMode(): Promise<void> {
    this.updateState({
      isInitialized: true,
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,
      mode: 'guest'
    });

    console.log('Switched to guest mode');
  }

  /**
   * 處理初始化錯誤
   */
  private async handleInitializationError(error: any): Promise<void> {
    // 使用增強的錯誤處理
    const errorInfo = AuthErrorHandler.handleAuthError(error);
    const recoveryStrategy = AuthErrorHandler.getRecoveryStrategy(errorInfo);

    const authError: AuthError = {
      type: errorInfo.type,
      message: errorInfo.message,
      code: errorInfo.code,
      timestamp: errorInfo.timestamp,
      recoverable: errorInfo.recoverable
    };

    this.updateState({
      isInitialized: false,
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: authError,
      mode: 'error'
    });

    // 報告錯誤
    this.reportError(authError.type, authError.message, error);

    // 根據恢復策略決定下一步行動
    if (recoveryStrategy.canAutoRecover && this.options.enableAutoRecovery) {
      this.scheduleRecovery(recoveryStrategy.retryDelay);
    } else if (recoveryStrategy.fallbackAction === 'switch-to-guest' && this.options.fallbackToGuest) {
      await this.setGuestMode();
    } else if (recoveryStrategy.fallbackAction === 'force-logout') {
      await this.logout();
    }
  }



  /**
   * 安排恢復嘗試
   */
  private scheduleRecovery(customDelay?: number): void {
    if (this.recoveryTimeoutId) {
      clearTimeout(this.recoveryTimeoutId);
    }

    // 使用自定義延遲或指數退避策略
    const delay = customDelay || Math.min(1000 * Math.pow(2, this.state.initAttempts), 30000);

    this.recoveryTimeoutId = setTimeout(async () => {
      if (this.state.initAttempts < this.options.maxInitAttempts) {
        console.log(`Attempting auth recovery (attempt ${this.state.initAttempts + 1})`);
        await this.initialize();
      } else {
        console.log('Max recovery attempts reached, falling back to guest mode');
        if (this.options.fallbackToGuest) {
          await this.setGuestMode();
        }
      }
    }, delay);
  }

  /**
   * 標準化用戶數據
   */
  private normalizeUser(user: any): AuthUser {
    return {
      id: user.id || '',
      name: user.name || '',
      email: user.email || '',
      tier: user.tier || 'free',
      membershipStatus: user.membershipStatus || {
        tier: user.tier || 'free',
        analysisCount: user.analysisCount || 0,
        analysisLimit: this.getAnalysisLimit(user.tier || 'free'),
        isActive: true
      },
      analysisCount: user.analysisCount || 0,
      analysisLimit: user.analysisLimit || this.getAnalysisLimit(user.tier || 'free')
    };
  }

  /**
   * 獲取分析限制
   */
  private getAnalysisLimit(tier: string): number {
    switch (tier) {
      case 'free': return 5;
      case 'gold': return 50;
      case 'diamond': return 999;
      default: return 5;
    }
  }

  /**
   * 持久化認證狀態
   */
  private persistAuthState(user: AuthUser): void {
    try {
      if (this.options.persistState) {
        localStorage.setItem('userInfo', JSON.stringify(user));
        localStorage.setItem('authInitialized', 'true');
      }
    } catch (error) {
      console.error('Failed to persist auth state:', error);
    }
  }

  /**
   * 更新狀態
   */
  private updateState(updates: Partial<AuthState>): void {
    this.state = { ...this.state, ...updates };
    this.notifyStateChange();
  }

  /**
   * 通知狀態變化
   */
  private notifyStateChange(): void {
    // 發送自定義事件
    window.dispatchEvent(new CustomEvent('auth-state-change', {
      detail: this.state
    }));
  }

  /**
   * 初始化事件監聽器
   */
  private initializeEventListeners(): void {
    // 監聽存儲變化
    window.addEventListener('storage', (event) => {
      if (event.key === 'authToken' || event.key === 'userInfo') {
        this.handleStorageChange(event);
      }
    });

    // 監聽頁面可見性變化
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.state.mode === 'error') {
        this.initialize();
      }
    });

    // 監聽網路狀態變化
    window.addEventListener('online', () => {
      if (this.state.mode === 'error' && this.state.error?.type === 'network') {
        this.initialize();
      }
    });
  }

  /**
   * 處理存儲變化
   */
  private handleStorageChange(event: StorageEvent): void {
    if (event.newValue === null) {
      // 認證數據被清除
      this.logout();
    }
  }

  /**
   * 登錄
   */
  public async login(credentials: any): Promise<{ success: boolean; error?: AuthError }> {
    try {
      this.updateState({ isLoading: true });

      // 驗證輸入
      if (!credentials || !credentials.email) {
        throw new Error('Email is required');
      }

      // 這裡應該調用實際的登錄API
      // const response = await authAPI.login(credentials);

      // 模擬登錄邏輯
      if (credentials.email === 'error@test.com') {
        throw new Error('Invalid credentials');
      }

      const mockUser: AuthUser = {
        id: '1',
        name: credentials.name || '測試用戶',
        email: credentials.email,
        tier: 'free',
        analysisCount: 0,
        analysisLimit: 5
      };

      await this.setAuthenticatedState(mockUser);
      return { success: true };

    } catch (error) {
      const errorInfo = AuthErrorHandler.handleAuthError(error);
      
      const authError: AuthError = {
        type: errorInfo.type,
        message: errorInfo.message,
        code: errorInfo.code,
        timestamp: errorInfo.timestamp,
        recoverable: errorInfo.recoverable
      };

      this.updateState({
        isLoading: false,
        error: authError
      });

      this.reportError('login', authError.message, error);

      return { success: false, error: authError };
    }
  }

  /**
   * 登出
   */
  public async logout(): Promise<void> {
    try {
      // 清理存儲的數據
      if (this.options.persistState) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('authInitialized');
      }

      // 清理定時器
      if (this.recoveryTimeoutId) {
        clearTimeout(this.recoveryTimeoutId);
        this.recoveryTimeoutId = null;
      }

      // 重置狀態
      this.updateState({
        isInitialized: true,
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null,
        mode: 'guest',
        initAttempts: 0
      });

      console.log('Logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  /**
   * 獲取當前狀態
   */
  public getState(): AuthState {
    return { ...this.state };
  }

  /**
   * 檢查是否已初始化
   */
  public isInitialized(): boolean {
    return this.state.isInitialized;
  }

  /**
   * 檢查是否已認證
   */
  public isAuthenticated(): boolean {
    return this.state.isAuthenticated;
  }

  /**
   * 獲取當前用戶
   */
  public getCurrentUser(): AuthUser | null {
    return this.state.user;
  }

  /**
   * 強制重新初始化
   */
  public async forceReinitialize(): Promise<AuthState> {
    this.state.initAttempts = 0;
    this.state.isInitialized = false;
    return await this.initialize();
  }

  /**
   * 報告錯誤
   */
  private reportError(type: string, message: string, error: any): void {
    try {
      reportComponentError('auth', `AuthStateManager ${type}: ${message}`, {
        type,
        error: error?.message || String(error),
        stack: error?.stack,
        state: this.state
      });
    } catch (reportingError) {
      console.error('Failed to report auth error:', reportingError);
      console.error('Original error:', error);
    }
  }

  /**
   * 清理資源
   */
  public cleanup(): void {
    if (this.recoveryTimeoutId) {
      clearTimeout(this.recoveryTimeoutId);
      this.recoveryTimeoutId = null;
    }
  }
}

// 導出單例實例
export const authStateManager = AuthStateManager.getInstance();

// 便利函數
export const initializeAuth = (options?: Partial<AuthInitOptions>) => {
  return AuthStateManager.getInstance(options).initialize();
};

export const getAuthState = () => {
  return authStateManager.getState();
};

export const isAuthInitialized = () => {
  return authStateManager.isInitialized();
};

export default AuthStateManager;