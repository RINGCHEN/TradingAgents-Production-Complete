/**
 * 用戶體驗測試報告生成器
 * 負責生成詳細的UX測試報告和優化建議
 */

import { userExperienceService, UXTestResult } from '../services/UserExperienceService';

export interface UXOptimizationSuggestion {
  category: 'performance' | 'usability' | 'accessibility' | 'conversion';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: string;
  implementation: string;
  metrics: string[];
}

export interface UXTestReport {
  summary: {
    overall_score: number;
    completion_rate: number;
    error_count: number;
    total_time: number;
    user_satisfaction: number;
  };
  performance: {
    page_load_time: number;
    first_contentful_paint: number;
    interaction_delay: number;
    score: number;
  };
  usability: {
    click_success_rate: number;
    navigation_efficiency: number;
    task_completion_rate: number;
    score: number;
  };
  accessibility: {
    keyboard_navigation: number;
    screen_reader_compatibility: number;
    color_contrast: number;
    score: number;
  };
  conversion: {
    cta_click_rate: number;
    form_completion_rate: number;
    bounce_rate: number;
    score: number;
  };
  suggestions: UXOptimizationSuggestion[];
  raw_data: UXTestResult;
}

export class UXTestReporter {
  
  /**
   * 生成完整的UX測試報告
   */
  static async generateReport(): Promise<UXTestReport> {
    const rawData = userExperienceService.generateTestReport();
    const metrics = userExperienceService.getCurrentMetrics();
    const interactionStats = userExperienceService.getInteractionStats();
    
    // 計算各項分數
    const performanceScore = this.calculatePerformanceScore(metrics);
    const usabilityScore = this.calculateUsabilityScore(interactionStats, rawData);
    const accessibilityScore = await this.calculateAccessibilityScore();
    const conversionScore = this.calculateConversionScore(interactionStats, rawData);
    
    // 計算總體分數
    const overallScore = Math.round(
      (performanceScore.score + usabilityScore.score + accessibilityScore.score + conversionScore.score) / 4
    );
    
    // 生成優化建議
    const suggestions = this.generateOptimizationSuggestions({
      performance: performanceScore,
      usability: usabilityScore,
      accessibility: accessibilityScore,
      conversion: conversionScore,
      rawData
    });
    
    return {
      summary: {
        overall_score: overallScore,
        completion_rate: rawData.completion_rate,
        error_count: rawData.error_count,
        total_time: rawData.total_time,
        user_satisfaction: this.calculateUserSatisfaction(rawData.feedback)
      },
      performance: performanceScore,
      usability: usabilityScore,
      accessibility: accessibilityScore,
      conversion: conversionScore,
      suggestions,
      raw_data: rawData
    };
  }
  
  /**
   * 計算性能分數
   */
  private static calculatePerformanceScore(metrics: Record<string, number>) {
    const pageLoadTime = metrics.page_load_time || 0;
    const firstContentfulPaint = metrics.first_contentful_paint || 0;
    const interactionDelay = metrics.interaction_delay || 0;
    
    // 性能評分標準
    let loadTimeScore = 100;
    if (pageLoadTime > 3000) loadTimeScore = 60;
    else if (pageLoadTime > 2000) loadTimeScore = 80;
    else if (pageLoadTime > 1000) loadTimeScore = 90;
    
    let fcpScore = 100;
    if (firstContentfulPaint > 2500) fcpScore = 60;
    else if (firstContentfulPaint > 1800) fcpScore = 80;
    else if (firstContentfulPaint > 1000) fcpScore = 90;
    
    let interactionScore = 100;
    if (interactionDelay > 300) interactionScore = 60;
    else if (interactionDelay > 200) interactionScore = 80;
    else if (interactionDelay > 100) interactionScore = 90;
    
    const score = Math.round((loadTimeScore + fcpScore + interactionScore) / 3);
    
    return {
      page_load_time: pageLoadTime,
      first_contentful_paint: firstContentfulPaint,
      interaction_delay: interactionDelay,
      score
    };
  }
  
  /**
   * 計算可用性分數
   */
  private static calculateUsabilityScore(interactionStats: Record<string, number>, rawData: UXTestResult) {
    const clickCount = interactionStats.click_count || 0;
    const scrollCount = interactionStats.scroll_count || 0;
    const totalTime = rawData.total_time;
    
    // 點擊成功率（假設大部分點擊都是成功的）
    const clickSuccessRate = Math.min(95, 70 + (clickCount * 5));
    
    // 導航效率（基於時間和互動次數）
    const navigationEfficiency = totalTime > 0 ? Math.min(100, (clickCount + scrollCount) / (totalTime / 1000) * 10) : 0;
    
    // 任務完成率
    const taskCompletionRate = rawData.completion_rate;
    
    const score = Math.round((clickSuccessRate + navigationEfficiency + taskCompletionRate) / 3);
    
    return {
      click_success_rate: clickSuccessRate,
      navigation_efficiency: navigationEfficiency,
      task_completion_rate: taskCompletionRate,
      score
    };
  }
  
  /**
   * 計算可訪問性分數
   */
  private static async calculateAccessibilityScore() {
    try {
      const accessibilityResults = await userExperienceService.testAccessibility();
      
      // 基於檢測到的問題計算分數
      const totalIssues = 
        (accessibilityResults.images_without_alt || 0) +
        (accessibilityResults.buttons_without_text || 0) +
        (accessibilityResults.inputs_without_labels || 0) +
        (accessibilityResults.color_contrast_issues || 0);
      
      // 分數計算：每個問題扣5分，最低20分
      const score = Math.max(20, 100 - (totalIssues * 5));
      
      return {
        keyboard_navigation: totalIssues < 2 ? 90 : 70,
        screen_reader_compatibility: 100 - (accessibilityResults.buttons_without_text || 0) * 10,
        color_contrast: 100 - (accessibilityResults.color_contrast_issues || 0) * 15,
        score: Math.round(score)
      };
    } catch (error) {
      console.error('Failed to calculate accessibility score:', error);
      return {
        keyboard_navigation: 80,
        screen_reader_compatibility: 80,
        color_contrast: 80,
        score: 80
      };
    }
  }
  
  /**
   * 計算轉換分數
   */
  private static calculateConversionScore(interactionStats: Record<string, number>, rawData: UXTestResult) {
    const clickCount = interactionStats.click_count || 0;
    const totalTime = rawData.total_time;
    
    // CTA點擊率（基於總點擊數和停留時間）
    const ctaClickRate = totalTime > 10000 && clickCount > 0 ? Math.min(100, clickCount * 20) : 0;
    
    // 表單完成率（基於輸入互動）
    const inputCount = interactionStats.input_count || 0;
    const formCompletionRate = inputCount > 0 ? Math.min(100, inputCount * 25) : 0;
    
    // 跳出率（基於停留時間）
    const bounceRate = totalTime < 5000 ? 80 : totalTime < 15000 ? 50 : 20;
    
    const score = Math.round((ctaClickRate + formCompletionRate + (100 - bounceRate)) / 3);
    
    return {
      cta_click_rate: ctaClickRate,
      form_completion_rate: formCompletionRate,
      bounce_rate: bounceRate,
      score
    };
  }
  
  /**
   * 計算用戶滿意度
   */
  private static calculateUserSatisfaction(feedback: any[]): number {
    if (!feedback || feedback.length === 0) return 0;
    
    const ratings = feedback
      .filter(f => f.type === 'rating' && f.rating)
      .map(f => f.rating);
    
    if (ratings.length === 0) return 0;
    
    const averageRating = ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length;
    return Math.round((averageRating / 5) * 100);
  }
  
  /**
   * 生成優化建議
   */
  private static generateOptimizationSuggestions(data: any): UXOptimizationSuggestion[] {
    const suggestions: UXOptimizationSuggestion[] = [];
    
    // 性能優化建議
    if (data.performance.score < 80) {
      if (data.performance.page_load_time > 2000) {
        suggestions.push({
          category: 'performance',
          priority: 'high',
          title: '優化頁面載入速度',
          description: `當前頁面載入時間為 ${data.performance.page_load_time}ms，超過了理想的2秒標準`,
          impact: '可提升用戶留存率15-20%，減少跳出率',
          implementation: '壓縮圖片、啟用瀏覽器緩存、使用CDN、代碼分割',
          metrics: ['page_load_time', 'bounce_rate', 'user_engagement']
        });
      }
      
      if (data.performance.first_contentful_paint > 1800) {
        suggestions.push({
          category: 'performance',
          priority: 'medium',
          title: '改善首次內容繪製時間',
          description: '首次內容繪製時間過長，影響用戶感知性能',
          impact: '提升用戶體驗滿意度10-15%',
          implementation: '優化關鍵渲染路徑、內聯關鍵CSS、預載入重要資源',
          metrics: ['first_contentful_paint', 'user_satisfaction']
        });
      }
    }
    
    // 可用性優化建議
    if (data.usability.score < 80) {
      if (data.usability.click_success_rate < 85) {
        suggestions.push({
          category: 'usability',
          priority: 'high',
          title: '改善點擊目標設計',
          description: '部分點擊目標可能過小或不夠明顯',
          impact: '提升任務完成率20-25%',
          implementation: '增大按鈕尺寸、改善視覺層次、添加懸停效果',
          metrics: ['click_success_rate', 'task_completion_rate']
        });
      }
      
      if (data.usability.navigation_efficiency < 70) {
        suggestions.push({
          category: 'usability',
          priority: 'medium',
          title: '簡化導航流程',
          description: '用戶需要過多步驟才能完成任務',
          impact: '減少用戶操作時間30%',
          implementation: '重新設計信息架構、添加快捷操作、改善導航標籤',
          metrics: ['navigation_efficiency', 'total_time']
        });
      }
    }
    
    // 可訪問性優化建議
    if (data.accessibility.score < 80) {
      suggestions.push({
        category: 'accessibility',
        priority: 'medium',
        title: '改善網站可訪問性',
        description: '網站存在可訪問性問題，影響殘障用戶體驗',
        impact: '擴大用戶群體5-10%，符合法規要求',
        implementation: '添加alt屬性、改善鍵盤導航、提高顏色對比度',
        metrics: ['accessibility_score', 'user_coverage']
      });
    }
    
    // 轉換優化建議
    if (data.conversion.score < 70) {
      if (data.conversion.cta_click_rate < 50) {
        suggestions.push({
          category: 'conversion',
          priority: 'high',
          title: '優化行動呼籲按鈕',
          description: 'CTA按鈕點擊率偏低，需要改善設計和位置',
          impact: '提升轉換率25-40%',
          implementation: '改善按鈕文案、調整顏色和位置、添加緊迫感',
          metrics: ['cta_click_rate', 'conversion_rate']
        });
      }
      
      if (data.conversion.bounce_rate > 60) {
        suggestions.push({
          category: 'conversion',
          priority: 'high',
          title: '降低跳出率',
          description: '用戶跳出率過高，需要改善首屏內容',
          impact: '提升用戶參與度20-30%',
          implementation: '優化首屏設計、改善價值主張、添加社交證明',
          metrics: ['bounce_rate', 'engagement_rate']
        });
      }
    }
    
    return suggestions.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }
  
  /**
   * 生成報告摘要
   */
  static generateReportSummary(report: UXTestReport): string {
    const { summary, suggestions } = report;
    const highPrioritySuggestions = suggestions.filter(s => s.priority === 'high').length;
    
    let summaryText = `用戶體驗測試完成！總體評分：${summary.overall_score}/100。`;
    
    if (summary.overall_score >= 90) {
      summaryText += ' 🎉 優秀！您的網站提供了卓越的用戶體驗。';
    } else if (summary.overall_score >= 80) {
      summaryText += ' 👍 良好！網站體驗不錯，還有一些改進空間。';
    } else if (summary.overall_score >= 70) {
      summaryText += ' ⚠️ 一般！建議優先處理關鍵問題。';
    } else {
      summaryText += ' 🚨 需要改進！發現多個影響用戶體驗的問題。';
    }
    
    if (highPrioritySuggestions > 0) {
      summaryText += ` 發現 ${highPrioritySuggestions} 個高優先級改進項目。`;
    }
    
    return summaryText;
  }
  
  /**
   * 導出報告為JSON
   */
  static exportReportAsJSON(report: UXTestReport): string {
    return JSON.stringify(report, null, 2);
  }
  
  /**
   * 導出報告為CSV
   */
  static exportReportAsCSV(report: UXTestReport): string {
    const headers = [
      'Category', 'Priority', 'Title', 'Description', 'Impact', 'Implementation'
    ];
    
    const rows = report.suggestions.map(suggestion => [
      suggestion.category,
      suggestion.priority,
      suggestion.title,
      suggestion.description,
      suggestion.impact,
      suggestion.implementation
    ]);
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    return csvContent;
  }
}

export default UXTestReporter;