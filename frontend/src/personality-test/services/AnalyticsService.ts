/**
 * 分析追蹤服務
 * 負責追蹤用戶行為、轉換事件和性能指標
 */

export interface AnalyticsEvent {
  event_name: string;
  properties: Record<string, any>;
  timestamp: string;
  session_id?: string;
  user_id?: string;
}

export interface UserProperties {
  user_id?: string;
  session_id?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  referrer?: string;
  user_agent?: string;
  screen_resolution?: string;
  viewport_size?: string;
  device_type?: 'desktop' | 'tablet' | 'mobile';
  browser?: string;
  os?: string;
}

export class AnalyticsService {
  private sessionId: string;
  private userId?: string;
  private userProperties: UserProperties = {};
  private eventQueue: AnalyticsEvent[] = [];
  private isInitialized = false;
  private apiBaseUrl: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.apiBaseUrl = window.location.origin;
  }

  /**
   * 初始化分析服務
   */
  async initialize(): Promise<void> {
    try {
      // 設置基本用戶屬性
      this.userProperties = {
        session_id: this.sessionId,
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        viewport_size: `${window.innerWidth}x${window.innerHeight}`,
        device_type: this.getDeviceType(),
        browser: this.getBrowser(),
        os: this.getOS(),
        referrer: document.referrer || 'direct'
      };

      // 初始化 Google Analytics 4 (如果可用)
      if (typeof gtag !== 'undefined') {
        gtag('config', 'GA_MEASUREMENT_ID', {
          custom_map: {
            custom_session_id: 'session_id',
            custom_user_type: 'user_type'
          }
        });
      }

      this.isInitialized = true;
      
      // 發送初始化事件
      this.track('analytics_initialized', {
        initialization_time: Date.now(),
        user_properties: this.userProperties
      });

      // 處理排隊的事件
      await this.flushEventQueue();

    } catch (error) {
      console.error('Analytics initialization failed:', error);
      this.isInitialized = true; // 即使失敗也標記為已初始化，避免阻塞
    }
  }

  /**
   * 追蹤事件
   */
  track(eventName: string, properties: Record<string, any> = {}): void {
    const event: AnalyticsEvent = {
      event_name: eventName,
      properties: {
        ...properties,
        ...this.userProperties,
        timestamp: new Date().toISOString(),
        page_url: window.location.href,
        page_title: document.title
      },
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      user_id: this.userId
    };

    if (!this.isInitialized) {
      // 如果未初始化，將事件加入隊列
      this.eventQueue.push(event);
      return;
    }

    this.sendEvent(event);
  }

  /**
   * 設置用戶ID
   */
  setUserId(userId: string): void {
    this.userId = userId;
    this.userProperties.user_id = userId;

    // 更新 Google Analytics 用戶ID
    if (typeof gtag !== 'undefined') {
      gtag('config', 'GA_MEASUREMENT_ID', {
        user_id: userId
      });
    }
  }

  /**
   * 設置用戶屬性
   */
  setUserProperties(properties: Partial<UserProperties>): void {
    this.userProperties = {
      ...this.userProperties,
      ...properties
    };
  }

  /**
   * 追蹤頁面瀏覽
   */
  trackPageView(pageName: string, additionalProperties: Record<string, any> = {}): void {
    this.track('page_view', {
      page_name: pageName,
      page_url: window.location.href,
      page_title: document.title,
      ...additionalProperties
    });

    // Google Analytics 頁面瀏覽
    if (typeof gtag !== 'undefined') {
      gtag('event', 'page_view', {
        page_title: document.title,
        page_location: window.location.href,
        custom_session_id: this.sessionId
      });
    }
  }

  /**
   * 追蹤轉換事件
   */
  trackConversion(conversionType: string, value?: number, additionalProperties: Record<string, any> = {}): void {
    this.track('conversion', {
      conversion_type: conversionType,
      conversion_value: value,
      ...additionalProperties
    });

    // Google Analytics 轉換
    if (typeof gtag !== 'undefined') {
      gtag('event', 'conversion', {
        send_to: 'GA_MEASUREMENT_ID',
        value: value,
        currency: 'TWD',
        custom_session_id: this.sessionId
      });
    }
  }

  /**
   * 追蹤錯誤
   */
  trackError(error: Error, context: Record<string, any> = {}): void {
    this.track('error', {
      error_message: error.message,
      error_stack: error.stack,
      error_name: error.name,
      ...context
    });
  }

  /**
   * 追蹤性能指標
   */
  trackPerformance(metricName: string, value: number, unit: string = 'ms'): void {
    this.track('performance', {
      metric_name: metricName,
      metric_value: value,
      metric_unit: unit
    });
  }

  /**
   * 發送事件到後端
   */
  private async sendEvent(event: AnalyticsEvent): Promise<void> {
    try {
      // 發送到自定義分析端點
      await fetch(`${this.apiBaseUrl}/api/analytics/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
      });

      // 發送到 Google Analytics
      if (typeof gtag !== 'undefined') {
        gtag('event', event.event_name, {
          ...event.properties,
          custom_session_id: this.sessionId
        });
      }

    } catch (error) {
      console.error('Failed to send analytics event:', error);
      // 可以考慮將失敗的事件存儲到本地存儲中，稍後重試
    }
  }

  /**
   * 處理事件隊列
   */
  private async flushEventQueue(): Promise<void> {
    const events = [...this.eventQueue];
    this.eventQueue = [];

    for (const event of events) {
      await this.sendEvent(event);
    }
  }

  /**
   * 生成會話ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 獲取設備類型
   */
  private getDeviceType(): 'desktop' | 'tablet' | 'mobile' {
    const userAgent = navigator.userAgent;
    
    if (/tablet|ipad|playbook|silk/i.test(userAgent)) {
      return 'tablet';
    }
    
    if (/mobile|iphone|ipod|android|blackberry|opera|mini|windows\sce|palm|smartphone|iemobile/i.test(userAgent)) {
      return 'mobile';
    }
    
    return 'desktop';
  }

  /**
   * 獲取瀏覽器信息
   */
  private getBrowser(): string {
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    if (userAgent.includes('Opera')) return 'Opera';
    
    return 'Unknown';
  }

  /**
   * 獲取操作系統信息
   */
  private getOS(): string {
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Windows')) return 'Windows';
    if (userAgent.includes('Mac')) return 'macOS';
    if (userAgent.includes('Linux')) return 'Linux';
    if (userAgent.includes('Android')) return 'Android';
    if (userAgent.includes('iOS')) return 'iOS';
    
    return 'Unknown';
  }

  /**
   * 獲取會話ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * 獲取用戶ID
   */
  getUserId(): string | undefined {
    return this.userId;
  }
}

// 全局分析服務實例
export const analytics = new AnalyticsService();

// 聲明全局 gtag 函數
declare global {
  function gtag(...args: any[]): void;
}