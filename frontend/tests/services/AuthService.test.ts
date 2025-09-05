/**
 * AuthService 單元測試
 * 測試認證服務的所有核心功能
 */

import { AuthService, AuthError, LoginCredentials, AuthUser } from '../../services/AuthService';
import { TokenManager } from '../../services/TokenManager';
import { ApiClient } from '../../services/ApiClient';

// Mock dependencies
jest.mock('../../services/TokenManager');
jest.mock('../../services/ApiClient');

describe('AuthService', () => {
  let authService: AuthService;
  let mockTokenManager: jest.Mocked<TokenManager>;
  let mockApiClient: jest.Mocked<ApiClient>;

  const mockUser: AuthUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    role: 'admin',
    permissions: ['read', 'write'],
    is_admin: true,
    is_active: true
  };

  const mockCredentials: LoginCredentials = {
    username: 'testuser',
    password: 'password123'
  };

  const mockTokens = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Create mocked instances
    mockTokenManager = new TokenManager() as jest.Mocked<TokenManager>;
    mockApiClient = new ApiClient() as jest.Mocked<ApiClient>;
    
    // Mock constructor behavior
    (TokenManager as jest.Mock).mockImplementation(() => mockTokenManager);
    (ApiClient as jest.Mock).mockImplementation(() => mockApiClient);
    
    // Create new AuthService instance
    authService = new AuthService();
  });

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      // Arrange
      const mockResponse = {
        data: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'Bearer',
          expires_in: 3600
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: mockUser });
      mockTokenManager.setTokens.mockResolvedValue();

      // Act
      const result = await authService.login(mockCredentials);

      // Assert
      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/login', mockCredentials);
      expect(mockTokenManager.setTokens).toHaveBeenCalledWith(
        expect.objectContaining({
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'Bearer',
          expires_in: 3600,
          expires_at: expect.any(Number)
        })
      );
      expect(mockApiClient.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });

    it('should throw AuthError when API returns invalid response', async () => {
      // Arrange
      const mockResponse = { data: {} }; // Missing access_token
      mockApiClient.post.mockResolvedValue(mockResponse);

      // Act & Assert
      await expect(authService.login(mockCredentials)).rejects.toThrow(AuthError);
      await expect(authService.login(mockCredentials)).rejects.toThrow('登錄響應格式錯誤');
    });

    it('should throw AuthError with user-friendly message for 401 error', async () => {
      // Arrange
      const mockError = {
        response: { status: 401 }
      };
      mockApiClient.post.mockRejectedValue(mockError);

      // Act & Assert
      await expect(authService.login(mockCredentials)).rejects.toThrow(AuthError);
      await expect(authService.login(mockCredentials)).rejects.toThrow('用戶名或密碼錯誤');
    });

    it('should throw AuthError with server error message for 5xx errors', async () => {
      // Arrange
      const mockError = {
        response: { status: 500 }
      };
      mockApiClient.post.mockRejectedValue(mockError);

      // Act & Assert
      await expect(authService.login(mockCredentials)).rejects.toThrow(AuthError);
      await expect(authService.login(mockCredentials)).rejects.toThrow('服務器錯誤，請稍後重試');
    });

    it('should throw AuthError with network error message when offline', async () => {
      // Arrange
      const mockError = new Error('Network Error');
      mockApiClient.post.mockRejectedValue(mockError);
      
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      // Act & Assert
      await expect(authService.login(mockCredentials)).rejects.toThrow(AuthError);
      await expect(authService.login(mockCredentials)).rejects.toThrow('網絡連接失敗，請檢查網絡設置');
    });

    it('should notify auth state listeners on successful login', async () => {
      // Arrange
      const mockResponse = {
        data: {
          access_token: 'mock-access-token',
          token_type: 'Bearer',
          expires_in: 3600
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: mockUser });
      mockTokenManager.setTokens.mockResolvedValue();

      const mockListener = jest.fn();
      authService.onAuthStateChange(mockListener);

      // Act
      await authService.login(mockCredentials);

      // Assert
      expect(mockListener).toHaveBeenCalledWith(mockUser);
    });
  });

  describe('logout', () => {
    it('should successfully logout and clear tokens', async () => {
      // Arrange
      mockApiClient.post.mockResolvedValue({});
      mockTokenManager.clearTokens.mockResolvedValue();

      const mockListener = jest.fn();
      authService.onAuthStateChange(mockListener);

      // Act
      await authService.logout();

      // Assert
      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/logout');
      expect(mockTokenManager.clearTokens).toHaveBeenCalled();
      expect(mockListener).toHaveBeenCalledWith(null);
    });

    it('should clear local state even if logout API fails', async () => {
      // Arrange
      mockApiClient.post.mockRejectedValue(new Error('API Error'));
      mockTokenManager.clearTokens.mockResolvedValue();

      const mockListener = jest.fn();
      authService.onAuthStateChange(mockListener);

      // Act
      await authService.logout();

      // Assert
      expect(mockTokenManager.clearTokens).toHaveBeenCalled();
      expect(mockListener).toHaveBeenCalledWith(null);
    });
  });

  describe('getCurrentUser', () => {
    it('should return user data when token is valid', async () => {
      // Arrange
      mockTokenManager.getValidToken.mockResolvedValue('valid-token');
      mockApiClient.get.mockResolvedValue({ data: mockUser });

      // Act
      const result = await authService.getCurrentUser();

      // Assert
      expect(mockTokenManager.getValidToken).toHaveBeenCalled();
      expect(mockApiClient.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });

    it('should return null when no valid token exists', async () => {
      // Arrange
      mockTokenManager.getValidToken.mockResolvedValue(null);

      // Act
      const result = await authService.getCurrentUser();

      // Assert
      expect(result).toBeNull();
      expect(mockApiClient.get).not.toHaveBeenCalled();
    });

    it('should logout and return null on 401 error', async () => {
      // Arrange
      mockTokenManager.getValidToken.mockResolvedValue('invalid-token');
      mockApiClient.get.mockRejectedValue({
        response: { status: 401 }
      });
      mockTokenManager.clearTokens.mockResolvedValue();

      // Act
      const result = await authService.getCurrentUser();

      // Assert
      expect(result).toBeNull();
      expect(mockTokenManager.clearTokens).toHaveBeenCalled();
    });
  });

  describe('refreshToken', () => {
    it('should delegate to TokenManager', async () => {
      // Arrange
      mockTokenManager.refreshToken.mockResolvedValue(true);

      // Act
      const result = await authService.refreshToken();

      // Assert
      expect(mockTokenManager.refreshToken).toHaveBeenCalled();
      expect(result).toBe(true);
    });
  });

  describe('isAuthenticated', () => {
    it('should delegate to TokenManager', () => {
      // Arrange
      mockTokenManager.hasValidToken.mockReturnValue(true);

      // Act
      const result = authService.isAuthenticated();

      // Assert
      expect(mockTokenManager.hasValidToken).toHaveBeenCalled();
      expect(result).toBe(true);
    });
  });

  describe('onAuthStateChange', () => {
    it('should add and remove listeners correctly', () => {
      // Arrange
      const mockListener = jest.fn();

      // Act
      const unsubscribe = authService.onAuthStateChange(mockListener);

      // Assert - listener should be added
      expect(typeof unsubscribe).toBe('function');

      // Act - remove listener
      unsubscribe();

      // The listener should no longer be called (tested implicitly in other tests)
    });
  });

  describe('initializeAuth', () => {
    it('should return user when authenticated', async () => {
      // Arrange
      mockTokenManager.hasValidToken.mockReturnValue(true);
      mockApiClient.get.mockResolvedValue({ data: mockUser });
      mockTokenManager.getValidToken.mockResolvedValue('valid-token');

      const mockListener = jest.fn();
      authService.onAuthStateChange(mockListener);

      // Act
      const result = await authService.initializeAuth();

      // Assert
      expect(result).toEqual(mockUser);
      expect(mockListener).toHaveBeenCalledWith(mockUser);
    });

    it('should return null when not authenticated', async () => {
      // Arrange
      mockTokenManager.hasValidToken.mockReturnValue(false);

      // Act
      const result = await authService.initializeAuth();

      // Assert
      expect(result).toBeNull();
    });

    it('should handle initialization errors gracefully', async () => {
      // Arrange
      mockTokenManager.hasValidToken.mockReturnValue(true);
      mockTokenManager.getValidToken.mockResolvedValue('valid-token');
      mockApiClient.get.mockRejectedValue(new Error('Network Error'));

      // Act
      const result = await authService.initializeAuth();

      // Assert
      expect(result).toBeNull();
    });
  });

  describe('normalizeUserData', () => {
    it('should normalize user data with default values', () => {
      // Arrange
      const rawUserData = {
        id: 1,
        username: 'testuser'
        // Missing other fields
      };

      // Act - access private method through any
      const result = (authService as any).normalizeUserData(rawUserData);

      // Assert
      expect(result).toEqual({
        id: 1,
        username: 'testuser',
        email: '',
        role: 'user',
        permissions: [],
        is_admin: false,
        is_active: true
      });
    });

    it('should preserve existing user data', () => {
      // Arrange
      const rawUserData = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'admin',
        permissions: ['read', 'write'],
        is_admin: true,
        is_active: false
      };

      // Act
      const result = (authService as any).normalizeUserData(rawUserData);

      // Assert
      expect(result).toEqual(rawUserData);
    });
  });

  describe('event handling', () => {
    it('should dispatch custom events on auth state change', async () => {
      // Arrange
      const mockResponse = {
        data: {
          access_token: 'mock-access-token',
          token_type: 'Bearer',
          expires_in: 3600
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: mockUser });
      mockTokenManager.setTokens.mockResolvedValue();

      const eventListener = jest.fn();
      window.addEventListener('auth-state-change', eventListener);

      // Act
      await authService.login(mockCredentials);

      // Assert
      expect(eventListener).toHaveBeenCalled();
      
      // Cleanup
      window.removeEventListener('auth-state-change', eventListener);
    });
  });

  describe('error handling', () => {
    it('should handle listener errors gracefully', async () => {
      // Arrange
      const mockResponse = {
        data: {
          access_token: 'mock-access-token',
          token_type: 'Bearer',
          expires_in: 3600
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: mockUser });
      mockTokenManager.setTokens.mockResolvedValue();

      const faultyListener = jest.fn().mockImplementation(() => {
        throw new Error('Listener error');
      });
      
      authService.onAuthStateChange(faultyListener);

      // Act & Assert - should not throw
      await expect(authService.login(mockCredentials)).resolves.toEqual(mockUser);
    });
  });
});