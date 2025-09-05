/**
 * Hooks Index - TradingAgents 響應式設計系統 Hooks
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 統一導出所有響應式設計相關的 React Hooks
 * 提供便利的導入方式和完整的型別支援
 */

// 媒體查詢相關 Hooks
export {
  useMediaQuery,
  useResponsiveQueries,
  BREAKPOINTS
} from './useMediaQuery';

// 視窗尺寸相關 Hooks  
export {
  useWindowSize,
  useWindowDimensions,
  useWindowAspectRatio,
  useWindowOrientation,
  useWindowSizeCategory,
  useResponsiveState
} from './useWindowSize';

// 響應式斷點相關 Hooks
export {
  useResponsiveBreakpoint,
  useBreakpoint,
  useBreakpointRange,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  RESPONSIVE_BREAKPOINTS
} from './useResponsiveBreakpoint';

// 型別定義導出
export type { WindowSize, UseWindowSizeOptions } from './useWindowSize';
export type { 
  BreakpointKey, 
  BreakpointValue, 
  BreakpointRange, 
  ResponsiveBreakpointState 
} from './useResponsiveBreakpoint';

// 品牌配置相關 Hooks
export {
  useBrandConfig,
  usePageTitle,
  useSeoMetadata
} from './useBrandConfig';

// 常用組合 Hooks
export { useResponsiveQueries as useBreakpoints } from './useMediaQuery';
export { useResponsiveState as useResponsive } from './useWindowSize';

/**
 * 使用示例:
 * 
 * ```tsx
 * // 基本使用
 * import { useMediaQuery, useWindowSize } from './hooks';
 * 
 * // 組合使用
 * import { useResponsive, useBreakpoints, useResponsiveBreakpoint } from './hooks';
 * 
 * // 特定功能
 * import { 
 *   useWindowOrientation, 
 *   useWindowAspectRatio,
 *   useIsMobile,
 *   useIsDesktop,
 *   BREAKPOINTS,
 *   RESPONSIVE_BREAKPOINTS
 * } from './hooks';
 * 
 * const MyComponent = () => {
 *   // 簡單響應式檢測
 *   const isMobile = useIsMobile();
 *   const isDesktop = useIsDesktop();
 *   
 *   // 完整響應式狀態
 *   const breakpoint = useResponsiveBreakpoint();
 *   const { width, height, orientation } = useResponsive();
 *   
 *   return (
 *     <div>
 *       {breakpoint.isMobile && <MobileLayout />}
 *       {breakpoint.isDesktop && <DesktopLayout />}
 *       <p>Current: {breakpoint.current} - Width: {width}px</p>
 *     </div>
 *   );
 * };
 * ```
 */