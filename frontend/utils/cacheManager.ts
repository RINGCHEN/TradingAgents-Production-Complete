/**
 * 快取管理器 - 第二階段Week 3 性能調優與監控
 * 統一快取策略、Service Worker 整合、CDN 優化
 * 支援多層快取、智能更新、性能監控
 */

// 快取層級
export enum CacheLayer {
  MEMORY = 'memory',
  LOCAL_STORAGE = 'localStorage',
  SESSION_STORAGE = 'sessionStorage',
  INDEXED_DB = 'indexedDB',
  SERVICE_WORKER = 'serviceWorker'
}

// 快取策略
export enum CacheStrategy {
  CACHE_FIRST = 'cacheFirst',
  NETWORK_FIRST = 'networkFirst',
  STALE_WHILE_REVALIDATE = 'staleWhileRevalidate',
  CACHE_ONLY = 'cacheOnly',
  NETWORK_ONLY = 'networkOnly'
}

// 快取配置
export interface CacheConfig {
  key: string;
  layer: CacheLayer;
  strategy: CacheStrategy;
  maxAge?: number;
  maxSize?: number;
  version?: string;
  compress?: boolean;
  encrypt?: boolean;
}

// 快取項目
export interface CacheItem<T = any> {
  key: string;
  data: T;
  timestamp: number;
  expiresAt?: number;
  version?: string;
  size: number;
  hits: number;
  compressed?: boolean;
  encrypted?: boolean;
}

// 快取統計
export interface CacheStats {
  totalItems: number;
  totalSize: number;
  hitRate: number;
  missRate: number;
  memoryUsage: number;
  oldestItem?: Date;
  newestItem?: Date;
}

// 快取管理器類別
class CacheManager {
  private memoryCache = new Map<string, CacheItem>();
  private maxMemorySize = 50 * 1024 * 1024; // 50MB
  private currentMemorySize = 0;
  private hitCount = 0;
  private missCount = 0;
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;

  constructor() {
    this.initializeServiceWorker();
    this.startCleanupInterval();
  }

  // 初始化 Service Worker
  private async initializeServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.serviceWorkerRegistration = await navigator.serviceWorker.register('/sw.js');
        console.log('[CacheManager] Service Worker registered successfully');
        
        // 監聽 Service Worker 更新
        this.serviceWorkerRegistration.addEventListener('updatefound', () => {
          console.log('[CacheManager] Service Worker update found');
        });

      } catch (error) {
        console.error('[CacheManager] Service Worker registration failed:', error);
      }
    }
  }

  // 設置快取項目
  async set<T>(
    key: string,
    data: T,
    config: Partial<CacheConfig> = {}
  ): Promise<void> {
    const finalConfig: CacheConfig = {
      key,
      layer: CacheLayer.MEMORY,
      strategy: CacheStrategy.CACHE_FIRST,
      maxAge: 60 * 60 * 1000, // 1小時
      compress: false,
      encrypt: false,
      ...config
    };

    const cacheItem: CacheItem<T> = {
      key,
      data: finalConfig.compress ? await this.compress(data) : data,
      timestamp: Date.now(),
      expiresAt: finalConfig.maxAge ? Date.now() + finalConfig.maxAge : undefined,
      version: finalConfig.version,
      size: this.calculateSize(data),
      hits: 0,
      compressed: finalConfig.compress,
      encrypted: finalConfig.encrypt
    };

    // 根據快取層級存儲
    switch (finalConfig.layer) {
      case CacheLayer.MEMORY:
        await this.setMemoryCache(cacheItem);
        break;
      case CacheLayer.LOCAL_STORAGE:
        await this.setLocalStorageCache(cacheItem);
        break;
      case CacheLayer.SESSION_STORAGE:
        await this.setSessionStorageCache(cacheItem);
        break;
      case CacheLayer.INDEXED_DB:
        await this.setIndexedDBCache(cacheItem);
        break;
      case CacheLayer.SERVICE_WORKER:
        await this.setServiceWorkerCache(cacheItem);
        break;
    }
  }

  // 獲取快取項目
  async get<T>(
    key: string,
    layer: CacheLayer = CacheLayer.MEMORY
  ): Promise<T | null> {
    let cacheItem: CacheItem<T> | null = null;

    // 根據快取層級獲取
    switch (layer) {
      case CacheLayer.MEMORY:
        cacheItem = this.getMemoryCache<T>(key);
        break;
      case CacheLayer.LOCAL_STORAGE:
        cacheItem = await this.getLocalStorageCache<T>(key);
        break;
      case CacheLayer.SESSION_STORAGE:
        cacheItem = await this.getSessionStorageCache<T>(key);
        break;
      case CacheLayer.INDEXED_DB:
        cacheItem = await this.getIndexedDBCache<T>(key);
        break;
      case CacheLayer.SERVICE_WORKER:
        cacheItem = await this.getServiceWorkerCache<T>(key);
        break;
    }

    if (!cacheItem) {
      this.missCount++;
      return null;
    }

    // 檢查過期
    if (cacheItem.expiresAt && Date.now() > cacheItem.expiresAt) {
      await this.delete(key, layer);
      this.missCount++;
      return null;
    }

    // 更新命中統計
    cacheItem.hits++;
    this.hitCount++;

    // 解壓縮數據
    const data = cacheItem.compressed 
      ? await this.decompress(cacheItem.data)
      : cacheItem.data;

    return data;
  }

  // 記憶體快取操作
  private async setMemoryCache<T>(item: CacheItem<T>) {
    // 檢查記憶體限制
    if (this.currentMemorySize + item.size > this.maxMemorySize) {
      await this.evictMemoryCache(item.size);
    }

    this.memoryCache.set(item.key, item);
    this.currentMemorySize += item.size;
  }

  private getMemoryCache<T>(key: string): CacheItem<T> | null {
    return this.memoryCache.get(key) as CacheItem<T> || null;
  }

  // 記憶體快取淘汰策略（LRU）
  private async evictMemoryCache(requiredSize: number) {
    const entries = Array.from(this.memoryCache.entries());
    
    // 按最後使用時間排序（LRU）
    entries.sort((a, b) => {
      const aLastUsed = a[1].timestamp + (a[1].hits * 1000);
      const bLastUsed = b[1].timestamp + (b[1].hits * 1000);
      return aLastUsed - bLastUsed;
    });

    let freedSize = 0;
    
    for (const [key, item] of entries) {
      this.memoryCache.delete(key);
      this.currentMemorySize -= item.size;
      freedSize += item.size;
      
      if (freedSize >= requiredSize) {
        break;
      }
    }
  }

  // LocalStorage 快取操作
  private async setLocalStorageCache<T>(item: CacheItem<T>) {
    try {
      const serialized = JSON.stringify(item);
      localStorage.setItem(`cache_${item.key}`, serialized);
    } catch (error) {
      console.error('[CacheManager] LocalStorage cache set failed:', error);
    }
  }

  private async getLocalStorageCache<T>(key: string): Promise<CacheItem<T> | null> {
    try {
      const serialized = localStorage.getItem(`cache_${key}`);
      if (!serialized) return null;
      
      return JSON.parse(serialized) as CacheItem<T>;
    } catch (error) {
      console.error('[CacheManager] LocalStorage cache get failed:', error);
      return null;
    }
  }

  // SessionStorage 快取操作
  private async setSessionStorageCache<T>(item: CacheItem<T>) {
    try {
      const serialized = JSON.stringify(item);
      sessionStorage.setItem(`cache_${item.key}`, serialized);
    } catch (error) {
      console.error('[CacheManager] SessionStorage cache set failed:', error);
    }
  }

  private async getSessionStorageCache<T>(key: string): Promise<CacheItem<T> | null> {
    try {
      const serialized = sessionStorage.getItem(`cache_${key}`);
      if (!serialized) return null;
      
      return JSON.parse(serialized) as CacheItem<T>;
    } catch (error) {
      console.error('[CacheManager] SessionStorage cache get failed:', error);
      return null;
    }
  }

  // IndexedDB 快取操作
  private async setIndexedDBCache<T>(item: CacheItem<T>) {
    return new Promise<void>((resolve, reject) => {
      const request = indexedDB.open('TradingAgentsCache', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        
        const putRequest = store.put(item);
        
        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(putRequest.error);
      };
      
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('cache')) {
          const store = db.createObjectStore('cache', { keyPath: 'key' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('expiresAt', 'expiresAt', { unique: false });
        }
      };
    });
  }

  private async getIndexedDBCache<T>(key: string): Promise<CacheItem<T> | null> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('TradingAgentsCache', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readonly');
        const store = transaction.objectStore('cache');
        
        const getRequest = store.get(key);
        
        getRequest.onsuccess = () => {
          resolve(getRequest.result || null);
        };
        
        getRequest.onerror = () => reject(getRequest.error);
      };
    });
  }

  // Service Worker 快取操作
  private async setServiceWorkerCache<T>(item: CacheItem<T>) {
    if (!this.serviceWorkerRegistration || !this.serviceWorkerRegistration.active) {
      throw new Error('Service Worker not available');
    }

    // 通過 postMessage 與 Service Worker 通信
    this.serviceWorkerRegistration.active.postMessage({
      type: 'CACHE_SET',
      key: item.key,
      data: item
    });
  }

  private async getServiceWorkerCache<T>(key: string): Promise<CacheItem<T> | null> {
    if (!this.serviceWorkerRegistration || !this.serviceWorkerRegistration.active) {
      return null;
    }

    return new Promise((resolve) => {
      const channel = new MessageChannel();
      
      channel.port1.onmessage = (event) => {
        if (event.data.type === 'CACHE_GET_RESPONSE') {
          resolve(event.data.data || null);
        }
      };

      this.serviceWorkerRegistration!.active!.postMessage({
        type: 'CACHE_GET',
        key
      }, [channel.port2]);

      // 超時處理
      setTimeout(() => resolve(null), 5000);
    });
  }

  // 刪除快取項目
  async delete(key: string, layer: CacheLayer = CacheLayer.MEMORY): Promise<boolean> {
    switch (layer) {
      case CacheLayer.MEMORY:
        const item = this.memoryCache.get(key);
        if (item) {
          this.memoryCache.delete(key);
          this.currentMemorySize -= item.size;
          return true;
        }
        return false;

      case CacheLayer.LOCAL_STORAGE:
        localStorage.removeItem(`cache_${key}`);
        return true;

      case CacheLayer.SESSION_STORAGE:
        sessionStorage.removeItem(`cache_${key}`);
        return true;

      case CacheLayer.INDEXED_DB:
        return this.deleteIndexedDBCache(key);

      case CacheLayer.SERVICE_WORKER:
        return this.deleteServiceWorkerCache(key);

      default:
        return false;
    }
  }

  // IndexedDB 刪除操作
  private async deleteIndexedDBCache(key: string): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('TradingAgentsCache', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        
        const deleteRequest = store.delete(key);
        
        deleteRequest.onsuccess = () => resolve(true);
        deleteRequest.onerror = () => resolve(false);
      };
    });
  }

  // Service Worker 刪除操作
  private async deleteServiceWorkerCache(key: string): Promise<boolean> {
    if (!this.serviceWorkerRegistration || !this.serviceWorkerRegistration.active) {
      return false;
    }

    this.serviceWorkerRegistration.active.postMessage({
      type: 'CACHE_DELETE',
      key
    });

    return true;
  }

  // 清除快取
  async clear(layer?: CacheLayer): Promise<void> {
    if (!layer) {
      // 清除所有層級
      this.memoryCache.clear();
      this.currentMemorySize = 0;
      localStorage.clear();
      sessionStorage.clear();
      await this.clearIndexedDBCache();
      await this.clearServiceWorkerCache();
    } else {
      switch (layer) {
        case CacheLayer.MEMORY:
          this.memoryCache.clear();
          this.currentMemorySize = 0;
          break;
        case CacheLayer.LOCAL_STORAGE:
          // 只清除快取相關的項目
          Object.keys(localStorage)
            .filter(key => key.startsWith('cache_'))
            .forEach(key => localStorage.removeItem(key));
          break;
        case CacheLayer.SESSION_STORAGE:
          Object.keys(sessionStorage)
            .filter(key => key.startsWith('cache_'))
            .forEach(key => sessionStorage.removeItem(key));
          break;
        case CacheLayer.INDEXED_DB:
          await this.clearIndexedDBCache();
          break;
        case CacheLayer.SERVICE_WORKER:
          await this.clearServiceWorkerCache();
          break;
      }
    }
  }

  // 清除 IndexedDB 快取
  private async clearIndexedDBCache(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('TradingAgentsCache', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        
        const clearRequest = store.clear();
        
        clearRequest.onsuccess = () => resolve();
        clearRequest.onerror = () => reject(clearRequest.error);
      };
    });
  }

  // 清除 Service Worker 快取
  private async clearServiceWorkerCache(): Promise<void> {
    if (this.serviceWorkerRegistration && this.serviceWorkerRegistration.active) {
      this.serviceWorkerRegistration.active.postMessage({
        type: 'CLEAR_CACHE'
      });
    }
  }

  // 獲取快取統計
  getStats(): CacheStats {
    const items = Array.from(this.memoryCache.values());
    const totalRequests = this.hitCount + this.missCount;
    
    return {
      totalItems: items.length,
      totalSize: this.currentMemorySize,
      hitRate: totalRequests > 0 ? (this.hitCount / totalRequests) * 100 : 0,
      missRate: totalRequests > 0 ? (this.missCount / totalRequests) * 100 : 0,
      memoryUsage: (this.currentMemorySize / this.maxMemorySize) * 100,
      oldestItem: items.length > 0 
        ? new Date(Math.min(...items.map(item => item.timestamp)))
        : undefined,
      newestItem: items.length > 0
        ? new Date(Math.max(...items.map(item => item.timestamp)))
        : undefined
    };
  }

  // 壓縮數據
  private async compress<T>(data: T): Promise<T> {
    try {
      // 簡單的 JSON 壓縮（實際項目中可能使用 LZ 演算法）
      const jsonString = JSON.stringify(data);
      const compressed = jsonString.replace(/\s+/g, '');
      return JSON.parse(compressed);
    } catch (error) {
      console.error('[CacheManager] Compression failed:', error);
      return data;
    }
  }

  // 解壓縮數據
  private async decompress<T>(data: T): Promise<T> {
    // 由於使用簡單壓縮，解壓縮就是原數據
    return data;
  }

  // 計算數據大小
  private calculateSize(data: any): number {
    try {
      return new Blob([JSON.stringify(data)]).size;
    } catch (error) {
      return 0;
    }
  }

  // 啟動清理定時器
  private startCleanupInterval() {
    setInterval(() => {
      this.cleanup();
    }, 5 * 60 * 1000); // 每5分鐘清理一次
  }

  // 清理過期項目
  private async cleanup() {
    const now = Date.now();
    const expiredKeys: string[] = [];

    // 清理記憶體快取中的過期項目
    for (const [key, item] of this.memoryCache.entries()) {
      if (item.expiresAt && now > item.expiresAt) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => {
      const item = this.memoryCache.get(key);
      if (item) {
        this.memoryCache.delete(key);
        this.currentMemorySize -= item.size;
      }
    });

    console.log(`[CacheManager] Cleaned up ${expiredKeys.length} expired items`);
  }
}

// 創建全域實例
export const cacheManager = new CacheManager();

// CDN 優化工具
export class CDNOptimizer {
  private cdnHosts: string[] = [];
  private failedHosts = new Set<string>();
  private hostLatency = new Map<string, number>();

  constructor(hosts: string[] = []) {
    this.cdnHosts = hosts;
    this.testHostsLatency();
  }

  // 測試主機延遲
  private async testHostsLatency() {
    const testPromises = this.cdnHosts.map(async (host) => {
      try {
        const start = performance.now();
        await fetch(`https://${host}/ping`, { method: 'HEAD' });
        const latency = performance.now() - start;
        this.hostLatency.set(host, latency);
        this.failedHosts.delete(host);
      } catch (error) {
        this.failedHosts.add(host);
        this.hostLatency.set(host, Infinity);
      }
    });

    await Promise.allSettled(testPromises);
  }

  // 獲取最佳主機
  getBestHost(): string | null {
    const availableHosts = this.cdnHosts.filter(host => !this.failedHosts.has(host));
    
    if (availableHosts.length === 0) {
      return null;
    }

    return availableHosts.reduce((best, current) => {
      const bestLatency = this.hostLatency.get(best) || Infinity;
      const currentLatency = this.hostLatency.get(current) || Infinity;
      return currentLatency < bestLatency ? current : best;
    });
  }

  // 優化資源 URL
  optimizeUrl(originalUrl: string): string {
    const bestHost = this.getBestHost();
    
    if (!bestHost) {
      return originalUrl;
    }

    try {
      const url = new URL(originalUrl);
      url.hostname = bestHost;
      return url.toString();
    } catch (error) {
      return originalUrl;
    }
  }

  // 預取資源
  async prefetch(urls: string[]): Promise<void> {
    const prefetchPromises = urls.map(async (url) => {
      try {
        const optimizedUrl = this.optimizeUrl(url);
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = optimizedUrl;
        document.head.appendChild(link);
      } catch (error) {
        console.error(`[CDNOptimizer] Prefetch failed for ${url}:`, error);
      }
    });

    await Promise.allSettled(prefetchPromises);
  }
}

export default cacheManager;