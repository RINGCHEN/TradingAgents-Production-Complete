/**
 * useMediaQuery Hook - TradingAgents 響應式媒體查詢
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 提供CSS媒體查詢功能的React Hook
 * - 實時監聽視窗大小變化
 * - 支援所有標準CSS媒體查詢語法
 * - 優化性能，避免重複渲染
 * - 支援伺服器端渲染 (SSR)
 */

import { useState, useEffect } from 'react';

/**
 * 媒體查詢Hook
 * 
 * @param query - CSS媒體查詢字串 (例如: "(max-width: 768px)")
 * @returns boolean - 媒體查詢是否匹配當前視窗狀態
 * 
 * @example
 * ```tsx
 * const isMobile = useMediaQuery('(max-width: 768px)');
 * const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
 * const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
 * 
 * return (
 *   <div>
 *     {isMobile && <MobileComponent />}
 *     {isTablet && <TabletComponent />}
 *     {!isMobile && !isTablet && <DesktopComponent />}
 *   </div>
 * );
 * ```
 */
export const useMediaQuery = (query: string): boolean => {
  // 初始化狀態，考慮SSR場景
  const [matches, setMatches] = useState(() => {
    // 在伺服器端或無window對象時返回false
    if (typeof window === 'undefined') {
      return false;
    }
    
    // 客戶端初始化時立即檢查媒體查詢狀態
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    // 避免在SSR環境中執行
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia(query);
    
    // 如果當前狀態與媒體查詢不匹配，立即更新
    if (mediaQuery.matches !== matches) {
      setMatches(mediaQuery.matches);
    }
    
    // 創建事件監聽器
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // 添加事件監聽器 (支援舊瀏覽器和新瀏覽器API)
    try {
      mediaQuery.addEventListener('change', listener);
    } catch (e) {
      // 舊版瀏覽器fallback
      mediaQuery.addListener(listener);
    }
    
    // 清理函數
    return () => {
      try {
        mediaQuery.removeEventListener('change', listener);
      } catch (e) {
        // 舊版瀏覽器fallback
        mediaQuery.removeListener(listener);
      }
    };
  }, [query, matches]);

  return matches;
};

// 常用斷點預設值
export const BREAKPOINTS = {
  mobile: 480,
  tablet: 768,
  desktop: 1024,
  wide: 1280,
  ultrawide: 1536
} as const;

/**
 * 預定義的響應式Hook集合
 */
export const useResponsiveQueries = () => {
  const isMobile = useMediaQuery(`(max-width: ${BREAKPOINTS.tablet - 1}px)`);
  const isTablet = useMediaQuery(`(min-width: ${BREAKPOINTS.tablet}px) and (max-width: ${BREAKPOINTS.desktop - 1}px)`);
  const isDesktop = useMediaQuery(`(min-width: ${BREAKPOINTS.desktop}px)`);
  const isWide = useMediaQuery(`(min-width: ${BREAKPOINTS.wide}px)`);
  const isUltrawide = useMediaQuery(`(min-width: ${BREAKPOINTS.ultrawide}px)`);
  
  // 觸控裝置檢測
  const isTouchDevice = useMediaQuery('(hover: none) and (pointer: coarse)');
  
  // 偏好設定檢測
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  const prefersHighContrast = useMediaQuery('(prefers-contrast: high)');

  return {
    // 斷點檢測
    isMobile,
    isTablet,
    isDesktop,
    isWide,
    isUltrawide,
    
    // 裝置特性
    isTouchDevice,
    
    // 用戶偏好
    prefersDarkMode,
    prefersReducedMotion,
    prefersHighContrast,
    
    // 便利組合
    isMobileOrTablet: isMobile || isTablet,
    isDesktopOrWide: isDesktop || isWide || isUltrawide
  };
};

export default useMediaQuery;