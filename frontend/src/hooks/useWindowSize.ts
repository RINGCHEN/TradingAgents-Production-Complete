/**
 * useWindowSize Hook - TradingAgents 視窗尺寸監聽
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 提供實時視窗尺寸監聽功能的React Hook
 * - 實時追蹤視窗寬度與高度變化
 * - 防抖優化，避免過度渲染
 * - 支援伺服器端渲染 (SSR)
 * - 記憶化計算，提升性能
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * 視窗尺寸介面定義
 */
export interface WindowSize {
  /** 視窗寬度 (px) */
  width: number;
  /** 視窗高度 (px) */
  height: number;
  /** 視窗內寬度 (px) - 不含滾動條 */
  innerWidth: number;
  /** 視窗內高度 (px) - 不含滾動條 */
  innerHeight: number;
}

/**
 * Hook 配置選項
 */
export interface UseWindowSizeOptions {
  /** 防抖延遲時間 (毫秒)，預設 100ms */
  debounceMs?: number;
  /** 是否立即執行，預設 true */
  immediate?: boolean;
  /** 是否包含滾動條尺寸，預設 true */
  includeScrollbar?: boolean;
}

/**
 * 防抖函數工具
 */
function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * 獲取當前視窗尺寸
 */
const getWindowSize = (includeScrollbar = true): WindowSize => {
  if (typeof window === 'undefined') {
    // SSR 預設值
    return {
      width: 0,
      height: 0,
      innerWidth: 0,
      innerHeight: 0
    };
  }

  const width = includeScrollbar ? window.outerWidth : window.innerWidth;
  const height = includeScrollbar ? window.outerHeight : window.innerHeight;

  return {
    width,
    height,
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight
  };
};

/**
 * 視窗尺寸監聽Hook
 * 
 * @param options - Hook配置選項
 * @returns WindowSize - 包含當前視窗尺寸的對象
 * 
 * @example
 * ```tsx
 * const windowSize = useWindowSize();
 * const { width, height, innerWidth, innerHeight } = windowSize;
 * 
 * // 使用防抖優化
 * const debouncedSize = useWindowSize({ debounceMs: 200 });
 * 
 * // 排除滾動條
 * const exactSize = useWindowSize({ includeScrollbar: false });
 * 
 * return (
 *   <div>
 *     <p>視窗寬度: {width}px</p>
 *     <p>視窗高度: {height}px</p>
 *     <p>內容區寬度: {innerWidth}px</p>
 *     <p>內容區高度: {innerHeight}px</p>
 *   </div>
 * );
 * ```
 */
export const useWindowSize = (options: UseWindowSizeOptions = {}): WindowSize => {
  const {
    debounceMs = 100,
    immediate = true,
    includeScrollbar = true
  } = options;

  // 初始化狀態
  const [windowSize, setWindowSize] = useState<WindowSize>(() => 
    immediate ? getWindowSize(includeScrollbar) : {
      width: 0,
      height: 0,
      innerWidth: 0,
      innerHeight: 0
    }
  );

  // 處理視窗尺寸變化
  const handleResize = useCallback(() => {
    const newSize = getWindowSize(includeScrollbar);
    setWindowSize(prevSize => {
      // 避免不必要的更新
      if (
        prevSize.width === newSize.width && 
        prevSize.height === newSize.height &&
        prevSize.innerWidth === newSize.innerWidth &&
        prevSize.innerHeight === newSize.innerHeight
      ) {
        return prevSize;
      }
      return newSize;
    });
  }, [includeScrollbar]);

  // 創建防抖處理函數
  const debouncedHandleResize = useCallback(
    debounce(handleResize, debounceMs),
    [handleResize, debounceMs]
  );

  useEffect(() => {
    // 避免在SSR環境中執行
    if (typeof window === 'undefined') {
      return;
    }

    // 如果不是立即執行，則在首次mount時獲取尺寸
    if (!immediate) {
      setWindowSize(getWindowSize(includeScrollbar));
    }

    // 添加resize事件監聽器
    window.addEventListener('resize', debouncedHandleResize, { passive: true });
    
    // 監聽方向變化 (移動裝置)
    window.addEventListener('orientationchange', debouncedHandleResize, { passive: true });

    // 清理函數
    return () => {
      window.removeEventListener('resize', debouncedHandleResize);
      window.removeEventListener('orientationchange', debouncedHandleResize);
    };
  }, [debouncedHandleResize, immediate, includeScrollbar]);

  return windowSize;
};

/**
 * 簡化版視窗尺寸Hook - 僅返回寬度和高度
 */
export const useWindowDimensions = (): { width: number; height: number } => {
  const { width, height } = useWindowSize();
  return { width, height };
};

/**
 * 視窗比例Hook - 返回寬高比
 */
export const useWindowAspectRatio = (): number => {
  const { width, height } = useWindowSize();
  return height === 0 ? 0 : width / height;
};

/**
 * 視窗方向Hook - 判斷橫屏或豎屏
 */
export const useWindowOrientation = (): 'portrait' | 'landscape' => {
  const { width, height } = useWindowSize();
  return width > height ? 'landscape' : 'portrait';
};

/**
 * 視窗尺寸類別Hook - 根據預設斷點返回類別
 */
export const useWindowSizeCategory = (): 'mobile' | 'tablet' | 'desktop' | 'wide' => {
  const { width } = useWindowSize();
  
  if (width < 480) return 'mobile';
  if (width < 768) return 'tablet';  
  if (width < 1280) return 'desktop';
  return 'wide';
};

/**
 * 響應式狀態組合Hook
 */
export const useResponsiveState = () => {
  const windowSize = useWindowSize();
  const aspectRatio = useWindowAspectRatio();
  const orientation = useWindowOrientation();
  const category = useWindowSizeCategory();
  
  return {
    ...windowSize,
    aspectRatio,
    orientation,
    category,
    isMobile: category === 'mobile',
    isTablet: category === 'tablet',
    isDesktop: category === 'desktop' || category === 'wide',
    isPortrait: orientation === 'portrait',
    isLandscape: orientation === 'landscape'
  };
};

export default useWindowSize;