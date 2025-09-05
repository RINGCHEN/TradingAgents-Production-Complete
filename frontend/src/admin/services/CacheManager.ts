/**
 * 高性能緩存管理器
 * 提供多層緩存機制，優化管理後台性能
 * 天工 - 第三優先級性能優化任務
 */

interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiry: number;
  accessCount: number;
  lastAccessed: number;
}

interface CacheStats {
  totalItems: number;
  hitRate: number;
  missRate: number;
  memoryUsage: number;
  oldestItem: number;
  newestItem: number;
}

interface CacheConfig {
  maxSize: number;
  defaultTTL: number; // Time To Live in milliseconds
  enableLRU: boolean;
  enableStats: boolean;
  compressionThreshold: number;
}

export class CacheManager {
  private cache = new Map<string, CacheItem<any>>();
  private stats = {
    hits: 0,
    misses: 0,
    sets: 0,
    deletes: 0,
    evictions: 0
  };
  
  private config: CacheConfig = {
    maxSize: 1000,
    defaultTTL: 5 * 60 * 1000, // 5 minutes
    enableLRU: true,
    enableStats: true,
    compressionThreshold: 50 * 1024 // 50KB
  };

  constructor(config?: Partial<CacheConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }
    
    // 定期清理過期項目
    setInterval(() => this.cleanup(), 60000); // 每分鐘清理一次
  }

  /**
   * 設置緩存項目
   */
  set<T>(key: string, data: T, ttl?: number): void {
    const expiry = ttl || this.config.defaultTTL;
    const timestamp = Date.now();
    
    // 如果緩存已滿，使用LRU策略移除最少使用的項目
    if (this.cache.size >= this.config.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }

    const cacheItem: CacheItem<T> = {
      data,
      timestamp,
      expiry: timestamp + expiry,
      accessCount: 0,
      lastAccessed: timestamp
    };

    this.cache.set(key, cacheItem);
    this.stats.sets++;
  }

  /**
   * 獲取緩存項目
   */
  get<T>(key: string): T | null {
    const item = this.cache.get(key);
    
    if (!item) {
      this.stats.misses++;
      return null;
    }

    const now = Date.now();
    
    // 檢查是否過期
    if (now > item.expiry) {
      this.cache.delete(key);
      this.stats.misses++;
      return null;
    }

    // 更新訪問統計
    item.accessCount++;
    item.lastAccessed = now;
    this.stats.hits++;

    return item.data as T;
  }

  /**
   * 獲取或設置緩存（如果不存在則執行獲取函數）
   */
  async getOrSet<T>(
    key: string, 
    fetchFn: () => Promise<T>, 
    ttl?: number
  ): Promise<T> {
    const cached = this.get<T>(key);
    
    if (cached !== null) {
      return cached;
    }

    try {
      const data = await fetchFn();
      this.set(key, data, ttl);
      return data;
    } catch (error) {
      console.error(`緩存獲取失敗 [${key}]:`, error);
      throw error;
    }
  }

  /**
   * 刪除緩存項目
   */
  delete(key: string): boolean {
    const deleted = this.cache.delete(key);
    if (deleted) {
      this.stats.deletes++;
    }
    return deleted;
  }

  /**
   * 清除所有緩存
   */
  clear(): void {
    this.cache.clear();
    this.resetStats();
  }

  /**
   * 檢查緩存是否存在且未過期
   */
  has(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) return false;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  /**
   * 獲取緩存統計信息
   */
  getStats(): CacheStats {
    const now = Date.now();
    const items = Array.from(this.cache.values());
    
    return {
      totalItems: this.cache.size,
      hitRate: this.stats.hits / (this.stats.hits + this.stats.misses) || 0,
      missRate: this.stats.misses / (this.stats.hits + this.stats.misses) || 0,
      memoryUsage: this.estimateMemoryUsage(),
      oldestItem: items.length > 0 ? Math.min(...items.map(item => item.timestamp)) : now,
      newestItem: items.length > 0 ? Math.max(...items.map(item => item.timestamp)) : now
    };
  }

  /**
   * 使用LRU策略移除最少使用的項目
   */
  private evictLRU(): void {
    if (this.cache.size === 0) return;

    let lruKey = '';
    let lruItem: CacheItem<any> | null = null;

    for (const [key, item] of this.cache) {
      if (!lruItem || item.lastAccessed < lruItem.lastAccessed) {
        lruKey = key;
        lruItem = item;
      }
    }

    if (lruKey) {
      this.cache.delete(lruKey);
      this.stats.evictions++;
    }
  }

  /**
   * 清理過期的緩存項目
   */
  private cleanup(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    for (const [key, item] of this.cache) {
      if (now > item.expiry) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => {
      this.cache.delete(key);
      this.stats.deletes++;
    });

    if (keysToDelete.length > 0) {
      console.log(`緩存清理完成，移除 ${keysToDelete.length} 個過期項目`);
    }
  }

  /**
   * 估算內存使用量
   */
  private estimateMemoryUsage(): number {
    let size = 0;
    
    for (const [key, item] of this.cache) {
      size += key.length * 2; // 字符串按UTF-16計算
      size += JSON.stringify(item.data).length * 2;
      size += 64; // 估算CacheItem元數據大小
    }
    
    return size;
  }

  /**
   * 重置統計數據
   */
  private resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      evictions: 0
    };
  }

  /**
   * 預熱緩存 - 預載入常用數據
   */
  async warmup(warmupData: Array<{key: string, fetchFn: () => Promise<any>, ttl?: number}>): Promise<void> {
    console.log('開始緩存預熱...');
    
    const promises = warmupData.map(async ({key, fetchFn, ttl}) => {
      try {
        const data = await fetchFn();
        this.set(key, data, ttl);
        return { key, success: true };
      } catch (error) {
        console.error(`預熱失敗 [${key}]:`, error);
        return { key, success: false, error };
      }
    });

    const results = await Promise.allSettled(promises);
    const successful = results.filter(result => 
      result.status === 'fulfilled' && result.value.success
    ).length;

    console.log(`緩存預熱完成：${successful}/${warmupData.length} 個項目成功載入`);
  }

  /**
   * 獲取緩存鍵的模式匹配
   */
  getKeysMatching(pattern: RegExp): string[] {
    const matchingKeys: string[] = [];
    
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) {
        matchingKeys.push(key);
      }
    }
    
    return matchingKeys;
  }

  /**
   * 批量刪除符合模式的緩存
   */
  deletePattern(pattern: RegExp): number {
    const keysToDelete = this.getKeysMatching(pattern);
    
    keysToDelete.forEach(key => this.cache.delete(key));
    this.stats.deletes += keysToDelete.length;
    
    return keysToDelete.length;
  }
}

// 全局緩存管理器實例
export const globalCacheManager = new CacheManager({
  maxSize: 500,
  defaultTTL: 10 * 60 * 1000, // 10分鐘
  enableLRU: true,
  enableStats: true
});

// 專用於API響應的緩存管理器
export const apiCacheManager = new CacheManager({
  maxSize: 200,
  defaultTTL: 5 * 60 * 1000, // 5分鐘
  enableLRU: true,
  enableStats: true
});

// 專用於用戶數據的緩存管理器  
export const userDataCacheManager = new CacheManager({
  maxSize: 100,
  defaultTTL: 15 * 60 * 1000, // 15分鐘
  enableLRU: true,
  enableStats: true
});