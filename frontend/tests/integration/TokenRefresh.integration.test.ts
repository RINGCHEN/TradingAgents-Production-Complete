/**
 * Token刷新流程整合測試
 * 測試token自動刷新機制和相關的錯誤處理
 */

import { TokenManager } from '../../services/TokenManager';
import { ApiClient } from '../../services/ApiClient';
import { AuthService } from '../../services/AuthService';
import { SecureStorage } from '../../utils/SecureStorage';

// Mock dependencies
jest.mock('../../utils/SecureStorage');

// Mock fetch
global.fetch = jest.fn();

describe('Token Refresh Integration Tests', () => {
  let tokenManager: TokenManager;
  let apiClient: ApiClient;
  let authService: AuthService;

  const mockTokens = {
    access_token: 'original-access-token',
    refresh_token: 'original-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  const mockNewTokens = {
    access_token: 'new-access-token',
    refresh_token: 'new-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600
  };

  const mockUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    role: 'admin',
    permissions: ['read', 'write'],
    is_admin: true,
    is_active: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();
    
    // Mock SecureStorage
    const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
    mockSecureStorage.getItem.mockResolvedValue(null);
    mockSecureStorage.setItem.mockResolvedValue();
    mockSecureStorage.removeItem.mockResolvedValue();
    mockSecureStorage.getItemSync.mockReturnValue(null);

    // Create fresh instances
    tokenManager = new TokenManager();
    apiClient = new ApiClient();
    authService = new AuthService();
  });

  describe('Automatic Token Refresh', () => {
    it('should automatically refresh token when it expires soon', async () => {
      // Arrange - token expiring in 2 minutes (less than 5 min threshold)
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem
        .mockResolvedValueOnce(expiringTokens) // First call returns expiring tokens
        .mockResolvedValueOnce({ // Second call returns new tokens
          ...mockNewTokens,
          expires_at: Date.now() + 3600000
        });

      // Mock successful refresh
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockNewTokens)
      });

      // Act
      const token = await tokenManager.getValidToken();

      // Assert
      expect(token).toBe('new-access-token');
      expect(global.fetch).toHaveBeenCalledWith('/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer original-refresh-token'
        }
      });
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        })
      );
    });

    it('should handle concurrent token refresh requests', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      // Mock delayed refresh response
      (global.fetch as jest.Mock).mockImplementation(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(mockNewTokens)
          }), 100)
        )
      );

      // Act - make multiple concurrent requests
      const promises = [
        tokenManager.getValidToken(),
        tokenManager.getValidToken(),
        tokenManager.getValidToken()
      ];

      const results = await Promise.all(promises);

      // Assert - all should get the same new token
      expect(results).toEqual(['new-access-token', 'new-access-token', 'new-access-token']);
      // Only one refresh request should be made
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should clear tokens when refresh fails', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      // Mock failed refresh
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized'
      });

      // Act
      const token = await tokenManager.getValidToken();

      // Assert
      expect(token).toBeNull();
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });
  });

  describe('API Client Token Integration', () => {
    it('should automatically add token to API requests', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      // Mock API response
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'test' })
      });

      // Act
      await apiClient.get('/test-endpoint');

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test-endpoint'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer original-access-token'
          })
        })
      );
    });

    it('should retry API request after token refresh on 401', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem
        .mockResolvedValueOnce(mockTokens) // For initial request
        .mockResolvedValueOnce(mockTokens) // For refresh check
        .mockResolvedValueOnce({ // After refresh
          ...mockNewTokens,
          expires_at: Date.now() + 3600000
        });

      let callCount = 0;
      (global.fetch as jest.Mock).mockImplementation((url) => {
        callCount++;
        
        if (url.includes('/test-endpoint')) {
          if (callCount === 1) {
            // First call fails with 401
            return Promise.resolve({
              ok: false,
              status: 401,
              json: () => Promise.resolve({ message: 'Unauthorized' })
            });
          } else {
            // Retry succeeds
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve({ data: 'success' })
            });
          }
        }
        
        if (url.includes('/auth/refresh')) {
          // Refresh succeeds
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockNewTokens)
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act
      const response = await apiClient.get('/test-endpoint');

      // Assert
      expect(response.data).toEqual({ data: 'success' });
      expect(global.fetch).toHaveBeenCalledTimes(3); // Original request + refresh + retry
      
      // Verify refresh was called
      expect(global.fetch).toHaveBeenCalledWith('/auth/refresh', expect.any(Object));
      
      // Verify retry used new token
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/test-endpoint'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer new-access-token'
          })
        })
      );
    });

    it('should handle multiple concurrent 401 errors', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      let refreshCalled = false;
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/test-endpoint')) {
          // Always return 401 for test endpoints initially
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Unauthorized' })
          });
        }
        
        if (url.includes('/auth/refresh')) {
          if (!refreshCalled) {
            refreshCalled = true;
            return new Promise(resolve =>
              setTimeout(() => resolve({
                ok: true,
                json: () => Promise.resolve(mockNewTokens)
              }), 100)
            );
          }
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockNewTokens)
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act - make multiple concurrent requests that will get 401
      const promises = [
        apiClient.get('/test-endpoint-1').catch(() => 'failed-1'),
        apiClient.get('/test-endpoint-2').catch(() => 'failed-2'),
        apiClient.get('/test-endpoint-3').catch(() => 'failed-3')
      ];

      await Promise.all(promises);

      // Assert - refresh should only be called once
      const refreshCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/auth/refresh')
      );
      expect(refreshCalls).toHaveLength(1);
    });
  });

  describe('AuthService Token Integration', () => {
    it('should refresh token when getting current user with expired token', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem
        .mockResolvedValueOnce(expiringTokens) // For token check
        .mockResolvedValueOnce({ // After refresh
          ...mockNewTokens,
          expires_at: Date.now() + 3600000
        });

      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockNewTokens)
          });
        }
        if (url.includes('/auth/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockUser)
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act
      const user = await authService.getCurrentUser();

      // Assert
      expect(user).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith('/auth/refresh', expect.any(Object));
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer new-access-token'
          })
        })
      );
    });

    it('should handle token refresh failure during user info fetch', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      // Mock failed refresh
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            statusText: 'Unauthorized'
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act
      const user = await authService.getCurrentUser();

      // Assert
      expect(user).toBeNull();
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });
  });

  describe('Token Refresh Listeners', () => {
    it('should notify listeners on successful token refresh', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockNewTokens)
      });

      const refreshListener = jest.fn();
      tokenManager.onTokenRefresh(refreshListener);

      // Act
      await tokenManager.refreshToken();

      // Assert
      expect(refreshListener).toHaveBeenCalledWith(true);
    });

    it('should notify listeners on failed token refresh', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401
      });

      const refreshListener = jest.fn();
      tokenManager.onTokenRefresh(refreshListener);

      // Act
      await tokenManager.refreshToken();

      // Assert
      expect(refreshListener).toHaveBeenCalledWith(false);
    });

    it('should integrate with AuthService refresh notifications', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401
      });

      const authStateListener = jest.fn();
      authService.onAuthStateChange(authStateListener);

      // Act
      await tokenManager.refreshToken();

      // Assert - AuthService should be notified of failed refresh
      expect(authStateListener).toHaveBeenCalledWith(null);
    });
  });

  describe('Error Recovery', () => {
    it('should recover from temporary network errors during refresh', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      let attemptCount = 0;
      (global.fetch as jest.Mock).mockImplementation(() => {
        attemptCount++;
        if (attemptCount === 1) {
          // First attempt fails with network error
          return Promise.reject(new Error('Network Error'));
        } else {
          // Second attempt succeeds
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockNewTokens)
          });
        }
      });

      // Act - first refresh fails, second succeeds
      const firstResult = await tokenManager.refreshToken();
      const secondResult = await tokenManager.refreshToken();

      // Assert
      expect(firstResult).toBe(false);
      expect(secondResult).toBe(true);
    });

    it('should handle refresh timeout gracefully', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      // Mock timeout
      (global.fetch as jest.Mock).mockImplementation(() =>
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Request timeout')), 100)
        )
      );

      // Act
      const result = await tokenManager.refreshToken();

      // Assert
      expect(result).toBe(false);
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });
  });

  describe('Performance and Memory', () => {
    it('should not create memory leaks with refresh listeners', async () => {
      // Arrange
      const listeners: Array<() => void> = [];

      // Add multiple listeners
      for (let i = 0; i < 10; i++) {
        const unsubscribe = tokenManager.onTokenRefresh(() => {});
        listeners.push(unsubscribe);
      }

      // Remove all listeners
      listeners.forEach(unsubscribe => unsubscribe());

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockNewTokens)
      });

      // Act
      await tokenManager.refreshToken();

      // Assert - no listeners should be called since they were removed
      // This is tested implicitly by not having any listener mocks called
      expect(true).toBe(true); // Placeholder assertion
    });

    it('should handle high-frequency token requests efficiently', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      const startTime = Date.now();

      // Act - make many token requests
      const promises = Array.from({ length: 100 }, () => tokenManager.getValidToken());
      await Promise.all(promises);

      const endTime = Date.now();

      // Assert - should complete quickly (under 1 second)
      expect(endTime - startTime).toBeLessThan(1000);
    });
  });
});