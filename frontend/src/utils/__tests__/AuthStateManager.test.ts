/**
 * AuthStateManager 測試
 * 測試認證狀態管理器的各種功能和錯誤處理
 */

import { AuthStateManager, AuthState, AuthUser } from '../AuthStateManager';
import { AuthErrorHandler } from '../AuthErrors';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock reportComponentError
jest.mock('../ErrorDiagnostics', () => ({
  reportComponentError: jest.fn()
}));

describe('AuthStateManager', () => {
  let authManager: AuthStateManager;

  beforeEach(() => {
    // 重置所有mock
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    
    // 由於是單例模式，我們需要重置狀態
    authManager = AuthStateManager.getInstance({
      enableGuestMode: true,
      maxInitAttempts: 3,
      initTimeout: 5000,
      enableAutoRecovery: true,
      fallbackToGuest: true,
      persistState: true
    });
    
    // 強制重新初始化以重置狀態
    authManager.cleanup();
  });

  afterEach(() => {
    // 清理資源
    authManager.cleanup();
  });

  describe('初始化', () => {
    test('應該成功初始化到訪客模式', async () => {
      const state = await authManager.initialize();
      
      expect(state.isInitialized).toBe(true);
      expect(state.isAuthenticated).toBe(false);
      expect(state.mode).toBe('guest');
      expect(state.error).toBeNull();
    });

    test('應該從localStorage恢復認證狀態', async () => {
      // 模擬有效的存儲數據
      const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.Lp-38GKDuZu9rhM6KvJDIZ_5Vr0GceVlEz2B9VOpBU4';
      const mockUser = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        tier: 'free'
      };

      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'authToken') return mockToken;
        if (key === 'userInfo') return JSON.stringify(mockUser);
        return null;
      });

      const state = await authManager.initialize();
      
      expect(state.isInitialized).toBe(true);
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toMatchObject(mockUser);
      expect(state.mode).toBe('authenticated');
    });

    test('應該處理損壞的localStorage數據', async () => {
      // 模擬損壞的數據
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'authToken') return '<html>Error page</html>';
        if (key === 'userInfo') return 'invalid json';
        return null;
      });

      const state = await authManager.initialize();
      
      expect(state.isInitialized).toBe(true);
      expect(state.isAuthenticated).toBe(false);
      expect(state.mode).toBe('guest');
    });

    test('應該處理初始化錯誤', async () => {
      // 模擬localStorage錯誤
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage access denied');
      });

      const state = await authManager.initialize();
      
      // 應該降級到訪客模式
      expect(state.isInitialized).toBe(true);
      expect(state.mode).toBe('guest');
    });
  });

  describe('登錄功能', () => {
    test('應該成功登錄', async () => {
      const credentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      const result = await authManager.login(credentials);
      
      expect(result.success).toBe(true);
      expect(result.error).toBeUndefined();
      
      const state = authManager.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.user?.email).toBe(credentials.email);
    });

    test('應該處理登錄失敗', async () => {
      const credentials = {
        email: 'error@test.com',
        password: 'wrongpassword'
      };

      const result = await authManager.login(credentials);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.error?.type).toBe('validation');
    });

    test('應該驗證必要的登錄字段', async () => {
      const result = await authManager.login({});
      
      expect(result.success).toBe(false);
      expect(result.error?.message).toContain('Email is required');
    });
  });

  describe('登出功能', () => {
    test('應該成功登出', async () => {
      // 先登錄
      await authManager.login({
        email: 'test@example.com',
        password: 'password123'
      });

      // 然後登出
      await authManager.logout();
      
      const state = authManager.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.mode).toBe('guest');
      
      // 驗證localStorage被清理
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('authToken');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userInfo');
    });
  });

  describe('狀態管理', () => {
    test('應該正確獲取當前狀態', () => {
      const state = authManager.getState();
      
      expect(state).toHaveProperty('isInitialized');
      expect(state).toHaveProperty('isAuthenticated');
      expect(state).toHaveProperty('isLoading');
      expect(state).toHaveProperty('user');
      expect(state).toHaveProperty('error');
      expect(state).toHaveProperty('mode');
    });

    test('應該正確檢查初始化狀態', async () => {
      // 由於單例模式，可能已經初始化過，所以我們先檢查當前狀態
      const initialState = authManager.isInitialized();
      
      await authManager.initialize();
      
      expect(authManager.isInitialized()).toBe(true);
    });

    test('應該正確檢查認證狀態', async () => {
      await authManager.initialize();
      expect(authManager.isAuthenticated()).toBe(false);
      
      await authManager.login({
        email: 'test@example.com',
        password: 'password123'
      });
      
      expect(authManager.isAuthenticated()).toBe(true);
    });
  });

  describe('錯誤處理', () => {
    test('應該正確分類網路錯誤', () => {
      const networkError = new Error('Network request failed');
      const errorInfo = AuthErrorHandler.handleAuthError(networkError);
      
      expect(errorInfo.type).toBe('network');
      expect(errorInfo.recoverable).toBe(true);
    });

    test('應該正確分類token錯誤', () => {
      const tokenError = { status: 401, message: 'Invalid token' };
      const errorInfo = AuthErrorHandler.handleAuthError(tokenError);
      
      expect(errorInfo.type).toBe('token');
      expect(errorInfo.recoverable).toBe(false);
    });

    test('應該提供恢復策略', () => {
      const networkError = new Error('Network timeout');
      const errorInfo = AuthErrorHandler.handleAuthError(networkError);
      const strategy = AuthErrorHandler.getRecoveryStrategy(errorInfo);
      
      expect(strategy.canAutoRecover).toBe(true);
      expect(strategy.maxRetries).toBeGreaterThan(0);
      expect(strategy.fallbackAction).toBe('switch-to-guest');
    });
  });

  describe('Token驗證', () => {
    test('應該驗證有效的JWT token', async () => {
      const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.Lp-38GKDuZu9rhM6KvJDIZ_5Vr0GceVlEz2B9VOpBU4';
      
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'authToken') return validToken;
        if (key === 'userInfo') return JSON.stringify({ id: '1', email: 'test@example.com' });
        return null;
      });

      const state = await authManager.initialize();
      expect(state.isAuthenticated).toBe(true);
    });

    test('應該拒絕無效的token', async () => {
      const invalidToken = 'invalid.token.format';
      
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'authToken') return invalidToken;
        return null;
      });

      const state = await authManager.initialize();
      expect(state.isAuthenticated).toBe(false);
      expect(state.mode).toBe('guest');
    });

    test('應該拒絕過期的token', async () => {
      // 創建一個過期的token (exp: 1516239022 是過去的時間)
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.4Adcj3UFYzPUVaVF43FmMab6RlaQD8A9V8wFzzht-KQ';
      
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'authToken') return expiredToken;
        return null;
      });

      const state = await authManager.initialize();
      expect(state.isAuthenticated).toBe(false);
      expect(state.mode).toBe('guest');
    });
  });

  describe('事件處理', () => {
    test('應該發送狀態變化事件', async () => {
      const eventListener = jest.fn();
      window.addEventListener('auth-state-change', eventListener);

      await authManager.initialize();
      
      expect(eventListener).toHaveBeenCalled();
      
      window.removeEventListener('auth-state-change', eventListener);
    });

    test('應該處理存儲變化事件', async () => {
      await authManager.initialize();
      
      // 模擬localStorage被清除
      const storageEvent = new StorageEvent('storage', {
        key: 'authToken',
        newValue: null,
        oldValue: 'some-token'
      });
      
      window.dispatchEvent(storageEvent);
      
      const state = authManager.getState();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('用戶數據標準化', () => {
    test('應該標準化用戶數據', async () => {
      const incompleteUser = {
        id: '1',
        email: 'test@example.com'
        // 缺少name, tier等字段
      };

      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'authToken') return 'valid.jwt.token';
        if (key === 'userInfo') return JSON.stringify(incompleteUser);
        return null;
      });

      const state = await authManager.initialize();
      
      expect(state.user).toMatchObject({
        id: '1',
        email: 'test@example.com',
        name: '',
        tier: 'free',
        analysisCount: 0,
        analysisLimit: 5
      });
    });
  });
});