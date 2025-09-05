/**
 * 實時監控系統 - 第二階段Week 3 性能調優與監控
 * 用戶行為追蹤、系統性能監控、實時分析
 * 支援多維度監控、異常檢測、自動報告
 */

import { personalizationManager, trackUserAction } from './personalization';

// 監控事件類型
export type MonitorEventType = 
  | 'performance' | 'error' | 'user_action' | 'system' 
  | 'network' | 'memory' | 'cpu' | 'custom';

// 監控級別
export type MonitorLevel = 'debug' | 'info' | 'warn' | 'error' | 'critical';

// 監控數據
export interface MonitorEvent {
  id: string;
  type: MonitorEventType;
  level: MonitorLevel;
  timestamp: number;
  sessionId: string;
  userId?: string;
  data: Record<string, any>;
  context?: {
    url: string;
    userAgent: string;
    screen: {
      width: number;
      height: number;
      devicePixelRatio: number;
    };
    viewport: {
      width: number;
      height: number;
    };
    connection?: {
      type: string;
      downlink?: number;
      rtt?: number;
      effectiveType?: string;
    };
  };
}

// 性能指標
export interface PerformanceMetrics {
  // 頁面性能
  pageLoadTime: number;
  domContentLoadedTime: number;
  firstPaintTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  firstInputDelay: number;
  cumulativeLayoutShift: number;
  
  // 資源性能
  totalRequestTime: number;
  resourceLoadTime: number;
  cacheHitRate: number;
  
  // 系統性能
  memoryUsage: number;
  cpuUsage: number;
  networkLatency: number;
  
  // 用戶體驗
  timeToInteractive: number;
  totalBlockingTime: number;
}

// 用戶行為指標
export interface UserBehaviorMetrics {
  sessionDuration: number;
  pageViews: number;
  interactions: number;
  scrollDepth: number;
  clickRate: number;
  bounceRate: number;
  errorRate: number;
  conversionRate: number;
}

// 異常檢測配置
export interface AnomalyConfig {
  metric: string;
  threshold: number;
  timeWindow: number; // 毫秒
  minSamples: number;
  sensitivity: number; // 0-1
}

// 實時監控管理器
class RealTimeMonitor {
  private events: MonitorEvent[] = [];
  private sessionId: string;
  private userId?: string;
  private isActive = true;
  private observers = new Map<MonitorEventType, Set<(event: MonitorEvent) => void>>();
  private performanceObserver: PerformanceObserver | null = null;
  private mutationObserver: MutationObserver | null = null;
  private intersectionObserver: IntersectionObserver | null = null;
  private reportingInterval: number | null = null;
  
  // 異常檢測
  private anomalyConfigs: AnomalyConfig[] = [];
  private metricHistory = new Map<string, Array<{ timestamp: number; value: number }>>();
  
  // 採樣配置
  private samplingRate = 1.0; // 100% 採樣
  private maxEvents = 1000;
  
  constructor() {
    this.sessionId = this.generateSessionId();
    this.initializeMonitoring();
    this.startReporting();
  }

  // 初始化監控
  private initializeMonitoring() {
    this.setupPerformanceMonitoring();
    this.setupUserBehaviorMonitoring();
    this.setupErrorMonitoring();
    this.setupNetworkMonitoring();
    this.setupSystemMonitoring();
  }

  // 設置性能監控
  private setupPerformanceMonitoring() {
    if ('PerformanceObserver' in window) {
      this.performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordEvent({
            type: 'performance',
            level: 'info',
            data: {
              entryType: entry.entryType,
              name: entry.name,
              startTime: entry.startTime,
              duration: entry.duration,
              ...this.extractPerformanceData(entry)
            }
          });
        }
      });

      // 觀察各種性能指標
      try {
        this.performanceObserver.observe({ entryTypes: [
          'navigation',
          'resource',
          'paint',
          'largest-contentful-paint',
          'first-input',
          'layout-shift'
        ]});
      } catch (error) {
        console.warn('[RealTimeMonitor] Some performance entry types not supported:', error);
      }
    }

    // Web Vitals 監控
    this.monitorWebVitals();
  }

  // 監控 Web Vitals
  private monitorWebVitals() {
    // LCP - Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        
        this.recordEvent({
          type: 'performance',
          level: 'info',
          data: {
            metric: 'LCP',
            value: lastEntry.startTime,
            element: (lastEntry as any).element?.tagName || 'unknown'
          }
        });
      });

      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (error) {
        console.warn('[RealTimeMonitor] LCP monitoring not supported:', error);
      }
    }

    // FID - First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.recordEvent({
          type: 'performance',
          level: 'info',
          data: {
            metric: 'FID',
            value: (entry as any).processingStart - entry.startTime,
            inputType: (entry as any).name
          }
        });
      }
    });

    try {
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (error) {
      console.warn('[RealTimeMonitor] FID monitoring not supported:', error);
    }

    // CLS - Cumulative Layout Shift
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
          
          this.recordEvent({
            type: 'performance',
            level: 'info',
            data: {
              metric: 'CLS',
              value: clsValue,
              shiftValue: (entry as any).value,
              sources: (entry as any).sources?.map((source: any) => ({
                node: source.node?.tagName || 'unknown',
                currentRect: source.currentRect,
                previousRect: source.previousRect
              }))
            }
          });
        }
      }
    });

    try {
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (error) {
      console.warn('[RealTimeMonitor] CLS monitoring not supported:', error);
    }
  }

  // 設置用戶行為監控
  private setupUserBehaviorMonitoring() {
    // 點擊追蹤
    document.addEventListener('click', (event) => {
      this.recordEvent({
        type: 'user_action',
        level: 'debug',
        data: {
          action: 'click',
          element: (event.target as Element)?.tagName || 'unknown',
          className: (event.target as Element)?.className || '',
          text: (event.target as Element)?.textContent?.substring(0, 100) || '',
          coordinates: {
            x: event.clientX,
            y: event.clientY
          },
          timestamp: Date.now()
        }
      });

      // 同時記錄到個人化系統
      trackUserAction('click', {
        element: (event.target as Element)?.tagName || 'unknown',
        coordinates: { x: event.clientX, y: event.clientY }
      });
    });

    // 滾動追蹤
    let scrollTimeout: number;
    document.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = window.setTimeout(() => {
        const scrollDepth = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        
        this.recordEvent({
          type: 'user_action',
          level: 'debug',
          data: {
            action: 'scroll',
            scrollDepth: Math.round(scrollDepth),
            scrollY: window.scrollY,
            documentHeight: document.documentElement.scrollHeight,
            viewportHeight: window.innerHeight
          }
        });

        trackUserAction('scroll', {
          value: scrollDepth
        });
      }, 100);
    });

    // 鍵盤操作追蹤
    document.addEventListener('keydown', (event) => {
      // 只記錄特殊鍵和導航鍵，避免記錄敏感輸入
      const trackedKeys = ['Tab', 'Enter', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
      
      if (trackedKeys.includes(event.key)) {
        this.recordEvent({
          type: 'user_action',
          level: 'debug',
          data: {
            action: 'keydown',
            key: event.key,
            ctrlKey: event.ctrlKey,
            altKey: event.altKey,
            shiftKey: event.shiftKey
          }
        });
      }
    });

    // 可見性變化追蹤
    document.addEventListener('visibilitychange', () => {
      this.recordEvent({
        type: 'user_action',
        level: 'info',
        data: {
          action: 'visibility_change',
          visible: !document.hidden,
          timestamp: Date.now()
        }
      });
    });

    // 頁面離開追蹤
    window.addEventListener('beforeunload', () => {
      this.recordEvent({
        type: 'user_action',
        level: 'info',
        data: {
          action: 'page_leave',
          sessionDuration: Date.now() - this.getSessionStartTime(),
          timestamp: Date.now()
        }
      });
    });
  }

  // 設置錯誤監控
  private setupErrorMonitoring() {
    // JavaScript 錯誤
    window.addEventListener('error', (event) => {
      this.recordEvent({
        type: 'error',
        level: 'error',
        data: {
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          stack: event.error?.stack,
          timestamp: Date.now()
        }
      });
    });

    // Promise 拒絕
    window.addEventListener('unhandledrejection', (event) => {
      this.recordEvent({
        type: 'error',
        level: 'error',
        data: {
          type: 'unhandled_promise_rejection',
          reason: event.reason?.toString() || 'Unknown reason',
          stack: event.reason?.stack,
          timestamp: Date.now()
        }
      });
    });

    // 資源載入錯誤
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.recordEvent({
          type: 'error',
          level: 'warn',
          data: {
            type: 'resource_error',
            element: (event.target as Element)?.tagName || 'unknown',
            source: (event.target as any)?.src || (event.target as any)?.href || 'unknown',
            timestamp: Date.now()
          }
        });
      }
    }, true);
  }

  // 設置網路監控
  private setupNetworkMonitoring() {
    // 網路狀態變化
    window.addEventListener('online', () => {
      this.recordEvent({
        type: 'network',
        level: 'info',
        data: {
          status: 'online',
          timestamp: Date.now()
        }
      });
    });

    window.addEventListener('offline', () => {
      this.recordEvent({
        type: 'network',
        level: 'warn',
        data: {
          status: 'offline',
          timestamp: Date.now()
        }
      });
    });

    // 連接信息監控
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      
      const recordConnectionInfo = () => {
        this.recordEvent({
          type: 'network',
          level: 'info',
          data: {
            type: connection.type || 'unknown',
            effectiveType: connection.effectiveType || 'unknown',
            downlink: connection.downlink || 0,
            rtt: connection.rtt || 0,
            saveData: connection.saveData || false,
            timestamp: Date.now()
          }
        });
      };

      connection.addEventListener('change', recordConnectionInfo);
      recordConnectionInfo(); // 初始記錄
    }
  }

  // 設置系統監控
  private setupSystemMonitoring() {
    // 記憶體使用監控
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        
        this.recordEvent({
          type: 'system',
          level: 'info',
          data: {
            metric: 'memory',
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit,
            usageRatio: (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100,
            timestamp: Date.now()
          }
        });
      }, 30000); // 每30秒記錄一次
    }

    // 設備信息監控
    this.recordEvent({
      type: 'system',
      level: 'info',
      data: {
        metric: 'device_info',
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        languages: navigator.languages,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
        hardwareConcurrency: navigator.hardwareConcurrency || 0,
        maxTouchPoints: navigator.maxTouchPoints || 0,
        screen: {
          width: screen.width,
          height: screen.height,
          availWidth: screen.availWidth,
          availHeight: screen.availHeight,
          colorDepth: screen.colorDepth,
          pixelDepth: screen.pixelDepth
        },
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        },
        timestamp: Date.now()
      }
    });
  }

  // 記錄事件
  recordEvent(eventData: Partial<MonitorEvent>) {
    if (!this.isActive || Math.random() > this.samplingRate) {
      return;
    }

    const event: MonitorEvent = {
      id: this.generateEventId(),
      sessionId: this.sessionId,
      userId: this.userId,
      timestamp: Date.now(),
      context: this.getEventContext(),
      ...eventData
    } as MonitorEvent;

    // 添加到事件列表
    this.events.push(event);

    // 限制事件數量
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }

    // 異常檢測
    this.checkAnomalies(event);

    // 通知觀察者
    const observers = this.observers.get(event.type);
    if (observers) {
      observers.forEach(callback => callback(event));
    }

    // 關鍵事件立即上報
    if (event.level === 'error' || event.level === 'critical') {
      this.reportEventImmediately(event);
    }
  }

  // 異常檢測
  private checkAnomalies(event: MonitorEvent) {
    this.anomalyConfigs.forEach(config => {
      if (event.data[config.metric] !== undefined) {
        const value = event.data[config.metric];
        const history = this.metricHistory.get(config.metric) || [];
        
        // 添加新數據點
        history.push({ timestamp: event.timestamp, value });
        
        // 保持時間窗口內的數據
        const cutoffTime = event.timestamp - config.timeWindow;
        const recentHistory = history.filter(point => point.timestamp >= cutoffTime);
        this.metricHistory.set(config.metric, recentHistory);
        
        // 檢測異常
        if (recentHistory.length >= config.minSamples) {
          const isAnomaly = this.detectAnomaly(value, recentHistory, config);
          
          if (isAnomaly) {
            this.recordEvent({
              type: 'system',
              level: 'warn',
              data: {
                anomaly: true,
                metric: config.metric,
                value,
                threshold: config.threshold,
                historicalAverage: recentHistory.reduce((sum, p) => sum + p.value, 0) / recentHistory.length
              }
            });
          }
        }
      }
    });
  }

  // 異常檢測算法
  private detectAnomaly(value: number, history: Array<{ timestamp: number; value: number }>, config: AnomalyConfig): boolean {
    const values = history.map(h => h.value);
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const stdDev = Math.sqrt(values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length);
    
    // Z-score 異常檢測
    const zScore = Math.abs((value - mean) / stdDev);
    const threshold = config.threshold * (1 + config.sensitivity);
    
    return zScore > threshold;
  }

  // 獲取性能指標
  getPerformanceMetrics(): PerformanceMetrics {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const paints = performance.getEntriesByType('paint');
    const memory = (performance as any).memory;

    return {
      pageLoadTime: navigation ? navigation.loadEventEnd - navigation.fetchStart : 0,
      domContentLoadedTime: navigation ? navigation.domContentLoadedEventEnd - navigation.fetchStart : 0,
      firstPaintTime: paints.find(p => p.name === 'first-paint')?.startTime || 0,
      firstContentfulPaint: paints.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
      largestContentfulPaint: this.getLargestContentfulPaint(),
      firstInputDelay: this.getFirstInputDelay(),
      cumulativeLayoutShift: this.getCumulativeLayoutShift(),
      totalRequestTime: navigation ? navigation.responseEnd - navigation.requestStart : 0,
      resourceLoadTime: this.getResourceLoadTime(),
      cacheHitRate: this.getCacheHitRate(),
      memoryUsage: memory ? (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100 : 0,
      cpuUsage: this.estimateCPUUsage(),
      networkLatency: this.getNetworkLatency(),
      timeToInteractive: this.getTimeToInteractive(),
      totalBlockingTime: this.getTotalBlockingTime()
    };
  }

  // 獲取用戶行為指標
  getUserBehaviorMetrics(): UserBehaviorMetrics {
    const userEvents = this.events.filter(e => e.type === 'user_action');
    const errorEvents = this.events.filter(e => e.type === 'error');
    
    return {
      sessionDuration: Date.now() - this.getSessionStartTime(),
      pageViews: userEvents.filter(e => e.data.action === 'page_view').length,
      interactions: userEvents.filter(e => ['click', 'keydown', 'scroll'].includes(e.data.action)).length,
      scrollDepth: Math.max(...userEvents
        .filter(e => e.data.action === 'scroll')
        .map(e => e.data.scrollDepth || 0), 0),
      clickRate: this.calculateClickRate(),
      bounceRate: this.calculateBounceRate(),
      errorRate: (errorEvents.length / Math.max(userEvents.length, 1)) * 100,
      conversionRate: this.calculateConversionRate()
    };
  }

  // 設置用戶 ID
  setUserId(userId: string) {
    this.userId = userId;
  }

  // 設置採樣率
  setSamplingRate(rate: number) {
    this.samplingRate = Math.max(0, Math.min(1, rate));
  }

  // 添加異常檢測配置
  addAnomalyConfig(config: AnomalyConfig) {
    this.anomalyConfigs.push(config);
  }

  // 觀察特定類型的事件
  observe(type: MonitorEventType, callback: (event: MonitorEvent) => void): () => void {
    if (!this.observers.has(type)) {
      this.observers.set(type, new Set());
    }
    
    this.observers.get(type)!.add(callback);
    
    return () => {
      this.observers.get(type)?.delete(callback);
    };
  }

  // 輔助方法
  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateEventId(): string {
    return `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private getEventContext() {
    const connection = (navigator as any).connection;
    
    return {
      url: window.location.href,
      userAgent: navigator.userAgent,
      screen: {
        width: screen.width,
        height: screen.height,
        devicePixelRatio: window.devicePixelRatio
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      connection: connection ? {
        type: connection.type || 'unknown',
        downlink: connection.downlink || 0,
        rtt: connection.rtt || 0,
        effectiveType: connection.effectiveType || 'unknown'
      } : undefined
    };
  }

  private extractPerformanceData(entry: PerformanceEntry): Record<string, any> {
    const data: Record<string, any> = {};
    
    if ('transferSize' in entry) {
      data.transferSize = (entry as any).transferSize;
    }
    
    if ('encodedBodySize' in entry) {
      data.encodedBodySize = (entry as any).encodedBodySize;
    }
    
    if ('decodedBodySize' in entry) {
      data.decodedBodySize = (entry as any).decodedBodySize;
    }
    
    return data;
  }

  private getSessionStartTime(): number {
    const startTimeStr = sessionStorage.getItem('monitor-session-start');
    if (startTimeStr) {
      return parseInt(startTimeStr, 10);
    }
    
    const startTime = Date.now();
    sessionStorage.setItem('monitor-session-start', startTime.toString());
    return startTime;
  }

  // 性能計算輔助方法
  private getLargestContentfulPaint(): number {
    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
    return lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : 0;
  }

  private getFirstInputDelay(): number {
    const fidEntries = performance.getEntriesByType('first-input');
    return fidEntries.length > 0 ? (fidEntries[0] as any).processingStart - fidEntries[0].startTime : 0;
  }

  private getCumulativeLayoutShift(): number {
    const clsEntries = performance.getEntriesByType('layout-shift');
    return clsEntries.reduce((cls, entry) => {
      if (!(entry as any).hadRecentInput) {
        return cls + (entry as any).value;
      }
      return cls;
    }, 0);
  }

  private getResourceLoadTime(): number {
    const resourceEntries = performance.getEntriesByType('resource');
    return resourceEntries.reduce((total, entry) => total + entry.duration, 0);
  }

  private getCacheHitRate(): number {
    const resourceEntries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    const totalResources = resourceEntries.length;
    const cachedResources = resourceEntries.filter(entry => entry.transferSize === 0).length;
    return totalResources > 0 ? (cachedResources / totalResources) * 100 : 0;
  }

  private estimateCPUUsage(): number {
    // 簡單的 CPU 使用率估算
    const start = performance.now();
    let iterations = 0;
    
    while (performance.now() - start < 10) {
      iterations++;
    }
    
    const baseline = 100000; // 基準迭代次數
    return Math.max(0, Math.min(100, (baseline - iterations) / baseline * 100));
  }

  private getNetworkLatency(): number {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigation ? navigation.responseStart - navigation.requestStart : 0;
  }

  private getTimeToInteractive(): number {
    // 簡化的 TTI 計算
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigation ? navigation.domContentLoadedEventEnd - navigation.fetchStart : 0;
  }

  private getTotalBlockingTime(): number {
    // 長任務監控需要額外的 PerformanceObserver
    const longTasks = performance.getEntriesByType('longtask');
    return longTasks.reduce((total, task) => total + Math.max(0, task.duration - 50), 0);
  }

  private calculateClickRate(): number {
    const clickEvents = this.events.filter(e => e.type === 'user_action' && e.data.action === 'click');
    const sessionDuration = (Date.now() - this.getSessionStartTime()) / 1000 / 60; // 分鐘
    return sessionDuration > 0 ? clickEvents.length / sessionDuration : 0;
  }

  private calculateBounceRate(): number {
    const pageViews = this.events.filter(e => e.type === 'user_action' && e.data.action === 'page_view');
    const interactions = this.events.filter(e => 
      e.type === 'user_action' && ['click', 'scroll', 'keydown'].includes(e.data.action)
    );
    
    return pageViews.length === 1 && interactions.length === 0 ? 100 : 0;
  }

  private calculateConversionRate(): number {
    // 簡化的轉換率計算（需要根據業務邏輯調整）
    const conversionEvents = this.events.filter(e => 
      e.type === 'user_action' && ['purchase', 'signup', 'subscribe'].includes(e.data.action)
    );
    const totalSessions = 1; // 當前會話
    return (conversionEvents.length / totalSessions) * 100;
  }

  // 上報方法
  private startReporting() {
    this.reportingInterval = window.setInterval(() => {
      this.reportBatch();
    }, 30000); // 每30秒上報一次
  }

  private async reportBatch() {
    if (this.events.length === 0) return;

    try {
      const batch = this.events.splice(0, 100); // 批量上報
      
      await fetch('/api/monitor/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sessionId: this.sessionId,
          events: batch,
          performance: this.getPerformanceMetrics(),
          behavior: this.getUserBehaviorMetrics()
        })
      });
      
    } catch (error) {
      console.error('[RealTimeMonitor] Failed to report events:', error);
    }
  }

  private async reportEventImmediately(event: MonitorEvent) {
    try {
      await fetch('/api/monitor/events/immediate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sessionId: this.sessionId,
          event
        })
      });
    } catch (error) {
      console.error('[RealTimeMonitor] Failed to report immediate event:', error);
    }
  }

  // 停止監控
  stop() {
    this.isActive = false;
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }
    
    if (this.mutationObserver) {
      this.mutationObserver.disconnect();
    }
    
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    
    if (this.reportingInterval) {
      clearInterval(this.reportingInterval);
    }
  }
}

// 創建全域實例
export const realTimeMonitor = new RealTimeMonitor();

// 便利函數
export const recordCustomEvent = (data: Record<string, any>, level: MonitorLevel = 'info') =>
  realTimeMonitor.recordEvent({
    type: 'custom',
    level,
    data
  });

export const getPerformanceMetrics = () => realTimeMonitor.getPerformanceMetrics();
export const getUserBehaviorMetrics = () => realTimeMonitor.getUserBehaviorMetrics();

export default realTimeMonitor;