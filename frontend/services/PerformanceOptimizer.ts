// 性能優化器 - 管理React組件記憶化和懶載入
// 提供統一的性能優化工具和監控

import { ComponentType, lazy, memo, useMemo, useCallback, useRef, useEffect } from 'react';

export interface PerformanceMetrics {
  renderCount: number;
  lastRenderTime: number;
  averageRenderTime: number;
  memoryUsage?: number;
}

export class PerformanceOptimizer {
  private static instance: PerformanceOptimizer;
  private componentMetrics = new Map<string, PerformanceMetrics>();
  private renderObserver: PerformanceObserver | null = null;

  private constructor() {
    this.initializePerformanceObserver();
  }

  static getInstance(): PerformanceOptimizer {
    if (!PerformanceOptimizer.instance) {
      PerformanceOptimizer.instance = new PerformanceOptimizer();
    }
    return PerformanceOptimizer.instance;
  }

  /**
   * 初始化性能觀察器
   */
  private initializePerformanceObserver(): void {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      try {
        this.renderObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.entryType === 'measure' && entry.name.startsWith('React')) {
              this.updateRenderMetrics(entry.name, entry.duration);
            }
          });
        });
        
        this.renderObserver.observe({ entryTypes: ['measure'] });
      } catch (error) {
        console.warn('性能觀察器初始化失敗:', error);
      }
    }
  }

  /**
   * 創建記憶化組件
   */
  memoizeComponent<P extends object>(
    Component: ComponentType<P>,
    displayName?: string,
    areEqual?: (prevProps: P, nextProps: P) => boolean
  ): ComponentType<P> {
    const MemoizedComponent = memo(Component, areEqual);
    
    if (displayName) {
      MemoizedComponent.displayName = `Memo(${displayName})`;
    }
    
    return MemoizedComponent;
  }

  /**
   * 創建懶載入組件
   */
  createLazyComponent<P extends object>(
    importFn: () => Promise<{ default: ComponentType<P> }>,
    displayName?: string
  ): ComponentType<P> {
    const LazyComponent = lazy(importFn);
    
    if (displayName) {
      LazyComponent.displayName = `Lazy(${displayName})`;
    }
    
    return LazyComponent;
  }

  /**
   * 優化的useMemo hook
   */
  useOptimizedMemo<T>(
    factory: () => T,
    deps: React.DependencyList,
    componentName?: string
  ): T {
    const startTime = performance.now();
    
    const result = useMemo(() => {
      const computeStartTime = performance.now();
      const value = factory();
      const computeEndTime = performance.now();
      
      if (componentName) {
        this.recordComputationTime(componentName, computeEndTime - computeStartTime);
      }
      
      return value;
    }, deps);
    
    const endTime = performance.now();
    
    if (componentName) {
      this.updateRenderMetrics(`useMemo-${componentName}`, endTime - startTime);
    }
    
    return result;
  }

  /**
   * 優化的useCallback hook
   */
  useOptimizedCallback<T extends (...args: any[]) => any>(
    callback: T,
    deps: React.DependencyList,
    componentName?: string
  ): T {
    const startTime = performance.now();
    
    const memoizedCallback = useCallback(callback, deps);
    
    const endTime = performance.now();
    
    if (componentName) {
      this.updateRenderMetrics(`useCallback-${componentName}`, endTime - startTime);
    }
    
    return memoizedCallback;
  }

  /**
   * 虛擬滾動優化器
   */
  createVirtualScrollConfig(
    itemCount: number,
    itemHeight: number,
    containerHeight: number
  ): {
    startIndex: number;
    endIndex: number;
    visibleItems: number;
    bufferSize: number;
  } {
    const visibleItems = Math.ceil(containerHeight / itemHeight);
    const bufferSize = Math.max(5, Math.ceil(visibleItems * 0.5));
    
    return {
      startIndex: 0,
      endIndex: Math.min(itemCount - 1, visibleItems + bufferSize - 1),
      visibleItems,
      bufferSize
    };
  }

  /**
   * 圖片懶載入優化
   */
  createImageLazyLoader(): {
    observer: IntersectionObserver | null;
    loadImage: (img: HTMLImageElement, src: string) => void;
  } {
    let observer: IntersectionObserver | null = null;
    
    if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement;
              const src = img.dataset.src;
              
              if (src) {
                img.src = src;
                img.removeAttribute('data-src');
                observer?.unobserve(img);
              }
            }
          });
        },
        {
          rootMargin: '50px 0px',
          threshold: 0.1
        }
      );
    }
    
    const loadImage = (img: HTMLImageElement, src: string) => {
      if (observer) {
        img.dataset.src = src;
        observer.observe(img);
      } else {
        // 降級處理
        img.src = src;
      }
    };
    
    return { observer, loadImage };
  }

  /**
   * 防抖優化
   */
  createDebouncer<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func(...args), delay);
    };
  }

  /**
   * 節流優化
   */
  createThrottler<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let lastCallTime = 0;
    
    return (...args: Parameters<T>) => {
      const now = Date.now();
      
      if (now - lastCallTime >= delay) {
        lastCallTime = now;
        func(...args);
      }
    };
  }

  /**
   * 批量DOM更新優化
   */
  batchDOMUpdates(updates: Array<() => void>): void {
    if (typeof window !== 'undefined' && 'requestAnimationFrame' in window) {
      requestAnimationFrame(() => {
        updates.forEach(update => {
          try {
            update();
          } catch (error) {
            console.error('DOM更新失敗:', error);
          }
        });
      });
    } else {
      // 降級處理
      setTimeout(() => {
        updates.forEach(update => {
          try {
            update();
          } catch (error) {
            console.error('DOM更新失敗:', error);
          }
        });
      }, 0);
    }
  }

  /**
   * 記錄計算時間
   */
  private recordComputationTime(componentName: string, duration: number): void {
    const key = `computation-${componentName}`;
    const existing = this.componentMetrics.get(key);
    
    if (existing) {
      existing.renderCount++;
      existing.lastRenderTime = duration;
      existing.averageRenderTime = 
        (existing.averageRenderTime * (existing.renderCount - 1) + duration) / existing.renderCount;
    } else {
      this.componentMetrics.set(key, {
        renderCount: 1,
        lastRenderTime: duration,
        averageRenderTime: duration
      });
    }
  }

  /**
   * 更新渲染指標
   */
  private updateRenderMetrics(componentName: string, duration: number): void {
    const existing = this.componentMetrics.get(componentName);
    
    if (existing) {
      existing.renderCount++;
      existing.lastRenderTime = duration;
      existing.averageRenderTime = 
        (existing.averageRenderTime * (existing.renderCount - 1) + duration) / existing.renderCount;
    } else {
      this.componentMetrics.set(componentName, {
        renderCount: 1,
        lastRenderTime: duration,
        averageRenderTime: duration
      });
    }
  }

  /**
   * 獲取性能指標
   */
  getPerformanceMetrics(componentName?: string): Map<string, PerformanceMetrics> | PerformanceMetrics | null {
    if (componentName) {
      return this.componentMetrics.get(componentName) || null;
    }
    return this.componentMetrics;
  }

  /**
   * 清除性能指標
   */
  clearMetrics(componentName?: string): void {
    if (componentName) {
      this.componentMetrics.delete(componentName);
    } else {
      this.componentMetrics.clear();
    }
  }

  /**
   * 獲取內存使用情況
   */
  getMemoryUsage(): {
    used: number;
    total: number;
    percentage: number;
  } | null {
    if (typeof window !== 'undefined' && 'performance' in window && 'memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        percentage: (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100
      };
    }
    return null;
  }

  /**
   * 性能監控報告
   */
  generatePerformanceReport(): {
    componentMetrics: Array<{
      name: string;
      renderCount: number;
      averageRenderTime: number;
      lastRenderTime: number;
    }>;
    memoryUsage: ReturnType<typeof this.getMemoryUsage>;
    timestamp: number;
  } {
    const componentMetrics = Array.from(this.componentMetrics.entries()).map(([name, metrics]) => ({
      name,
      renderCount: metrics.renderCount,
      averageRenderTime: metrics.averageRenderTime,
      lastRenderTime: metrics.lastRenderTime
    }));

    return {
      componentMetrics,
      memoryUsage: this.getMemoryUsage(),
      timestamp: Date.now()
    };
  }

  /**
   * 清理資源
   */
  cleanup(): void {
    if (this.renderObserver) {
      this.renderObserver.disconnect();
      this.renderObserver = null;
    }
    this.componentMetrics.clear();
  }
}

// 創建全局性能優化器實例
export const performanceOptimizer = PerformanceOptimizer.getInstance();

// React Hook 包裝器
export function usePerformanceOptimizer(componentName: string) {
  const optimizer = PerformanceOptimizer.getInstance();
  
  const optimizedMemo = useCallback(
    <T>(factory: () => T, deps: React.DependencyList) => 
      optimizer.useOptimizedMemo(factory, deps, componentName),
    [optimizer, componentName]
  );
  
  const optimizedCallback = useCallback(
    <T extends (...args: any[]) => any>(callback: T, deps: React.DependencyList) =>
      optimizer.useOptimizedCallback(callback, deps, componentName),
    [optimizer, componentName]
  );
  
  const debounce = useCallback(
    <T extends (...args: any[]) => any>(func: T, delay: number) =>
      optimizer.createDebouncer(func, delay),
    [optimizer]
  );
  
  const throttle = useCallback(
    <T extends (...args: any[]) => any>(func: T, delay: number) =>
      optimizer.createThrottler(func, delay),
    [optimizer]
  );
  
  return {
    optimizedMemo,
    optimizedCallback,
    debounce,
    throttle,
    getMetrics: () => optimizer.getPerformanceMetrics(componentName),
    clearMetrics: () => optimizer.clearMetrics(componentName)
  };
}