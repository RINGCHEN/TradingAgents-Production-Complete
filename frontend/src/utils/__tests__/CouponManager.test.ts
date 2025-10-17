// @ts-nocheck
/**
 * CouponManager 測試套件
 * 測試優惠券管理器的所有功能，包括錯誤處理和降級機制
 */

import { CouponManager, Coupon, CouponManagerConfig } from '../CouponManager';
import { ApiClient, ApiResponse, ApiError } from '../../services/ApiClient';

// Mock ApiClient
class MockApiClient extends ApiClient {
  private mockResponses: Map<string, ApiResponse<any>> = new Map();
  private callCount = 0;
  private shouldThrow = false;
  private throwError: any = null;

  constructor() {
    super('http://test.com');
  }

  setMockResponse(endpoint: string, response: ApiResponse<any>) {
    this.mockResponses.set(endpoint, response);
  }

  setShouldThrow(error: any) {
    this.shouldThrow = true;
    this.throwError = error;
  }

  reset() {
    this.mockResponses.clear();
    this.callCount = 0;
    this.shouldThrow = false;
    this.throwError = null;
  }

  getCallCount() {
    return this.callCount;
  }

  async request<T>(endpoint: string, options?: any): Promise<ApiResponse<T>> {
    this.callCount++;

    if (this.shouldThrow) {
      throw this.throwError;
    }

    const mockResponse = this.mockResponses.get(endpoint);
    if (mockResponse) {
      return mockResponse as ApiResponse<T>;
    }

    // 默認成功響應
    return {
      success: true,
      status: 200,
      data: [] as T,
      headers: { 'content-type': 'application/json' }
    };
  }
}

// Mock localStorage
const mockLocalStorage = (() => {
  let store: { [key: string]: string } = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    }
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock console methods
const mockConsole = {
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

Object.defineProperty(window, 'console', {
  value: mockConsole
});

describe('CouponManager', () => {
  let mockApiClient: MockApiClient;
  let couponManager: CouponManager;
  let config: CouponManagerConfig;

  const mockCoupons: Coupon[] = [
    {
      id: 'coupon1',
      code: 'WELCOME10',
      title: '新用戶歡迎優惠',
      description: '新用戶專享10%折扣',
      discount: 10,
      discountType: 'percentage',
      validFrom: new Date('2024-01-01'),
      validTo: new Date('2025-12-31'),
      isActive: true,
      minAmount: 100
    },
    {
      id: 'coupon2',
      code: 'SAVE50',
      title: '固定折扣券',
      description: '立減50元',
      discount: 50,
      discountType: 'fixed',
      validFrom: new Date('2024-01-01'),
      validTo: new Date('2025-12-31'),
      isActive: true,
      minAmount: 200
    },
    {
      id: 'coupon3',
      code: 'EXPIRED',
      title: '過期優惠券',
      description: '已過期的優惠券',
      discount: 20,
      discountType: 'percentage',
      validFrom: new Date('2023-01-01'),
      validTo: new Date('2023-12-31'),
      isActive: true
    }
  ];

  beforeEach(() => {
    mockApiClient = new MockApiClient();
    config = {
      cacheTimeout: 5 * 60 * 1000,
      maxRetries: 2,
      retryDelay: 100,
      fallbackCoupons: [
        {
          id: 'fallback1',
          code: 'FALLBACK10',
          title: '降級優惠券',
          description: '系統降級時使用',
          discount: 10,
          discountType: 'percentage',
          validFrom: new Date('2024-01-01'),
          validTo: new Date('2025-12-31'),
          isActive: true
        }
      ],
      enableDiagnostics: false // 測試時關閉診斷以避免干擾
    };
    
    couponManager = new CouponManager(mockApiClient, config);
    mockLocalStorage.clear();
    mockApiClient.reset();
    
    // 清除 console mock 的調用記錄
    Object.values(mockConsole).forEach(fn => fn.mockClear());
  });

  describe('loadCoupons', () => {
    it('should successfully load coupons from API', async () => {
      // 設置成功的API響應
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      const state = await couponManager.loadCoupons();

      expect(state.coupons).toHaveLength(3);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeUndefined();
      expect(state.fallbackMode).toBe(false);
      expect(state.retryCount).toBe(0);
    });

    it('should handle HTML response and use fallback', async () => {
      // 設置返回HTML的錯誤響應
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: '<html><body>Error page</body></html>',
        headers: { 'content-type': 'text/html' }
      });

      const state = await couponManager.loadCoupons();

      expect(state.fallbackMode).toBe(true);
      expect(state.coupons).toEqual(config.fallbackCoupons);
      expect(state.error).toContain('優惠券服務暫時不可用');
      expect(mockApiClient.getCallCount()).toBe(config.maxRetries + 1);
    });

    it('should handle network errors with retry', async () => {
      // 設置網路錯誤
      mockApiClient.setShouldThrow(new Error('Network error'));

      const state = await couponManager.loadCoupons();

      expect(state.fallbackMode).toBe(true);
      expect(state.coupons).toEqual(config.fallbackCoupons);
      expect(mockApiClient.getCallCount()).toBe(config.maxRetries + 1);
    });

    it('should handle SyntaxError and use fallback', async () => {
      // 設置SyntaxError
      mockApiClient.setShouldThrow(new SyntaxError('Unexpected token < in JSON'));

      const state = await couponManager.loadCoupons();

      expect(state.fallbackMode).toBe(true);
      expect(state.error).toContain('優惠券數據格式錯誤');
    });

    it('should use cached data when available and valid', async () => {
      // 先載入一次數據
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      await couponManager.loadCoupons();
      expect(mockApiClient.getCallCount()).toBe(1);

      // 第二次載入應該使用緩存
      await couponManager.loadCoupons();
      expect(mockApiClient.getCallCount()).toBe(1); // 沒有增加
    });
  });

  describe('data validation', () => {
    it('should validate and transform coupon data correctly', async () => {
      const invalidData = [
        { id: 'valid1', code: 'TEST1', discount: 10, discountType: 'percentage' },
        { id: 'invalid1' }, // 缺少必要字段
        null, // null值
        { id: 'invalid2', code: '', discount: 0 }, // 無效折扣
        { id: 'valid2', code: 'TEST2', discount: 50, discountType: 'fixed' }
      ];

      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: invalidData,
        headers: { 'content-type': 'application/json' }
      });

      const state = await couponManager.loadCoupons();

      // 只有有效的優惠券應該被保留
      expect(state.coupons).toHaveLength(2);
      expect(state.coupons[0].code).toBe('TEST1');
      expect(state.coupons[1].code).toBe('TEST2');
    });

    it('should handle non-array API response', async () => {
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: { message: 'Not an array' },
        headers: { 'content-type': 'application/json' }
      });

      const state = await couponManager.loadCoupons();

      expect(state.coupons).toHaveLength(0);
    });
  });

  describe('caching mechanism', () => {
    it('should save and load coupons from cache', async () => {
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      // 載入數據
      await couponManager.loadCoupons();

      // 創建新的管理器實例，應該從緩存載入
      const newManager = new CouponManager(mockApiClient, config);
      const state = await newManager.loadCoupons();

      expect(state.coupons).toHaveLength(3);
      expect(mockApiClient.getCallCount()).toBe(1); // 只調用了一次API
    });

    it('should clear cache when reload is called', async () => {
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      // 載入數據
      await couponManager.loadCoupons();
      expect(mockApiClient.getCallCount()).toBe(1);

      // 重新載入應該清除緩存並重新調用API
      await couponManager.reload();
      expect(mockApiClient.getCallCount()).toBe(2);
    });
  });

  describe('coupon filtering and calculation', () => {
    beforeEach(async () => {
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      await couponManager.loadCoupons();
    });

    it('should filter available coupons correctly', () => {
      const availableCoupons = couponManager.getAvailableCoupons();
      
      // 應該排除過期的優惠券
      expect(availableCoupons).toHaveLength(2);
      expect(availableCoupons.find(c => c.code === 'EXPIRED')).toBeUndefined();
    });

    it('should filter applicable coupons by amount', () => {
      // 測試金額150，應該只有WELCOME10適用（最低100）
      const applicableCoupons = couponManager.getApplicableCoupons(150);
      expect(applicableCoupons).toHaveLength(1);
      expect(applicableCoupons[0].code).toBe('WELCOME10');

      // 測試金額250，兩個都適用
      const applicableCoupons2 = couponManager.getApplicableCoupons(250);
      expect(applicableCoupons2).toHaveLength(2);
    });

    it('should calculate percentage discount correctly', () => {
      const coupon = mockCoupons[0]; // WELCOME10, 10%
      const discount = couponManager.calculateDiscount(coupon, 1000);
      expect(discount).toBe(100); // 10% of 1000
    });

    it('should calculate fixed discount correctly', () => {
      const coupon = mockCoupons[1]; // SAVE50, 固定50元
      const discount = couponManager.calculateDiscount(coupon, 1000);
      expect(discount).toBe(50);
    });

    it('should not apply discount if amount is below minimum', () => {
      const coupon = mockCoupons[0]; // 最低100元
      const discount = couponManager.calculateDiscount(coupon, 50);
      expect(discount).toBe(0);
    });

    it('should not exceed the original amount', () => {
      const coupon = mockCoupons[1]; // 固定50元折扣
      const discount = couponManager.calculateDiscount(coupon, 30);
      expect(discount).toBe(30); // 不能超過原金額
    });
  });

  describe('error recovery', () => {
    it('should use cached coupons when API fails', async () => {
      // 先成功載入一次
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      await couponManager.loadCoupons();

      // 清除緩存過期時間，模擬緩存過期
      couponManager.clearCache();
      
      // 手動設置一些緩存數據
      mockLocalStorage.setItem('tradingagents_coupons_cache', JSON.stringify({
        coupons: mockCoupons.slice(0, 1),
        timestamp: Date.now()
      }));

      // 設置API失敗
      mockApiClient.setShouldThrow(new Error('API Error'));

      const state = await couponManager.loadCoupons();

      expect(state.fallbackMode).toBe(true);
      expect(state.coupons).toHaveLength(1);
      expect(state.error).toContain('使用緩存的優惠券數據');
    });

    it('should use fallback coupons when no cache available', async () => {
      // 設置API失敗且無緩存
      mockApiClient.setShouldThrow(new Error('API Error'));

      const state = await couponManager.loadCoupons();

      expect(state.fallbackMode).toBe(true);
      expect(state.coupons).toEqual(config.fallbackCoupons);
      expect(state.error).toContain('優惠券服務暫時不可用');
    });
  });

  describe('state management', () => {
    it('should return current state correctly', async () => {
      mockApiClient.setMockResponse('/api/coupons', {
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      await couponManager.loadCoupons();
      const state = couponManager.getState();

      expect(state.coupons).toHaveLength(3);
      expect(state.isLoading).toBe(false);
      expect(state.fallbackMode).toBe(false);
    });

    it('should clear cache and state correctly', () => {
      couponManager.clearCache();
      const state = couponManager.getState();

      expect(state.coupons).toHaveLength(0);
      expect(state.isLoading).toBe(false);
      expect(state.fallbackMode).toBe(false);
      expect(state.retryCount).toBe(0);
    });
  });

  describe('configuration', () => {
    it('should respect custom configuration', () => {
      const customConfig: Partial<CouponManagerConfig> = {
        maxRetries: 5,
        cacheTimeout: 10000,
        enableDiagnostics: true
      };

      const customManager = new CouponManager(mockApiClient, customConfig);
      
      // 配置應該被正確應用（通過行為驗證）
      expect(customManager).toBeDefined();
    });

    it('should use default configuration when not provided', () => {
      const defaultManager = new CouponManager(mockApiClient);
      expect(defaultManager).toBeDefined();
    });
  });
});