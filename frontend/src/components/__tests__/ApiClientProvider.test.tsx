/**
 * ApiClientProvider 測試套件
 * 測試API客戶端提供者組件和相關hooks
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { ApiClientProvider, useApiClient, useApiRequest, useCouponsApi } from '../ApiClientProvider';
import { ApiError } from '../../services/ApiClient';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock ErrorDiagnostics
jest.mock('../../utils/ErrorDiagnostics', () => ({
  reportComponentError: jest.fn()
}));

// 測試組件
const TestComponent: React.FC = () => {
  const { client, makeRequest, isHealthy, lastError, errorCount, clearErrors } = useApiClient();
  
  const handleTestRequest = async () => {
    await makeRequest('/api/test', { method: 'GET' }, {
      component: 'TestComponent',
      feature: 'test'
    });
  };

  return (
    <div>
      <div data-testid="health-status">{isHealthy ? 'healthy' : 'unhealthy'}</div>
      <div data-testid="error-count">{errorCount}</div>
      <div data-testid="last-error">{lastError?.message || 'none'}</div>
      <button onClick={handleTestRequest} data-testid="test-request">
        Test Request
      </button>
      <button onClick={clearErrors} data-testid="clear-errors">
        Clear Errors
      </button>
    </div>
  );
};

const ApiRequestTestComponent: React.FC = () => {
  const { data, loading, error, refetch } = useApiRequest('/api/data');
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="data">{data ? JSON.stringify(data) : 'no-data'}</div>
      <div data-testid="error">{error?.message || 'no-error'}</div>
      <button onClick={refetch} data-testid="refetch">Refetch</button>
    </div>
  );
};

const CouponsTestComponent: React.FC = () => {
  const { coupons, loading, error, reload } = useCouponsApi();
  
  return (
    <div>
      <div data-testid="coupons-loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="coupons-count">{coupons.length}</div>
      <div data-testid="coupons-error">{error || 'no-error'}</div>
      <button onClick={reload} data-testid="reload-coupons">Reload</button>
    </div>
  );
};

describe('ApiClientProvider', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('基本功能', () => {
    it('應該提供API客戶端上下文', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('OK')
      });

      render(
        <ApiClientProvider>
          <TestComponent />
        </ApiClientProvider>
      );

      expect(screen.getByTestId('health-status')).toHaveTextContent('healthy');
      expect(screen.getByTestId('error-count')).toHaveTextContent('0');
      expect(screen.getByTestId('last-error')).toHaveTextContent('none');
    });

    it('應該在沒有Provider時拋出錯誤', () => {
      // 抑制錯誤輸出
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useApiClient must be used within an ApiClientProvider');

      consoleSpy.mockRestore();
    });
  });

  describe('健康檢查', () => {
    it('應該定期執行健康檢查', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('OK')
      });

      render(
        <ApiClientProvider>
          <TestComponent />
        </ApiClientProvider>
      );

      // 等待初始健康檢查
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/health'),
          expect.any(Object)
        );
      });

      expect(screen.getByTestId('health-status')).toHaveTextContent('healthy');
    });

    it('應該檢測健康檢查失敗', async () => {
      mockFetch.mockRejectedValue(new Error('Health check failed'));

      render(
        <ApiClientProvider>
          <TestComponent />
        </ApiClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('health-status')).toHaveTextContent('unhealthy');
      });
    });
  });

  describe('錯誤處理', () => {
    it('應該處理API錯誤並更新狀態', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Headers(),
        text: () => Promise.resolve('Server Error')
      });

      const onError = jest.fn();

      render(
        <ApiClientProvider onError={onError}>
          <TestComponent />
        </ApiClientProvider>
      );

      // 觸發測試請求
      act(() => {
        screen.getByTestId('test-request').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-count')).toHaveTextContent('1');
        expect(screen.getByTestId('last-error')).toHaveTextContent('服務器錯誤 500');
      });

      expect(onError).toHaveBeenCalled();
    });

    it('應該清除錯誤', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
        text: () => Promise.resolve('Not Found')
      });

      render(
        <ApiClientProvider>
          <TestComponent />
        </ApiClientProvider>
      );

      // 觸發錯誤
      act(() => {
        screen.getByTestId('test-request').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-count')).toHaveTextContent('1');
      });

      // 清除錯誤
      act(() => {
        screen.getByTestId('clear-errors').click();
      });

      expect(screen.getByTestId('error-count')).toHaveTextContent('0');
      expect(screen.getByTestId('last-error')).toHaveTextContent('none');
    });
  });

  describe('useApiRequest hook', () => {
    it('應該自動執行API請求', async () => {
      const mockData = { id: 1, name: 'test' };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockData))
      });

      render(
        <ApiClientProvider>
          <ApiRequestTestComponent />
        </ApiClientProvider>
      );

      // 初始狀態
      expect(screen.getByTestId('loading')).toHaveTextContent('loading');
      expect(screen.getByTestId('data')).toHaveTextContent('no-data');

      // 等待請求完成
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
        expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(mockData));
        expect(screen.getByTestId('error')).toHaveTextContent('no-error');
      });
    });

    it('應該處理API請求錯誤', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Headers(),
        text: () => Promise.resolve('Server Error')
      });

      render(
        <ApiClientProvider>
          <ApiRequestTestComponent />
        </ApiClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
        expect(screen.getByTestId('data')).toHaveTextContent('no-data');
        expect(screen.getByTestId('error')).toHaveTextContent('服務器錯誤 500');
      });
    });

    it('應該支持重新獲取數據', async () => {
      const mockData = { id: 1, name: 'test' };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockData))
      });

      render(
        <ApiClientProvider>
          <ApiRequestTestComponent />
        </ApiClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(mockData));
      });

      // 清除mock並設置新數據
      mockFetch.mockClear();
      const newMockData = { id: 2, name: 'updated' };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(newMockData))
      });

      // 觸發重新獲取
      act(() => {
        screen.getByTestId('refetch').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(newMockData));
      });
    });
  });

  describe('useCouponsApi hook', () => {
    it('應該成功載入優惠券', async () => {
      const mockCoupons = [
        { id: 1, code: 'SAVE10', discount: 10 },
        { id: 2, code: 'SAVE20', discount: 20 }
      ];

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockCoupons))
      });

      render(
        <ApiClientProvider>
          <CouponsTestComponent />
        </ApiClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('coupons-loading')).toHaveTextContent('not-loading');
        expect(screen.getByTestId('coupons-count')).toHaveTextContent('2');
        expect(screen.getByTestId('coupons-error')).toHaveTextContent('no-error');
      });
    });

    it('應該處理優惠券API格式錯誤', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/html' }),
        text: () => Promise.resolve('<html>Error page</html>')
      });

      render(
        <ApiClientProvider>
          <CouponsTestComponent />
        </ApiClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('coupons-loading')).toHaveTextContent('not-loading');
        expect(screen.getByTestId('coupons-count')).toHaveTextContent('0');
        expect(screen.getByTestId('coupons-error')).toHaveTextContent('優惠券服務暫時不可用');
      });
    });

    it('應該支持重新載入優惠券', async () => {
      const mockCoupons = [{ id: 1, code: 'TEST', discount: 5 }];

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockCoupons))
      });

      render(
        <ApiClientProvider>
          <CouponsTestComponent />
        </ApiClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('coupons-count')).toHaveTextContent('1');
      });

      // 清除mock並設置新數據
      mockFetch.mockClear();
      const newMockCoupons = [
        { id: 1, code: 'TEST', discount: 5 },
        { id: 2, code: 'NEW', discount: 15 }
      ];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(newMockCoupons))
      });

      // 觸發重新載入
      act(() => {
        screen.getByTestId('reload-coupons').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('coupons-count')).toHaveTextContent('2');
      });
    });
  });

  describe('配置選項', () => {
    it('應該使用自定義baseUrl和timeout', () => {
      const customBaseUrl = 'https://custom-api.com';
      const customTimeout = 5000;

      render(
        <ApiClientProvider baseUrl={customBaseUrl} timeout={customTimeout}>
          <TestComponent />
        </ApiClientProvider>
      );

      // 驗證組件正常渲染（間接驗證配置被接受）
      expect(screen.getByTestId('health-status')).toBeInTheDocument();
    });

    it('應該調用自定義錯誤處理器', async () => {
      const onError = jest.fn();

      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: new Headers(),
        text: () => Promise.resolve('Bad Request')
      });

      render(
        <ApiClientProvider onError={onError}>
          <TestComponent />
        </ApiClientProvider>
      );

      act(() => {
        screen.getByTestId('test-request').click();
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'client',
            status: 400
          }),
          expect.objectContaining({
            userMessage: expect.any(String),
            severity: expect.any(String)
          })
        );
      });
    });
  });
});