/**
 * ApiClientProvider - API客戶端提供者組件
 * 整合ApiClient和錯誤處理，提供統一的API調用接口
 */

import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { ApiClient, ApiResponse, ApiError } from '../services/ApiClient';
import { apiErrorHandler, ErrorHandlingStrategy } from '../utils/ApiErrorHandler';
import { reportComponentError } from '../utils/ErrorDiagnostics';

interface ApiClientContextType {
  client: ApiClient;
  makeRequest: <T = any>(
    endpoint: string,
    options?: any,
    context?: { component?: string; feature?: string; userAction?: string }
  ) => Promise<ApiResponse<T>>;
  isHealthy: boolean;
  lastError: ApiError | null;
  errorCount: number;
  clearErrors: () => void;
}

const ApiClientContext = createContext<ApiClientContextType | null>(null);

interface ApiClientProviderProps {
  children: React.ReactNode;
  baseUrl?: string;
  timeout?: number;
  onError?: (error: ApiError, strategy: ErrorHandlingStrategy) => void;
}

export const ApiClientProvider: React.FC<ApiClientProviderProps> = ({
  children,
  baseUrl = '',
  timeout = 10000,
  onError
}) => {
  const [client] = useState(() => new ApiClient(baseUrl, timeout));
  const [isHealthy, setIsHealthy] = useState(true);
  const [lastError, setLastError] = useState<ApiError | null>(null);
  const [errorCount, setErrorCount] = useState(0);

  // 定期健康檢查
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const healthy = await client.healthCheck();
        setIsHealthy(healthy);
      } catch (error) {
        setIsHealthy(false);
      }
    };

    // 立即檢查一次
    checkHealth();

    // 每30秒檢查一次
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, [client]);

  // 統一的請求處理方法
  const makeRequest = useCallback(async <T = any>(
    endpoint: string,
    options: any = {},
    context: { component?: string; feature?: string; userAction?: string } = {}
  ): Promise<ApiResponse<T>> => {
    try {
      const response = await client.request<T>(endpoint, options);

      if (!response.success && response.error) {
        // 處理錯誤
        const errorContext = {
          ...context,
          timestamp: new Date()
        };

        const strategy = apiErrorHandler.handleError(response.error, errorContext);
        
        // 更新錯誤狀態
        setLastError(response.error);
        setErrorCount(prev => prev + 1);

        // 報告錯誤到診斷系統
        reportComponentError(
          response.error.type === 'network' ? 'network' : 'api',
          strategy.userMessage,
          {
            error: response.error,
            strategy,
            context: errorContext
          }
        );

        // 調用外部錯誤處理器
        if (onError) {
          onError(response.error, strategy);
        }

        // 根據策略決定是否重試
        if (strategy.shouldRetry && strategy.maxRetries && strategy.maxRetries > 0) {
          // 延遲後重試
          if (strategy.retryDelay) {
            await new Promise(resolve => setTimeout(resolve, strategy.retryDelay));
          }

          // 遞歸重試（減少重試次數）
          const retryOptions = {
            ...options,
            retryAttempts: Math.max(0, (options.retryAttempts || strategy.maxRetries) - 1)
          };

          if (retryOptions.retryAttempts > 0) {
            return makeRequest<T>(endpoint, retryOptions, context);
          }
        }
      }

      return response;

    } catch (error) {
      // 處理意外錯誤
      const apiError: ApiError = {
        type: 'client',
        message: error instanceof Error ? error.message : '未知錯誤',
        endpoint,
        timestamp: new Date(),
        details: { error }
      };

      setLastError(apiError);
      setErrorCount(prev => prev + 1);

      reportComponentError('api', '請求執行失敗', {
        error: apiError,
        context
      });

      return {
        success: false,
        status: 0,
        error: apiError,
        headers: {}
      };
    }
  }, [client, onError]);

  // 清除錯誤
  const clearErrors = useCallback(() => {
    setLastError(null);
    setErrorCount(0);
    apiErrorHandler.clearErrorLog();
  }, []);

  const contextValue: ApiClientContextType = {
    client,
    makeRequest,
    isHealthy,
    lastError,
    errorCount,
    clearErrors
  };

  return (
    <ApiClientContext.Provider value={contextValue}>
      {children}
    </ApiClientContext.Provider>
  );
};

// Hook for using the API client
export const useApiClient = (): ApiClientContextType => {
  const context = useContext(ApiClientContext);
  if (!context) {
    throw new Error('useApiClient must be used within an ApiClientProvider');
  }
  return context;
};

// 便捷的API調用hooks
export const useApiRequest = <T = any>(
  endpoint: string,
  options: any = {},
  dependencies: any[] = []
) => {
  const { makeRequest } = useApiClient();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await makeRequest<T>(endpoint, options, {
        component: 'useApiRequest',
        feature: endpoint
      });

      if (response.success) {
        setData(response.data || null);
      } else {
        setError(response.error || null);
      }
    } catch (err) {
      setError({
        type: 'client',
        message: err instanceof Error ? err.message : '請求失敗',
        endpoint,
        timestamp: new Date()
      });
    } finally {
      setLoading(false);
    }
  }, [makeRequest, endpoint, ...dependencies]);

  useEffect(() => {
    execute();
  }, [execute]);

  return {
    data,
    loading,
    error,
    refetch: execute
  };
};

// 專門用於優惠券API的hook（解決已知問題）
// 注意：此hook已被CouponManager取代，建議使用CouponManagerProvider
export const useCouponsApi = () => {
  const { makeRequest } = useApiClient();
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCoupons = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await makeRequest('/api/coupons', {
        method: 'GET',
        validateJsonResponse: true,
        expectJson: true,
        retryAttempts: 2,
        timeout: 8000
      }, {
        component: 'CouponsApi',
        feature: 'loadCoupons',
        userAction: 'load_coupons'
      });

      if (response.success) {
        setCoupons(response.data || []);
      } else if (response.error?.type === 'format') {
        // 特別處理格式錯誤，使用空列表作為降級
        setCoupons([]);
        setError('優惠券服務暫時不可用，請稍後重試');
        
        // 報告到診斷系統
        reportComponentError('coupon', 'Coupon API returned invalid format', {
          error: response.error,
          suggestion: 'Use CouponManager for better error handling'
        });
      } else {
        setCoupons([]);
        setError(response.error?.message || '載入優惠券失敗');
      }
    } catch (err) {
      setCoupons([]);
      setError('載入優惠券時發生錯誤');
      
      // 報告錯誤
      reportComponentError('coupon', 'Failed to load coupons in legacy hook', { 
        error: err,
        suggestion: 'Migrate to CouponManager for better error handling'
      });
    } finally {
      setLoading(false);
    }
  }, [makeRequest]);

  useEffect(() => {
    loadCoupons();
  }, [loadCoupons]);

  return {
    coupons,
    loading,
    error,
    reload: loadCoupons
  };
};

// CORS配置檢查hook
export const useCorsCheck = () => {
  const { client } = useApiClient();
  const [corsStatus, setCorsStatus] = useState<{
    isConfigured: boolean;
    details?: any;
    error?: string;
  }>({ isConfigured: false });

  const checkCors = useCallback(async () => {
    try {
      const result = await client.checkCorsConfiguration();
      setCorsStatus({
        isConfigured: result.success,
        details: result.details
      });
    } catch (error) {
      setCorsStatus({
        isConfigured: false,
        error: error instanceof Error ? error.message : '檢查CORS配置失敗'
      });
    }
  }, [client]);

  useEffect(() => {
    checkCors();
  }, [checkCors]);

  return {
    ...corsStatus,
    recheckCors: checkCors
  };
};

export default ApiClientProvider;