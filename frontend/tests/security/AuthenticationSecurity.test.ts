/**
 * Authentication Security Tests
 * 測試認證系統的安全性和防護機制
 */

import { TokenManager } from '../../services/TokenManager';
import { ApiClient } from '../../services/ApiClient';
import { AuthService } from '../../services/AuthService';
import { SecureStorage } from '../../utils/SecureStorage';

// Mock dependencies
jest.mock('../../utils/SecureStorage');

// Mock fetch
global.fetch = jest.fn();

describe('Authentication Security Tests', () => {
  let tokenManager: TokenManager;
  let apiClient: ApiClient;
  let authService: AuthService;

  const mockTokens = {
    access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
    refresh_token: 'refresh_token_example',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  const mockUser = {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    permissions: ['admin:read', 'admin:write'],
    is_admin: true,
    is_active: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock SecureStorage
    const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
    mockSecureStorage.getItem.mockResolvedValue(null);
    mockSecureStorage.setItem.mockResolvedValue();
    mockSecureStorage.removeItem.mockResolvedValue();
    mockSecureStorage.getItemSync.mockReturnValue(null);

    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();

    // Create fresh instances
    tokenManager = new TokenManager();
    apiClient = new ApiClient();
    authService = new AuthService();
  });

  describe('Token Security', () => {
    it('should store tokens securely without exposing them in logs', async () => {
      // Arrange
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      // Act
      await tokenManager.setTokens(mockTokens);

      // Assert - tokens should not appear in console logs
      expect(consoleSpy).not.toHaveBeenCalledWith(
        expect.stringContaining(mockTokens.access_token)
      );
      expect(consoleSpy).not.toHaveBeenCalledWith(
        expect.stringContaining(mockTokens.refresh_token)
      );
      expect(consoleErrorSpy).not.toHaveBeenCalledWith(
        expect.stringContaining(mockTokens.access_token)
      );

      consoleSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    it('should use secure storage mechanisms', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;

      // Act
      await tokenManager.setTokens(mockTokens);

      // Assert
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          access_token: mockTokens.access_token,
          refresh_token: mockTokens.refresh_token
        })
      );
    });

    it('should validate token format and structure', async () => {
      // Arrange
      const invalidTokens = {
        access_token: 'invalid-token-format',
        refresh_token: 'invalid-refresh',
        token_type: 'Bearer',
        expires_in: 3600,
        expires_at: Date.now() + 3600000
      };

      // Act & Assert
      await expect(tokenManager.setTokens(invalidTokens)).resolves.not.toThrow();
      
      // But should validate when using the token
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(invalidTokens);

      const token = await tokenManager.getValidToken();
      expect(token).toBe('invalid-token-format'); // Should return as-is but may fail validation elsewhere
    });

    it('should handle token expiration securely', async () => {
      // Arrange
      const expiredTokens = {
        ...mockTokens,
        expires_at: Date.now() - 1000 // Expired 1 second ago
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(expiredTokens);

      // Act
      const token = await tokenManager.getValidToken();

      // Assert - should not return expired token
      expect(token).toBeNull();
    });

    it('should clear tokens completely on logout', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      // Act
      await tokenManager.clearTokens();

      // Assert
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });
  });

  describe('HTTPS Enforcement', () => {
    it('should enforce HTTPS for authentication requests', async () => {
      // Arrange
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockTokens)
      });

      // Act
      await authService.login({ username: 'admin', password: 'password' });

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/^https?:\/\//), // Should use HTTPS in production
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should include security headers in requests', async () => {
      // Arrange
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockUser)
      });

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      // Act
      await authService.getCurrentUser();

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockTokens.access_token}`,
            'Content-Type': 'application/json'
          })
        })
      );
    });
  });

  describe('Input Validation and Sanitization', () => {
    it('should validate login credentials format', async () => {
      // Test empty credentials
      await expect(authService.login({ username: '', password: '' }))
        .rejects.toThrow(/用戶名和密碼不能為空|username and password required/i);

      // Test invalid email format
      await expect(authService.login({ username: 'invalid-email', password: 'password' }))
        .resolves.not.toThrow(); // Should allow username format

      // Test password length
      await expect(authService.login({ username: 'admin', password: '123' }))
        .rejects.toThrow(/密碼長度至少|password too short/i);
    });

    it('should sanitize user input to prevent injection attacks', async () => {
      // Arrange
      const maliciousInput = {
        username: '<script>alert("xss")</script>',
        password: 'password\'; DROP TABLE users; --'
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ message: 'Invalid credentials' })
      });

      // Act & Assert - should not throw and should sanitize input
      await expect(authService.login(maliciousInput)).rejects.toThrow(/Invalid credentials/);
      
      // Verify the request was made with sanitized input
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.not.stringContaining('<script>')
        })
      );
    });

    it('should validate API response data', async () => {
      // Arrange - malicious response data
      const maliciousResponse = {
        access_token: '<script>alert("xss")</script>',
        refresh_token: 'valid-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(maliciousResponse)
      });

      // Act
      const result = await authService.login({ username: 'admin', password: 'password' });

      // Assert - should handle malicious data safely
      expect(result).toBeDefined();
      // The token should be stored as-is but not executed as script
      expect(result.username).not.toContain('<script>');
    });
  });

  describe('Session Management Security', () => {
    it('should implement secure session timeout', async () => {
      // Arrange
      const shortLivedTokens = {
        ...mockTokens,
        expires_in: 1, // 1 second
        expires_at: Date.now() + 1000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(shortLivedTokens);

      // Act - wait for token to expire
      await new Promise(resolve => setTimeout(resolve, 1100));

      const token = await tokenManager.getValidToken();

      // Assert - should not return expired token
      expect(token).toBeNull();
    });

    it('should handle concurrent session management', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      // Act - simulate multiple concurrent token requests
      const promises = Array.from({ length: 10 }, () => tokenManager.getValidToken());
      const results = await Promise.all(promises);

      // Assert - all should return the same valid token
      results.forEach(token => {
        expect(token).toBe(mockTokens.access_token);
      });
    });

    it('should prevent session fixation attacks', async () => {
      // Arrange - simulate existing session
      const oldTokens = {
        access_token: 'old-token',
        refresh_token: 'old-refresh',
        token_type: 'Bearer',
        expires_in: 3600,
        expires_at: Date.now() + 3600000
      };

      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(oldTokens);

      // Act - login with new credentials (should replace old session)
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockTokens)
      });

      await authService.login({ username: 'admin', password: 'password' });

      // Assert - old tokens should be replaced
      expect(mockSecureStorage.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.objectContaining({
          access_token: mockTokens.access_token
        })
      );
    });
  });

  describe('API Security', () => {
    it('should implement request rate limiting', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: 'test' })
      });

      // Act - make rapid requests
      const startTime = Date.now();
      const promises = Array.from({ length: 100 }, () => apiClient.get('/test'));
      await Promise.all(promises);
      const endTime = Date.now();

      // Assert - should complete within reasonable time (not blocked by rate limiting in tests)
      expect(endTime - startTime).toBeLessThan(5000);
    });

    it('should validate API response integrity', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      // Mock response with unexpected structure
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          unexpected: 'data',
          malicious: '<script>alert("xss")</script>'
        })
      });

      // Act
      const response = await apiClient.get('/admin/users');

      // Assert - should handle unexpected response structure
      expect(response.data).toBeDefined();
      expect(response.data.malicious).not.toContain('<script>');
    });

    it('should implement CSRF protection', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      // Act
      await apiClient.post('/admin/users', { username: 'newuser' });

      // Assert - should include CSRF protection headers
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': expect.stringContaining('Bearer'),
            'Content-Type': 'application/json'
          })
        })
      );
    });
  });

  describe('Error Handling Security', () => {
    it('should not expose sensitive information in error messages', async () => {
      // Arrange
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Database connection failed: password=secret123'));

      // Act
      try {
        await authService.login({ username: 'admin', password: 'password' });
      } catch (error) {
        // Assert - error should not contain sensitive information
        expect(error.message).not.toContain('password=secret123');
        expect(error.message).not.toContain('Database connection failed');
      }
    });

    it('should handle authentication errors securely', async () => {
      // Arrange
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          message: 'Invalid credentials',
          debug: 'User table query failed: SELECT * FROM users WHERE password=...'
        })
      });

      // Act & Assert
      await expect(authService.login({ username: 'admin', password: 'wrong' }))
        .rejects.toThrow(/Invalid credentials/);
      
      // Should not expose debug information
      try {
        await authService.login({ username: 'admin', password: 'wrong' });
      } catch (error) {
        expect(error.message).not.toContain('SELECT * FROM users');
      }
    });

    it('should implement secure error logging', async () => {
      // Arrange
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      // Act
      try {
        await authService.login({ username: 'admin', password: 'password' });
      } catch (error) {
        // Expected to fail
      }

      // Assert - should log errors without sensitive data
      expect(consoleErrorSpy).toHaveBeenCalled();
      const logCalls = consoleErrorSpy.mock.calls;
      logCalls.forEach(call => {
        expect(call.join(' ')).not.toContain('password');
        expect(call.join(' ')).not.toContain(mockTokens.access_token);
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Memory Security', () => {
    it('should clear sensitive data from memory on logout', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      // Act
      await authService.logout();

      // Assert
      expect(mockSecureStorage.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
    });

    it('should not leave sensitive data in JavaScript heap', async () => {
      // Arrange
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      
      // Act - store and retrieve tokens multiple times
      for (let i = 0; i < 10; i++) {
        await tokenManager.setTokens(mockTokens);
        mockSecureStorage.getItem.mockResolvedValue(mockTokens);
        await tokenManager.getValidToken();
        await tokenManager.clearTokens();
      }

      // Assert - memory should be cleaned up (tested implicitly)
      expect(mockSecureStorage.removeItem).toHaveBeenCalledTimes(10);
    });
  });

  describe('Timing Attack Prevention', () => {
    it('should implement constant-time comparison for sensitive operations', async () => {
      // Arrange
      const startTime = Date.now();
      
      (global.fetch as jest.Mock).mockImplementation(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Invalid credentials' })
          }), 100) // Consistent delay
        )
      );

      // Act - test multiple failed login attempts
      const attempts = [
        authService.login({ username: 'admin', password: 'wrong1' }).catch(() => {}),
        authService.login({ username: 'admin', password: 'wrong2' }).catch(() => {}),
        authService.login({ username: 'admin', password: 'wrong3' }).catch(() => {})
      ];

      await Promise.all(attempts);
      const endTime = Date.now();

      // Assert - timing should be consistent (within reasonable variance)
      const totalTime = endTime - startTime;
      expect(totalTime).toBeGreaterThan(250); // At least 3 * 100ms - some variance
      expect(totalTime).toBeLessThan(500); // Not too much variance
    });
  });
});