/**
 * CouponManager 簡化測試
 * 測試核心功能，避免複雜的DOM斷言
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CouponManagerProvider, useCoupons } from '../CouponManagerProvider';
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
    discountType: 'percentage',
    validFrom: '2024-01-01T00:00:00.000Z',
    validTo: '2025-12-31T23:59:59.999Z',
    isActive: true,
    minAmount: 100
  }
];

describe('CouponManager Simple Tests', () => {
  let mockApiClient: jest.Mocked<ApiClient>;

  beforeEach(() => {
    mockLocalStorage.clear();
    
    mockApiClient = {
      request: jest.fn(),
      healthCheck: jest.fn().mockResolvedValue(true)
    } as any;

    MockedApiClient.mockImplementation(() => mockApiClient);
  });

  const TestComponent: React.FC = () => {
    const { coupons, loading, error, refetch } = useCoupons();
    
    return (
      <div>
        <div data-testid="loading">{loading ? 'true' : 'false'}</div>
        <div data-testid="error">{error || 'none'}</div>
        <div data-testid="count">{coupons.length}</div>
        <button onClick={refetch} data-testid="refetch">Refetch</button>
        {coupons.map(coupon => (
          <div key={coupon.id} data-testid={`coupon-${coupon.id}`}>
            {coupon.code}
          </div>
        ))}
      </div>
    );
  };

  const renderTest = () => {
    return render(
      <ApiClientProvider>
        <CouponManagerProvider autoLoad={false}>
          <TestComponent />
        </CouponManagerProvider>
      </ApiClientProvider>
    );
  };

  it('should load coupons successfully', async () => {
    mockApiClient.request.mockResolvedValue({
      success: true,
      status: 200,
      data: mockCoupons,
      headers: { 'content-type': 'application/json' }
    });

    renderTest();
    
    // 初始狀態
    expect(screen.getByTestId('count').textContent).toBe('0');
    expect(screen.getByTestId('loading').textContent).toBe('false');
    
    // 觸發載入
    await act(async () => {
      userEvent.click(screen.getByTestId('refetch'));
    });

    // 等待載入完成
    await waitFor(() => {
      expect(screen.getByTestId('count').textContent).toBe('1');
    });

    expect(screen.getByTestId('loading').textContent).toBe('false');
    expect(screen.getByTestId('error').textContent).toBe('none');
    expect(screen.getByTestId('coupon-coupon1')).toBeDefined();
  });

  it('should handle API errors gracefully', async () => {
    mockApiClient.request.mockRejectedValue(new Error('API Error'));

    renderTest();
    
    await act(async () => {
      userEvent.click(screen.getByTestId('refetch'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('error').textContent).not.toBe('none');
    });

    // 應該使用降級優惠券
    expect(screen.getByTestId('count').textContent).toBe('1');
  });

  it('should handle HTML response (SyntaxError fix)', async () => {
    mockApiClient.request.mockResolvedValue({
      success: true,
      status: 200,
      data: '<html><body>Error</body></html>',
      headers: { 'content-type': 'text/html' }
    });

    renderTest();
    
    await act(async () => {
      userEvent.click(screen.getByTestId('refetch'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('error').textContent).toContain('優惠券服務暫時不可用');
    });

    // 應該使用降級優惠券
    expect(screen.getByTestId('count').textContent).toBe('1');
  });

  it('should handle SyntaxError specifically', async () => {
    mockApiClient.request.mockRejectedValue(
      new SyntaxError('Unexpected token < in JSON')
    );

    renderTest();
    
    await act(async () => {
      userEvent.click(screen.getByTestId('refetch'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('error').textContent).toContain('優惠券數據格式錯誤');
    });

    // 應該使用降級優惠券
    expect(screen.getByTestId('count').textContent).toBe('1');
  });

  it('should retry on network errors', async () => {
    mockApiClient.request
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        success: true,
        status: 200,
        data: mockCoupons,
        headers: { 'content-type': 'application/json' }
      });

    renderTest();
    
    await act(async () => {
      userEvent.click(screen.getByTestId('refetch'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('count').textContent).toBe('1');
    });

    // 應該重試3次
    expect(mockApiClient.request).toHaveBeenCalledTimes(3);
  });
});