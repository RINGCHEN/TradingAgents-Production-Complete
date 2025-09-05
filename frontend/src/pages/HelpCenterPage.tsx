import React, { useState, useEffect } from 'react';
import './HelpCenterPage.css';

interface FAQItem {
  id: string;
  category: string;
  question: string;
  answer: string;
  tags: string[];
}

interface HelpCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  articleCount: number;
}

const HelpCenterPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedFAQ, setExpandedFAQ] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 模擬數據
  const helpCategories: HelpCategory[] = [
    {
      id: 'getting-started',
      name: '新手入門',
      icon: '🚀',
      description: '了解如何開始使用 TradingAgents',
      articleCount: 8
    },
    {
      id: 'analysis',
      name: '股票分析',
      icon: '📊',
      description: '學習如何使用 AI 分析師進行股票分析',
      articleCount: 12
    },
    {
      id: 'portfolio',
      name: '投資組合',
      icon: '💼',
      description: '管理和優化您的投資組合',
      articleCount: 6
    },
    {
      id: 'account',
      name: '帳戶設置',
      icon: '⚙️',
      description: '帳戶管理和個人設置',
      articleCount: 5
    },
    {
      id: 'subscription',
      name: '訂閱方案',
      icon: '💎',
      description: '了解不同的訂閱方案和功能',
      articleCount: 4
    },
    {
      id: 'technical',
      name: '技術支援',
      icon: '🔧',
      description: '解決技術問題和故障排除',
      articleCount: 10
    }
  ];

  const faqItems: FAQItem[] = [
    {
      id: '1',
      category: 'getting-started',
      question: '如何開始使用 TradingAgents？',
      answer: '首先註冊一個帳戶，然後完成身份驗證。接著您可以開始搜尋股票並使用我們的 AI 分析師進行分析。建議先閱讀新手指南了解基本功能。',
      tags: ['註冊', '新手', '開始']
    },
    {
      id: '2',
      category: 'analysis',
      question: 'AI 分析師的準確度如何？',
      answer: '我們的 AI 分析師基於大量歷史數據和實時市場信息進行分析，準確度約為 75-85%。但請注意，所有投資都有風險，AI 分析僅供參考，不構成投資建議。',
      tags: ['AI', '準確度', '分析']
    },
    {
      id: '3',
      category: 'portfolio',
      question: '如何創建和管理投資組合？',
      answer: '在投資組合頁面點擊「創建組合」，輸入組合名稱和描述，然後添加股票。您可以設置每隻股票的權重，系統會自動計算組合的整體表現和風險指標。',
      tags: ['投資組合', '創建', '管理']
    },
    {
      id: '4',
      category: 'subscription',
      question: '免費版和付費版有什麼區別？',
      answer: '免費版每日可進行 5 次分析，付費版無限制。付費版還包括高級分析師、實時監控、投資組合優化建議等功能。詳細比較請查看訂閱方案頁面。',
      tags: ['訂閱', '付費', '功能']
    },
    {
      id: '5',
      category: 'technical',
      question: '為什麼分析結果載入很慢？',
      answer: '分析速度取決於市場數據的複雜度和服務器負載。通常需要 10-30 秒。如果持續緩慢，請檢查網絡連接或聯繫技術支援。',
      tags: ['性能', '載入', '技術']
    },
    {
      id: '6',
      category: 'account',
      question: '如何修改個人資料？',
      answer: '點擊右上角頭像，選擇「個人設置」，在那裡您可以修改姓名、郵箱、密碼等信息。某些敏感信息修改可能需要郵箱驗證。',
      tags: ['個人資料', '設置', '修改']
    }
  ];

  const filteredFAQs = faqItems.filter(faq => {
    const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
    const matchesSearch = searchQuery === '' || 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesCategory && matchesSearch;
  });

  useEffect(() => {
    // 模擬載入
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const handleFAQToggle = (faqId: string) => {
    setExpandedFAQ(expandedFAQ === faqId ? null : faqId);
  };

  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setExpandedFAQ(null);
  };

  if (isLoading) {
    return (
      <div className="help-center-page">
        <div className="help-loading">
          <div className="loading-spinner"></div>
          <p>載入幫助中心...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="help-center-page">
      {/* 頁面標題 */}
      <div className="help-header">
        <div className="header-content">
          <h1 className="help-title">
            <span className="help-icon">❓</span>
            幫助中心
          </h1>
          <p className="help-subtitle">
            找到您需要的答案，快速解決問題
          </p>
        </div>
      </div>

      <div className="help-container">
        {/* 搜尋區域 */}
        <div className="help-search-section">
          <div className="search-container">
            <div className="search-input-wrapper">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="search-input"
                placeholder="搜尋問題、關鍵字..."
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
        </div>

        <div className="help-content">
          {/* 側邊欄 - 分類 */}
          <div className="help-sidebar">
            <div className="categories-section">
              <h3 className="section-title">分類</h3>
              <div className="category-list">
                <button
                  className={`category-item ${selectedCategory === 'all' ? 'active' : ''}`}
                  onClick={() => handleCategorySelect('all')}
                >
                  <span className="category-icon">📋</span>
                  <div className="category-info">
                    <span className="category-name">全部</span>
                    <span className="category-count">{faqItems.length}</span>
                  </div>
                </button>
                {helpCategories.map(category => (
                  <button
                    key={category.id}
                    className={`category-item ${selectedCategory === category.id ? 'active' : ''}`}
                    onClick={() => handleCategorySelect(category.id)}
                  >
                    <span className="category-icon">{category.icon}</span>
                    <div className="category-info">
                      <span className="category-name">{category.name}</span>
                      <span className="category-count">{category.articleCount}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* 快速連結 */}
            <div className="quick-links-section">
              <h3 className="section-title">快速連結</h3>
              <div className="quick-links">
                <a href="/contact" className="quick-link">
                  <span className="link-icon">📧</span>
                  聯繫客服
                </a>
                <a href="/feedback" className="quick-link">
                  <span className="link-icon">💬</span>
                  意見反饋
                </a>
                <a href="/status" className="quick-link">
                  <span className="link-icon">🟢</span>
                  系統狀態
                </a>
                <a href="/api-docs" className="quick-link">
                  <span className="link-icon">📚</span>
                  API 文檔
                </a>
              </div>
            </div>
          </div>

          {/* 主要內容 */}
          <div className="help-main">
            {/* 分類概覽 */}
            {selectedCategory === 'all' && searchQuery === '' && (
              <div className="categories-overview">
                <h2 className="overview-title">選擇一個分類開始</h2>
                <div className="categories-grid">
                  {helpCategories.map(category => (
                    <div
                      key={category.id}
                      className="category-card"
                      onClick={() => handleCategorySelect(category.id)}
                    >
                      <div className="card-icon">{category.icon}</div>
                      <h3 className="card-title">{category.name}</h3>
                      <p className="card-description">{category.description}</p>
                      <div className="card-meta">
                        <span className="article-count">{category.articleCount} 篇文章</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* FAQ 列表 */}
            {(selectedCategory !== 'all' || searchQuery !== '') && (
              <div className="faq-section">
                <div className="faq-header">
                  <h2 className="faq-title">
                    {selectedCategory !== 'all' 
                      ? helpCategories.find(c => c.id === selectedCategory)?.name 
                      : '搜尋結果'
                    }
                  </h2>
                  <p className="faq-count">找到 {filteredFAQs.length} 個結果</p>
                </div>

                {filteredFAQs.length === 0 ? (
                  <div className="no-results">
                    <div className="no-results-icon">🔍</div>
                    <h3>沒有找到相關結果</h3>
                    <p>嘗試使用不同的關鍵字或選擇其他分類</p>
                    <button
                      className="reset-search"
                      onClick={() => {
                        setSearchQuery('');
                        setSelectedCategory('all');
                      }}
                    >
                      重置搜尋
                    </button>
                  </div>
                ) : (
                  <div className="faq-list">
                    {filteredFAQs.map(faq => (
                      <div key={faq.id} className="faq-item">
                        <button
                          className={`faq-question ${expandedFAQ === faq.id ? 'expanded' : ''}`}
                          onClick={() => handleFAQToggle(faq.id)}
                          aria-expanded={expandedFAQ === faq.id}
                        >
                          <span className="question-text">{faq.question}</span>
                          <span className="expand-icon">
                            {expandedFAQ === faq.id ? '−' : '+'}
                          </span>
                        </button>
                        {expandedFAQ === faq.id && (
                          <div className="faq-answer">
                            <p>{faq.answer}</p>
                            <div className="faq-tags">
                              {faq.tags.map(tag => (
                                <span key={tag} className="faq-tag">{tag}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 底部聯繫區域 */}
        <div className="help-footer">
          <div className="footer-content">
            <div className="contact-section">
              <h3>還有問題？</h3>
              <p>如果您沒有找到需要的答案，我們的客服團隊隨時為您提供幫助。</p>
              <div className="contact-options">
                <a href="/contact" className="contact-button primary">
                  <span className="button-icon">💬</span>
                  聯繫客服
                </a>
                <a href="mailto:support@tradingagents.com" className="contact-button secondary">
                  <span className="button-icon">📧</span>
                  發送郵件
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpCenterPage;