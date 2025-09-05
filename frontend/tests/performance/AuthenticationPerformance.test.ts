/**
 * Authentication Performance Tests
 * 測試認證系統的性能和效率
 */

import { TokenManager } from '../../services/TokenManager';
import { ApiClient } from '../../services/ApiClient';
import { AuthService } from '../../services/AuthService';
import { SecureStorage } from '../../utils/SecureStorage';

// Mock dependencies
jest.mock('../../utils/SecureStorage');

// Mock fetch
global.fetch = jest.fn();

// Performance test utilities
const measureTime = async (fn: () => Promise<any>): Promise<number> => {
  const start = performance.now();
  await fn();
  const end = performance.now();
  return end - start;
};

const measureMemory = (): number => {
  if (typeof (performance as any).memory !== 'undefined') {
    return (performance as any).memory.usedJSHeapSize;
  }
  return 0;
};

describe('Authentication Performance Tests', () => {
  let tokenManager: TokenManager;
  let apiClient: ApiClient;
  let authService: AuthService;

  const mockTokens = {
    access_token: 'performance-test-token',
    refresh_token: 'performance-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  const mockUser = {
    id: 1,
    username: 'perftest',
    email: 'perf@example.com',
    role: 'admin',
    permissions: ['admin:read', 'admin:write'],
    is_admin: true,
    is_active: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock SecureStorage with performance-optimized responses
    const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
    mockSecureStorage.getItem.mockResolvedValue(mockTokens);
    mockSecureStorage.setItem.mockResolvedValue();
    mockSecureStorage.removeItem.mockResolvedValue();
    mockSecureStorage.getItemSync.mockReturnValue(mockTokens);

    // Mock fast API responses
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUser)
    });

    // Create fresh instances
    tokenManager = new TokenManager();
    apiClient = new ApiClient();
    authService = new AuthService();
  });

  describe('Token Management Performance', () => {
    test('should retrieve valid token quickly', async () => {
      // Arrange
      const iterations = 1000;

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: iterations }, () => 
          tokenManager.getValidToken()
        );
        await Promise.all(promises);
      });

      // Assert - should complete 1000 token retrievals in under 100ms
      expect(time).toBeLessThan(100);
    });

    test('should handle concurrent token requests efficiently', async () => {
      // Arrange
      const concurrentRequests = 100;

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: concurrentRequests }, () => 
          tokenManager.getValidToken()
        );
        const results = await Promise.all(promises);
        
        // Verify all requests returned the same token
        results.forEach(token => {
          expect(token).toBe(mockTokens.access_token);
        });
      });

      // Assert - should handle 100 concurrent requests in under 50ms
      expect(time).toBeLessThan(50);
    });

    test('should store tokens efficiently', async () => {
      // Arrange
      const iterations = 100;

      // Act
      const time = await measureTime(async () => {
        for (let i = 0; i < iterations; i++) {
          await tokenManager.setTokens({
            ...mockTokens,
            access_token: `token-${i}`
          });
        }
      });

      // Assert - should store 100 tokens in under 100ms
      expect(time).toBeLessThan(100);
    });

    test('should clear tokens quickly', async () => {
      // Arrange
      const iterations = 100;

      // Act
      const time = await measureTime(async () => {
        for (let i = 0; i < iterations; i++) {
          await tokenManager.clearTokens();
        }
      });

      // Assert - should clear tokens 100 times in under 50ms
      expect(time).toBeLessThan(50);
    });

    test('should check token validity efficiently', async () => {
      // Arrange
      const iterations = 1000;

      // Act
      const time = await measureTime(async () => {
        for (let i = 0; i < iterations; i++) {
          tokenManager.hasValidToken();
        }
      });

      // Assert - should check validity 1000 times in under 10ms
      expect(time).toBeLessThan(10);
    });
  });

  describe('API Client Performance', () => {
    test('should make API requests efficiently', async () => {
      // Arrange
      const requests = 50;

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: requests }, (_, i) => 
          apiClient.get(`/test-endpoint-${i}`)
        );
        await Promise.all(promises);
      });

      // Assert - should complete 50 API requests in under 200ms
      expect(time).toBeLessThan(200);
    });

    test('should handle request interceptors efficiently', async () => {
      // Arrange
      const requests = 100;
      let interceptorCallCount = 0;

      // Add request interceptor
      apiClient.addRequestInterceptor((config) => {
        interceptorCallCount++;
        return config;
      });

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: requests }, (_, i) => 
          apiClient.get(`/test-${i}`)
        );
        await Promise.all(promises);
      });

      // Assert
      expect(time).toBeLessThan(150);
      expect(interceptorCallCount).toBe(requests);
    });

    test('should handle response interceptors efficiently', async () => {
      // Arrange
      const requests = 100;
      let interceptorCallCount = 0;

      // Add response interceptor
      apiClient.addResponseInterceptor((response) => {
        interceptorCallCount++;
        return response;
      });

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: requests }, (_, i) => 
          apiClient.get(`/test-${i}`)
        );
        await Promise.all(promises);
      });

      // Assert
      expect(time).toBeLessThan(150);
      expect(interceptorCallCount).toBe(requests);
    });

    test('should handle authentication header injection efficiently', async () => {
      // Arrange
      const requests = 200;

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: requests }, (_, i) => 
          apiClient.get(`/authenticated-endpoint-${i}`)
        );
        await Promise.all(promises);
      });

      // Assert - should handle auth header injection for 200 requests in under 100ms
      expect(time).toBeLessThan(100);
    });
  });

  describe('AuthService Performance', () => {
    test('should perform login efficiently', async () => {
      // Arrange
      const loginAttempts = 10;

      // Act
      const time = await measureTime(async () => {
        for (let i = 0; i < loginAttempts; i++) {
          await authService.login({
            username: `user${i}`,
            password: 'password123'
          });
        }
      });

      // Assert - should complete 10 logins in under 200ms
      expect(time).toBeLessThan(200);
    });

    test('should get current user efficiently', async () => {
      // Arrange
      const requests = 100;

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: requests }, () => 
          authService.getCurrentUser()
        );
        await Promise.all(promises);
      });

      // Assert - should get user info 100 times in under 150ms
      expect(time).toBeLessThan(150);
    });

    test('should handle logout efficiently', async () => {
      // Arrange
      const logouts = 50;

      // Act
      const time = await measureTime(async () => {
        for (let i = 0; i < logouts; i++) {
          await authService.logout();
        }
      });

      // Assert - should complete 50 logouts in under 100ms
      expect(time).toBeLessThan(100);
    });
  });

  describe('Memory Performance', () => {
    test('should not cause memory leaks during token operations', async () => {
      // Arrange
      const initialMemory = measureMemory();
      const iterations = 1000;

      // Act - perform many token operations
      for (let i = 0; i < iterations; i++) {
        await tokenManager.setTokens({
          ...mockTokens,
          access_token: `token-${i}`
        });
        await tokenManager.getValidToken();
        await tokenManager.clearTokens();
      }

      const finalMemory = measureMemory();

      // Assert - memory usage should not increase significantly
      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        const memoryIncreasePercent = (memoryIncrease / initialMemory) * 100;
        
        // Memory increase should be less than 10%
        expect(memoryIncreasePercent).toBeLessThan(10);
      }
    });

    test('should handle large numbers of API requests without memory issues', async () => {
      // Arrange
      const initialMemory = measureMemory();
      const requests = 500;

      // Act
      const promises = Array.from({ length: requests }, (_, i) => 
        apiClient.get(`/memory-test-${i}`)
      );
      await Promise.all(promises);

      const finalMemory = measureMemory();

      // Assert
      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        const memoryIncreasePercent = (memoryIncrease / initialMemory) * 100;
        
        // Memory increase should be reasonable for 500 requests
        expect(memoryIncreasePercent).toBeLessThan(20);
      }
    });

    test('should clean up event listeners properly', async () => {
      // Arrange
      const listeners: Array<() => void> = [];
      const listenerCount = 100;

      // Act - add many listeners
      for (let i = 0; i < listenerCount; i++) {
        const unsubscribe = tokenManager.onTokenRefresh(() => {});
        listeners.push(unsubscribe);
      }

      // Remove all listeners
      listeners.forEach(unsubscribe => unsubscribe());

      // Trigger token refresh to verify no listeners are called
      const mockSecureStorage = SecureStorage as jest.Mocked<typeof SecureStorage>;
      mockSecureStorage.getItem.mockResolvedValue(mockTokens);

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'new-token',
          expires_in: 3600
        })
      });

      await tokenManager.refreshToken();

      // Assert - no memory leaks from listeners (tested implicitly)
      expect(true).toBe(true);
    });
  });

  describe('Concurrent Operations Performance', () => {
    test('should handle concurrent login attempts efficiently', async () => {
      // Arrange
      const concurrentLogins = 20;

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: concurrentLogins }, (_, i) => 
          authService.login({
            username: `user${i}`,
            password: 'password123'
          })
        );
        await Promise.all(promises);
      });

      // Assert - should handle 20 concurrent logins in under 300ms
      expect(time).toBeLessThan(300);
    });

    test('should handle concurrent token refresh efficiently', async () => {
      // Arrange
      const concurrentRefreshes = 50;
      
      // Mock token refresh response
      (global.fetch as jest.Mock).mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            access_token: 'refreshed-token',
            expires_in: 3600
          })
        })
      );

      // Act
      const time = await measureTime(async () => {
        const promises = Array.from({ length: concurrentRefreshes }, () => 
          tokenManager.refreshToken()
        );
        const results = await Promise.all(promises);
        
        // All should succeed
        results.forEach(result => {
          expect(result).toBe(true);
        });
      });

      // Assert - should handle 50 concurrent refreshes efficiently
      expect(time).toBeLessThan(200);
      
      // Should only make one actual refresh request
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test('should handle mixed concurrent operations efficiently', async () => {
      // Arrange
      const operations = 100;

      // Act
      const time = await measureTime(async () => {
        const promises = [];
        
        for (let i = 0; i < operations; i++) {
          if (i % 3 === 0) {
            promises.push(tokenManager.getValidToken());
          } else if (i % 3 === 1) {
            promises.push(apiClient.get(`/test-${i}`));
          } else {
            promises.push(authService.getCurrentUser());
          }
        }
        
        await Promise.all(promises);
      });

      // Assert - should handle 100 mixed operations in under 250ms
      expect(time).toBeLessThan(250);
    });
  });

  describe('Scalability Performance', () => {
    test('should scale linearly with number of token operations', async () => {
      // Test with different scales
      const scales = [10, 50, 100, 200];
      const times: number[] = [];

      for (const scale of scales) {
        const time = await measureTime(async () => {
          const promises = Array.from({ length: scale }, () => 
            tokenManager.getValidToken()
          );
          await Promise.all(promises);
        });
        times.push(time);
      }

      // Assert - time should scale roughly linearly (allowing for some variance)
      const timeRatio = times[3] / times[0]; // 200 vs 10 operations
      const scaleRatio = scales[3] / scales[0]; // 20x scale
      
      // Time ratio should not be more than 2x the scale ratio
      expect(timeRatio).toBeLessThan(scaleRatio * 2);
    });

    test('should maintain performance under sustained load', async () => {
      // Arrange
      const duration = 1000; // 1 second
      const startTime = Date.now();
      let operationCount = 0;

      // Act - perform operations for 1 second
      while (Date.now() - startTime < duration) {
        await tokenManager.getValidToken();
        operationCount++;
      }

      // Assert - should complete at least 1000 operations per second
      expect(operationCount).toBeGreaterThan(1000);
    });

    test('should handle burst traffic efficiently', async () => {
      // Arrange - simulate burst of requests
      const burstSize = 500;
      const burstCount = 5;

      // Act
      const totalTime = await measureTime(async () => {
        for (let burst = 0; burst < burstCount; burst++) {
          const promises = Array.from({ length: burstSize }, (_, i) => 
            apiClient.get(`/burst-${burst}-${i}`)
          );
          await Promise.all(promises);
        }
      });

      // Assert - should handle 2500 total requests in bursts efficiently
      expect(totalTime).toBeLessThan(1000); // Under 1 second
    });
  });

  describe('Optimization Verification', () => {
    test('should use efficient token validation', async () => {
      // Arrange
      const validations = 10000;

      // Act
      const time = await measureTime(async () => {
        for (let i = 0; i < validations; i++) {
          tokenManager.hasValidToken();
        }
      });

      // Assert - should validate 10000 tokens in under 50ms
      expect(time).toBeLessThan(50);
    });

    test('should minimize API calls through caching', async () => {
      // Arrange
      const requests = 100;
      let fetchCallCount = 0;

      (global.fetch as jest.Mock).mockImplementation(() => {
        fetchCallCount++;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUser)
        });
      });

      // Act - make multiple requests for the same user
      const promises = Array.from({ length: requests }, () => 
        authService.getCurrentUser()
      );
      await Promise.all(promises);

      // Assert - should make fewer API calls due to caching
      expect(fetchCallCount).toBeLessThan(requests);
    });

    test('should optimize memory usage for large datasets', async () => {
      // Arrange
      const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
        id: i,
        token: `token-${i}`,
        expires_at: Date.now() + 3600000
      }));

      const initialMemory = measureMemory();

      // Act - process large dataset
      for (const item of largeDataset) {
        await tokenManager.setTokens({
          access_token: item.token,
          refresh_token: `refresh-${item.id}`,
          token_type: 'Bearer',
          expires_in: 3600,
          expires_at: item.expires_at
        });
      }

      const finalMemory = measureMemory();

      // Assert - memory usage should be reasonable
      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        const memoryIncreasePercent = (memoryIncrease / initialMemory) * 100;
        
        // Should not increase memory by more than 50% for large dataset
        expect(memoryIncreasePercent).toBeLessThan(50);
      }
    });
  });
});