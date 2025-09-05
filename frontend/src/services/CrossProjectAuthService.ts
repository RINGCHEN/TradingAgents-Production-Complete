/**
 * 跨專案認證同步服務
 * 處理 tradingagents-main 和 twstock-admin-466914 之間的認證同步
 */

export interface CrossProjectAuthData {
  token: string;
  user: {
    id: string;
    name: string;
    email: string;
    tier: string;
    authMethod: string;
  };
  expiresAt: string;
  projectId: string;
}

export class CrossProjectAuthService {
  private static instance: CrossProjectAuthService;
  private readonly AUTH_STORAGE_KEY = 'cross_project_auth';
  private readonly TOKEN_STORAGE_KEY = 'cross_project_token';

  private constructor() {}

  public static getInstance(): CrossProjectAuthService {
    if (!CrossProjectAuthService.instance) {
      CrossProjectAuthService.instance = new CrossProjectAuthService();
    }
    return CrossProjectAuthService.instance;
  }

  /**
   * 同步認證狀態到其他專案
   */
  public syncAuthToProjects(authData: CrossProjectAuthData): void {
    try {
      // 儲存到 localStorage 供其他專案讀取
      localStorage.setItem(this.AUTH_STORAGE_KEY, JSON.stringify(authData));
      localStorage.setItem(this.TOKEN_STORAGE_KEY, authData.token);
      
      console.log('認證狀態已同步到跨專案儲存');
    } catch (error) {
      console.error('跨專案認證同步失敗:', error);
    }
  }

  /**
   * 從其他專案獲取認證狀態
   */
  public getAuthFromProjects(): CrossProjectAuthData | null {
    try {
      const authDataStr = localStorage.getItem(this.AUTH_STORAGE_KEY);
      if (!authDataStr) {
        return null;
      }

      const authData: CrossProjectAuthData = JSON.parse(authDataStr);
      
      // 檢查是否過期
      if (new Date(authData.expiresAt) < new Date()) {
        this.clearCrossProjectAuth();
        return null;
      }

      return authData;
    } catch (error) {
      console.error('讀取跨專案認證狀態失敗:', error);
      return null;
    }
  }

  /**
   * 驗證跨專案認證令牌
   */
  public async validateCrossProjectToken(token: string): Promise<boolean> {
    try {
      // 這裡應該調用主系統的令牌驗證 API
      // 暫時使用本地驗證
      const storedToken = localStorage.getItem(this.TOKEN_STORAGE_KEY);
      return storedToken === token;
    } catch (error) {
      console.error('跨專案令牌驗證失敗:', error);
      return false;
    }
  }

  /**
   * 清除跨專案認證狀態
   */
  public clearCrossProjectAuth(): void {
    localStorage.removeItem(this.AUTH_STORAGE_KEY);
    localStorage.removeItem(this.TOKEN_STORAGE_KEY);
    console.log('跨專案認證狀態已清除');
  }

  /**
   * 檢查當前用戶是否有管理員權限
   */
  public hasAdminAccess(): boolean {
    const authData = this.getAuthFromProjects();
    if (!authData) {
      return false;
    }

    // 檢查用戶等級或特定權限
    return authData.user.tier === 'diamond' || 
           authData.user.email.includes('@admin') ||
           authData.user.tier === 'admin';
  }

  /**
   * 生成跨專案訪問 URL
   */
  public generateCrossProjectUrl(targetProject: 'admin' | 'main', path: string = '/'): string {
    const authData = this.getAuthFromProjects();
    if (!authData) {
      return path;
    }

    const baseUrls = {
      admin: 'https://twstock-admin-466914.web.app',
      main: 'https://03king.web.app'
    };

    const baseUrl = baseUrls[targetProject];
    const params = new URLSearchParams({
      auth_token: authData.token,
      redirect: path
    });

    return `${baseUrl}${path}?${params.toString()}`;
  }

  /**
   * 處理從 URL 參數中的認證信息
   */
  public handleAuthFromUrl(): boolean {
    try {
      const params = new URLSearchParams(window.location.search);
      const authToken = params.get('auth_token');
      
      if (authToken) {
        // 驗證令牌並設置認證狀態
        const isValid = this.validateCrossProjectToken(authToken);
        if (isValid) {
          console.log('從 URL 參數恢復跨專案認證狀態');
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('處理 URL 認證參數失敗:', error);
      return false;
    }
  }

  /**
   * 創建跨專案認證數據
   */
  public createCrossProjectAuth(userInfo: any, authMethod: string): CrossProjectAuthData {
    const token = `cross_project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(); // 24小時後過期

    return {
      token,
      user: {
        id: userInfo.id,
        name: userInfo.name,
        email: userInfo.email,
        tier: userInfo.tier || 'free',
        authMethod
      },
      expiresAt,
      projectId: 'tradingagents-main'
    };
  }
}

// 導出單例實例
export const crossProjectAuthService = CrossProjectAuthService.getInstance();