// 性能優化測試套件
// 測試TokenManager、ApiClient和PerformanceOptimizer的性能改進

import { TokenManager } from '../../services/TokenManager';
import { ApiClient } from '../../services/ApiClient';
import { PerformanceOptimizer } from '../../services/PerformanceOptimizer';

describe('Performance Optimization Tests', () => {
  let tokenManager: TokenManager;
  let apiClient: ApiClient;
  let performanceOptimizer: PerformanceOptimizer;

  beforeEach(() => {
    tokenManager = new TokenManager();
    apiClient = new ApiClient();
    performanceOptimizer = PerformanceOptimizer.getInstance();
    
    // 清理之前的測試數據
    performanceOptimizer.clearMetrics();
  });

  afterEach(() => {
    // 清理資源
    tokenManager.cleanup();
    apiClient.cleanup();
    performanceOptimizer.clearMetrics();
  });

  describe('TokenManager Performance', () => {
    test('should cache tokens in memory for fast access', async () => {
      const mockTokens = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        expires_in: 3600,
        expires_at: Date.now() + 3600000
      };

      // 設置token
      await tokenManager.setTokens(mockTokens);

      // 測試多次獲取token的性能
      const iterations = 100;
      const startTime = performance.now();

      for (let i = 0; i < iterations; i++) {
        await tokenManager.getValidToken();
      }

      const endTime = performance.now();
      const averageTime = (endTime - startTime) / iterations;

      // 平均每次獲取應該小於1ms（使用緩存）
      expect(averageTime).toBeLessThan(1);
    });

    test('should schedule proactive token refresh', async () => {
      const mockTokens = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        expires_in: 600, // 10分鐘
        expires_at: Date.now() + 600000
      };

      await tokenManager.setTokens(mockTokens);
      
      // 檢查token統計信息
      const stats = tokenManager.getTokenStats();
      expect(stats.hasCache).toBe(true);
      expect(stats.cacheExpiresIn).toBeGreaterThan(0);
    });

    test('should handle batch token operations efficiently', async () => {
      const mockTokens = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        expires_in: 3600,
        expires_at: Date.now() + 3600000
      };

      await tokenManager.setTokens(mockTokens);

      // 批量操作
      const operations = Array(10).fill(0).map(() => 
        () => Promise.resolve(`operation-${Math.random()}`)
      );

      const startTime = performance.now();
      const results = await tokenManager.batchTokenOperations(operations);
      const endTime = performance.now();

      expect(results).toHaveLength(10);
      expect(endTime - startTime).toBeLessThan(100); // 應該在100ms內完成
    });
  });

  describe('ApiClient Performance', () => {
    test('should cache GET requests to reduce network calls', async () => {
      // Mock fetch
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: 'test' })
      });
      global.fetch = mockFetch;

      const url = '/test-endpoint';
      
      // 第一次請求
      await apiClient.get(url, { useCache: true });
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // 第二次請求應該使用緩存
      await apiClient.get(url, { useCache: true });
      expect(mockFetch).toHaveBeenCalledTimes(1); // 仍然是1次，使用了緩存
    });

    test('should deduplicate concurrent requests', async () => {
      const mockFetch = jest.fn().mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ data: 'test' })
          }), 100)
        )
      );
      global.fetch = mockFetch;

      const url = '/test-endpoint';
      
      // 並發發送多個相同請求
      const promises = Array(5).fill(0).map(() => apiClient.get(url));
      await Promise.all(promises);

      // 應該只發送一次實際請求
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test('should handle batch requests efficiently', async () => {
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: 'test' })
      });
      global.fetch = mockFetch;

      const requests = [
        { method: 'GET' as const, url: '/endpoint1' },
        { method: 'GET' as const, url: '/endpoint2' },
        { method: 'POST' as const, url: '/endpoint3', data: { test: true } }
      ];

      const startTime = performance.now();
      const results = await apiClient.batchRequests(requests);
      const endTime = performance.now();

      expect(results).toHaveLength(3);
      expect(endTime - startTime).toBeLessThan(200); // 批量處理應該很快
    });

    test('should provide performance statistics', () => {
      const stats = apiClient.getStats();
      
      expect(stats).toHaveProperty('cacheSize');
      expect(stats).toHaveProperty('pendingRequests');
      expect(stats).toHaveProperty('queueSize');
      expect(stats).toHaveProperty('isRefreshingToken');
      
      expect(typeof stats.cacheSize).toBe('number');
      expect(typeof stats.pendingRequests).toBe('number');
      expect(typeof stats.queueSize).toBe('number');
      expect(typeof stats.isRefreshingToken).toBe('boolean');
    });
  });

  describe('PerformanceOptimizer', () => {
    test('should create optimized memoization', () => {
      let computeCount = 0;
      const expensiveComputation = () => {
        computeCount++;
        return 'computed-value';
      };

      const memoized = performanceOptimizer.useOptimizedMemo(
        expensiveComputation,
        [],
        'test-component'
      );

      // 第一次調用
      expect(memoized).toBe('computed-value');
      expect(computeCount).toBe(1);

      // 第二次調用應該使用緩存
      const memoized2 = performanceOptimizer.useOptimizedMemo(
        expensiveComputation,
        [],
        'test-component'
      );
      expect(memoized2).toBe('computed-value');
      expect(computeCount).toBe(1); // 沒有重新計算
    });

    test('should create debounced functions', (done) => {
      let callCount = 0;
      const testFunction = () => {
        callCount++;
      };

      const debouncedFn = performanceOptimizer.createDebouncer(testFunction, 100);

      // 快速調用多次
      debouncedFn();
      debouncedFn();
      debouncedFn();

      // 立即檢查，應該還沒有執行
      expect(callCount).toBe(0);

      // 等待debounce延遲後檢查
      setTimeout(() => {
        expect(callCount).toBe(1); // 只執行一次
        done();
      }, 150);
    });

    test('should create throttled functions', (done) => {
      let callCount = 0;
      const testFunction = () => {
        callCount++;
      };

      const throttledFn = performanceOptimizer.createThrottler(testFunction, 100);

      // 快速調用多次
      throttledFn(); // 第一次立即執行
      throttledFn(); // 被節流
      throttledFn(); // 被節流

      expect(callCount).toBe(1);

      // 等待節流延遲後再調用
      setTimeout(() => {
        throttledFn(); // 應該執行
        expect(callCount).toBe(2);
        done();
      }, 150);
    });

    test('should batch DOM updates', (done) => {
      const updates: Array<() => void> = [];
      let updateCount = 0;

      // 創建多個DOM更新操作
      for (let i = 0; i < 5; i++) {
        updates.push(() => {
          updateCount++;
        });
      }

      performanceOptimizer.batchDOMUpdates(updates);

      // 使用requestAnimationFrame的下一個週期檢查
      requestAnimationFrame(() => {
        expect(updateCount).toBe(5);
        done();
      });
    });

    test('should generate performance reports', () => {
      // 添加一些測試指標
      performanceOptimizer.clearMetrics();
      
      const report = performanceOptimizer.generatePerformanceReport();
      
      expect(report).toHaveProperty('componentMetrics');
      expect(report).toHaveProperty('memoryUsage');
      expect(report).toHaveProperty('timestamp');
      
      expect(Array.isArray(report.componentMetrics)).toBe(true);
      expect(typeof report.timestamp).toBe('number');
    });

    test('should track memory usage', () => {
      const memoryUsage = performanceOptimizer.getMemoryUsage();
      
      if (memoryUsage) {
        expect(memoryUsage).toHaveProperty('used');
        expect(memoryUsage).toHaveProperty('total');
        expect(memoryUsage).toHaveProperty('percentage');
        
        expect(typeof memoryUsage.used).toBe('number');
        expect(typeof memoryUsage.total).toBe('number');
        expect(typeof memoryUsage.percentage).toBe('number');
        
        expect(memoryUsage.percentage).toBeGreaterThanOrEqual(0);
        expect(memoryUsage.percentage).toBeLessThanOrEqual(100);
      }
    });
  });

  describe('Integration Performance Tests', () => {
    test('should maintain performance under load', async () => {
      const mockTokens = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        expires_in: 3600,
        expires_at: Date.now() + 3600000
      };

      await tokenManager.setTokens(mockTokens);

      // 模擬高負載情況
      const operations = Array(50).fill(0).map((_, i) => async () => {
        const token = await tokenManager.getValidToken();
        expect(token).toBe('test-token');
        return `operation-${i}`;
      });

      const startTime = performance.now();
      const results = await Promise.all(operations.map(op => op()));
      const endTime = performance.now();

      expect(results).toHaveLength(50);
      expect(endTime - startTime).toBeLessThan(100); // 應該在100ms內完成
    });

    test('should optimize component rendering performance', () => {
      // 模擬組件渲染
      const TestComponent = () => 'test';
      const MemoizedComponent = performanceOptimizer.memoizeComponent(TestComponent, 'TestComponent');

      expect(MemoizedComponent).toBeDefined();
      expect(MemoizedComponent.displayName).toBe('Memo(TestComponent)');
    });

    test('should handle virtual scrolling configuration', () => {
      const config = performanceOptimizer.createVirtualScrollConfig(1000, 50, 500);
      
      expect(config).toHaveProperty('startIndex');
      expect(config).toHaveProperty('endIndex');
      expect(config).toHaveProperty('visibleItems');
      expect(config).toHaveProperty('bufferSize');
      
      expect(config.visibleItems).toBe(10); // 500 / 50
      expect(config.bufferSize).toBe(5); // Math.max(5, Math.ceil(10 * 0.5))
      expect(config.endIndex).toBeLessThan(1000);
    });
  });

  describe('Performance Benchmarks', () => {
    test('token operations should meet performance benchmarks', async () => {
      const mockTokens = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        expires_in: 3600,
        expires_at: Date.now() + 3600000
      };

      await tokenManager.setTokens(mockTokens);

      // 基準測試：1000次token獲取應該在10ms內完成
      const iterations = 1000;
      const startTime = performance.now();

      for (let i = 0; i < iterations; i++) {
        await tokenManager.getValidToken();
      }

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      expect(totalTime).toBeLessThan(10); // 10ms基準
      
      const averageTime = totalTime / iterations;
      expect(averageTime).toBeLessThan(0.01); // 平均每次小於0.01ms
    });

    test('API cache should improve response times', async () => {
      const mockFetch = jest.fn().mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ data: 'test' })
          }), 50) // 模擬50ms網絡延遲
        )
      );
      global.fetch = mockFetch;

      const url = '/benchmark-endpoint';

      // 第一次請求（無緩存）
      const startTime1 = performance.now();
      await apiClient.get(url, { useCache: true });
      const endTime1 = performance.now();
      const firstRequestTime = endTime1 - startTime1;

      // 第二次請求（使用緩存）
      const startTime2 = performance.now();
      await apiClient.get(url, { useCache: true });
      const endTime2 = performance.now();
      const cachedRequestTime = endTime2 - startTime2;

      // 緩存請求應該明顯更快
      expect(cachedRequestTime).toBeLessThan(firstRequestTime / 10);
      expect(cachedRequestTime).toBeLessThan(5); // 緩存請求應該在5ms內
    });
  });
});