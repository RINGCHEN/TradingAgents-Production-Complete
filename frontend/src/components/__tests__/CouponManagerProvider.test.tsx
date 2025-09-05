/**
 * CouponManagerProvider 測試套件
 * 測試React上下文和hooks的功能
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CouponManagerProvider, useCoupons, useAvailableCoupons, useCouponCalculator } from '../CouponManagerProvider';
import { ApiClientProvider } from '../ApiClientProvider';
import { ApiClient } from '../../services/ApiClient';

// Mock ApiClient
jest.mock('../../services/ApiClient');
const MockedApiClient = ApiClient as jest.MockedClass<typeof ApiClient>;

// Mock ErrorDiagnostics
jest.mock('../../utils/ErrorDiagnostics', () => ({
  reportComponentError: jest.fn()
}));

// Mock localStorage
const mockLocalStorage = (() => {
  let store: { [key: string]: string } = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

const mockCoupons = [
  {
    id: 'coupon1',
    code: 'WELCOME10',
    title: '新用戶歡迎優惠',
    description: '新用戶專享10%折扣',
    discount: 10,
    discountType: 'percentage' as const,
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
    discountType: 'fixed' as const,
    validFrom: new Date('2024-01-01'),
    validTo: new Date('2025-12-31'),
    isActive: true,
    minAmount: 200
  }
];

// 測試組件
const TestComponent: React.FC = () => {
  const { coupons, loading, error, refetch, reload } = useCoupons();
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'loaded'}</div>
      <div data-testid="error">{error || 'no-error'}</div>
      <div data-testid="coupon-count">{coupons.length}</div>
      <button onClick={refetch} data-testid="refetch-btn">Refetch</button>
      <button onClick={reload} data-testid="reload-btn">Reload</button>
      {coupons.map(coupon => (
        <div key={coupon.id} data-testid={`coupon-${coupon.id}`}>
          {coupon.code}
        </div>
      ))}
    </div>
  );
};

const AvailableCouponsTestComponent: React.FC = () => {
  const availableCoupons = useAvailableCoupons();
  
  return (
    <div>
      <div data-testid="available-count">{availableCoupons.length}</div>
      {availableCoupons.map(coupon => (
        <div key={coupon.id} data-testid={`available-${coupon.id}`}>
          {coupon.code}
        </div>
      ))}
    </div>
  );
};

const CalculatorTestComponent: React.FC = () => {
  const { getApplicableCoupons, calculateDiscount, getBestCoupon } = useCouponCalculator();
  const [amount, setAmount] = React.useState(1000);
  
  const applicableCoupons = getApplicableCoupons(amount);
  const bestCoupon = getBestCoupon(amount);
  
  return (
    <div>
      <input
        data-testid="amount-input"
        type="number"
        value={amount}
        onChange={(e) => setAmount(Number(e.target.value))}
      />
      <div data-testid="applicable-count">{applicableCoupons.length}</div>
      <div data-testid="best-coupon">{bestCoupon.coupon?.code || 'none'}</div>
      <div data-testid="best-discount">{bestCoupon.discount}</div>
    </div>
  );
};

describe('CouponManagerProvider', () => {
  let mockApiClient: jest.Mocked<ApiClient>;

  beforeEach(() => {
    mockLocalStorage.clear();
    
    // 創建 mock ApiClient 實例
    mockApiClient = {
      request: jest.fn(),
      healthCheck: jest.fn().mockResolvedValue(true)
    } as any;

    // 設置 ApiClient 構造函數返回 mock 實例
    MockedApiClient.mockImplementation(() => mockApiClient);
  });

  const renderWithProviders = (component: React.ReactElement, config = {}) => {
    return render(
      <ApiClientProvider>
        <CouponManagerProvider config={config} autoLoad={false}>
          {component}
        </CouponManagerProvider>
      </ApiClientProvider>
    );
  };

  describe('useCoupons hook', () => {
    it('should provide initial state', () => {
      renderWithProviders(<TestComponent />);
      
      expect(screen.getByTestId('loading')).toHaveTextContent('loaded');
      expect(screen.getByTestId('error')).toHaveTextContent('no-error');
      expect(screen.getByTestId('coupon-count')).toHaveTextContent('0');
    });

    it('should load coupons successfully', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      renderWithProviders(<TestComponent />);
      
      // 觸發載入
      await act(async () => {
        userEvent.click(screen.getByTestId('refetch-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('coupon-count')).toHaveTextContent('2');
      });

      expect(screen.getByTestId('coupon-coupon1')).toHaveTextContent('WELCOME10');
      expect(screen.getByTestId('coupon-coupon2')).toHaveTextContent('SAVE50');
    });

    it('should handle API errors gracefully', async () => {
      mockApiClient.request.mockRejectedValue(new Error('API Error'));

      renderWithProviders(<TestComponent />);
      
      await act(async () => {
        userEvent.click(screen.getByTestId('refetch-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('error')).not.toHaveTextContent('no-error');
      });
    });

    it('should handle reload functionality', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      renderWithProviders(<TestComponent />);
      
      await act(async () => {
        userEvent.click(screen.getByTestId('reload-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('coupon-count')).toHaveTextContent('2');
      });
    });
  });

  describe('useAvailableCoupons hook', () => {
    it('should filter available coupons', async () => {
      const couponsWithExpired = [
        ...mockCoupons,
        {
          id: 'expired',
          code: 'EXPIRED',
          title: '過期優惠券',
          description: '已過期',
          discount: 20,
          discountType: 'percentage' as const,
          validFrom: new Date('2023-01-01'),
          validTo: new Date('2023-12-31'),
          isActive: true
        }
      ];

      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: couponsWithExpired,
        headers: { 'content-type': 'application/json' }
      });

      const TestWrapper = () => (
        <div>
          <TestComponent />
          <AvailableCouponsTestComponent />
        </div>
      );

      renderWithProviders(<TestWrapper />);
      
      await act(async () => {
        userEvent.click(screen.getByTestId('refetch-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('coupon-count')).toHaveTextContent('3');
        expect(screen.getByTestId('available-count')).toHaveTextContent('2'); // 排除過期的
      });

      expect(screen.getByTestId('available-coupon1')).toHaveTextContent('WELCOME10');
      expect(screen.getByTestId('available-coupon2')).toHaveTextContent('SAVE50');
      expect(screen.queryByTestId('available-expired')).not.toBeInTheDocument();
    });
  });

  describe('useCouponCalculator hook', () => {
    beforeEach(async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });
    });

    it('should calculate applicable coupons based on amount', async () => {
      const TestWrapper = () => (
        <div>
          <TestComponent />
          <CalculatorTestComponent />
        </div>
      );

      renderWithProviders(<TestWrapper />);
      
      await act(async () => {
        userEvent.click(screen.getByTestId('refetch-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('coupon-count')).toHaveTextContent('2');
      });

      // 測試金額1000，兩個優惠券都適用
      expect(screen.getByTestId('applicable-count')).toHaveTextContent('2');

      // 改變金額到150，只有WELCOME10適用（最低100）
      await act(async () => {
        const input = screen.getByTestId('amount-input');
        await userEvent.clear(input);
        await userEvent.type(input, '150');
      });

      await waitFor(() => {
        expect(screen.getByTestId('applicable-count')).toHaveTextContent('1');
      });
    });

    it('should find the best coupon', async () => {
      const TestWrapper = () => (
        <div>
          <TestComponent />
          <CalculatorTestComponent />
        </div>
      );

      renderWithProviders(<TestWrapper />);
      
      await act(async () => {
        userEvent.click(screen.getByTestId('refetch-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('coupon-count')).toHaveTextContent('2');
      });

      // 對於金額1000，WELCOME10給100折扣（10%），SAVE50給50折扣
      // 所以WELCOME10應該是最佳選擇
      await waitFor(() => {
        expect(screen.getByTestId('best-coupon')).toHaveTextContent('WELCOME10');
        expect(screen.getByTestId('best-discount')).toHaveTextContent('100');
      });

      // 改變金額到300，SAVE50可能更好
      await act(async () => {
        const input = screen.getByTestId('amount-input');
        await userEvent.clear(input);
        await userEvent.type(input, '300');
      });

      await waitFor(() => {
        // WELCOME10: 300 * 10% = 30
        // SAVE50: 50 (固定)
        // 所以SAVE50更好
        expect(screen.getByTestId('best-coupon')).toHaveTextContent('SAVE50');
        expect(screen.getByTestId('best-discount')).toHaveTextContent('50');
      });
    });
  });

  describe('error handling', () => {
    it('should handle provider initialization errors', () => {
      const onError = jest.fn();
      
      renderWithProviders(<TestComponent />, { onError });
      
      // Provider應該正常初始化，不會調用onError
      expect(onError).not.toHaveBeenCalled();
    });

    it('should call onError when API fails', async () => {
      const onError = jest.fn();
      mockApiClient.request.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<TestComponent />, { onError });
      
      await act(async () => {
        userEvent.click(screen.getByTestId('refetch-btn'));
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });
  });

  describe('configuration', () => {
    it('should accept custom configuration', () => {
      const customConfig = {
        maxRetries: 5,
        cacheTimeout: 10000
      };

      renderWithProviders(<TestComponent />, customConfig);
      
      // 組件應該正常渲染
      expect(screen.getByTestId('loading')).toHaveTextContent('loaded');
    });

    it('should support autoLoad=false', () => {
      renderWithProviders(<TestComponent />);
      
      // 不應該自動載入，API不應該被調用
      expect(mockApiClient.request).not.toHaveBeenCalled();
    });
  });

  describe('context error handling', () => {
    it('should throw error when used outside provider', () => {
      // 抑制 console.error 以避免測試輸出中的錯誤信息
      const originalError = console.error;
      console.error = jest.fn();

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useCouponManager must be used within a CouponManagerProvider');

      console.error = originalError;
    });
  });
});