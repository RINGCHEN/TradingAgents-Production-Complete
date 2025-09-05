/**
 * CouponManagerProvider - 優惠券管理器提供者組件
 * 整合CouponManager，提供React上下文和hooks
 */

import React, { createContext, useContext, useCallback, useState, useEffect, useRef } from 'react';
import { CouponManager, CouponState, Coupon, CouponManagerConfig } from '../utils/CouponManager';
import { useApiClient } from './ApiClientProvider';
import { reportComponentError } from '../utils/ErrorDiagnostics';

interface CouponManagerContextType {
  manager: CouponManager;
  state: CouponState;
  loadCoupons: () => Promise<void>;
  reload: () => Promise<void>;
  clearCache: () => void;
  getAvailableCoupons: () => Coupon[];
  getApplicableCoupons: (amount: number) => Coupon[];
  calculateDiscount: (coupon: Coupon, amount: number) => number;
  isHealthy: boolean;
}

const CouponManagerContext = createContext<CouponManagerContextType | null>(null);

interface CouponManagerProviderProps {
  children: React.ReactNode;
  config?: Partial<CouponManagerConfig>;
  autoLoad?: boolean;
  onError?: (error: any) => void;
}

export const CouponManagerProvider: React.FC<CouponManagerProviderProps> = ({
  children,
  config = {},
  autoLoad = true,
  onError
}) => {
  const { client } = useApiClient();
  const managerRef = useRef<CouponManager | null>(null);
  const [state, setState] = useState<CouponState>({
    coupons: [],
    isLoading: false,
    fallbackMode: false,
    retryCount: 0
  });
  const [isHealthy, setIsHealthy] = useState(true);

  // 初始化CouponManager
  useEffect(() => {
    if (!managerRef.current) {
      managerRef.current = new CouponManager(client, {
        enableDiagnostics: true,
        ...config
      });
      
      // 載入初始狀態
      setState(managerRef.current.getState());
    }
  }, [client, config]);

  // 載入優惠券
  const loadCoupons = useCallback(async () => {
    if (!managerRef.current) return;

    try {
      const newState = await managerRef.current.loadCoupons();
      setState(newState);
      setIsHealthy(!newState.error);

      // 報告載入結果
      if (newState.fallbackMode) {
        reportComponentError('coupon', 'Using fallback coupons due to API issues', {
          fallbackMode: true,
          retryCount: newState.retryCount,
          error: newState.error
        });
      }
    } catch (error) {
      setIsHealthy(false);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: '載入優惠券時發生錯誤'
      }));

      reportComponentError('coupon', 'Failed to load coupons in provider', { error });
      
      if (onError) {
        onError(error);
      }
    }
  }, [onError]);

  // 重新載入優惠券
  const reload = useCallback(async () => {
    if (!managerRef.current) return;

    try {
      const newState = await managerRef.current.reload();
      setState(newState);
      setIsHealthy(!newState.error);
    } catch (error) {
      setIsHealthy(false);
      if (onError) {
        onError(error);
      }
    }
  }, [onError]);

  // 清除緩存
  const clearCache = useCallback(() => {
    if (!managerRef.current) return;

    managerRef.current.clearCache();
    setState(managerRef.current.getState());
  }, []);

  // 獲取可用優惠券
  const getAvailableCoupons = useCallback((): Coupon[] => {
    if (!managerRef.current) return [];
    return managerRef.current.getAvailableCoupons();
  }, []);

  // 獲取適用優惠券
  const getApplicableCoupons = useCallback((amount: number): Coupon[] => {
    if (!managerRef.current) return [];
    return managerRef.current.getApplicableCoupons(amount);
  }, []);

  // 計算折扣
  const calculateDiscount = useCallback((coupon: Coupon, amount: number): number => {
    if (!managerRef.current) return 0;
    return managerRef.current.calculateDiscount(coupon, amount);
  }, []);

  // 自動載入
  useEffect(() => {
    if (autoLoad && managerRef.current) {
      loadCoupons();
    }
  }, [autoLoad, loadCoupons]);

  const contextValue: CouponManagerContextType = {
    manager: managerRef.current!,
    state,
    loadCoupons,
    reload,
    clearCache,
    getAvailableCoupons,
    getApplicableCoupons,
    calculateDiscount,
    isHealthy
  };

  return (
    <CouponManagerContext.Provider value={contextValue}>
      {children}
    </CouponManagerContext.Provider>
  );
};

// Hook for using the coupon manager
export const useCouponManager = (): CouponManagerContextType => {
  const context = useContext(CouponManagerContext);
  if (!context) {
    throw new Error('useCouponManager must be used within a CouponManagerProvider');
  }
  return context;
};

// 便捷的優惠券hooks
export const useCoupons = () => {
  const { state, loadCoupons, reload, isHealthy } = useCouponManager();
  
  return {
    coupons: state.coupons,
    loading: state.isLoading,
    error: state.error,
    fallbackMode: state.fallbackMode,
    retryCount: state.retryCount,
    isHealthy,
    refetch: loadCoupons,
    reload
  };
};

export const useAvailableCoupons = () => {
  const { getAvailableCoupons, state } = useCouponManager();
  const [availableCoupons, setAvailableCoupons] = useState<Coupon[]>([]);

  useEffect(() => {
    setAvailableCoupons(getAvailableCoupons());
  }, [getAvailableCoupons, state.coupons]);

  return availableCoupons;
};

export const useCouponCalculator = () => {
  const { getApplicableCoupons, calculateDiscount } = useCouponManager();

  const getBestCoupon = useCallback((amount: number): { coupon: Coupon | null; discount: number } => {
    const applicableCoupons = getApplicableCoupons(amount);
    
    if (applicableCoupons.length === 0) {
      return { coupon: null, discount: 0 };
    }

    let bestCoupon = applicableCoupons[0];
    let bestDiscount = calculateDiscount(bestCoupon, amount);

    for (const coupon of applicableCoupons.slice(1)) {
      const discount = calculateDiscount(coupon, amount);
      if (discount > bestDiscount) {
        bestCoupon = coupon;
        bestDiscount = discount;
      }
    }

    return { coupon: bestCoupon, discount: bestDiscount };
  }, [getApplicableCoupons, calculateDiscount]);

  return {
    getApplicableCoupons,
    calculateDiscount,
    getBestCoupon
  };
};

export default CouponManagerProvider;