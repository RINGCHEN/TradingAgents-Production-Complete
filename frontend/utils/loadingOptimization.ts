/**
 * 載入優化工具 - 第二階段Week 3 性能調優與監控
 * 代碼分割、懶載入、預載入策略
 * 支援優先級載入、批量載入、載入狀態管理
 */

import React from 'react';

// 載入優先級
export type LoadPriority = 'critical' | 'high' | 'normal' | 'low';

// 載入狀態
export interface LoadingState {
  isLoading: boolean;
  isLoaded: boolean;
  isError: boolean;
  error?: Error;
  progress?: number;
}

// 載入任務
export interface LoadingTask<T = any> {
  id: string;
  priority: LoadPriority;
  loader: () => Promise<T>;
  dependencies?: string[];
  timeout?: number;
  retries?: number;
  cache?: boolean;
}

// 預載入資源類型
export type PreloadResourceType = 'script' | 'style' | 'image' | 'font' | 'audio' | 'video';

// 預載入配置
export interface PreloadConfig {
  href: string;
  as: PreloadResourceType;
  priority?: LoadPriority;
  crossorigin?: boolean;
  integrity?: string;
}

// 載入管理器類別
class LoadingOptimizationManager {
  private loadingTasks = new Map<string, LoadingTask>();
  private loadingStates = new Map<string, LoadingState>();
  private loadedCache = new Map<string, any>();
  private observers = new Map<string, Set<(state: LoadingState) => void>>();
  private priorityQueues = new Map<LoadPriority, LoadingTask[]>();
  private isProcessing = false;
  
  // 優先級權重
  private readonly priorityWeights = {
    critical: 1000,
    high: 100,
    normal: 10,
    low: 1
  };

  constructor() {
    this.initializePriorityQueues();
    this.startProcessing();
  }

  // 初始化優先級佇列
  private initializePriorityQueues() {
    Object.keys(this.priorityWeights).forEach(priority => {
      this.priorityQueues.set(priority as LoadPriority, []);
    });
  }

  // 開始處理載入任務
  private startProcessing() {
    if (this.isProcessing) return;
    
    this.isProcessing = true;
    this.processNextTask();
  }

  // 處理下一個任務
  private async processNextTask() {
    const task = this.getNextTask();
    
    if (!task) {
      this.isProcessing = false;
      return;
    }

    await this.executeTask(task);
    
    // 繼續處理下一個任務
    requestAnimationFrame(() => this.processNextTask());
  }

  // 獲取下一個任務
  private getNextTask(): LoadingTask | null {
    // 按優先級順序檢查佇列
    for (const priority of ['critical', 'high', 'normal', 'low'] as LoadPriority[]) {
      const queue = this.priorityQueues.get(priority)!;
      
      // 找到可執行的任務（依賴項已完成）
      const taskIndex = queue.findIndex(task => this.canExecuteTask(task));
      
      if (taskIndex >= 0) {
        return queue.splice(taskIndex, 1)[0];
      }
    }
    
    return null;
  }

  // 檢查任務是否可執行
  private canExecuteTask(task: LoadingTask): boolean {
    if (!task.dependencies || task.dependencies.length === 0) {
      return true;
    }

    return task.dependencies.every(depId => 
      this.loadingStates.get(depId)?.isLoaded === true
    );
  }

  // 執行載入任務
  private async executeTask(task: LoadingTask) {
    const { id, loader, timeout = 10000, retries = 3, cache = true } = task;
    
    // 檢查快取
    if (cache && this.loadedCache.has(id)) {
      this.updateLoadingState(id, {
        isLoading: false,
        isLoaded: true,
        isError: false,
        progress: 100
      });
      return this.loadedCache.get(id);
    }

    // 更新載入狀態
    this.updateLoadingState(id, {
      isLoading: true,
      isLoaded: false,
      isError: false,
      progress: 0
    });

    let attempt = 0;
    
    while (attempt < retries) {
      try {
        // 設置超時
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error(`Loading timeout: ${id}`)), timeout);
        });

        const result = await Promise.race([
          loader(),
          timeoutPromise
        ]);

        // 載入成功
        if (cache) {
          this.loadedCache.set(id, result);
        }

        this.updateLoadingState(id, {
          isLoading: false,
          isLoaded: true,
          isError: false,
          progress: 100
        });

        return result;
        
      } catch (error) {
        attempt++;
        
        if (attempt >= retries) {
          // 載入失敗
          this.updateLoadingState(id, {
            isLoading: false,
            isLoaded: false,
            isError: true,
            error: error as Error,
            progress: 0
          });
          throw error;
        }

        // 重試前等待
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }

  // 更新載入狀態
  private updateLoadingState(id: string, state: LoadingState) {
    this.loadingStates.set(id, state);
    
    // 通知觀察者
    const observers = this.observers.get(id);
    if (observers) {
      observers.forEach(callback => callback(state));
    }
  }

  // 添加載入任務
  addTask<T>(task: LoadingTask<T>): void {
    const { id, priority } = task;
    
    // 檢查是否已存在
    if (this.loadingTasks.has(id)) {
      return;
    }

    this.loadingTasks.set(id, task);
    this.priorityQueues.get(priority)!.push(task);

    // 初始化載入狀態
    this.updateLoadingState(id, {
      isLoading: false,
      isLoaded: false,
      isError: false,
      progress: 0
    });

    // 如果不在處理中，開始處理
    if (!this.isProcessing) {
      this.startProcessing();
    }
  }

  // 載入資源
  async load<T>(id: string): Promise<T> {
    const task = this.loadingTasks.get(id);
    if (!task) {
      throw new Error(`Loading task not found: ${id}`);
    }

    const state = this.loadingStates.get(id);
    
    // 如果已載入，直接返回快取
    if (state?.isLoaded && this.loadedCache.has(id)) {
      return this.loadedCache.get(id);
    }

    // 如果正在載入，等待完成
    if (state?.isLoading) {
      return new Promise((resolve, reject) => {
        const unsubscribe = this.observeLoadingState(id, (newState) => {
          if (newState.isLoaded && this.loadedCache.has(id)) {
            unsubscribe();
            resolve(this.loadedCache.get(id));
          } else if (newState.isError) {
            unsubscribe();
            reject(newState.error);
          }
        });
      });
    }

    // 立即執行載入
    return this.executeTask(task);
  }

  // 觀察載入狀態
  observeLoadingState(id: string, callback: (state: LoadingState) => void): () => void {
    if (!this.observers.has(id)) {
      this.observers.set(id, new Set());
    }
    
    this.observers.get(id)!.add(callback);

    // 立即調用一次當前狀態
    const currentState = this.loadingStates.get(id);
    if (currentState) {
      callback(currentState);
    }

    // 返回取消訂閱函數
    return () => {
      this.observers.get(id)?.delete(callback);
    };
  }

  // 獲取載入狀態
  getLoadingState(id: string): LoadingState | undefined {
    return this.loadingStates.get(id);
  }

  // 預載入資源
  preloadResource(config: PreloadConfig): Promise<void> {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = config.href;
      link.as = config.as;
      
      if (config.crossorigin) {
        link.crossOrigin = 'anonymous';
      }
      
      if (config.integrity) {
        link.integrity = config.integrity;
      }

      link.onload = () => resolve();
      link.onerror = () => reject(new Error(`Failed to preload: ${config.href}`));

      document.head.appendChild(link);
    });
  }

  // 批量預載入
  async preloadResources(configs: PreloadConfig[]): Promise<void> {
    // 按優先級分組
    const groupedConfigs = configs.reduce((acc, config) => {
      const priority = config.priority || 'normal';
      if (!acc[priority]) acc[priority] = [];
      acc[priority].push(config);
      return acc;
    }, {} as Record<LoadPriority, PreloadConfig[]>);

    // 按優先級順序載入
    for (const priority of ['critical', 'high', 'normal', 'low'] as LoadPriority[]) {
      const configs = groupedConfigs[priority];
      if (configs) {
        await Promise.all(configs.map(config => this.preloadResource(config)));
      }
    }
  }

  // 清理快取
  clearCache(pattern?: RegExp): void {
    if (pattern) {
      const keysToDelete = Array.from(this.loadedCache.keys()).filter(key => pattern.test(key));
      keysToDelete.forEach(key => this.loadedCache.delete(key));
    } else {
      this.loadedCache.clear();
    }
  }

  // 獲取快取統計
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.loadedCache.size,
      keys: Array.from(this.loadedCache.keys())
    };
  }
}

// 創建全域實例
const loadingManager = new LoadingOptimizationManager();

// 懶載入組件高階組件
export function withLazyLoading<T extends React.ComponentType<any>>(
  loader: () => Promise<{ default: T }>,
  options: {
    fallback?: React.ComponentType;
    errorBoundary?: React.ComponentType<{ error: Error }>;
    priority?: LoadPriority;
  } = {}
): React.ComponentType<React.ComponentProps<T>> {
  const { fallback: Fallback, errorBoundary: ErrorBoundary, priority = 'normal' } = options;
  
  return React.lazy(() => {
    const taskId = `lazy-component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    loadingManager.addTask({
      id: taskId,
      priority,
      loader,
      cache: true
    });

    return loadingManager.load(taskId);
  });
}

// 代碼分割載入器
export class CodeSplitLoader {
  private static instance: CodeSplitLoader;
  
  static getInstance(): CodeSplitLoader {
    if (!CodeSplitLoader.instance) {
      CodeSplitLoader.instance = new CodeSplitLoader();
    }
    return CodeSplitLoader.instance;
  }

  // 載入模組
  async loadModule<T>(
    moduleLoader: () => Promise<T>,
    options: {
      id?: string;
      priority?: LoadPriority;
      dependencies?: string[];
      cache?: boolean;
    } = {}
  ): Promise<T> {
    const {
      id = `module-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      priority = 'normal',
      dependencies = [],
      cache = true
    } = options;

    loadingManager.addTask({
      id,
      priority,
      loader: moduleLoader,
      dependencies,
      cache
    });

    return loadingManager.load(id);
  }

  // 載入工具庫
  async loadLibrary(
    libraryName: string,
    loader: () => Promise<any>,
    priority: LoadPriority = 'normal'
  ): Promise<any> {
    const taskId = `library-${libraryName}`;
    
    loadingManager.addTask({
      id: taskId,
      priority,
      loader,
      cache: true
    });

    return loadingManager.load(taskId);
  }

  // 預載入關鍵模組
  preloadCriticalModules(moduleLoaders: Array<{
    id: string;
    loader: () => Promise<any>;
    dependencies?: string[];
  }>): void {
    moduleLoaders.forEach(({ id, loader, dependencies }) => {
      loadingManager.addTask({
        id,
        priority: 'critical',
        loader,
        dependencies,
        cache: true
      });
    });
  }
}

// 圖片懶載入
export class LazyImageLoader {
  private observer: IntersectionObserver;
  private loadedImages = new Set<string>();

  constructor() {
    this.observer = new IntersectionObserver(
      this.handleIntersection.bind(this),
      {
        rootMargin: '50px 0px',
        threshold: 0.01
      }
    );
  }

  // 處理交集事件
  private handleIntersection(entries: IntersectionObserverEntry[]) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        this.loadImage(img);
        this.observer.unobserve(img);
      }
    });
  }

  // 載入圖片
  private async loadImage(img: HTMLImageElement) {
    const src = img.dataset.src;
    if (!src || this.loadedImages.has(src)) {
      return;
    }

    try {
      // 添加載入狀態
      img.classList.add('loading');
      
      // 創建新圖片進行預載入
      const newImg = new Image();
      newImg.onload = () => {
        img.src = src;
        img.classList.remove('loading');
        img.classList.add('loaded');
        this.loadedImages.add(src);
      };
      
      newImg.onerror = () => {
        img.classList.remove('loading');
        img.classList.add('error');
      };
      
      newImg.src = src;
      
    } catch (error) {
      console.error('Failed to load image:', error);
      img.classList.remove('loading');
      img.classList.add('error');
    }
  }

  // 觀察圖片
  observe(img: HTMLImageElement) {
    this.observer.observe(img);
  }

  // 停止觀察
  unobserve(img: HTMLImageElement) {
    this.observer.unobserve(img);
  }

  // 銷毀
  destroy() {
    this.observer.disconnect();
    this.loadedImages.clear();
  }
}

// Hook: 使用載入狀態
export function useLoadingState(taskId: string): LoadingState {
  const [state, setState] = React.useState<LoadingState>({
    isLoading: false,
    isLoaded: false,
    isError: false
  });

  React.useEffect(() => {
    const unsubscribe = loadingManager.observeLoadingState(taskId, setState);
    return unsubscribe;
  }, [taskId]);

  return state;
}

// Hook: 懶載入資源
export function useLazyLoad<T>(
  loader: () => Promise<T>,
  options: {
    id?: string;
    priority?: LoadPriority;
    immediate?: boolean;
  } = {}
): [T | null, LoadingState, () => Promise<T>] {
  const {
    id = `lazy-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    priority = 'normal',
    immediate = false
  } = options;

  const [data, setData] = React.useState<T | null>(null);
  const loadingState = useLoadingState(id);

  const load = React.useCallback(async (): Promise<T> => {
    const result = await loadingManager.load<T>(id);
    setData(result);
    return result;
  }, [id]);

  React.useEffect(() => {
    // 添加任務
    loadingManager.addTask({
      id,
      priority,
      loader,
      cache: true
    });

    // 如果需要立即載入
    if (immediate) {
      load().catch(console.error);
    }
  }, [id, priority, immediate, load]);

  return [data, loadingState, load];
}

// 便利函數
export const codeSplitLoader = CodeSplitLoader.getInstance();
export const lazyImageLoader = new LazyImageLoader();

// 預載入關鍵資源
export const preloadCriticalResources = (configs: PreloadConfig[]) =>
  loadingManager.preloadResources(configs);

// 清理載入快取
export const clearLoadingCache = (pattern?: RegExp) =>
  loadingManager.clearCache(pattern);

// 獲取載入統計
export const getLoadingStats = () =>
  loadingManager.getCacheStats();

export default loadingManager;