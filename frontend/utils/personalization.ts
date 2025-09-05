/**
 * 個人化推薦引擎 - 第二階段Week 2 UX優化
 * 用戶行為分析、智能推薦算法、個性化儀表板
 * 支援隱私保護、離線運行、即時更新
 */

// 用戶行為事件類型
export type UserActionType = 
  | 'page_view' | 'click' | 'scroll' | 'hover' | 'search' 
  | 'filter' | 'sort' | 'export' | 'bookmark' | 'share'
  | 'analyze' | 'trade' | 'portfolio_view' | 'news_read'
  | 'setting_change' | 'theme_change' | 'language_change';

// 用戶行為事件介面
export interface UserAction {
  id: string;
  type: UserActionType;
  timestamp: number;
  data: {
    page?: string;
    element?: string;
    value?: any;
    duration?: number;
    coordinates?: { x: number; y: number };
    context?: Record<string, any>;
  };
}

// 用戶偏好設定
export interface UserPreferences {
  // 界面偏好
  theme: string;
  language: string;
  layout: 'grid' | 'list' | 'card';
  
  // 內容偏好
  favoriteMarkets: string[];
  favoriteStocks: string[];
  preferredAnalysisTypes: string[];
  newsCategories: string[];
  
  // 功能偏好
  autoRefresh: boolean;
  notifications: boolean;
  advancedFeatures: boolean;
  
  // 個性化設定
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  investmentGoals: string[];
  experienceLevel: 'beginner' | 'intermediate' | 'advanced';
}

// 推薦項目介面
export interface RecommendationItem {
  id: string;
  type: 'stock' | 'news' | 'analysis' | 'feature' | 'content';
  title: string;
  description?: string;
  score: number; // 推薦分數 (0-1)
  reason: string; // 推薦理由
  category?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  createdAt: number;
  expiresAt?: number;
}

// 用戶行為模式
export interface BehaviorPattern {
  actionType: UserActionType;
  frequency: number;
  avgDuration: number;
  lastOccurrence: number;
  contexts: Record<string, number>;
  timeDistribution: number[]; // 24小時分佈
  dayOfWeekDistribution: number[]; // 星期分佈
}

// 個人化引擎配置
export interface PersonalizationConfig {
  maxActionsInMemory: number;
  recommendationUpdateInterval: number;
  decayFactor: number;
  minInteractionThreshold: number;
  enableRealTimeUpdates: boolean;
  privacyMode: boolean;
}

// 個人化管理器類別
class PersonalizationManager {
  private userActions: UserAction[] = [];
  private userPreferences: UserPreferences;
  private behaviorPatterns: Map<UserActionType, BehaviorPattern> = new Map();
  private recommendations: RecommendationItem[] = [];
  private config: PersonalizationConfig;
  private updateTimer: number | null = null;
  private listeners: Array<(recommendations: RecommendationItem[]) => void> = [];

  constructor(config: Partial<PersonalizationConfig> = {}) {
    this.config = {
      maxActionsInMemory: 1000,
      recommendationUpdateInterval: 5 * 60 * 1000, // 5分鐘
      decayFactor: 0.95, // 時間衰減因子
      minInteractionThreshold: 3,
      enableRealTimeUpdates: true,
      privacyMode: false,
      ...config
    };

    this.userPreferences = this.loadUserPreferences();
    this.loadUserActions();
    this.loadBehaviorPatterns();
    this.startUpdateTimer();
  }

  // 載入用戶偏好
  private loadUserPreferences(): UserPreferences {
    try {
      const saved = localStorage.getItem('user-preferences');
      if (saved) {
        return { ...this.getDefaultPreferences(), ...JSON.parse(saved) };
      }
    } catch (error) {
      console.warn('Failed to load user preferences:', error);
    }
    return this.getDefaultPreferences();
  }

  // 獲取預設偏好
  private getDefaultPreferences(): UserPreferences {
    return {
      theme: 'auto',
      language: 'zh-TW',
      layout: 'card',
      favoriteMarkets: [],
      favoriteStocks: [],
      preferredAnalysisTypes: [],
      newsCategories: [],
      autoRefresh: true,
      notifications: true,
      advancedFeatures: false,
      riskTolerance: 'moderate',
      investmentGoals: [],
      experienceLevel: 'intermediate'
    };
  }

  // 保存用戶偏好
  private saveUserPreferences() {
    if (this.config.privacyMode) return;
    
    try {
      localStorage.setItem('user-preferences', JSON.stringify(this.userPreferences));
    } catch (error) {
      console.warn('Failed to save user preferences:', error);
    }
  }

  // 載入用戶行為
  private loadUserActions() {
    if (this.config.privacyMode) return;
    
    try {
      const saved = localStorage.getItem('user-actions');
      if (saved) {
        this.userActions = JSON.parse(saved);
        this.cleanupOldActions();
      }
    } catch (error) {
      console.warn('Failed to load user actions:', error);
    }
  }

  // 保存用戶行為
  private saveUserActions() {
    if (this.config.privacyMode) return;
    
    try {
      localStorage.setItem('user-actions', JSON.stringify(this.userActions.slice(-this.config.maxActionsInMemory)));
    } catch (error) {
      console.warn('Failed to save user actions:', error);
    }
  }

  // 載入行為模式
  private loadBehaviorPatterns() {
    if (this.config.privacyMode) return;
    
    try {
      const saved = localStorage.getItem('behavior-patterns');
      if (saved) {
        const patterns = JSON.parse(saved);
        this.behaviorPatterns = new Map(Object.entries(patterns) as [UserActionType, BehaviorPattern][]);
      }
    } catch (error) {
      console.warn('Failed to load behavior patterns:', error);
    }
  }

  // 保存行為模式
  private saveBehaviorPatterns() {
    if (this.config.privacyMode) return;
    
    try {
      const patterns = Object.fromEntries(this.behaviorPatterns);
      localStorage.setItem('behavior-patterns', JSON.stringify(patterns));
    } catch (error) {
      console.warn('Failed to save behavior patterns:', error);
    }
  }

  // 清理舊行為記錄
  private cleanupOldActions() {
    const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
    this.userActions = this.userActions.filter(action => action.timestamp > thirtyDaysAgo);
  }

  // 啟動更新計時器
  private startUpdateTimer() {
    if (!this.config.enableRealTimeUpdates) return;
    
    this.updateTimer = window.setInterval(() => {
      this.updateRecommendations();
    }, this.config.recommendationUpdateInterval);
  }

  // 停止更新計時器
  private stopUpdateTimer() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }

  // 記錄用戶行為
  trackAction(type: UserActionType, data: UserAction['data'] = {}): void {
    const action: UserAction = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      timestamp: Date.now(),
      data
    };

    this.userActions.push(action);
    this.updateBehaviorPattern(action);

    // 限制記憶體中的行為記錄數量
    if (this.userActions.length > this.config.maxActionsInMemory) {
      this.userActions = this.userActions.slice(-this.config.maxActionsInMemory);
    }

    this.saveUserActions();
    
    // 即時更新推薦（如果啟用）
    if (this.config.enableRealTimeUpdates) {
      this.updateRecommendations();
    }
  }

  // 更新行為模式
  private updateBehaviorPattern(action: UserAction) {
    const existing = this.behaviorPatterns.get(action.type);
    const now = new Date();
    const hour = now.getHours();
    const dayOfWeek = now.getDay();

    if (existing) {
      existing.frequency += 1;
      existing.lastOccurrence = action.timestamp;
      
      // 更新持續時間平均值
      if (action.data.duration) {
        existing.avgDuration = (existing.avgDuration + action.data.duration) / 2;
      }
      
      // 更新上下文統計
      if (action.data.context) {
        Object.keys(action.data.context).forEach(key => {
          existing.contexts[key] = (existing.contexts[key] || 0) + 1;
        });
      }
      
      // 更新時間分佈
      existing.timeDistribution[hour] += 1;
      existing.dayOfWeekDistribution[dayOfWeek] += 1;
    } else {
      const newPattern: BehaviorPattern = {
        actionType: action.type,
        frequency: 1,
        avgDuration: action.data.duration || 0,
        lastOccurrence: action.timestamp,
        contexts: action.data.context ? { ...action.data.context } : {},
        timeDistribution: new Array(24).fill(0),
        dayOfWeekDistribution: new Array(7).fill(0)
      };
      
      newPattern.timeDistribution[hour] = 1;
      newPattern.dayOfWeekDistribution[dayOfWeek] = 1;
      
      this.behaviorPatterns.set(action.type, newPattern);
    }

    this.saveBehaviorPatterns();
  }

  // 更新用戶偏好
  updatePreferences(preferences: Partial<UserPreferences>): void {
    this.userPreferences = { ...this.userPreferences, ...preferences };
    this.saveUserPreferences();
    this.updateRecommendations();
  }

  // 獲取用戶偏好
  getPreferences(): UserPreferences {
    return { ...this.userPreferences };
  }

  // 獲取行為模式
  getBehaviorPatterns(): Map<UserActionType, BehaviorPattern> {
    return new Map(this.behaviorPatterns);
  }

  // 生成推薦
  private async updateRecommendations(): Promise<void> {
    const newRecommendations: RecommendationItem[] = [];

    // 基於偏好的推薦
    newRecommendations.push(...this.generatePreferenceBasedRecommendations());
    
    // 基於行為的推薦
    newRecommendations.push(...this.generateBehaviorBasedRecommendations());
    
    // 基於上下文的推薦
    newRecommendations.push(...this.generateContextBasedRecommendations());
    
    // 基於時間的推薦
    newRecommendations.push(...this.generateTimeBasedRecommendations());

    // 排序和去重
    this.recommendations = this.rankAndDeduplicateRecommendations(newRecommendations);
    
    // 通知監聽器
    this.notifyListeners();
  }

  // 基於偏好的推薦
  private generatePreferenceBasedRecommendations(): RecommendationItem[] {
    const recommendations: RecommendationItem[] = [];

    // 推薦喜愛的股票相關內容
    this.userPreferences.favoriteStocks.forEach(stock => {
      recommendations.push({
        id: `pref-stock-${stock}`,
        type: 'analysis',
        title: `${stock} 技術分析`,
        description: `基於您對 ${stock} 的關注`,
        score: 0.8,
        reason: '您經常關注此股票',
        category: 'analysis',
        tags: ['stock', 'technical', stock],
        createdAt: Date.now()
      });
    });

    // 推薦偏好的新聞類別
    this.userPreferences.newsCategories.forEach(category => {
      recommendations.push({
        id: `pref-news-${category}`,
        type: 'news',
        title: `${category}最新消息`,
        description: `基於您的興趣偏好`,
        score: 0.7,
        reason: `您關注${category}類別的新聞`,
        category,
        tags: ['news', category],
        createdAt: Date.now()
      });
    });

    return recommendations;
  }

  // 基於行為的推薦
  private generateBehaviorBasedRecommendations(): RecommendationItem[] {
    const recommendations: RecommendationItem[] = [];
    
    // 分析最頻繁的行為
    const sortedPatterns = Array.from(this.behaviorPatterns.entries())
      .sort(([, a], [, b]) => b.frequency - a.frequency)
      .slice(0, 5);

    sortedPatterns.forEach(([actionType, pattern]) => {
      if (pattern.frequency < this.config.minInteractionThreshold) return;

      switch (actionType) {
        case 'analyze':
          recommendations.push({
            id: 'behavior-analysis-tools',
            type: 'feature',
            title: '高級分析工具',
            description: '基於您頻繁的分析行為',
            score: 0.9,
            reason: `您在過去進行了 ${pattern.frequency} 次分析`,
            category: 'tools',
            tags: ['analysis', 'advanced'],
            createdAt: Date.now()
          });
          break;
        
        case 'news_read':
          recommendations.push({
            id: 'behavior-news-digest',
            type: 'content',
            title: '個人化新聞摘要',
            description: '基於您的閱讀習慣',
            score: 0.8,
            reason: `您經常閱讀新聞（${pattern.frequency}次）`,
            category: 'news',
            tags: ['news', 'digest'],
            createdAt: Date.now()
          });
          break;
        
        case 'portfolio_view':
          recommendations.push({
            id: 'behavior-portfolio-analytics',
            type: 'feature',
            title: '投資組合深度分析',
            description: '基於您對投資組合的關注',
            score: 0.85,
            reason: `您頻繁查看投資組合（${pattern.frequency}次）`,
            category: 'portfolio',
            tags: ['portfolio', 'analytics'],
            createdAt: Date.now()
          });
          break;
      }
    });

    return recommendations;
  }

  // 基於上下文的推薦
  private generateContextBasedRecommendations(): RecommendationItem[] {
    const recommendations: RecommendationItem[] = [];
    const now = new Date();
    const currentHour = now.getHours();

    // 市場開盤時間推薦
    if (currentHour >= 9 && currentHour <= 13) {
      recommendations.push({
        id: 'context-market-hours',
        type: 'content',
        title: '即時市場動態',
        description: '當前市場正在交易',
        score: 0.9,
        reason: '市場開盤時間',
        category: 'market',
        tags: ['realtime', 'market'],
        createdAt: Date.now(),
        expiresAt: Date.now() + 4 * 60 * 60 * 1000 // 4小時後過期
      });
    }

    // 週末推薦
    if (now.getDay() === 0 || now.getDay() === 6) {
      recommendations.push({
        id: 'context-weekend',
        type: 'content',
        title: '週末市場回顧',
        description: '利用週末時間深度分析',
        score: 0.7,
        reason: '週末時間適合深度學習',
        category: 'education',
        tags: ['weekend', 'review'],
        createdAt: Date.now()
      });
    }

    return recommendations;
  }

  // 基於時間的推薦
  private generateTimeBasedRecommendations(): RecommendationItem[] {
    const recommendations: RecommendationItem[] = [];
    
    // 分析用戶活躍時間
    this.behaviorPatterns.forEach((pattern, actionType) => {
      const peakHour = pattern.timeDistribution.indexOf(Math.max(...pattern.timeDistribution));
      const currentHour = new Date().getHours();
      
      // 如果當前是用戶活躍時間
      if (Math.abs(currentHour - peakHour) <= 1) {
        recommendations.push({
          id: `time-${actionType}`,
          type: 'feature',
          title: `${actionType} 功能提醒`,
          description: '基於您的使用習慣',
          score: 0.6,
          reason: `您通常在 ${peakHour}:00 左右使用此功能`,
          category: 'timing',
          tags: ['timing', actionType],
          createdAt: Date.now()
        });
      }
    });

    return recommendations;
  }

  // 排序和去重推薦
  private rankAndDeduplicateRecommendations(recommendations: RecommendationItem[]): RecommendationItem[] {
    // 去重（基於 ID）
    const uniqueRecommendations = recommendations.reduce((acc, rec) => {
      if (!acc.find(existing => existing.id === rec.id)) {
        acc.push(rec);
      }
      return acc;
    }, [] as RecommendationItem[]);

    // 應用時間衰減
    const now = Date.now();
    uniqueRecommendations.forEach(rec => {
      const ageInDays = (now - rec.createdAt) / (24 * 60 * 60 * 1000);
      rec.score *= Math.pow(this.config.decayFactor, ageInDays);
    });

    // 過濾過期的推薦
    const validRecommendations = uniqueRecommendations.filter(rec => 
      !rec.expiresAt || rec.expiresAt > now
    );

    // 按分數排序
    return validRecommendations
      .sort((a, b) => b.score - a.score)
      .slice(0, 20); // 限制推薦數量
  }

  // 獲取推薦
  getRecommendations(type?: RecommendationItem['type'], category?: string): RecommendationItem[] {
    let filtered = [...this.recommendations];
    
    if (type) {
      filtered = filtered.filter(rec => rec.type === type);
    }
    
    if (category) {
      filtered = filtered.filter(rec => rec.category === category);
    }
    
    return filtered;
  }

  // 記錄推薦互動
  recordRecommendationInteraction(recommendationId: string, interaction: 'view' | 'click' | 'dismiss'): void {
    this.trackAction('click', {
      element: 'recommendation',
      value: recommendationId,
      context: { interaction }
    });

    // 如果是點擊，提高相關推薦的權重
    if (interaction === 'click') {
      const recommendation = this.recommendations.find(rec => rec.id === recommendationId);
      if (recommendation) {
        recommendation.score *= 1.1; // 提升10%權重
      }
    }

    // 如果是忽略，降低相關推薦的權重
    if (interaction === 'dismiss') {
      const recommendation = this.recommendations.find(rec => rec.id === recommendationId);
      if (recommendation) {
        recommendation.score *= 0.8; // 降低20%權重
      }
    }
  }

  // 添加推薦更新監聽器
  onRecommendationsUpdate(listener: (recommendations: RecommendationItem[]) => void): () => void {
    this.listeners.push(listener);
    
    // 立即觸發一次
    listener(this.recommendations);
    
    // 返回取消訂閱函數
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  // 通知監聽器
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.recommendations));
  }

  // 獲取用戶洞察
  getUserInsights(): {
    mostActiveHours: number[];
    mostActiveDays: number[];
    topActions: Array<{ action: UserActionType; frequency: number }>;
    engagementScore: number;
    preferredContent: string[];
  } {
    const insights = {
      mostActiveHours: [],
      mostActiveDays: [],
      topActions: [],
      engagementScore: 0,
      preferredContent: []
    };

    // 分析最活躍時間
    const hourlyActivity = new Array(24).fill(0);
    const dailyActivity = new Array(7).fill(0);
    let totalActions = 0;

    this.behaviorPatterns.forEach(pattern => {
      totalActions += pattern.frequency;
      pattern.timeDistribution.forEach((count, hour) => {
        hourlyActivity[hour] += count;
      });
      pattern.dayOfWeekDistribution.forEach((count, day) => {
        dailyActivity[day] += count;
      });
    });

    // 找出最活躍的3個小時
    insights.mostActiveHours = hourlyActivity
      .map((count, hour) => ({ hour, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 3)
      .map(item => item.hour) as number[];

    // 找出最活躍的2天
    insights.mostActiveDays = dailyActivity
      .map((count, day) => ({ day, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 2)
      .map(item => item.day) as number[];

    // 最頻繁的行為
    insights.topActions = Array.from(this.behaviorPatterns.entries())
      .sort(([, a], [, b]) => b.frequency - a.frequency)
      .slice(0, 5)
      .map(([action, pattern]) => ({ action, frequency: pattern.frequency })) as { action: UserActionType; frequency: number; }[];

    // 計算參與度分數（0-100）
    const avgActionsPerDay = totalActions / 30; // 假設30天週期
    insights.engagementScore = Math.min(100, Math.round(avgActionsPerDay * 2));

    // 偏好內容
    insights.preferredContent = [
      ...this.userPreferences.favoriteMarkets,
      ...this.userPreferences.newsCategories,
      ...this.userPreferences.preferredAnalysisTypes
    ] as string[];

    return insights;
  }

  // 匯出用戶數據（用於數據可攜性）
  exportUserData(): {
    preferences: UserPreferences;
    behaviorSummary: any;
    recommendations: RecommendationItem[];
    insights: any;
  } {
    return {
      preferences: this.getPreferences(),
      behaviorSummary: Object.fromEntries(
        Array.from(this.behaviorPatterns.entries()).map(([key, pattern]) => [
          key,
          {
            frequency: pattern.frequency,
            lastOccurrence: pattern.lastOccurrence,
            avgDuration: pattern.avgDuration
          }
        ])
      ),
      recommendations: this.getRecommendations(),
      insights: this.getUserInsights()
    };
  }

  // 清除所有數據
  clearAllData(): void {
    this.userActions = [];
    this.behaviorPatterns.clear();
    this.recommendations = [];
    this.userPreferences = this.getDefaultPreferences();
    
    if (!this.config.privacyMode) {
      localStorage.removeItem('user-actions');
      localStorage.removeItem('behavior-patterns');
      localStorage.removeItem('user-preferences');
    }
    
    this.notifyListeners();
  }

  // 銷毀管理器
  destroy(): void {
    this.stopUpdateTimer();
    this.listeners = [];
  }
}

// 創建全域實例
export const personalizationManager = new PersonalizationManager();

// 便利函數
export const trackUserAction = (type: UserActionType, data?: UserAction['data']) => 
  personalizationManager.trackAction(type, data);

export const getUserPreferences = () => personalizationManager.getPreferences();
export const updateUserPreferences = (preferences: Partial<UserPreferences>) => 
  personalizationManager.updatePreferences(preferences);

export const getRecommendations = (type?: RecommendationItem['type'], category?: string) => 
  personalizationManager.getRecommendations(type, category);

export const recordRecommendationInteraction = (id: string, interaction: 'view' | 'click' | 'dismiss') => 
  personalizationManager.recordRecommendationInteraction(id, interaction);

export const getUserInsights = () => personalizationManager.getUserInsights();
export const exportUserData = () => personalizationManager.exportUserData();
export const clearUserData = () => personalizationManager.clearAllData();

export default personalizationManager;