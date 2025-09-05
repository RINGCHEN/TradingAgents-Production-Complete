/**
 * useResponsiveBreakpoint Hook - TradingAgents 斷點管理
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 提供統一的響應式斷點管理功能
 * - 基於設計系統的標準斷點
 * - 提供便利的斷點檢測方法
 * - 支援自定義斷點配置
 * - 優化性能和記憶化
 */

import { useMemo } from 'react';
import { useMediaQuery } from './useMediaQuery';
import { useWindowSize } from './useWindowSize';

/**
 * 標準響應式斷點定義
 * 與 CSS 設計系統保持一致
 */
export const RESPONSIVE_BREAKPOINTS = {
  xs: 0,      // Extra small devices (portrait phones)
  sm: 480,    // Small devices (landscape phones)
  md: 768,    // Medium devices (tablets)
  lg: 1024,   // Large devices (laptops/desktops)
  xl: 1280,   // Extra large devices (large laptops)
  xxl: 1536   // Extra extra large devices (larger desktops)
} as const;

export type BreakpointKey = keyof typeof RESPONSIVE_BREAKPOINTS;
export type BreakpointValue = typeof RESPONSIVE_BREAKPOINTS[BreakpointKey];

/**
 * 斷點範圍定義
 */
export interface BreakpointRange {
  min?: number;
  max?: number;
}

/**
 * 響應式狀態介面
 */
export interface ResponsiveBreakpointState {
  /** 當前斷點鍵值 */
  current: BreakpointKey;
  /** 當前視窗寬度 */
  width: number;
  /** 斷點狀態檢測 */
  is: {
    xs: boolean;
    sm: boolean;
    md: boolean;
    lg: boolean;
    xl: boolean;
    xxl: boolean;
  };
  /** 範圍檢測 */
  isAbove: (breakpoint: BreakpointKey) => boolean;
  isBelow: (breakpoint: BreakpointKey) => boolean;
  isBetween: (min: BreakpointKey, max: BreakpointKey) => boolean;
  /** 便利方法 */
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeScreen: boolean;
}

/**
 * 獲取當前斷點
 */
const getCurrentBreakpoint = (width: number): BreakpointKey => {
  if (width >= RESPONSIVE_BREAKPOINTS.xxl) return 'xxl';
  if (width >= RESPONSIVE_BREAKPOINTS.xl) return 'xl';
  if (width >= RESPONSIVE_BREAKPOINTS.lg) return 'lg';
  if (width >= RESPONSIVE_BREAKPOINTS.md) return 'md';
  if (width >= RESPONSIVE_BREAKPOINTS.sm) return 'sm';
  return 'xs';
};

/**
 * 響應式斷點管理Hook
 * 
 * @returns ResponsiveBreakpointState - 完整的響應式狀態對象
 * 
 * @example
 * ```tsx
 * const breakpoint = useResponsiveBreakpoint();
 * 
 * // 檢測當前斷點
 * console.log(breakpoint.current); // 'lg'
 * 
 * // 條件渲染
 * if (breakpoint.isMobile) {
 *   return <MobileComponent />;
 * }
 * 
 * // 範圍檢測
 * if (breakpoint.isBetween('md', 'lg')) {
 *   return <TabletComponent />;
 * }
 * 
 * // 斷點比較
 * if (breakpoint.isAbove('md')) {
 *   return <DesktopComponent />;
 * }
 * ```
 */
export const useResponsiveBreakpoint = (): ResponsiveBreakpointState => {
  const { width } = useWindowSize();
  
  // 媒體查詢檢測
  const isXs = useMediaQuery(`(max-width: ${RESPONSIVE_BREAKPOINTS.sm - 1}px)`);
  const isSm = useMediaQuery(`(min-width: ${RESPONSIVE_BREAKPOINTS.sm}px) and (max-width: ${RESPONSIVE_BREAKPOINTS.md - 1}px)`);
  const isMd = useMediaQuery(`(min-width: ${RESPONSIVE_BREAKPOINTS.md}px) and (max-width: ${RESPONSIVE_BREAKPOINTS.lg - 1}px)`);
  const isLg = useMediaQuery(`(min-width: ${RESPONSIVE_BREAKPOINTS.lg}px) and (max-width: ${RESPONSIVE_BREAKPOINTS.xl - 1}px)`);
  const isXl = useMediaQuery(`(min-width: ${RESPONSIVE_BREAKPOINTS.xl}px) and (max-width: ${RESPONSIVE_BREAKPOINTS.xxl - 1}px)`);
  const isXxl = useMediaQuery(`(min-width: ${RESPONSIVE_BREAKPOINTS.xxl}px)`);

  // 記憶化計算狀態對象
  const state = useMemo((): ResponsiveBreakpointState => {
    const current = getCurrentBreakpoint(width);
    
    const isAbove = (breakpoint: BreakpointKey): boolean => {
      return width >= RESPONSIVE_BREAKPOINTS[breakpoint];
    };
    
    const isBelow = (breakpoint: BreakpointKey): boolean => {
      return width < RESPONSIVE_BREAKPOINTS[breakpoint];
    };
    
    const isBetween = (min: BreakpointKey, max: BreakpointKey): boolean => {
      return width >= RESPONSIVE_BREAKPOINTS[min] && width < RESPONSIVE_BREAKPOINTS[max];
    };

    return {
      current,
      width,
      is: {
        xs: isXs,
        sm: isSm,
        md: isMd,
        lg: isLg,
        xl: isXl,
        xxl: isXxl
      },
      isAbove,
      isBelow,
      isBetween,
      // 便利屬性
      isMobile: isXs || isSm,
      isTablet: isMd,
      isDesktop: isLg || isXl,
      isLargeScreen: isXxl
    };
  }, [width, isXs, isSm, isMd, isLg, isXl, isXxl]);

  return state;
};

/**
 * 簡化版斷點檢測Hook
 */
export const useBreakpoint = (breakpoint: BreakpointKey): boolean => {
  return useMediaQuery(`(min-width: ${RESPONSIVE_BREAKPOINTS[breakpoint]}px)`);
};

/**
 * 斷點範圍檢測Hook
 */
export const useBreakpointRange = (min: BreakpointKey, max?: BreakpointKey): boolean => {
  const minQuery = `(min-width: ${RESPONSIVE_BREAKPOINTS[min]}px)`;
  const maxQuery = max ? `(max-width: ${RESPONSIVE_BREAKPOINTS[max] - 1}px)` : '';
  
  const query = maxQuery ? `${minQuery} and ${maxQuery}` : minQuery;
  
  return useMediaQuery(query);
};

/**
 * 移動裝置檢測Hook (組合 xs 和 sm)
 */
export const useIsMobile = (): boolean => {
  return useMediaQuery(`(max-width: ${RESPONSIVE_BREAKPOINTS.md - 1}px)`);
};

/**
 * 平板裝置檢測Hook
 */
export const useIsTablet = (): boolean => {
  return useBreakpointRange('md', 'lg');
};

/**
 * 桌面裝置檢測Hook
 */
export const useIsDesktop = (): boolean => {
  return useBreakpoint('lg');
};

export default useResponsiveBreakpoint;