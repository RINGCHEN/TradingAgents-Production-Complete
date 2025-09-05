/**
 * CouponManager - 優惠券管理器
 * 安全載入優惠券數據，修復SyntaxError錯誤，實施緩存和降級機制
 */

import { ApiClient, ApiResponse, ApiError } from '../services/ApiClient';
import { reportComponentError } from './ErrorDiagnostics';

export interface Coupon {
  id: string;
  code: string;
  title: string;
  description: string;
  discount: number;
  discountType: 'percentage' | 'fixed';
  validFrom: Date;
  validTo: Date;
  isActive: boolean;
  usageLimit?: number;
  usedCount?: number;
  minAmount?: number;
  applicableProducts?: string[];
}

export interface CouponState {
  coupons: Coupon[];
  isLoading: boolean;
  error?: string;
  lastFetch?: Date;
  cacheExpiry?: Date;
  fallbackMode: boolean;
  retryCount: number;
}

export interface CouponManagerConfig {
  cacheTimeout: number; // 緩存超時時間（毫秒）
  maxRetries: number;    // 最大重試次數
  retryDelay: number;    // 重試延遲（毫秒）
  fallbackCoupons: Coupon[]; // 降級時使用的優惠券
  enableDiagnostics: boolean; // 是否啟用診斷
}

const DEFAULT_CONFIG: CouponManagerConfig = {
  cacheTimeout: 5 * 60 * 1000, // 5分鐘
  maxRetries: 3,
  retryDelay: 2000,
  fallbackCoupons: [
    {
      id: 'fallback-welcome',
      code: 'WELCOME10',
      title: '新用戶歡迎優惠',
      description: '新用戶專享10%折扣',
      discount: 10,
      discountType: 'percentage',
      validFrom: new Date('2024-01-01'),
      validTo: new Date('2025-12-31'),
      isActive: true,
      minAmount: 100
    }
  ],
  enableDiagnostics: true
};

export class CouponManager {
  private apiClient: ApiClient;
  private config: CouponManagerConfig;
  private state: CouponState;
  private cacheKey = 'tradingagents_coupons_cache';
  private stateKey = 'tradingagents_coupons_state';

  constructor(apiClient: ApiClient, config: Partial<CouponManagerConfig> = {}) {
    this.apiClient = apiClient;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.state = this.loadStateFromCache() || {
      coupons: [],
      isLoading: false,
      fallbackMode: false,
      retryCount: 0
    };
  }

  /**
   * 安全載入優惠券數據
   */
  async loadCoupons(): Promise<CouponState> {
    // 檢查緩存是否有效
    if (this.isCacheValid()) {
      if (this.config.enableDiagnostics) {
        console.log('[CouponManager] Using cached coupons');
      }
      return this.state;
    }

    this.state.isLoading = true;
    this.state.error = undefined;
    this.saveStateToCache();

    try {
      const response = await this.fetchCouponsWithRetry();
      
      if (response.success && response.data) {
        // 成功載入
        this.state = {
          coupons: this.validateAndTransformCoupons(response.data),
          isLoading: false,
          lastFetch: new Date(),
          cacheExpiry: new Date(Date.now() + this.config.cacheTimeout),
          fallbackMode: false,
          retryCount: 0
        };

        this.saveCouponsToCache(this.state.coupons);
        
        if (this.config.enableDiagnostics) {
          console.log('[CouponManager] Successfully loaded coupons:', this.state.coupons.length);
        }
      } else {
        // API失敗，使用降級機制
        await this.handleApiFailure(response.error);
      }
    } catch (error) {
      // 處理意外錯誤
      await this.handleUnexpectedError(error);
    }

    this.saveStateToCache();
    return this.state;
  }

  /**
   * 帶重試機制的API調用
   */
  private async fetchCouponsWithRetry(): Promise<ApiResponse<any>> {
    let lastError: ApiError | undefined;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        if (this.config.enableDiagnostics) {
          console.log(`[CouponManager] Fetching coupons, attempt ${attempt + 1}/${this.config.maxRetries + 1}`);
        }

        const response = await this.apiClient.request('/api/coupons', {
          method: 'GET',
          timeout: 8000,
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        // 檢查響應格式
        if (response && response.success) {
          const contentType = response.headers?.['content-type'] || '';
          
          // 檢測HTML響應（常見的SyntaxError原因）
          if (contentType.includes('text/html')) {
            const formatError: ApiError = {
              type: 'format',
              message: 'API returned HTML instead of JSON - likely routing issue',
              endpoint: '/api/coupons',
              timestamp: new Date(),
              details: { contentType, attempt: attempt + 1 }
            };

            if (this.config.enableDiagnostics) {
              reportComponentError('coupon', 'Coupon API returned HTML instead of JSON', {
                error: formatError,
                suggestion: 'Check API routing configuration'
              });
            }

            lastError = formatError;
            
            // 如果不是最後一次嘗試，繼續重試
            if (attempt < this.config.maxRetries) {
              await this.delay(this.config.retryDelay * (attempt + 1));
              continue;
            }
          } else {
            // 成功的JSON響應
            return response;
          }
        } else if (response) {
          lastError = response.error;
          
          // 如果不是最後一次嘗試，繼續重試
          if (attempt < this.config.maxRetries) {
            await this.delay(this.config.retryDelay * (attempt + 1));
            continue;
          }
        }
      } catch (error) {
        lastError = {
          type: 'network',
          message: error instanceof Error ? error.message : 'Network error',
          endpoint: '/api/coupons',
          timestamp: new Date(),
          details: { error, attempt: attempt + 1 }
        };

        if (this.config.enableDiagnostics) {
          console.error(`[CouponManager] Network error on attempt ${attempt + 1}:`, error);
        }

        // 如果不是最後一次嘗試，繼續重試
        if (attempt < this.config.maxRetries) {
          await this.delay(this.config.retryDelay * (attempt + 1));
          continue;
        }
      }
    }

    // 所有重試都失敗了
    return {
      success: false,
      status: 0,
      error: lastError || {
        type: 'client',
        message: 'All retry attempts failed',
        endpoint: '/api/coupons',
        timestamp: new Date()
      },
      headers: {}
    };
  }

  /**
   * 處理API失敗
   */
  private async handleApiFailure(error?: ApiError): Promise<void> {
    this.state.retryCount++;
    
    if (this.config.enableDiagnostics && error) {
      reportComponentError('coupon', `Coupon API failed: ${error.message}`, {
        error,
        retryCount: this.state.retryCount,
        fallbackActivated: true
      });
    }

    // 嘗試使用緩存的優惠券
    const cachedCoupons = this.loadCouponsFromCache();
    if (cachedCoupons && cachedCoupons.length > 0) {
      this.state = {
        coupons: cachedCoupons,
        isLoading: false,
        error: '使用緩存的優惠券數據',
        lastFetch: this.state.lastFetch,
        fallbackMode: true,
        retryCount: this.state.retryCount
      };

      if (this.config.enableDiagnostics) {
        console.log('[CouponManager] Using cached coupons as fallback');
      }
    } else {
      // 使用預設的降級優惠券
      this.state = {
        coupons: this.config.fallbackCoupons,
        isLoading: false,
        error: '優惠券服務暫時不可用，顯示預設優惠',
        fallbackMode: true,
        retryCount: this.state.retryCount
      };

      if (this.config.enableDiagnostics) {
        console.log('[CouponManager] Using fallback coupons');
      }
    }
  }

  /**
   * 處理意外錯誤
   */
  private async handleUnexpectedError(error: any): Promise<void> {
    this.state.retryCount++;
    
    if (this.config.enableDiagnostics) {
      reportComponentError('coupon', 'Unexpected error loading coupons', {
        error,
        retryCount: this.state.retryCount
      });
    }

    // 檢查是否是SyntaxError（通常由HTML響應引起）
    if (error instanceof SyntaxError && error.message.includes('JSON')) {
      this.state.error = '優惠券數據格式錯誤，可能是服務器配置問題';
    } else {
      this.state.error = '載入優惠券時發生未預期錯誤';
    }

    // 使用降級機制
    await this.handleApiFailure();
  }

  /**
   * 驗證和轉換優惠券數據
   */
  private validateAndTransformCoupons(data: any): Coupon[] {
    if (!Array.isArray(data)) {
      if (this.config.enableDiagnostics) {
        console.warn('[CouponManager] Invalid coupon data format, expected array');
      }
      return [];
    }

    return data
      .filter(item => item && typeof item === 'object')
      .map(item => ({
        id: item.id || `coupon_${Date.now()}_${Math.random()}`,
        code: item.code || '',
        title: item.title || item.name || '優惠券',
        description: item.description || '',
        discount: Number(item.discount) || 0,
        discountType: item.discountType === 'fixed' ? 'fixed' : 'percentage',
        validFrom: item.validFrom ? new Date(item.validFrom) : new Date(),
        validTo: item.validTo ? new Date(item.validTo) : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        isActive: Boolean(item.isActive !== false),
        usageLimit: item.usageLimit ? Number(item.usageLimit) : undefined,
        usedCount: item.usedCount ? Number(item.usedCount) : 0,
        minAmount: item.minAmount ? Number(item.minAmount) : undefined,
        applicableProducts: Array.isArray(item.applicableProducts) ? item.applicableProducts : undefined
      }))
      .filter(coupon => coupon.code && coupon.discount > 0);
  }

  /**
   * 檢查緩存是否有效
   */
  private isCacheValid(): boolean {
    if (!this.state.cacheExpiry || !this.state.lastFetch) {
      return false;
    }

    return new Date() < this.state.cacheExpiry && this.state.coupons.length > 0;
  }

  /**
   * 保存優惠券到緩存
   */
  private saveCouponsToCache(coupons: Coupon[]): void {
    try {
      localStorage.setItem(this.cacheKey, JSON.stringify({
        coupons,
        timestamp: Date.now()
      }));
    } catch (error) {
      if (this.config.enableDiagnostics) {
        console.warn('[CouponManager] Failed to save coupons to cache:', error);
      }
    }
  }

  /**
   * 從緩存載入優惠券
   */
  private loadCouponsFromCache(): Coupon[] | null {
    try {
      const cached = localStorage.getItem(this.cacheKey);
      if (!cached) return null;

      const data = JSON.parse(cached);
      const age = Date.now() - data.timestamp;
      
      // 緩存超過24小時就不使用
      if (age > 24 * 60 * 60 * 1000) {
        localStorage.removeItem(this.cacheKey);
        return null;
      }

      return data.coupons || null;
    } catch (error) {
      if (this.config.enableDiagnostics) {
        console.warn('[CouponManager] Failed to load coupons from cache:', error);
      }
      return null;
    }
  }

  /**
   * 保存狀態到緩存
   */
  private saveStateToCache(): void {
    try {
      localStorage.setItem(this.stateKey, JSON.stringify(this.state));
    } catch (error) {
      if (this.config.enableDiagnostics) {
        console.warn('[CouponManager] Failed to save state to cache:', error);
      }
    }
  }

  /**
   * 從緩存載入狀態
   */
  private loadStateFromCache(): CouponState | null {
    try {
      const cached = localStorage.getItem(this.stateKey);
      if (!cached) return null;

      const state = JSON.parse(cached);
      
      // 轉換日期字符串回Date對象
      if (state.lastFetch) state.lastFetch = new Date(state.lastFetch);
      if (state.cacheExpiry) state.cacheExpiry = new Date(state.cacheExpiry);
      
      return state;
    } catch (error) {
      if (this.config.enableDiagnostics) {
        console.warn('[CouponManager] Failed to load state from cache:', error);
      }
      return null;
    }
  }

  /**
   * 延遲函數
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 獲取當前狀態
   */
  getState(): CouponState {
    return { ...this.state };
  }

  /**
   * 強制重新載入優惠券
   */
  async reload(): Promise<CouponState> {
    // 清除緩存
    this.state.cacheExpiry = undefined;
    this.state.lastFetch = undefined;
    localStorage.removeItem(this.cacheKey);
    localStorage.removeItem(this.stateKey);
    
    return this.loadCoupons();
  }

  /**
   * 清除所有緩存和狀態
   */
  clearCache(): void {
    localStorage.removeItem(this.cacheKey);
    localStorage.removeItem(this.stateKey);
    this.state = {
      coupons: [],
      isLoading: false,
      fallbackMode: false,
      retryCount: 0
    };
  }

  /**
   * 獲取可用的優惠券
   */
  getAvailableCoupons(): Coupon[] {
    const now = new Date();
    return this.state.coupons.filter(coupon => 
      coupon.isActive && 
      coupon.validFrom <= now && 
      coupon.validTo >= now &&
      (!coupon.usageLimit || (coupon.usedCount || 0) < coupon.usageLimit)
    );
  }

  /**
   * 根據金額獲取適用的優惠券
   */
  getApplicableCoupons(amount: number): Coupon[] {
    return this.getAvailableCoupons().filter(coupon =>
      !coupon.minAmount || amount >= coupon.minAmount
    );
  }

  /**
   * 計算優惠券折扣
   */
  calculateDiscount(coupon: Coupon, amount: number): number {
    if (coupon.minAmount && amount < coupon.minAmount) {
      return 0;
    }

    if (coupon.discountType === 'percentage') {
      return Math.min(amount * (coupon.discount / 100), amount);
    } else {
      return Math.min(coupon.discount, amount);
    }
  }
}

export default CouponManager;