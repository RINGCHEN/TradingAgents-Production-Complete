/**
 * 用戶體驗測試和記錄服務
 * 負責收集用戶行為數據、性能指標和體驗反饋
 */

export interface UserInteraction {
  type: 'click' | 'scroll' | 'hover' | 'focus' | 'input';
  element: string;
  timestamp: number;
  position?: { x: number; y: number };
  value?: string;
  duration?: number;
}

export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
  context?: Record<string, any>;
}

export interface UserFeedback {
  type: 'rating' | 'comment' | 'bug_report' | 'suggestion';
  content: string;
  rating?: number;
  page: string;
  timestamp: number;
  user_agent: string;
  screen_resolution: string;
}

export interface UXTestResult {
  session_id: string;
  test_type: 'usability' | 'performance' | 'accessibility' | 'conversion';
  metrics: Record<string, number>;
  interactions: UserInteraction[];
  feedback: UserFeedback[];
  completion_rate: number;
  error_count: number;
  total_time: number;
  created_at: string;
}

export class UserExperienceService {
  private sessionId: string;
  private interactions: UserInteraction[] = [];
  private performanceMetrics: PerformanceMetric[] = [];
  private feedback: UserFeedback[] = [];
  private startTime: number;
  private errorCount: number = 0;
  private isRecording: boolean = false;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.startTime = Date.now();
    this.initializeTracking();
  }

  /**
   * 初始化用戶體驗追蹤
   */
  private initializeTracking(): void {
    // 追蹤頁面載入性能
    this.trackPageLoadPerformance();
    
    // 追蹤用戶互動
    this.setupInteractionTracking();
    
    // 追蹤錯誤
    this.setupErrorTracking();
    
    // 追蹤視窗大小變化
    this.setupViewportTracking();
  }

  /**
   * 開始記錄用戶體驗
   */
  startRecording(): void {
    this.isRecording = true;
    this.trackMetric('recording_started', 1, 'boolean');
  }

  /**
   * 停止記錄用戶體驗
   */
  stopRecording(): void {
    this.isRecording = false;
    this.trackMetric('recording_stopped', 1, 'boolean');
  }

  /**
   * 追蹤用戶互動
   */
  private setupInteractionTracking(): void {
    // 點擊事件
    document.addEventListener('click', (event) => {
      if (!this.isRecording) return;
      
      const target = event.target as HTMLElement;
      this.trackInteraction({
        type: 'click',
        element: this.getElementSelector(target),
        timestamp: Date.now(),
        position: { x: event.clientX, y: event.clientY }
      });
    });

    // 滾動事件
    let scrollTimeout: NodeJS.Timeout;
    document.addEventListener('scroll', () => {
      if (!this.isRecording) return;
      
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.trackInteraction({
          type: 'scroll',
          element: 'window',
          timestamp: Date.now(),
          position: { x: window.scrollX, y: window.scrollY }
        });
      }, 100);
    });

    // 輸入事件
    document.addEventListener('input', (event) => {
      if (!this.isRecording) return;
      
      const target = event.target as HTMLInputElement;
      this.trackInteraction({
        type: 'input',
        element: this.getElementSelector(target),
        timestamp: Date.now(),
        value: target.type === 'password' ? '[HIDDEN]' : target.value.substring(0, 50)
      });
    });
  }

  /**
   * 追蹤頁面載入性能
   */
  private trackPageLoadPerformance(): void {
    if (typeof window !== 'undefined' && 'performance' in window) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          
          if (navigation) {
            this.trackMetric('page_load_time', navigation.loadEventEnd - navigation.fetchStart, 'ms');
            this.trackMetric('dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.fetchStart, 'ms');
            this.trackMetric('first_paint', this.getFirstPaint(), 'ms');
            this.trackMetric('first_contentful_paint', this.getFirstContentfulPaint(), 'ms');
          }
        }, 0);
      });
    }
  }

  /**
   * 獲取首次繪製時間
   */
  private getFirstPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
    return firstPaint ? firstPaint.startTime : 0;
  }

  /**
   * 獲取首次內容繪製時間
   */
  private getFirstContentfulPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const firstContentfulPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    return firstContentfulPaint ? firstContentfulPaint.startTime : 0;
  }

  /**
   * 設置錯誤追蹤
   */
  private setupErrorTracking(): void {
    window.addEventListener('error', (event) => {
      this.errorCount++;
      this.trackMetric('javascript_error', 1, 'count');
      
      // 記錄錯誤詳情
      this.trackInteraction({
        type: 'click', // 使用click類型來記錄錯誤
        element: 'error',
        timestamp: Date.now(),
        value: `${event.error?.message || event.message} at ${event.filename}:${event.lineno}`
      });
    });

    window.addEventListener('unhandledrejection', (event) => {
      this.errorCount++;
      this.trackMetric('promise_rejection', 1, 'count');
      
      this.trackInteraction({
        type: 'click',
        element: 'promise_error',
        timestamp: Date.now(),
        value: event.reason?.toString() || 'Unhandled promise rejection'
      });
    });
  }

  /**
   * 設置視窗追蹤
   */
  private setupViewportTracking(): void {
    window.addEventListener('resize', () => {
      this.trackMetric('viewport_width', window.innerWidth, 'px');
      this.trackMetric('viewport_height', window.innerHeight, 'px');
    });
  }

  /**
   * 追蹤用戶互動
   */
  trackInteraction(interaction: UserInteraction): void {
    this.interactions.push(interaction);
    
    // 限制記錄數量，避免記憶體溢出
    if (this.interactions.length > 1000) {
      this.interactions = this.interactions.slice(-500);
    }
  }

  /**
   * 追蹤性能指標
   */
  trackMetric(name: string, value: number, unit: string, context?: Record<string, any>): void {
    const metric: PerformanceMetric = {
      name,
      value,
      unit,
      timestamp: Date.now(),
      context
    };
    
    this.performanceMetrics.push(metric);
    
    // 限制記錄數量
    if (this.performanceMetrics.length > 500) {
      this.performanceMetrics = this.performanceMetrics.slice(-250);
    }
  }

  /**
   * 收集用戶反饋
   */
  collectFeedback(feedback: Omit<UserFeedback, 'timestamp' | 'user_agent' | 'screen_resolution'>): void {
    const fullFeedback: UserFeedback = {
      ...feedback,
      timestamp: Date.now(),
      user_agent: navigator.userAgent,
      screen_resolution: `${window.screen.width}x${window.screen.height}`
    };
    
    this.feedback.push(fullFeedback);
  }

  /**
   * 測試可訪問性
   */
  async testAccessibility(): Promise<Record<string, any>> {
    const results: Record<string, any> = {};
    
    // 檢查圖片alt屬性
    const images = document.querySelectorAll('img');
    const imagesWithoutAlt = Array.from(images).filter(img => !img.alt);
    results.images_without_alt = imagesWithoutAlt.length;
    
    // 檢查按鈕和連結的可訪問性
    const buttons = document.querySelectorAll('button, a');
    const buttonsWithoutText = Array.from(buttons).filter(btn => 
      !btn.textContent?.trim() && !btn.getAttribute('aria-label')
    );
    results.buttons_without_text = buttonsWithoutText.length;
    
    // 檢查表單標籤
    const inputs = document.querySelectorAll('input, textarea, select');
    const inputsWithoutLabels = Array.from(inputs).filter(input => {
      const id = input.getAttribute('id');
      return !id || !document.querySelector(`label[for="${id}"]`);
    });
    results.inputs_without_labels = inputsWithoutLabels.length;
    
    // 檢查顏色對比度（簡化版本）
    results.color_contrast_issues = await this.checkColorContrast();
    
    return results;
  }

  /**
   * 簡化的顏色對比度檢查
   */
  private async checkColorContrast(): Promise<number> {
    // 這是一個簡化的實現，實際應用中可能需要更複雜的算法
    const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
    let issueCount = 0;
    
    Array.from(textElements).slice(0, 50).forEach(element => {
      const styles = window.getComputedStyle(element);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;
      
      // 簡單的對比度檢查（實際應該使用WCAG算法）
      if (color && backgroundColor && color !== 'rgba(0, 0, 0, 0)' && backgroundColor !== 'rgba(0, 0, 0, 0)') {
        // 這裡應該實現真正的對比度計算
        // 現在只是一個佔位符
      }
    });
    
    return issueCount;
  }

  /**
   * 生成測試報告
   */
  generateTestReport(): UXTestResult {
    const totalTime = Date.now() - this.startTime;
    const completionRate = this.calculateCompletionRate();
    
    return {
      session_id: this.sessionId,
      test_type: 'usability',
      metrics: this.aggregateMetrics(),
      interactions: this.interactions,
      feedback: this.feedback,
      completion_rate: completionRate,
      error_count: this.errorCount,
      total_time: totalTime,
      created_at: new Date().toISOString()
    };
  }

  /**
   * 計算完成率
   */
  private calculateCompletionRate(): number {
    // 基於用戶互動和頁面停留時間計算完成率
    const clickCount = this.interactions.filter(i => i.type === 'click').length;
    const scrollCount = this.interactions.filter(i => i.type === 'scroll').length;
    const totalTime = Date.now() - this.startTime;
    
    // 簡化的完成率計算
    let completionScore = 0;
    
    if (clickCount > 0) completionScore += 30;
    if (scrollCount > 2) completionScore += 20;
    if (totalTime > 10000) completionScore += 25; // 停留超過10秒
    if (this.errorCount === 0) completionScore += 25;
    
    return Math.min(completionScore, 100);
  }

  /**
   * 聚合性能指標
   */
  private aggregateMetrics(): Record<string, number> {
    const metrics: Record<string, number> = {};
    
    this.performanceMetrics.forEach(metric => {
      if (!metrics[metric.name]) {
        metrics[metric.name] = metric.value;
      } else {
        // 對於重複的指標，取平均值
        metrics[metric.name] = (metrics[metric.name] + metric.value) / 2;
      }
    });
    
    return metrics;
  }

  /**
   * 獲取元素選擇器
   */
  private getElementSelector(element: HTMLElement): string {
    if (element.id) {
      return `#${element.id}`;
    }
    
    if (element.className) {
      return `.${element.className.split(' ')[0]}`;
    }
    
    return element.tagName.toLowerCase();
  }

  /**
   * 生成會話ID
   */
  private generateSessionId(): string {
    return `ux_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 發送測試結果到後端
   */
  async submitTestResult(): Promise<void> {
    const report = this.generateTestReport();
    
    try {
      await fetch('/api/user-experience/test-result', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report),
      });
    } catch (error) {
      console.error('Failed to submit UX test result:', error);
    }
  }

  /**
   * 獲取會話ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * 獲取當前指標
   */
  getCurrentMetrics(): Record<string, number> {
    return this.aggregateMetrics();
  }

  /**
   * 獲取互動統計
   */
  getInteractionStats(): Record<string, number> {
    const stats: Record<string, number> = {};
    
    this.interactions.forEach(interaction => {
      const key = `${interaction.type}_count`;
      stats[key] = (stats[key] || 0) + 1;
    });
    
    return stats;
  }
}

// 全局用戶體驗服務實例
export const userExperienceService = new UserExperienceService();