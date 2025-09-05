import React, { useState, useEffect } from 'react';
import './NewsPage.css';

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: string;
  author: string;
  publishDate: string;
  readTime: number;
  image?: string;
  tags: string[];
  featured: boolean;
}

interface NewsCategory {
  id: string;
  name: string;
  icon: string;
  count: number;
}

const NewsPage: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);

  // 新聞分類
  const categories: NewsCategory[] = [
    { id: 'all', name: '全部', icon: '📰', count: 0 },
    { id: 'product', name: '產品更新', icon: '🚀', count: 0 },
    { id: 'market', name: '市場分析', icon: '📊', count: 0 },
    { id: 'company', name: '公司動態', icon: '🏢', count: 0 },
    { id: 'technology', name: '技術創新', icon: '💡', count: 0 },
    { id: 'education', name: '投資教育', icon: '📚', count: 0 }
  ];

  // 模擬新聞數據
  const mockArticles: NewsArticle[] = [
    {
      id: '1',
      title: 'TradingAgents 推出全新 AI 分析師 3.0',
      summary: '新版本 AI 分析師準確率提升至 90%，支援更多市場和投資策略分析。',
      content: `我們很高興宣布 TradingAgents AI 分析師 3.0 正式上線！這次更新帶來了重大的技術突破和功能改進。

## 主要更新內容

### 1. 準確率大幅提升
通過深度學習算法的優化和更大規模的訓練數據，新版本的分析準確率從 85% 提升至 90%。

### 2. 支援更多市場
除了原有的台股、美股分析，現在還支援港股、日股和歐洲主要市場。

### 3. 個性化推薦
基於用戶的投資偏好和風險承受能力，提供更精準的個性化投資建議。

### 4. 實時市場監控
24/7 監控市場動態，及時發送重要市場變化通知。

這次更新是我們持續創新的重要里程碑，感謝所有用戶的支持和反饋！`,
      category: 'product',
      author: '產品團隊',
      publishDate: '2025-01-08',
      readTime: 3,
      image: '/news/ai-analyst-3.jpg',
      tags: ['AI', '產品更新', '機器學習'],
      featured: true
    },
    {
      id: '2',
      title: '2025年第一季市場展望：AI驅動的投資機會',
      summary: '分析師團隊深度解讀2025年第一季的市場趨勢和投資機會。',
      content: `隨著2025年的到來，全球市場呈現出新的投資機會和挑戰。我們的分析師團隊為您帶來第一季的市場展望。

## 主要趨勢分析

### 1. AI 技術股持續強勢
人工智能相關企業預計將繼續受到市場青睞，特別是在企業級AI應用領域。

### 2. 綠色能源轉型加速
隨著各國政策支持，再生能源和電動車產業鏈將迎來新的成長機會。

### 3. 利率政策影響
央行政策變化將對不同資產類別產生重要影響，需要密切關注。

## 投資建議

我們建議投資者保持多元化配置，重點關注具有長期成長潛力的科技和綠能股票。`,
      category: 'market',
      author: '市場分析團隊',
      publishDate: '2025-01-07',
      readTime: 5,
      image: '/news/market-outlook.jpg',
      tags: ['市場分析', '投資策略', '2025展望'],
      featured: true
    },
    {
      id: '3',
      title: 'TradingAgents 完成 B 輪融資，估值達 5 億美元',
      summary: '公司獲得知名創投基金投資，將用於產品研發和國際市場擴展。',
      content: `TradingAgents 今日宣布完成 B 輪融資，融資金額達 8000 萬美元，公司估值達到 5 億美元。

## 融資詳情

本輪融資由知名創投基金 ABC Capital 領投，現有投資者 XYZ Ventures 跟投。

## 資金用途

1. **產品研發**：加強 AI 技術研發，提升分析準確率
2. **市場擴展**：進軍東南亞和歐洲市場
3. **團隊建設**：招募頂尖技術和產品人才
4. **基礎設施**：擴展服務器和數據處理能力

## 未來規劃

我們將繼續專注於為用戶提供最優質的 AI 投資分析服務，目標是成為全球領先的智能投資平台。`,
      category: 'company',
      author: '公關部',
      publishDate: '2025-01-06',
      readTime: 4,
      image: '/news/funding-b-round.jpg',
      tags: ['融資', '公司發展', '投資'],
      featured: false
    },
    {
      id: '4',
      title: '深度學習在股票預測中的應用與挑戰',
      summary: '技術團隊分享如何運用深度學習技術提升股票分析的準確性。',
      content: `在 TradingAgents，我們一直在探索如何運用最新的深度學習技術來提升股票分析的準確性。

## 技術架構

### 1. 多模態數據融合
我們的模型能夠同時處理：
- 歷史價格數據
- 財務報表信息
- 新聞情緒分析
- 社交媒體討論

### 2. 時序預測模型
使用 LSTM 和 Transformer 架構來捕捉股價的時序特徵。

### 3. 風險控制機制
內建多層風險控制，確保預測結果的可靠性。

## 面臨的挑戰

1. **數據質量**：確保訓練數據的準確性和完整性
2. **模型解釋性**：讓用戶理解 AI 的決策邏輯
3. **市場變化**：適應不斷變化的市場環境

我們將持續優化技術，為用戶提供更準確的投資分析。`,
      category: 'technology',
      author: '技術團隊',
      publishDate: '2025-01-05',
      readTime: 6,
      image: '/news/deep-learning.jpg',
      tags: ['深度學習', '技術', 'AI'],
      featured: false
    },
    {
      id: '5',
      title: '投資新手必讀：如何開始你的投資之旅',
      summary: '專為投資新手準備的完整指南，從基礎概念到實戰技巧。',
      content: `投資可能看起來很複雜，但只要掌握基本原則，任何人都可以開始投資之旅。

## 投資基礎

### 1. 了解風險與報酬
投資的基本原則是風險與報酬成正比，高報酬通常伴隨高風險。

### 2. 分散投資
不要把所有雞蛋放在同一個籃子裡，分散投資可以降低風險。

### 3. 長期投資
時間是投資者最好的朋友，長期投資能夠平滑市場波動。

## 實戰建議

1. **設定投資目標**：明確你的投資目的和時間框架
2. **評估風險承受能力**：了解自己能承受多大的損失
3. **定期檢視投資組合**：根據市場變化調整配置
4. **持續學習**：投資是一門需要不斷學習的學問

## 使用 TradingAgents 的建議

我們的 AI 分析師可以幫助新手：
- 分析股票基本面
- 提供投資建議
- 監控投資組合表現
- 學習投資知識

記住，投資有風險，請謹慎評估後再做決定。`,
      category: 'education',
      author: '投資教育團隊',
      publishDate: '2025-01-04',
      readTime: 8,
      image: '/news/investment-guide.jpg',
      tags: ['投資教育', '新手指南', '理財'],
      featured: false
    }
  ];

  useEffect(() => {
    // 模擬載入數據
    const timer = setTimeout(() => {
      setArticles(mockArticles);
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  // 計算每個分類的文章數量
  const categoriesWithCount = categories.map(category => ({
    ...category,
    count: category.id === 'all' 
      ? articles.length 
      : articles.filter(article => article.category === category.id).length
  }));

  // 過濾文章
  const filteredArticles = articles.filter(article => {
    const matchesCategory = selectedCategory === 'all' || article.category === selectedCategory;
    const matchesSearch = searchQuery === '' || 
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesCategory && matchesSearch;
  });

  // 分離精選文章和普通文章
  const featuredArticles = filteredArticles.filter(article => article.featured);
  const regularArticles = filteredArticles.filter(article => !article.featured);

  const handleCategoryChange = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setSelectedArticle(null);
  };

  const handleArticleClick = (article: NewsArticle) => {
    setSelectedArticle(article);
  };

  const handleBackToList = () => {
    setSelectedArticle(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className="news-page">
        <div className="news-loading">
          <div className="loading-spinner"></div>
          <p>載入新聞...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="news-page">
      {/* 頁面標題 */}
      <div className="news-header">
        <div className="header-content">
          <h1 className="news-title">
            <span className="news-icon">📰</span>
            新聞中心
          </h1>
          <p className="news-subtitle">
            獲取最新的產品動態、市場分析和投資洞察
          </p>
        </div>
      </div>

      <div className="news-container">
        {!selectedArticle ? (
          <>
            {/* 搜尋和篩選 */}
            <div className="news-controls">
              <div className="search-section">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="搜尋新聞..."
                    value={searchQuery}
                    onChange={(e: any) => setSearchQuery(e.target.value)}
                  />
                  {searchQuery && (
                    <button
                      className="clear-search"
                      onClick={() => setSearchQuery('')}
                      aria-label="清除搜尋"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>

              <div className="category-filters">
                {categoriesWithCount.map(category => (
                  <button
                    key={category.id}
                    className={`category-filter ${selectedCategory === category.id ? 'active' : ''}`}
                    onClick={() => handleCategoryChange(category.id)}
                  >
                    <span className="filter-icon">{category.icon}</span>
                    <span className="filter-name">{category.name}</span>
                    <span className="filter-count">({category.count})</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 新聞內容 */}
            <div className="news-content">
              {filteredArticles.length === 0 ? (
                <div className="no-articles">
                  <div className="no-articles-icon">📰</div>
                  <h3>沒有找到相關新聞</h3>
                  <p>嘗試使用不同的關鍵字或選擇其他分類</p>
                  <button
                    className="reset-filters"
                    onClick={() => {
                      setSearchQuery('');
                      setSelectedCategory('all');
                    }}
                  >
                    重置篩選
                  </button>
                </div>
              ) : (
                <>
                  {/* 精選文章 */}
                  {featuredArticles.length > 0 && (
                    <div className="featured-section">
                      <h2 className="section-title">精選文章</h2>
                      <div className="featured-articles">
                        {featuredArticles.map(article => (
                          <article
                            key={article.id}
                            className="featured-article"
                            onClick={() => handleArticleClick(article)}
                          >
                            <div className="article-image">
                              <img 
                                src={article.image} 
                                alt={article.title}
                                onError={(e: any) => {
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = 'none';
                                  target.nextElementSibling!.classList.remove('hidden');
                                }}
                              />
                              <div className="image-placeholder hidden">
                                📰
                              </div>
                              <div className="featured-badge">精選</div>
                            </div>
                            <div className="article-content">
                              <div className="article-meta">
                                <span className="article-category">
                                  {categoriesWithCount.find(c => c.id === article.category)?.name}
                                </span>
                                <span className="article-date">
                                  {formatDate(article.publishDate)}
                                </span>
                              </div>
                              <h3 className="article-title">{article.title}</h3>
                              <p className="article-summary">{article.summary}</p>
                              <div className="article-footer">
                                <span className="article-author">作者：{article.author}</span>
                                <span className="read-time">{article.readTime} 分鐘閱讀</span>
                              </div>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 一般文章 */}
                  {regularArticles.length > 0 && (
                    <div className="regular-section">
                      <h2 className="section-title">
                        {featuredArticles.length > 0 ? '更多文章' : '最新文章'}
                      </h2>
                      <div className="regular-articles">
                        {regularArticles.map(article => (
                          <article
                            key={article.id}
                            className="regular-article"
                            onClick={() => handleArticleClick(article)}
                          >
                            <div className="article-image">
                              <img 
                                src={article.image} 
                                alt={article.title}
                                onError={(e: any) => {
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = 'none';
                                  target.nextElementSibling!.classList.remove('hidden');
                                }}
                              />
                              <div className="image-placeholder hidden">
                                📰
                              </div>
                            </div>
                            <div className="article-content">
                              <div className="article-meta">
                                <span className="article-category">
                                  {categoriesWithCount.find(c => c.id === article.category)?.name}
                                </span>
                                <span className="article-date">
                                  {formatDate(article.publishDate)}
                                </span>
                              </div>
                              <h3 className="article-title">{article.title}</h3>
                              <p className="article-summary">{article.summary}</p>
                              <div className="article-footer">
                                <span className="article-author">作者：{article.author}</span>
                                <span className="read-time">{article.readTime} 分鐘閱讀</span>
                              </div>
                              <div className="article-tags">
                                {article.tags.map(tag => (
                                  <span key={tag} className="article-tag">{tag}</span>
                                ))}
                              </div>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        ) : (
          /* 文章詳情 */
          <div className="article-detail">
            <button className="back-button" onClick={handleBackToList}>
              <span className="back-icon">←</span>
              返回新聞列表
            </button>
            
            <article className="detail-content">
              <header className="detail-header">
                <div className="detail-meta">
                  <span className="detail-category">
                    {categoriesWithCount.find(c => c.id === selectedArticle.category)?.name}
                  </span>
                  <span className="detail-date">
                    {formatDate(selectedArticle.publishDate)}
                  </span>
                </div>
                <h1 className="detail-title">{selectedArticle.title}</h1>
                <div className="detail-info">
                  <span className="detail-author">作者：{selectedArticle.author}</span>
                  <span className="detail-read-time">{selectedArticle.readTime} 分鐘閱讀</span>
                </div>
                {selectedArticle.image && (
                  <div className="detail-image">
                    <img 
                      src={selectedArticle.image} 
                      alt={selectedArticle.title}
                      onError={(e: any) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </header>
              
              <div className="detail-body">
                <div className="article-content-text">
                  {selectedArticle.content.split('\n').map((paragraph, index) => {
                    if (paragraph.startsWith('## ')) {
                      return <h2 key={index}>{paragraph.replace('## ', '')}</h2>;
                    } else if (paragraph.startsWith('### ')) {
                      return <h3 key={index}>{paragraph.replace('### ', '')}</h3>;
                    } else if (paragraph.trim() === '') {
                      return <br key={index} />;
                    } else {
                      return <p key={index}>{paragraph}</p>;
                    }
                  })}
                </div>
                
                <div className="detail-tags">
                  <h4>相關標籤</h4>
                  <div className="tags-list">
                    {selectedArticle.tags.map(tag => (
                      <span key={tag} className="detail-tag">{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
            </article>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsPage;