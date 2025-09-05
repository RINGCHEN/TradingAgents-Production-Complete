/**
 * Google OAuth 認證服務 - 使用新的 Google Identity Services
 * 解決 idpiframe_initialization_failed 問題
 * 
 * 遷移說明：
 * - 從舊的 gapi.auth2 遷移到新的 Google Identity Services
 * - 符合 Google 最新認證標準
 * - 提供完整的錯誤處理和診斷功能
 */

interface GoogleUser {
  id: string;
  email: string;
  name: string;
  picture: string;
  verified_email: boolean;
}

interface GoogleAuthResponse {
  credential: string;
  select_by: string;
}

interface GoogleAuthError {
  type: string;
  message: string;
  details?: any;
}

class GoogleAuthService {
  private clientId: string;
  private isInitialized: boolean = false;
  private currentUser: GoogleUser | null = null;
  private onSignInCallback: ((user: GoogleUser) => void) | null = null;
  private onSignOutCallback: (() => void) | null = null;

  constructor() {
    this.clientId = '351731559902-11g45sv5947cr3q89lhkar272kfeiput.apps.googleusercontent.com';
  }

  /**
   * 初始化 Google Identity Services
   */
  async initialize(): Promise<void> {
    try {
      console.log('🔧 初始化 Google Identity Services...');
      console.log(`Client ID: ${this.clientId}`);
      
      // 檢查是否已經初始化
      if (this.isInitialized) {
        console.log('✅ Google Auth 已經初始化');
        return;
      }

      // 載入 Google Identity Services 腳本
      await this.loadGoogleIdentityScript();

      // 初始化 Google Identity Services
      if (window.google && window.google.accounts) {
        this.initializeGoogleIdentity();
        this.isInitialized = true;
        console.log('✅ Google Identity Services 初始化成功');
      } else {
        throw new Error('Google Identity Services 載入失敗');
      }

    } catch (error) {
      console.error('❌ Google Auth 初始化失敗:', error);
      this.handleAuthError({
        type: 'initialization_failed',
        message: 'Google 認證服務初始化失敗',
        details: error
      });
      throw error;
    }
  }

  /**
   * 載入 Google Identity Services 腳本
   */
  private loadGoogleIdentityScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 檢查是否已經載入
      if (window.google && window.google.accounts) {
        resolve();
        return;
      }

      // 檢查是否已經有腳本標籤
      const existingScript = document.querySelector('script[src*="accounts.google.com"]');
      if (existingScript) {
        existingScript.addEventListener('load', () => resolve());
        existingScript.addEventListener('error', () => reject(new Error('腳本載入失敗')));
        return;
      }

      // 創建新的腳本標籤
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      
      script.onload = () => {
        console.log('✅ Google Identity Services 腳本載入成功');
        // 等待一小段時間確保 API 完全載入
        setTimeout(() => resolve(), 100);
      };
      
      script.onerror = () => {
        console.error('❌ Google Identity Services 腳本載入失敗');
        reject(new Error('Google Identity Services 腳本載入失敗'));
      };

      document.head.appendChild(script);
    });
  }

  /**
   * 初始化 Google Identity Services
   */
  private initializeGoogleIdentity(): void {
    try {
      // 初始化 Google Identity Services
      window.google.accounts.id.initialize({
        client_id: this.clientId,
        callback: this.handleCredentialResponse.bind(this),
        auto_select: false,
        cancel_on_tap_outside: true,
        context: 'signin',
        ux_mode: 'popup',
        use_fedcm_for_prompt: false
      });

      console.log('✅ Google Identity Services 配置完成');
    } catch (error) {
      console.error('❌ Google Identity Services 配置失敗:', error);
      throw error;
    }
  }

  /**
   * 處理 Google 認證響應
   */
  private async handleCredentialResponse(response: GoogleAuthResponse): Promise<void> {
    try {
      console.log('🔐 處理 Google 認證響應...');
      
      // 解析 JWT token
      const userInfo = this.parseJwtToken(response.credential);
      
      if (userInfo) {
        this.currentUser = {
          id: userInfo.sub,
          email: userInfo.email,
          name: userInfo.name,
          picture: userInfo.picture,
          verified_email: userInfo.email_verified
        };

        console.log('✅ 用戶認證成功:', this.currentUser.email);
        
        // 將用戶資料發送到後端進行註冊/登入
        await this.registerUserWithBackend(response.credential, this.currentUser);
        
        // 保存認證狀態
        this.saveAuthState();
        
        // 觸發登入回調
        if (this.onSignInCallback) {
          this.onSignInCallback(this.currentUser);
        }
      } else {
        throw new Error('無法解析用戶信息');
      }
    } catch (error) {
      console.error('❌ 處理認證響應失敗:', error);
      this.handleAuthError({
        type: 'credential_processing_failed',
        message: '處理認證響應失敗',
        details: error
      });
    }
  }

  /**
   * 解析 JWT token
   */
  private parseJwtToken(token: string): any {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('❌ JWT token 解析失敗:', error);
      return null;
    }
  }

  /**
   * 顯示登入按鈕
   */
  renderSignInButton(element: HTMLElement, options?: any): void {
    if (!this.isInitialized) {
      console.error('❌ Google Auth 尚未初始化');
      return;
    }

    try {
      window.google.accounts.id.renderButton(element, {
        theme: options?.theme || 'outline',
        size: options?.size || 'large',
        type: options?.type || 'standard',
        shape: options?.shape || 'rectangular',
        text: options?.text || 'signin_with',
        logo_alignment: options?.logo_alignment || 'left',
        width: options?.width || 250,
        locale: options?.locale || 'zh_TW'
      });
      
      console.log('✅ Google 登入按鈕渲染成功');
    } catch (error) {
      console.error('❌ 渲染登入按鈕失敗:', error);
      this.handleAuthError({
        type: 'button_render_failed',
        message: '渲染登入按鈕失敗',
        details: error
      });
    }
  }

  /**
   * 程式化觸發登入
   */
  async signIn(): Promise<GoogleUser | null> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      try {
        // 設定臨時回調
        const originalCallback = this.onSignInCallback;
        this.onSignInCallback = (user: GoogleUser) => {
          this.onSignInCallback = originalCallback;
          resolve(user);
        };

        // 觸發登入流程
        window.google.accounts.id.prompt((notification: any) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            console.log('🔔 Google 登入提示被跳過或未顯示');
            // 恢復原始回調
            this.onSignInCallback = originalCallback;
            resolve(null);
          }
        });
      } catch (error) {
        console.error('❌ 觸發登入失敗:', error);
        reject(error);
      }
    });
  }

  /**
   * 登出
   */
  async signOut(): Promise<void> {
    try {
      if (this.currentUser) {
        // 撤銷 Google 認證
        if (window.google && window.google.accounts) {
          window.google.accounts.id.disableAutoSelect();
        }

        // 清除本地狀態
        this.currentUser = null;
        this.clearAuthState();

        console.log('✅ 用戶登出成功');

        // 觸發登出回調
        if (this.onSignOutCallback) {
          this.onSignOutCallback();
        }
      }
    } catch (error) {
      console.error('❌ 登出失敗:', error);
      this.handleAuthError({
        type: 'signout_failed',
        message: '登出失敗',
        details: error
      });
    }
  }

  /**
   * 獲取當前用戶
   */
  getCurrentUser(): GoogleUser | null {
    return this.currentUser;
  }

  /**
   * 檢查是否已登入
   */
  isSignedIn(): boolean {
    return this.currentUser !== null;
  }

  /**
   * 設定登入回調
   */
  onSignIn(callback: (user: GoogleUser) => void): void {
    this.onSignInCallback = callback;
  }

  /**
   * 設定登出回調
   */
  onSignOut(callback: () => void): void {
    this.onSignOutCallback = callback;
  }

  /**
   * 保存認證狀態到 localStorage
   */
  private saveAuthState(): void {
    if (this.currentUser) {
      try {
        localStorage.setItem('google_auth_user', JSON.stringify(this.currentUser));
        localStorage.setItem('google_auth_timestamp', Date.now().toString());
        console.log('✅ 認證狀態已保存');
      } catch (error) {
        console.error('❌ 保存認證狀態失敗:', error);
      }
    }
  }

  /**
   * 從 localStorage 恢復認證狀態
   */
  async restoreAuthState(): Promise<GoogleUser | null> {
    try {
      const userStr = localStorage.getItem('google_auth_user');
      const timestampStr = localStorage.getItem('google_auth_timestamp');

      if (userStr && timestampStr) {
        const timestamp = parseInt(timestampStr);
        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000; // 24小時

        // 檢查是否過期（24小時）
        if (now - timestamp < oneDay) {
          this.currentUser = JSON.parse(userStr);
          console.log('✅ 認證狀態已恢復:', this.currentUser.email);
          return this.currentUser;
        } else {
          console.log('⏰ 認證狀態已過期，清除本地數據');
          this.clearAuthState();
        }
      }
    } catch (error) {
      console.error('❌ 恢復認證狀態失敗:', error);
      this.clearAuthState();
    }
    return null;
  }

  /**
   * 將用戶資料發送到後端進行註冊/登入
   */
  private async registerUserWithBackend(googleToken: string, user: GoogleUser): Promise<void> {
    try {
      console.log('🔄 將用戶資料發送到後端...');
      
      // 根據當前環境決定 API 基礎 URL
      const currentHost = window.location.hostname;
      let apiBaseUrl: string;
      
      if (currentHost.includes('localhost') || currentHost.includes('127.0.0.1')) {
        apiBaseUrl = 'http://localhost:8001';
      } else if (currentHost.includes('03king.com')) {
        apiBaseUrl = 'https://tradingagents-main-351731559902.asia-east1.run.app';
      } else {
        apiBaseUrl = 'https://tradingagents-main-351731559902.asia-east1.run.app';
      }
      
      // 設定超時機制
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超時

      const response = await fetch(`${apiBaseUrl}/api/auth/google-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          google_token: googleToken,
          name: user.name,
          email: user.email,
          picture: user.picture
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId); // 清除超時定時器

      if (!response.ok) {
        throw new Error(`後端 API 錯誤: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        console.log('✅ 用戶資料已成功同步到後端');
        console.log(`用戶ID: ${result.user_id}, 新用戶: ${result.is_new_user ? '是' : '否'}`);
        
        // 儲存後端返回的用戶資訊和 access token
        localStorage.setItem('backend_access_token', result.access_token);
        localStorage.setItem('backend_user_id', result.user_id.toString());
        
        // 更新用戶對象，加入後端資訊
        this.currentUser = {
          ...this.currentUser,
          backendUserId: result.user_id,
          accessToken: result.access_token,
          isNewUser: result.is_new_user
        } as GoogleUser & { backendUserId: number; accessToken: string; isNewUser: boolean };
        
      } else {
        throw new Error(result.message || '後端註冊失敗');
      }
      
    } catch (error) {
      console.error('❌ 後端用戶註冊失敗:', error);
      
      // 檢查是否是超時錯誤
      if (error instanceof Error && error.name === 'AbortError') {
        console.warn('⚠️ 後端連接超時，用戶將以前端模式登入');
      } else {
        console.warn('⚠️ 後端API錯誤，用戶將以前端模式登入，部分功能可能受限');
      }
      
      // 儲存基本的前端認證狀態
      localStorage.setItem('frontend_google_auth', 'true');
      localStorage.setItem('frontend_user_email', user.email);
      localStorage.setItem('frontend_user_name', user.name);
    }
  }

  /**
   * 清除認證狀態
   */
  private clearAuthState(): void {
    try {
      localStorage.removeItem('google_auth_user');
      localStorage.removeItem('google_auth_timestamp');
      console.log('✅ 認證狀態已清除');
    } catch (error) {
      console.error('❌ 清除認證狀態失敗:', error);
    }
  }

  /**
   * 處理認證錯誤
   */
  private handleAuthError(error: GoogleAuthError): void {
    console.error('🚨 Google Auth 錯誤:', error);
    
    // 可以在這裡添加錯誤報告邏輯
    // 例如發送到錯誤追蹤服務
    
    // 觸發自定義錯誤事件
    const errorEvent = new CustomEvent('google-auth-error', {
      detail: error
    });
    window.dispatchEvent(errorEvent);
  }

  /**
   * 診斷功能 - 檢查系統狀態
   */
  async diagnose(): Promise<any> {
    const diagnosis = {
      timestamp: new Date().toISOString(),
      clientId: this.clientId,
      isInitialized: this.isInitialized,
      currentUser: this.currentUser ? {
        email: this.currentUser.email,
        name: this.currentUser.name
      } : null,
      googleApiAvailable: !!(window.google && window.google.accounts),
      localStorageAvailable: this.checkLocalStorageAvailable(),
      domain: window.location.hostname,
      userAgent: navigator.userAgent
    };

    console.log('🔍 Google Auth 診斷結果:', diagnosis);
    return diagnosis;
  }

  /**
   * 檢查 localStorage 是否可用
   */
  private checkLocalStorageAvailable(): boolean {
    try {
      const test = '__localStorage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (error) {
      return false;
    }
  }
}

// 全域實例
const googleAuthService = new GoogleAuthService();

// 擴展 Window 介面以支援 Google Identity Services
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, options: any) => void;
          prompt: (callback?: (notification: any) => void) => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}

export default googleAuthService;
export { googleAuthService };
export type { GoogleUser, GoogleAuthError };