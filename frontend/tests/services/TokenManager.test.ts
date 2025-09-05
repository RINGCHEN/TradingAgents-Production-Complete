/**
 * TokenManager 單元測試
 * 測試token管理器的所有核心功能
 */

import { TokenManager } from '../../services/TokenManager';
import { SecureStorage } from '../../utils/SecureStorage';
import type { AuthTokens } from '../../services/AuthService';

// Mock dependencies
jest.mock('../../utils/SecureStorage');

// Mock fetch for token refresh
global.fetch = jest.fn();

describe('TokenManager', () => {
  let tokenManager: TokenManager;
  let mockSecureStorage: jest.Mocked<typeof SecureStorage>;

  const mockTokens: AuthTokens = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock SecureStorage
    mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
    
    // Create new TokenManager instance
    tokenManager = new TokenManager();
    
    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();
  });

  describe('setTokens', () => {
    it('should store tokens with calculated expiry time', async () => {
      // Arrange
      const tokensWithoutExpiry = {
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        token_type: 'Bearer',
        expires_in: 3600,
        expires_at: 0 // Will be calculated
      };

      mockSecureStorage.setItem.mockResolvedValue();

      // Act
      await tokenManager.setTokens(tokensWithoutExpiry);

      // Assert
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          access_token: 'test-token',
          refresh_token: 'test-refresh',
          token_type: 'Bearer',
          expires_in: 3600,
          expires_at: expect.any(Number)
        })
      );

      const calledWith = mockSecureStorage.setItem.mock.calls[0][1] as AuthTokens;
      expect(calledWith.expires_at).toBeGreaterThan(Date.now());
    });

    it('should preserve existing expiry time if provided', async () => {
      // Arrange
      const expiryTime = Date.now() + 7200000; // 2 hours
      const tokensWithExpiry = {
        ...mockTokens,
        expires_at: expiryTime
      };

      mockSecureStorage.setItem.mockResolvedValue();

      // Act
      await tokenManager.setTokens(tokensWithExpiry);

      // Assert
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          expires_at: expiryTime
        })
      );
    });

    it('should throw error when storage fails', async () => {
      // Arrange
      mockSecureStorage.setItem.mockRejectedValue(new Error('Storage error'));

      // Act & Assert
      await expect(tokenManager.setTokens(mockTokens)).rejects.toThrow('Token存儲失敗');
    });
  });

  describe('getValidToken', () => {
    it('should return token when valid and not expiring soon', async () => {
      // Arrange
      const validTokens = {
        ...mockTokens,
        expires_at: Date.now() + 10 * 60 * 1000 // 10 minutes from now
      };

      mockSecureStorage.getItem.mockResolvedValue(validTokens);

      // Act
      const result = await tokenManager.getValidToken();

      // Assert
      expect(result).toBe('mock-access-token');
    });

    it('should refresh token when expiring soon', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000 // 2 minutes from now (less than 5 min threshold)
      };

      const newTokens = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      };

      mockSecureStorage.getItem
        .mockResolvedValueOnce(expiringTokens) // First call returns expiring tokens
        .mockResolvedValueOnce({ // Second call returns new tokens
          ...newTokens,
          expires_at: Date.now() + 3600000
        });

      mockSecureStorage.setItem.mockResolvedValue();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(newTokens)
      });

      // Act
      const result = await tokenManager.getValidToken();

      // Assert
      expect(result).toBe('new-access-token');
      expect(global.fetch).toHaveBeenCalledWith('/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-refresh-token'
        }
      });
    });

    it('should return null when no tokens exist', async () => {
      // Arrange
      mockSecureStorage.getItem.mockResolvedValue(null);

      // Act
      const result = await tokenManager.getValidToken();

      // Assert
      expect(result).toBeNull();
    });

    it('should return null when refresh fails', async () => {
      // Arrange
      const expiringTokens = {
        ...mockTokens,
        expires_at: Date.now() + 2 * 60 * 1000
      };

      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);
      mockSecureStorage.removeItem.mockResolvedValue();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized'
      });

      // Act
      const result = await tokenManager.getValidToken();

      // Assert
      expect(result).toBeNull();
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });
  });

  describe('refreshToken', () => {
    it('should successfully refresh token', async () => {
      // Arrange
      const newTokens = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      };

      mockSecureStorage.getItem.mockResolvedValue(mockTokens);
      mockSecureStorage.setItem.mockResolvedValue();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(newTokens)
      });

      const refreshListener = jest.fn();
      tokenManager.onTokenRefresh(refreshListener);

      // Act
      const result = await tokenManager.refreshToken();

      // Assert
      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith('/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-refresh-token'
        }
      });
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          access_token: 'new-access-token',
          expires_at: expect.any(Number)
        })
      );
      expect(refreshListener).toHaveBeenCalledWith(true);
    });

    it('should return false when no refresh token exists', async () => {
      // Arrange
      const tokensWithoutRefresh = {
        ...mockTokens,
        refresh_token: undefined
      };

      mockSecureStorage.getItem.mockResolvedValue(tokensWithoutRefresh);

      const refreshListener = jest.fn();
      tokenManager.onTokenRefresh(refreshListener);

      // Act
      const result = await tokenManager.refreshToken();

      // Assert
      expect(result).toBe(false);
      expect(refreshListener).toHaveBeenCalledWith(false);
    });

    it('should handle concurrent refresh requests', async () => {
      // Arrange
      const newTokens = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      };

      mockSecureStorage.getItem.mockResolvedValue(mockTokens);
      mockSecureStorage.setItem.mockResolvedValue();

      (global.fetch as jest.Mock).mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(newTokens)
          }), 100)
        )
      );

      // Act - start multiple refresh requests concurrently
      const promise1 = tokenManager.refreshToken();
      const promise2 = tokenManager.refreshToken();
      const promise3 = tokenManager.refreshToken();

      const results = await Promise.all([promise1, promise2, promise3]);

      // Assert - all should succeed and fetch should only be called once
      expect(results).toEqual([true, true, true]);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should clear tokens on refresh failure', async () => {
      // Arrange
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);
      mockSecureStorage.removeItem.mockResolvedValue();

      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const refreshListener = jest.fn();
      tokenManager.onTokenRefresh(refreshListener);

      // Act
      const result = await tokenManager.refreshToken();

      // Assert
      expect(result).toBe(false);
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
      expect(refreshListener).toHaveBeenCalledWith(false);
    });
  });

  describe('clearTokens', () => {
    it('should remove tokens from storage', async () => {
      // Arrange
      mockSecureStorage.removeItem.mockResolvedValue();

      // Act
      await tokenManager.clearTokens();

      // Assert
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });

    it('should handle storage errors gracefully', async () => {
      // Arrange
      mockSecureStorage.removeItem.mockRejectedValue(new Error('Storage error'));

      // Act & Assert - should not throw
      await expect(tokenManager.clearTokens()).resolves.toBeUndefined();
    });
  });

  describe('hasValidToken', () => {
    it('should return true for valid tokens', () => {
      // Arrange
      const validTokens = {
        ...mockTokens,
        expires_at: Date.now() + 10 * 60 * 1000
      };

      mockSecureStorage.getItemSync.mockReturnValue(validTokens);

      // Act
      const result = tokenManager.hasValidToken();

      // Assert
      expect(result).toBe(true);
    });

    it('should return false for expired tokens', () => {
      // Arrange
      const expiredTokens = {
        ...mockTokens,
        expires_at: Date.now() - 1000 // 1 second ago
      };

      mockSecureStorage.getItemSync.mockReturnValue(expiredTokens);

      // Act
      const result = tokenManager.hasValidToken();

      // Assert
      expect(result).toBe(false);
    });

    it('should return false when no tokens exist', () => {
      // Arrange
      mockSecureStorage.getItemSync.mockReturnValue(null);

      // Act
      const result = tokenManager.hasValidToken();

      // Assert
      expect(result).toBe(false);
    });

    it('should return false on storage errors', () => {
      // Arrange
      mockSecureStorage.getItemSync.mockImplementation(() => {
        throw new Error('Storage error');
      });

      // Act
      const result = tokenManager.hasValidToken();

      // Assert
      expect(result).toBe(false);
    });
  });

  describe('onTokenRefresh', () => {
    it('should add and remove refresh listeners', () => {
      // Arrange
      const listener = jest.fn();

      // Act
      const unsubscribe = tokenManager.onTokenRefresh(listener);

      // Assert
      expect(typeof unsubscribe).toBe('function');

      // Act - remove listener
      unsubscribe();

      // The listener should no longer be called (tested implicitly in refresh tests)
    });

    it('should handle listener errors gracefully', async () => {
      // Arrange
      const faultyListener = jest.fn().mockImplementation(() => {
        throw new Error('Listener error');
      });

      tokenManager.onTokenRefresh(faultyListener);

      mockSecureStorage.getItem.mockResolvedValue(mockTokens);
      mockSecureStorage.setItem.mockResolvedValue();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'new-token',
          expires_in: 3600
        })
      });

      // Act & Assert - should not throw
      await expect(tokenManager.refreshToken()).resolves.toBe(true);
    });
  });

  describe('getTokenTimeRemaining', () => {
    it('should return correct time remaining', async () => {
      // Arrange
      const futureTime = Date.now() + 10 * 60 * 1000; // 10 minutes
      const tokensWithFutureExpiry = {
        ...mockTokens,
        expires_at: futureTime
      };

      mockSecureStorage.getItem.mockResolvedValue(tokensWithFutureExpiry);

      // Act
      const result = await tokenManager.getTokenTimeRemaining();

      // Assert
      expect(result).toBeGreaterThan(9 * 60 * 1000); // Should be close to 10 minutes
      expect(result).toBeLessThanOrEqual(10 * 60 * 1000);
    });

    it('should return 0 for expired tokens', async () => {
      // Arrange
      const pastTime = Date.now() - 1000; // 1 second ago
      const expiredTokens = {
        ...mockTokens,
        expires_at: pastTime
      };

      mockSecureStorage.getItem.mockResolvedValue(expiredTokens);

      // Act
      const result = await tokenManager.getTokenTimeRemaining();

      // Assert
      expect(result).toBe(0);
    });

    it('should return 0 when no tokens exist', async () => {
      // Arrange
      mockSecureStorage.getItem.mockResolvedValue(null);

      // Act
      const result = await tokenManager.getTokenTimeRemaining();

      // Assert
      expect(result).toBe(0);
    });
  });

  describe('isTokenExpiringSoon', () => {
    it('should return true when token expires within threshold', async () => {
      // Arrange
      const soonExpiry = Date.now() + 2 * 60 * 1000; // 2 minutes (less than 5 min threshold)
      const expiringTokens = {
        ...mockTokens,
        expires_at: soonExpiry
      };

      mockSecureStorage.getItem.mockResolvedValue(expiringTokens);

      // Act
      const result = await tokenManager.isTokenExpiringSoon();

      // Assert
      expect(result).toBe(true);
    });

    it('should return false when token has plenty of time', async () => {
      // Arrange
      const futureExpiry = Date.now() + 10 * 60 * 1000; // 10 minutes
      const validTokens = {
        ...mockTokens,
        expires_at: futureExpiry
      };

      mockSecureStorage.getItem.mockResolvedValue(validTokens);

      // Act
      const result = await tokenManager.isTokenExpiringSoon();

      // Assert
      expect(result).toBe(false);
    });

    it('should return false when no tokens exist', async () => {
      // Arrange
      mockSecureStorage.getItem.mockResolvedValue(null);

      // Act
      const result = await tokenManager.isTokenExpiringSoon();

      // Assert
      expect(result).toBe(false);
    });
  });
});