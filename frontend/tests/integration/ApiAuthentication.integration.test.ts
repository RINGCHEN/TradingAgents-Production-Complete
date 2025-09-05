/**
 * API調用認證整合測試
 * 測試API客戶端與認證系統的完整整合
 */

import { ApiClient } from '../../services/ApiClient';
import { TokenManager } from '../../services/TokenManager';
import { AuthService } from '../../services/AuthService';
import { SecureStorage } from '../../utils/SecureStorage';

// Mock dependencies
jest.mock('../../utils/SecureStorage');

// Mock fetch
global.fetch = jest.fn();

describe('API Authentication Integration Tests', () => {
  let apiClient: ApiClient;
  let tokenManager: TokenManager;
  let authService: AuthService;

  const mockTokens = {
    access_token: 'valid-access-token',
    refresh_token: 'valid-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  const mockNewTokens = {
    access_token: 'refreshed-access-token',
    refresh_token: 'refreshed-refresh-token',
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
    apiClient = new ApiClient();
    tokenManager = new TokenManager();
    authService = new AuthService();
  });

  describe('Authenticated API Requests', () => {
    it('should automatically include authentication headers in API requests', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'success' })
      });

      // Act
      await apiClient.get('/api/protected-endpoint');

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/protected-endpoint'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );
    });

    it('should handle requests without authentication when no token exists', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(null);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'public' })
      });

      // Act
      await apiClient.get('/api/public-endpoint');

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/public-endpoint'),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.anything()
          })
        })
      );
    });

    it('should work with all HTTP methods', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      const testData = { test: 'data' };

      // Act & Assert
      await apiClient.get('/api/test');
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/test'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );

      await apiClient.post('/api/test', testData);
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(testData),
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );

      await apiClient.put('/api/test', testData);
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/test'),
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );

      await apiClient.delete('/api/test');
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/test'),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );

      await apiClient.patch('/api/test', testData);
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/test'),
        expect.objectContaining({
          method: 'PATCH',
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );
    });
  });

  describe('Authentication Error Handling', () => {
    it('should automatically retry request after token refresh on 401', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem
        .mockResolvedValueOnce(mockTokens) // Initial token
        .mockResolvedValueOnce(mockTokens) // For refresh check
        .mockResolvedValueOnce({ // After refresh
          ...mockNewTokens,
          expires_at: Date.now() + 3600000
        });

      let requestCount = 0;
      (global.fetch as jest.Mock).mockImplementation((url) => {
        requestCount++;
        
        if (url.includes('/api/protected')) {
          if (requestCount === 1) {
            // First request fails with 401
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
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockNewTokens)
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act
      const response = await apiClient.get('/api/protected');

      // Assert
      expect(response.data).toEqual({ data: 'success' });
      expect(requestCount).toBe(3); // Original + refresh + retry
      
      // Verify new token was stored
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          access_token: 'refreshed-access-token'
        })
      );
    });

    it('should not retry request if already retried', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ message: 'Unauthorized' })
      });

      // Act & Assert
      await expect(apiClient.get('/api/protected')).rejects.toMatchObject({
        status: 401,
        isAuthError: true
      });

      // Should only make one request (no retry)
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should handle token refresh failure during API request', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/api/protected')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Unauthorized' })
          });
        }
        
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Refresh token expired' })
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const eventListener = jest.fn();
      window.addEventListener('auth-error', eventListener);

      // Act & Assert
      await expect(apiClient.get('/api/protected')).rejects.toMatchObject({
        isAuthError: true
      });

      // Verify auth error event was dispatched
      expect(eventListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: { type: 'token-refresh-failed' }
        })
      );

      // Cleanup
      window.removeEventListener('auth-error', eventListener);
    });

    it('should handle 403 Forbidden errors appropriately', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
        json: () => Promise.resolve({ message: 'Forbidden' })
      });

      // Act & Assert
      await expect(apiClient.get('/api/admin-only')).rejects.toMatchObject({
        status: 403,
        isAuthError: false // 403 is not considered an auth error for retry
      });

      // Should not attempt token refresh for 403
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Request Queue Management', () => {
    it('should queue requests during token refresh', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      let refreshInProgress = false;
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/api/protected')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Unauthorized' })
          });
        }
        
        if (url.includes('/auth/refresh')) {
          if (refreshInProgress) {
            throw new Error('Multiple refresh attempts');
          }
          refreshInProgress = true;
          
          return new Promise(resolve =>
            setTimeout(() => {
              refreshInProgress = false;
              resolve({
                ok: true,
                json: () => Promise.resolve(mockNewTokens)
              });
            }, 100)
          );
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act - make multiple concurrent requests that will get 401
      const promises = [
        apiClient.get('/api/protected-1').catch(() => 'failed-1'),
        apiClient.get('/api/protected-2').catch(() => 'failed-2'),
        apiClient.get('/api/protected-3').catch(() => 'failed-3')
      ];

      await Promise.all(promises);

      // Assert - only one refresh should be attempted
      const refreshCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/auth/refresh')
      );
      expect(refreshCalls).toHaveLength(1);
    });

    it('should clear request queue on auth failure', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/api/protected')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Unauthorized' })
          });
        }
        
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Refresh failed' })
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act
      const promises = [
        apiClient.get('/api/protected-1').catch(err => err),
        apiClient.get('/api/protected-2').catch(err => err),
        apiClient.get('/api/protected-3').catch(err => err)
      ];

      const results = await Promise.all(promises);

      // Assert - all requests should fail with auth error
      results.forEach(result => {
        expect(result).toMatchObject({
          isAuthError: true
        });
      });
    });
  });

  describe('Integration with AuthService', () => {
    it('should work seamlessly with AuthService login flow', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      
      // Mock login flow
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/login')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTokens)
          });
        }
        
        if (url.includes('/auth/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockUser)
          });
        }
        
        if (url.includes('/api/user-data')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ userData: 'success' })
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act - login and then make API request
      await authService.login({ username: 'testuser', password: 'password' });
      
      // Mock that tokens are now stored
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);
      
      const response = await apiClient.get('/api/user-data');

      // Assert
      expect(response.data).toEqual({ userData: 'success' });
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/user-data'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer valid-access-token'
          })
        })
      );
    });

    it('should handle logout and clear authentication from API requests', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem
        .mockResolvedValueOnce(mockTokens) // Before logout
        .mockResolvedValueOnce(null); // After logout

      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/logout')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true })
          });
        }
        
        if (url.includes('/api/public')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ data: 'public' })
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      // Act - logout and then make API request
      await authService.logout();
      const response = await apiClient.get('/api/public');

      // Assert - request should not include authorization header
      expect(response.data).toEqual({ data: 'public' });
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/public'),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.anything()
          })
        })
      );
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle network errors gracefully', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network Error'));

      // Act & Assert
      await expect(apiClient.get('/api/test')).rejects.toMatchObject({
        message: 'Network Error',
        isNetworkError: true,
        isAuthError: false
      });
    });

    it('should handle server errors appropriately', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: 'Internal Server Error' })
      });

      // Act & Assert
      await expect(apiClient.get('/api/test')).rejects.toMatchObject({
        status: 500,
        isNetworkError: false,
        isAuthError: false
      });
    });

    it('should handle malformed responses', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON'))
      });

      // Act & Assert
      await expect(apiClient.get('/api/test')).rejects.toThrow('Invalid JSON');
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle high-frequency API requests efficiently', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'success' })
      });

      const startTime = Date.now();

      // Act - make many concurrent requests
      const promises = Array.from({ length: 50 }, (_, i) =>
        apiClient.get(`/api/test-${i}`)
      );

      await Promise.all(promises);
      const endTime = Date.now();

      // Assert - should complete quickly
      expect(endTime - startTime).toBeLessThan(2000); // Under 2 seconds
      expect(global.fetch).toHaveBeenCalledTimes(50);
    });

    it('should not create memory leaks with request interceptors', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'success' })
      });

      // Act - add and remove multiple interceptors
      const interceptorIds: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const id = apiClient.addRequestInterceptor(
          (config) => config,
          (error: any) => Promise.reject(error)
        );
        interceptorIds.push(id);
      }

      // Remove all interceptors
      interceptorIds.forEach(id => {
        apiClient.removeInterceptor('request', id);
      });

      // Make request after cleanup
      await apiClient.get('/api/test');

      // Assert - request should still work
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/test'),
        expect.any(Object)
      );
    });
  });
});