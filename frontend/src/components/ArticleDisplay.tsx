/**
 * 公開文章展示組件
 * 為已發布的文章提供公共瀏覽界面
 */
import React, { useState, useEffect } from 'react';

interface Article {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content?: string;
  type: 'article' | 'page' | 'announcement' | 'faq';
  author: string;
  views: number;
  likes: number;
  is_featured: boolean;
  published_at: string;
  created_at: string;
  category?: {
    name: string;
    slug: string;
  };
  tags: Array<{
    name: string;
    color: string;
  }>;
}

interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  article_count: number;
}

interface Tag {
  id: number;
  name: string;
  slug: string;
  color: string;
  article_count: number;
}

interface ArticleDisplayProps {
  viewMode?: 'list' | 'detail';
  articleSlug?: string;
}

export const ArticleDisplay: React.FC<ArticleDisplayProps> = ({ 
  viewMode = 'list', 
  articleSlug 
}) => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [currentArticle, setCurrentArticle] = useState<Article | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    total_pages: 0
  });

  // 載入文章列表
  const loadArticles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        limit: pagination.limit.toString(),
      });
      
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedTag) params.append('tag', selectedTag);
      if (searchTerm) params.append('search', searchTerm);
      
      const response = await fetch(`http://localhost:8000/articles?${params}`);
      const result = await response.json();
      
      if (result.status === 'success') {
        setArticles(result.data.articles || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.pagination.total,
          total_pages: result.data.pagination.total_pages
        }));
      } else {
        // 使用模擬數據
        setArticles([
          {
            id: 1,
            title: '股票投資新手完全指南',
            slug: 'stock-investment-beginner-guide',
            excerpt: '完整的股票投資入門指南，適合初學者學習',
            type: 'article',
            author: '張投資顧問',
            views: 1250,
            likes: 89,
            is_featured: true,
            published_at: '2025-07-30T01:32:42',
            created_at: '2025-08-26T01:32:42',
            category: { name: '投資教學', slug: 'investment-education' },
            tags: [
              { name: '股票', color: '#e74c3c' },
              { name: '初學者', color: '#95a5a6' }
            ]
          },
          {
            id: 2,
            title: '台股2024年第四季展望分析',
            slug: 'taiwan-stock-q4-2024-outlook',
            excerpt: '深度分析台股第四季投資機會與風險',
            type: 'article',
            author: '李市場分析師',
            views: 890,
            likes: 67,
            is_featured: true,
            published_at: '2025-08-15T01:32:42',
            created_at: '2025-08-26T01:32:42',
            category: { name: '市場分析', slug: 'market-analysis' },
            tags: []
          }
        ]);
      }
    } catch (error) {
      console.error('載入文章失敗:', error);
      // 使用模擬數據作為後備
    } finally {
      setLoading(false);
    }
  };

  // 載入單篇文章
  const loadArticle = async (slug: string) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/articles/${slug}`);
      const result = await response.json();
      
      if (result.status === 'success') {
        setCurrentArticle(result.data);
      } else {
        // 模擬數據
        setCurrentArticle({
          id: 1,
          title: '股票投資新手完全指南',
          slug: 'stock-investment-beginner-guide',
          excerpt: '完整的股票投資入門指南，適合初學者學習',
          content: `
            <h2>股票投資基礎概念</h2>
            <p>股票投資是建立財富的重要方式，但需要正確的知識和策略。本指南將帶您了解：</p>
            <ul>
              <li>股票市場的基本運作原理</li>
              <li>如何選擇適合的股票</li>
              <li>風險管理的重要性</li>
              <li>長期投資vs短期交易</li>
            </ul>
            
            <h3>開始投資前的準備</h3>
            <p>在開始股票投資前，您需要：</p>
            <ol>
              <li>建立緊急基金</li>
              <li>了解個人風險承受能力</li>
              <li>選擇合適的證券商</li>
              <li>學習基本的財務分析</li>
            </ol>
            
            <h3>投資策略</h3>
            <p>對於新手投資者，建議採用分散投資策略，不要將所有資金投入單一股票。定期定額投資法是一個不錯的開始方式。</p>
          `,
          type: 'article',
          author: '張投資顧問',
          views: 1251, // 增加瀏覽量
          likes: 89,
          is_featured: true,
          published_at: '2025-07-30T01:32:42',
          created_at: '2025-08-26T01:32:42',
          category: { name: '投資教學', slug: 'investment-education' },
          tags: [
            { name: '股票', color: '#e74c3c' },
            { name: '初學者', color: '#95a5a6' }
          ]
        });
      }
    } catch (error) {
      console.error('載入文章失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 載入分類和標籤
  const loadMetadata = async () => {
    try {
      const [categoriesRes, tagsRes] = await Promise.all([
        fetch('http://localhost:8000/categories'),
        fetch('http://localhost:8000/tags')
      ]);

      const categoriesResult = await categoriesRes.json();
      const tagsResult = await tagsRes.json();

      if (categoriesResult.status === 'success') {
        setCategories(categoriesResult.data || []);
      }

      if (tagsResult.status === 'success') {
        setTags(tagsResult.data || []);
      }
    } catch (error) {
      console.error('載入元數據失敗:', error);
      // 使用模擬數據
      setCategories([
        { id: 1, name: '投資教學', slug: 'investment-education', description: '', article_count: 2 },
        { id: 2, name: '市場分析', slug: 'market-analysis', description: '', article_count: 1 }
      ]);
      setTags([
        { id: 1, name: '股票', slug: 'stock', color: '#e74c3c', article_count: 1 },
        { id: 2, name: '初學者', slug: 'beginner', color: '#95a5a6', article_count: 1 }
      ]);
    }
  };

  useEffect(() => {
    if (viewMode === 'detail' && articleSlug) {
      loadArticle(articleSlug);
    } else {
      loadArticles();
    }
    loadMetadata();
  }, [viewMode, articleSlug, pagination.page, selectedCategory, selectedTag, searchTerm]);

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // 獲取文章類型標籤樣式
  const getTypeStyle = (type: string) => {
    const styles = {
      article: 'bg-primary',
      page: 'bg-info',
      announcement: 'bg-warning',
      faq: 'bg-secondary'
    };
    return styles[type as keyof typeof styles] || 'bg-secondary';
  };

  // 獲取文章類型名稱
  const getTypeName = (type: string) => {
    const names = {
      article: '文章',
      page: '頁面', 
      announcement: '公告',
      faq: '常見問題'
    };
    return names[type as keyof typeof names] || type;
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">載入中...</span>
        </div>
      </div>
    );
  }

  // 文章詳情頁面
  if (viewMode === 'detail' && currentArticle) {
    return (
      <div className="article-detail">
        <div className="container py-5">
          <div className="row justify-content-center">
            <div className="col-lg-8">
              {/* 麵包屑導航 */}
              <nav aria-label="breadcrumb">
                <ol className="breadcrumb">
                  <li className="breadcrumb-item">
                    <a href="/" className="text-decoration-none">首頁</a>
                  </li>
                  {currentArticle.category && (
                    <li className="breadcrumb-item">
                      <a href={`/category/${currentArticle.category.slug}`} className="text-decoration-none">
                        {currentArticle.category.name}
                      </a>
                    </li>
                  )}
                  <li className="breadcrumb-item active">{currentArticle.title}</li>
                </ol>
              </nav>

              {/* 文章標題區域 */}
              <div className="article-header mb-4">
                <div className="d-flex align-items-center mb-2">
                  <span className={`badge ${getTypeStyle(currentArticle.type)} me-2`}>
                    {getTypeName(currentArticle.type)}
                  </span>
                  {currentArticle.is_featured && (
                    <span className="badge bg-warning text-dark me-2">
                      <i className="fas fa-star me-1"></i>推薦
                    </span>
                  )}
                  {currentArticle.category && (
                    <span className="badge bg-light text-dark">
                      {currentArticle.category.name}
                    </span>
                  )}
                </div>

                <h1 className="article-title mb-3">{currentArticle.title}</h1>

                <div className="article-meta text-muted mb-3">
                  <span className="me-3">
                    <i className="fas fa-user me-1"></i>
                    {currentArticle.author}
                  </span>
                  <span className="me-3">
                    <i className="fas fa-calendar me-1"></i>
                    {formatDate(currentArticle.published_at)}
                  </span>
                  <span className="me-3">
                    <i className="fas fa-eye me-1"></i>
                    {currentArticle?.views?.toLocaleString() || '0'} 次瀏覽
                  </span>
                  <span>
                    <i className="fas fa-heart me-1"></i>
                    {currentArticle?.likes?.toLocaleString() || '0'} 個讚
                  </span>
                </div>

                {/* 標籤 */}
                {currentArticle.tags.length > 0 && (
                  <div className="article-tags mb-4">
                    {currentArticle.tags.map((tag, index) => (
                      <span 
                        key={index}
                        className="badge me-2 mb-1"
                        style={{ backgroundColor: tag.color }}
                      >
                        <i className="fas fa-tag me-1"></i>
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 文章摘要 */}
              {currentArticle.excerpt && (
                <div className="article-excerpt bg-light p-3 rounded mb-4">
                  <p className="mb-0 fst-italic">{currentArticle.excerpt}</p>
                </div>
              )}

              {/* 文章內容 */}
              <div 
                className="article-content"
                dangerouslySetInnerHTML={{ __html: currentArticle.content || '' }}
              />

              {/* 文章底部操作 */}
              <div className="article-actions mt-5 pt-4 border-top">
                <div className="d-flex justify-content-between align-items-center">
                  <div className="article-stats">
                    <button className="btn btn-outline-primary btn-sm me-2">
                      <i className="fas fa-heart me-1"></i>
                      讚 ({currentArticle.likes})
                    </button>
                    <button className="btn btn-outline-secondary btn-sm">
                      <i className="fas fa-share me-1"></i>
                      分享
                    </button>
                  </div>
                  <div>
                    <a href="/articles" className="btn btn-outline-secondary btn-sm">
                      <i className="fas fa-arrow-left me-1"></i>
                      返回列表
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 文章列表頁面
  return (
    <div className="articles-list">
      <div className="container py-5">
        <div className="row">
          {/* 側邊欄 - 篩選器 */}
          <div className="col-lg-3">
            <div className="sidebar">
              {/* 搜尋 */}
              <div className="card mb-4">
                <div className="card-header">
                  <h5 className="mb-0">搜尋文章</h5>
                </div>
                <div className="card-body">
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="輸入關鍵字..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <button className="btn btn-outline-secondary" type="button">
                      <i className="fas fa-search"></i>
                    </button>
                  </div>
                </div>
              </div>

              {/* 分類篩選 */}
              <div className="card mb-4">
                <div className="card-header">
                  <h5 className="mb-0">文章分類</h5>
                </div>
                <div className="card-body">
                  <div className="list-group list-group-flush">
                    <button
                      className={`list-group-item list-group-item-action ${selectedCategory === '' ? 'active' : ''}`}
                      onClick={() => setSelectedCategory('')}
                    >
                      全部分類
                    </button>
                    {categories.map(category => (
                      <button
                        key={category.id}
                        className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${selectedCategory === category.slug ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(category.slug)}
                      >
                        {category.name}
                        <span className="badge bg-secondary rounded-pill">
                          {category.article_count}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 標籤雲 */}
              <div className="card">
                <div className="card-header">
                  <h5 className="mb-0">熱門標籤</h5>
                </div>
                <div className="card-body">
                  <div className="tag-cloud">
                    {tags.map(tag => (
                      <button
                        key={tag.id}
                        className={`btn btn-sm me-2 mb-2 ${selectedTag === tag.slug ? 'btn-primary' : 'btn-outline-secondary'}`}
                        style={selectedTag !== tag.slug ? { 
                          borderColor: tag.color, 
                          color: tag.color 
                        } : { backgroundColor: tag.color, borderColor: tag.color }}
                        onClick={() => setSelectedTag(selectedTag === tag.slug ? '' : tag.slug)}
                      >
                        {tag.name} ({tag.article_count})
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 主要內容區域 */}
          <div className="col-lg-9">
            {/* 頁面標題 */}
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h1>文章列表</h1>
              <div className="text-muted">
                共 {pagination.total} 篇文章
              </div>
            </div>

            {/* 當前篩選條件 */}
            {(selectedCategory || selectedTag || searchTerm) && (
              <div className="current-filters mb-4">
                <div className="d-flex align-items-center flex-wrap">
                  <span className="text-muted me-2">當前篩選：</span>
                  {selectedCategory && (
                    <span className="badge bg-primary me-2">
                      分類: {categories.find(c => c.slug === selectedCategory)?.name}
                      <button 
                        className="btn-close btn-close-white ms-1" 
                        style={{ fontSize: '0.6em' }}
                        onClick={() => setSelectedCategory('')}
                      ></button>
                    </span>
                  )}
                  {selectedTag && (
                    <span className="badge bg-info me-2">
                      標籤: {tags.find(t => t.slug === selectedTag)?.name}
                      <button 
                        className="btn-close btn-close-white ms-1" 
                        style={{ fontSize: '0.6em' }}
                        onClick={() => setSelectedTag('')}
                      ></button>
                    </span>
                  )}
                  {searchTerm && (
                    <span className="badge bg-success me-2">
                      搜尋: {searchTerm}
                      <button 
                        className="btn-close btn-close-white ms-1" 
                        style={{ fontSize: '0.6em' }}
                        onClick={() => setSearchTerm('')}
                      ></button>
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* 文章列表 */}
            <div className="articles-grid">
              {articles.length === 0 ? (
                <div className="text-center py-5">
                  <div className="text-muted">
                    <i className="fas fa-folder-open fa-3x mb-3"></i>
                    <p>沒有找到符合條件的文章</p>
                  </div>
                </div>
              ) : (
                articles.map(article => (
                  <div key={article.id} className="card mb-4">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <div className="article-badges">
                          <span className={`badge ${getTypeStyle(article.type)} me-2`}>
                            {getTypeName(article.type)}
                          </span>
                          {article.is_featured && (
                            <span className="badge bg-warning text-dark me-2">
                              <i className="fas fa-star me-1"></i>推薦
                            </span>
                          )}
                          {article.category && (
                            <span className="badge bg-light text-dark">
                              {article.category.name}
                            </span>
                          )}
                        </div>
                        <div className="article-meta-compact text-muted small">
                          {formatDate(article.published_at)}
                        </div>
                      </div>

                      <h5 className="card-title">
                        <a 
                          href={`/articles/${article.slug}`} 
                          className="text-decoration-none"
                        >
                          {article.title}
                        </a>
                      </h5>

                      <p className="card-text text-muted">{article.excerpt}</p>

                      {/* 標籤 */}
                      {article.tags.length > 0 && (
                        <div className="article-tags mb-3">
                          {article.tags.map((tag, index) => (
                            <span 
                              key={index}
                              className="badge me-1 mb-1"
                              style={{ backgroundColor: tag.color }}
                            >
                              {tag.name}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="d-flex justify-content-between align-items-center">
                        <div className="article-stats text-muted small">
                          <span className="me-3">
                            <i className="fas fa-user me-1"></i>
                            {article.author}
                          </span>
                          <span className="me-3">
                            <i className="fas fa-eye me-1"></i>
                            {article?.views?.toLocaleString() || '0'}
                          </span>
                          <span>
                            <i className="fas fa-heart me-1"></i>
                            {article?.likes?.toLocaleString() || '0'}
                          </span>
                        </div>
                        <div>
                          <a 
                            href={`/articles/${article.slug}`} 
                            className="btn btn-outline-primary btn-sm"
                          >
                            閱讀更多
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* 分頁 */}
            {pagination.total_pages > 1 && (
              <nav aria-label="文章分頁">
                <ul className="pagination justify-content-center">
                  <li className={`page-item ${pagination.page === 1 ? 'disabled' : ''}`}>
                    <button 
                      className="page-link"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.page === 1}
                    >
                      上一頁
                    </button>
                  </li>
                  
                  {Array.from({ length: pagination.total_pages }, (_, i) => i + 1)
                    .filter(page => {
                      return page === 1 || 
                             page === pagination.total_pages || 
                             Math.abs(page - pagination.page) <= 2;
                    })
                    .map(page => (
                      <li 
                        key={page}
                        className={`page-item ${pagination.page === page ? 'active' : ''}`}
                      >
                        <button 
                          className="page-link"
                          onClick={() => setPagination(prev => ({ ...prev, page }))}
                        >
                          {page}
                        </button>
                      </li>
                    ))
                  }
                  
                  <li className={`page-item ${pagination.page === pagination.total_pages ? 'disabled' : ''}`}>
                    <button 
                      className="page-link"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                      disabled={pagination.page === pagination.total_pages}
                    >
                      下一頁
                    </button>
                  </li>
                </ul>
              </nav>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticleDisplay;