/**
 * 全局搜尋服務
 * 整合所有管理後台模組的搜尋功能
 * 基於 functional_admin.html 的優秀實現
 */

interface SearchResult {
  id: string;
  title: string;
  type: 'user' | 'content' | 'analytics' | 'financial' | 'system' | 'subscription';
  content: string;
  url?: string;
  score: number;
}

interface SearchableModule {
  name: string;
  search: (query: string) => Promise<SearchResult[]>;
}

export class GlobalSearchService {
  private modules: Map<string, SearchableModule> = new Map();
  private searchHistory: string[] = [];
  private maxHistorySize = 10;

  constructor() {
    this.loadSearchHistory();
  }

  /**
   * 註冊搜尋模組
   */
  registerModule(name: string, module: SearchableModule): void {
    this.modules.set(name, module);
  }

  /**
   * 執行全局搜尋
   */
  async performGlobalSearch(query: string): Promise<SearchResult[]> {
    if (!query.trim()) {
      return [];
    }

    // 記錄搜尋歷史
    this.addToHistory(query);

    // 並行搜尋所有模組
    const searchPromises = Array.from(this.modules.values()).map(module =>
      module.search(query).catch(error => {
        console.warn(`Search module error:`, error);
        return [];
      })
    );

    const results = await Promise.all(searchPromises);
    
    // 合併並排序結果
    const allResults = results.flat();
    return this.sortAndDeduplicateResults(allResults, query);
  }

  /**
   * 高亮搜尋結果
   */
  highlightSearchResults(query: string, container: HTMLElement): void {
    if (!query.trim()) {
      this.removeHighlights(container);
      return;
    }

    const walker = document.createTreeWalker(
      container,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          const parent = node.parentElement;
          if (!parent || parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') {
            return NodeFilter.FILTER_REJECT;
          }
          return node.textContent && node.textContent.includes(query) 
            ? NodeFilter.FILTER_ACCEPT 
            : NodeFilter.FILTER_REJECT;
        }
      }
    );

    const textNodes: Text[] = [];
    let node;
    while (node = walker.nextNode()) {
      textNodes.push(node as Text);
    }

    textNodes.forEach(textNode => {
      const parent = textNode.parentElement!;
      const text = textNode.textContent || '';
      
      if (text.includes(query)) {
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        const highlightedHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
        
        const wrapper = document.createElement('span');
        wrapper.innerHTML = highlightedHTML;
        parent.replaceChild(wrapper, textNode);
      }
    });
  }

  /**
   * 移除高亮效果
   */
  removeHighlights(container: HTMLElement): void {
    const highlights = container.querySelectorAll('.search-highlight');
    highlights.forEach(highlight => {
      const parent = highlight.parentNode!;
      parent.replaceChild(document.createTextNode(highlight.textContent || ''), highlight);
      parent.normalize();
    });
  }

  /**
   * 獲取搜尋建議
   */
  getSearchSuggestions(query: string): string[] {
    const suggestions = [
      // 基於搜尋歷史的建議
      ...this.searchHistory.filter(item => 
        item.toLowerCase().includes(query.toLowerCase()) && item !== query
      ),
      
      // 基於常見搜尋詞的建議
      ...this.getCommonSuggestions(query)
    ];

    return [...new Set(suggestions)].slice(0, 5);
  }

  /**
   * 獲取搜尋歷史
   */
  getSearchHistory(): string[] {
    return [...this.searchHistory];
  }

  /**
   * 清除搜尋歷史
   */
  clearSearchHistory(): void {
    this.searchHistory = [];
    localStorage.removeItem('admin_search_history');
  }

  private sortAndDeduplicateResults(results: SearchResult[], query: string): SearchResult[] {
    // 去重
    const uniqueResults = results.filter((result, index, self) =>
      index === self.findIndex(r => r.id === result.id)
    );

    // 計算相關性分數
    uniqueResults.forEach(result => {
      result.score = this.calculateRelevanceScore(result, query);
    });

    // 按分數排序
    return uniqueResults.sort((a, b) => b.score - a.score);
  }

  private calculateRelevanceScore(result: SearchResult, query: string): number {
    const queryLower = query.toLowerCase();
    const titleLower = result.title.toLowerCase();
    const contentLower = result.content.toLowerCase();

    let score = 0;

    // 標題完全匹配
    if (titleLower === queryLower) score += 100;
    // 標題包含查詢
    else if (titleLower.includes(queryLower)) score += 50;
    // 標題開頭匹配
    else if (titleLower.startsWith(queryLower)) score += 30;

    // 內容包含查詢
    if (contentLower.includes(queryLower)) score += 20;

    // 查詢詞在內容中的出現頻率
    const queryCount = (contentLower.match(new RegExp(this.escapeRegex(queryLower), 'g')) || []).length;
    score += queryCount * 5;

    return score;
  }

  private getCommonSuggestions(query: string): string[] {
    const commonTerms = [
      '用戶管理', '權限設置', '數據分析', '財務報表',
      '系統監控', '內容管理', '訂閱管理', '系統設置',
      '登入日誌', '性能指標', '錯誤報告', '備份恢復'
    ];

    return commonTerms.filter(term =>
      term.toLowerCase().includes(query.toLowerCase())
    );
  }

  private addToHistory(query: string): void {
    // 移除重複項
    this.searchHistory = this.searchHistory.filter(item => item !== query);
    
    // 添加到開頭
    this.searchHistory.unshift(query);
    
    // 限制歷史記錄數量
    if (this.searchHistory.length > this.maxHistorySize) {
      this.searchHistory = this.searchHistory.slice(0, this.maxHistorySize);
    }

    this.saveSearchHistory();
  }

  private loadSearchHistory(): void {
    try {
      const saved = localStorage.getItem('admin_search_history');
      if (saved) {
        this.searchHistory = JSON.parse(saved);
      }
    } catch (error) {
      console.warn('Failed to load search history:', error);
    }
  }

  private saveSearchHistory(): void {
    try {
      localStorage.setItem('admin_search_history', JSON.stringify(this.searchHistory));
    } catch (error) {
      console.warn('Failed to save search history:', error);
    }
  }

  private escapeRegex(text: string): string {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}

// 單例實例
export const globalSearchService = new GlobalSearchService();