/**
 * CouponManager 整合測試
 * 測試CouponManager與現有系統的整合
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CouponManagerProvider, useCoupons } from '../CouponManagerProvider';
import { ApiClientProvider } from '../ApiClientProvider';
import CouponManagerDemo from '../CouponManagerDemo';
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
    discountType: 'percentage',
    validFrom: '2024-01-01T00:00:00.000Z',
    validTo: '2025-12-31T23:59:59.999Z',
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
    validFrom: '2024-01-01T00:00:00.000Z',
    validTo: '2025-12-31T23:59:59.999Z',
    isActive: true,
    minAmount: 200
  }
];

describe('CouponManager Integration Tests', () => {
  let mockApiClient: jest.Mocked<ApiClient>;

  beforeEach(() => {
    mockLocalStorage.clear();
    
    mockApiClient = {
      request: jest.fn(),
      healthCheck: jest.fn().mockResolvedValue(true)
    } as any;

    MockedApiClient.mockImplementation(() => mockApiClient);
  });

  const renderIntegrationTest = (component: React.ReactElement) => {
    return render(
      <ApiClientProvider>
        <CouponManagerProvider autoLoad={false}>
          {component}
        </CouponManagerProvider>
      </ApiClientProvider>
    );
  };

  describe('與ApiClientProvider整合', () => {
    it('should work with ApiClientProvider', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      const TestComponent = () => {
        const { coupons, loading, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="status">{loading ? 'loading' : 'loaded'}</div>
            <div data-testid="count">{coupons.length}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      expect(screen.getByTestId('count')).toHaveTextContent('0');

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('2');
      });

      expect(mockApiClient.request).toHaveBeenCalledWith('/api/coupons', expect.any(Object));
    });
  });

  describe('錯誤處理整合', () => {
    it('should handle HTML response error (SyntaxError fix)', async () => {
      // 模擬返回HTML的錯誤（常見的SyntaxError原因）
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: '<html><body>Error page</body></html>',
        headers: { 'content-type': 'text/html' }
      });

      const TestComponent = () => {
        const { coupons, loading, error, fallbackMode, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="status">{loading ? 'loading' : 'loaded'}</div>
            <div data-testid="count">{coupons.length}</div>
            <div data-testid="error">{error || 'no-error'}</div>
            <div data-testid="fallback">{fallbackMode ? 'fallback' : 'normal'}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('fallback')).toHaveTextContent('fallback');
      });

      // 應該使用降級優惠券
      expect(screen.getByTestId('count')).toHaveTextContent('1'); // 預設有一個降級優惠券
      expect(screen.getByTestId('error')).toHaveTextContent('優惠券服務暫時不可用，顯示預設優惠');
    });

    it('should handle network errors with retry', async () => {
      mockApiClient.request
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          success: true,
          status: 200,
          data: mockCoupons,
          headers: { 'content-type': 'application/json' }
        });

      const TestComponent = () => {
        const { coupons, loading, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="count">{coupons.length}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('2');
      });

      // 應該重試3次（初始 + 2次重試）
      expect(mockApiClient.request).toHaveBeenCalledTimes(3);
    });

    it('should handle SyntaxError specifically', async () => {
      mockApiClient.request.mockRejectedValue(
        new SyntaxError('Unexpected token < in JSON at position 0')
      );

      const TestComponent = () => {
        const { error, fallbackMode, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="error">{error || 'no-error'}</div>
            <div data-testid="fallback">{fallbackMode ? 'fallback' : 'normal'}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('優惠券數據格式錯誤');
        expect(screen.getByTestId('fallback')).toHaveTextContent('fallback');
      });
    });
  });

  describe('緩存機制整合', () => {
    it('should use cache across component remounts', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      const TestComponent = () => {
        const { coupons, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="count">{coupons.length}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      // 第一次渲染並載入數據
      const { unmount } = renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('2');
      });

      expect(mockApiClient.request).toHaveBeenCalledTimes(1);

      // 卸載組件
      unmount();

      // 重新渲染，應該使用緩存
      renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      // 應該立即顯示緩存的數據，不再調用API
      expect(screen.getByTestId('count')).toHaveTextContent('2');
      expect(mockApiClient.request).toHaveBeenCalledTimes(1); // 沒有增加
    });
  });

  describe('CouponManagerDemo整合', () => {
    it('should render demo component without errors', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      renderIntegrationTest(<CouponManagerDemo />);

      // 檢查主要元素是否存在
      expect(screen.getByText('🎫 優惠券管理器演示')).toBeInTheDocument();
      expect(screen.getByText('系統狀態')).toBeInTheDocument();
      expect(screen.getByText('控制操作')).toBeInTheDocument();
      expect(screen.getByText('優惠券計算器')).toBeInTheDocument();

      // 檢查初始狀態
      expect(screen.getByText('✅ 正常')).toBeInTheDocument(); // 健康狀態
      expect(screen.getByText('✅ 正常模式')).toBeInTheDocument(); // 運行模式
    });

    it('should show fallback mode in demo when API fails', async () => {
      mockApiClient.request.mockRejectedValue(new Error('API Error'));

      renderIntegrationTest(<CouponManagerDemo />);

      // 觸發載入
      const loadButton = screen.getByText('重新載入');
      await act(async () => {
        userEvent.click(loadButton);
      });

      await waitFor(() => {
        expect(screen.getByText('⚠️ 降級模式')).toBeInTheDocument();
      });
    });
  });

  describe('性能測試', () => {
    it('should handle multiple rapid requests gracefully', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

      const TestComponent = () => {
        const { coupons, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="count">{coupons.length}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      // 快速點擊多次
      const loadButton = screen.getByTestId('load-btn');
      
      await act(async () => {
        userEvent.click(loadButton);
        userEvent.click(loadButton);
        userEvent.click(loadButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('2');
      });

      // 應該正常處理，不會崩潰
      expect(screen.getByTestId('count')).toBeInTheDocument();
    });
  });

  describe('邊界情況測試', () => {
    it('should handle empty API response', async () => {
      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: [],
        headers: { 'content-type': 'application/json' }
      });

      const TestComponent = () => {
        const { coupons, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="count">{coupons.length}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('0');
      });
    });

    it('should handle malformed coupon data', async () => {
      const malformedData = [
        { id: 'valid', code: 'VALID', discount: 10, discountType: 'percentage' },
        { invalid: 'data' },
        null,
        { id: 'invalid2', code: '', discount: 0 }
      ];

      mockApiClient.request.mockResolvedValue({
        success: true,
        status: 200,
        data: malformedData,
        headers: { 'content-type': 'application/json' }
      });

      const TestComponent = () => {
        const { coupons, refetch } = useCoupons();
        
        return (
          <div>
            <div data-testid="count">{coupons.length}</div>
            <button onClick={refetch} data-testid="load-btn">Load</button>
          </div>
        );
      };

      renderIntegrationTest(<TestComponent />);

      await act(async () => {
        userEvent.click(screen.getByTestId('load-btn'));
      });

      await waitFor(() => {
        // 只有有效的優惠券應該被保留
        expect(screen.getByTestId('count')).toHaveTextContent('1');
      });
    });
  });
});