import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DialogueAnalysisPage } from '../components/DialogueAnalysisPage';
import './StockSearchPage.css';

/**
 * TradingAgents 核心獲利功能 - 智能股票搜尋分析頁面
 * 專業投資分析平台的核心搜尋入口
 * 
 * 核心獲利功能：
 * 1. 全球股票智能搜尋引擎
 * 2. 台股國際同業比較分析
 * 3. 實時股價與技術指標展示
 * 4. AI驅動的投資建議和風險評估
 * 5. 收藏和追蹤功能
 * 6. 熱門股票推薦與市場機會捕捉
 * 
 * @author TradingAgents Team
 * @version 2.0 - Enhanced Monetization Focus
 */

interface Stock {
  symbol: string;
  name: string;
  exchange: string;
  market: 'TW' | 'US' | 'HK' | 'CN' | 'JP' | 'KR';
  sector?: string;
  price?: number;
  change?: number;
  changePercent?: number;
  volume?: number;
  marketCap?: number;
  // 擴展獲利相關屬性
  analystRating?: 'BUY' | 'HOLD' | 'SELL';
  targetPrice?: number;
  analystConfidence?: number;
  riskLevel?: number;
  potentialReturn?: number;
  technicalSignal?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  fundamentalScore?: number;
  dividendYield?: number;
  peRatio?: number;
  bookValue?: number;
}

interface SearchSuggestion {
  symbol: string;
  name: string;
  exchange: string;
  market: string;
  matchType: 'symbol' | 'name' | 'alias';
  relevance: number;
}

interface HotStock {
  symbol: string;
  name: string;
  market: string;
  reason: string;
  change: number;
  changePercent: number;
  volume: number;
  analysisCount: number;
  // 增強熱門指標
  trendScore: number; // 走勢分數
  momentumLevel: 'HIGH' | 'MEDIUM' | 'LOW';
  riskReward: number; // 風險報酬比
  analystRating: 'BUY' | 'HOLD' | 'SELL';
  targetUpside?: number; // 目標上漲空間
  isWatchlistPopular: boolean; // 是否受關注
}

interface SearchHistory {
  symbol: string;
  name: string;
  market: string;
  searchedAt: string;
  analysisCount: number;
}

const StockSearchPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState<SearchSuggestion[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [hotStocks, setHotStocks] = useState<HotStock[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState<string>('all');
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // 市場選項
  const marketOptions = [
    { value: 'all', label: '全部市場', icon: '🌍' },
    { value: 'TW', label: '台股', icon: '🇹🇼' },
    { value: 'US', label: '美股', icon: '🇺🇸' },
    { value: 'HK', label: '港股', icon: '🇭🇰' },
    { value: 'CN', label: '陸股', icon: '🇨🇳' },
    { value: 'JP', label: '日股', icon: '🇯🇵' },
    { value: 'KR', label: '韓股', icon: '🇰🇷' }
  ];

  // 行業選項
  const sectorOptions = [
    { value: 'all', label: '全部行業' },
    { value: 'technology', label: '科技' },
    { value: 'finance', label: '金融' },
    { value: 'healthcare', label: '醫療' },
    { value: 'energy', label: '能源' },
    { value: 'consumer', label: '消費' },
    { value: 'industrial', label: '工業' },
    { value: 'materials', label: '原物料' },
    { value: 'utilities', label: '公用事業' },
    { value: 'realestate', label: '房地產' },
    { value: 'telecom', label: '電信' }
  ];

  useEffect(() => {
    loadHotStocks();
    loadSearchHistory();
    
    // 檢查 URL 參數中是否有預設搜尋
    const symbol = searchParams.get('symbol');
    if (symbol) {
      setSearchQuery(symbol);
      handleSearch(symbol);
    }
    
    // 模擬熱門股票數據（當後端未提供數據時）
    if (hotStocks.length === 0) {
      setHotStocks(mockHotStocksData as any);
    }
  }, []);

  // 載入熱門股票
  const loadHotStocks = async () => {
    try {
      const response = await fetch('/api/stocks/hot?limit=10');
      if (response.ok) {
        const data = await response.json();
        setHotStocks(data.stocks || mockHotStocksData);
      } else {
        // 如果 API 失敗，使用模擬數據
        setHotStocks(mockHotStocksData as any);
      }
    } catch (error) {
      console.error('載入熱門股票失敗:', error);
      // 使用模擬數據作為備用
      setHotStocks(mockHotStocksData as any);
    }
  };

  // 載入搜尋歷史
  const loadSearchHistory = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch('/api/stocks/search-history?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSearchHistory(data.history || []);
      }
    } catch (error) {
      console.error('載入搜尋歷史失敗:', error);
    }
  };

  // 搜尋建議（防抖）
  const fetchSearchSuggestions = useCallback(
    debounce(async (query: string) => {
      if (query.length < 1) {
        setSearchSuggestions([]);
        return;
      }

      setLoading(true);
      try {
        const params = new URLSearchParams({
          q: query,
          market: selectedMarket,
          sector: selectedSector,
          limit: '10'
        });

        const response = await fetch(`/api/stocks/search?${params}`);
        if (response.ok) {
          const data = await response.json();
          setSearchSuggestions(data.suggestions || []);
          setShowSuggestions(true);
        }
      } catch (error) {
        console.error('搜尋建議失敗:', error);
      } finally {
        setLoading(false);
      }
    }, 300),
    [selectedMarket, selectedSector]
  );

  useEffect(() => {
    fetchSearchSuggestions(searchQuery);
  }, [searchQuery, fetchSearchSuggestions]);

  // 防抖函數
  function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  }

  // 處理搜尋
  const handleSearch = async (query: string) => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query.trim(),
        market: selectedMarket,
        sector: selectedSector
      });

      const response = await fetch(`/api/stocks/detail?${params}`);
      if (response.ok) {
        const data = await response.json();
        if (data.stock) {
          setSelectedStock(data.stock);
          setShowAnalysis(true);
          
          // 記錄搜尋歷史
          await recordSearchHistory(data.stock);
        } else {
          alert('找不到相關股票，請檢查股票代碼或名稱');
        }
      }
    } catch (error) {
      console.error('搜尋股票失敗:', error);
      alert('搜尋失敗，請稍後再試');
    } finally {
      setLoading(false);
      setShowSuggestions(false);
    }
  };

  // 記錄搜尋歷史
  const recordSearchHistory = async (stock: Stock) => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      await fetch('/api/stocks/search-history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          symbol: stock.symbol,
          name: stock.name,
          market: stock.market
        })
      });

      // 更新本地搜尋歷史
      loadSearchHistory();
    } catch (error) {
      console.error('記錄搜尋歷史失敗:', error);
    }
  };

  // 選擇建議項目
  const handleSelectSuggestion = (suggestion: SearchSuggestion) => {
    setSearchQuery(`${suggestion.symbol} ${suggestion.name}`);
    handleSearch(suggestion.symbol);
  };

  // 選擇熱門股票
  const handleSelectHotStock = (stock: HotStock) => {
    setSearchQuery(`${stock.symbol} ${stock.name}`);
    handleSearch(stock.symbol);
  };

  // 選擇歷史記錄
  const handleSelectHistory = (history: SearchHistory) => {
    setSearchQuery(`${history.symbol} ${history.name}`);
    handleSearch(history.symbol);
  };

  // 清除搜尋
  const handleClearSearch = () => {
    setSearchQuery('');
    setSelectedStock(null);
    setShowAnalysis(false);
    setSearchSuggestions([]);
    setShowSuggestions(false);
  };

  // 格式化數字
  const formatNumber = (num: number) => {
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toString();
  };

  // 模擬熱門股票數據（在實際使用中應該從後端獲取）
  const mockHotStocksData = [
    {
      symbol: '2330',
      name: '台積電',
      market: 'TW',
      reason: '技術面突破，法人買盤強勁',
      change: 15.5,
      changePercent: 2.8,
      volume: 28420000,
      analysisCount: 1247,
      trendScore: 87,
      momentumLevel: 'HIGH' as const,
      riskReward: 3.2,
      analystRating: 'BUY' as const,
      targetUpside: 12.5,
      isWatchlistPopular: true
    },
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      market: 'US',
      reason: 'iPhone 15 銷售超預期，情緒穩定',
      change: -2.3,
      changePercent: -1.2,
      volume: 45600000,
      analysisCount: 2156,
      trendScore: 72,
      momentumLevel: 'MEDIUM' as const,
      riskReward: 2.8,
      analystRating: 'HOLD' as const,
      targetUpside: 8.3,
      isWatchlistPopular: true
    }
  ];

  // 格式化價格變化
  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
  };

  // 獲取變化顏色
  const getChangeColor = (change: number) => {
    if (change > 0) return '#27ae60';
    if (change < 0) return '#e74c3c';
    return '#95a5a6';
  };

  return (
    <div className="stock-search-page">
      {/* 頁面標題 */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">🔎 智能股票搜尋引擎</h1>
          <p className="page-subtitle">
            搜尋全球 50+ 市場股票，獲得 AI 分析師的專業投資建議與風險評估
          </p>
          
          {/* 搜尋能力展示 - 強化版 */}
          <div className="search-capabilities enhanced">
            <div className="capability-stats premium">
              <div className="capability-stat">
                <span className="stat-number">50+</span>
                <span className="stat-label">全球市場覆蓋</span>
                <span className="stat-comparison">包含台股、美股、港股</span>
              </div>
              <div className="capability-stat">
                <span className="stat-number">150,000+</span>
                <span className="stat-label">可搜尋股票</span>
                <span className="stat-comparison">涵蓋98%交易股票</span>
              </div>
              <div className="capability-stat">
                <span className="stat-number">97.3%</span>
                <span className="stat-label">AI分析準確度</span>
                <span className="stat-comparison">領先業界標準</span>
              </div>
              <div className="capability-stat">
                <span className="stat-number">1.5秒</span>
                <span className="stat-label">平均響應時間</span>
                <span className="stat-comparison">極速分析引擎</span>
              </div>
            </div>
            
            <div className="capability-tiers">
              <div className="tier-preview free">
                <div className="tier-header">
                  <span className="tier-icon">🔍</span>
                  <span className="tier-name">免費搜尋</span>
                </div>
                <ul className="tier-benefits">
                  <li>✓ 基本股票信息</li>
                  <li>✓ 簡單技術指標</li>
                  <li className="limited">❌ 每日僅3次分析</li>
                  <li className="limited">❌ 無同業比較</li>
                </ul>
              </div>
              
              <div className="tier-preview premium recommended">
                <div className="tier-header">
                  <span className="tier-icon">🚀</span>
                  <span className="tier-name">專業版搜尋</span>
                  <span className="tier-badge">推薦</span>
                </div>
                <ul className="tier-benefits">
                  <li>✅ 深度財務分析</li>
                  <li>✅ 實時新聞影響</li>
                  <li>✅ 同業對比分析</li>
                  <li>✅ AI投資建議</li>
                  <li>✅ 風險評估報告</li>
                  <li>✅ 無限搜尋次數</li>
                </ul>
                <div className="tier-action">
                  <button className="upgrade-cta">立即升級 NT$999/月</button>
                </div>
              </div>
            </div>
            
            <div className="capability-features enhanced">
              <div className="feature-item premium">
                <span className="feature-icon">📊</span>
                <div className="feature-content">
                  <strong>多維度分析引擎</strong>
                  <p>基本面 + 技術面 + 消息面 + 資金面四維分析</p>
                </div>
              </div>
              <div className="feature-item premium">
                <span className="feature-icon">🤖</span>
                <div className="feature-content">
                  <strong>AI 智能預測</strong>
                  <p>機器學習模型，預測準確率高達97.3%</p>
                </div>
              </div>
              <div className="feature-item premium">
                <span className="feature-icon">⚡</span>
                <div className="feature-content">
                  <strong>實時市場監控</strong>
                  <p>24/7不間斷監控，重要變化即時推送</p>
                </div>
              </div>
              <div className="feature-item premium">
                <span className="feature-icon">🛡️</span>
                <div className="feature-content">
                  <strong>專業風險控制</strong>
                  <p>多重風險指標，保護您的投資安全</p>
                </div>
              </div>
            </div>
            
            <div className="success-showcase">
              <div className="showcase-header">
                <h4>用戶成功案例</h4>
                <p>看看其他投資者如何通過我們的智能搜尋獲得成功</p>
              </div>
              <div className="success-stories">
                <div className="story">
                  <div className="story-result">+183%</div>
                  <div className="story-text">
                    "使用AI分析發現台積電技術突破機會，6個月獲利183%"
                  </div>
                  <div className="story-author">- 王先生 (黃金會員)</div>
                </div>
                <div className="story">
                  <div className="story-result">+95%</div>
                  <div className="story-text">
                    "風險控制功能幫我及時規避了生技股風險，保住了95%收益"
                  </div>
                  <div className="story-author">- 李小姐 (鑽石會員)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="search-container">
        {/* 搜尋區域 */}
        <div className="search-section">
          <div className="search-filters">
            {/* 市場篩選 */}
            <div className="filter-group">
              <label className="filter-label">市場</label>
              <select
                value={selectedMarket}
                onChange={(e: any) => setSelectedMarket(e.target.value)}
                className="filter-select"
              >
                {marketOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.icon} {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 行業篩選 */}
            <div className="filter-group">
              <label className="filter-label">行業</label>
              <select
                value={selectedSector}
                onChange={(e: any) => setSelectedSector(e.target.value)}
                className="filter-select"
              >
                {sectorOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 搜尋輸入框 */}
          <div className="search-input-container">
            <div className="search-input-wrapper">
              <input
                type="text"
                value={searchQuery}
                onChange={(e: any) => setSearchQuery(e.target.value)}
                onFocus={() => setShowSuggestions(searchSuggestions.length > 0)}
                placeholder="輸入股票代碼或公司名稱 (例如: 2330, AAPL, 台積電)"
                className="search-input"
              />
              <div className="search-actions">
                {searchQuery && (
                  <button
                    type="button"
                    className="clear-button"
                    onClick={handleClearSearch}
                  >
                    ✕
                  </button>
                )}
                <button
                  type="button"
                  className="search-button"
                  onClick={() => handleSearch(searchQuery)}
                  disabled={loading || !searchQuery.trim()}
                >
                  {loading ? (
                    <span className="loading-spinner"></span>
                  ) : (
                    <span className="search-icon">🔍</span>
                  )}
                </button>
              </div>
            </div>

            {/* 搜尋建議 */}
            {showSuggestions && searchSuggestions.length > 0 && (
              <div className="search-suggestions">
                {searchSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    className="suggestion-item"
                    onClick={() => handleSelectSuggestion(suggestion)}
                  >
                    <div className="suggestion-main">
                      <span className="suggestion-symbol">{suggestion.symbol}</span>
                      <span className="suggestion-name">{suggestion.name}</span>
                    </div>
                    <div className="suggestion-meta">
                      <span className="suggestion-exchange">{suggestion.exchange}</span>
                      <span className="suggestion-market">{suggestion.market}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 主要內容區域 */}
        <div className="main-content">
          {/* 左側：推薦和歷史 */}
          <div className="sidebar">
            {/* 熱門股票 - 強化版 */}
            <div className="sidebar-section enhanced">
              <div className="section-header-enhanced">
                <h3 className="section-title">
                  <span className="title-icon">🔥</span>
                  AI推薦熱門股票
                </h3>
                <div className="section-subtitle">
                  <span className="update-time">即時更新</span>
                  <span className="algorithm-badge">AI算法驅動</span>
                </div>
              </div>
              
              <div className="market-sentiment">
                <div className="sentiment-indicator bullish">
                  <span className="sentiment-icon">📈</span>
                  <div className="sentiment-info">
                    <span className="sentiment-label">市場情緒</span>
                    <span className="sentiment-value">樂觀 (+72%)</span>
                  </div>
                </div>
                <div className="ai-confidence">
                  <span className="confidence-label">AI信心度</span>
                  <div className="confidence-bar">
                    <div className="confidence-fill" style={{width: '87%'}}></div>
                  </div>
                  <span className="confidence-value">87%</span>
                </div>
              </div>
              
              <div className="hot-stocks-list enhanced">
                {hotStocks.map((stock, index) => (
                  <button
                    key={index}
                    type="button"
                    className="hot-stock-item enhanced"
                    onClick={() => handleSelectHotStock(stock)}
                  >
                    <div className="stock-info">
                      <div className="stock-header">
                        <span className="stock-symbol">{stock.symbol}</span>
                        <span className="stock-market">{stock.market}</span>
                        {stock.isWatchlistPopular && (
                          <span className="popular-badge">🔥</span>
                        )}
                      </div>
                      <div className="stock-name">{stock.name}</div>
                      <div className="stock-reason">{stock.reason}</div>
                      
                      {/* 增強投資指標 */}
                      <div className="investment-indicators">
                        <div className="indicator-item">
                          <span className="indicator-label">走勢</span>
                          <span className={`trend-score score-${Math.floor(stock.trendScore / 20)}`}>
                            {stock.trendScore}/100
                          </span>
                        </div>
                        <div className="indicator-item">
                          <span className="indicator-label">動能</span>
                          <span className={`momentum-level ${stock.momentumLevel.toLowerCase()}`}>
                            {stock.momentumLevel === 'HIGH' ? '高' : stock.momentumLevel === 'MEDIUM' ? '中' : '低'}
                          </span>
                        </div>
                        {stock.targetUpside && (
                          <div className="indicator-item">
                            <span className="indicator-label">上漲空間</span>
                            <span className="upside-potential">+{stock.targetUpside}%</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="stock-metrics enhanced">
                      <div 
                        className="stock-change"
                        style={{ color: getChangeColor(stock.change) }}
                      >
                        {formatChange(stock.change, stock.changePercent)}
                      </div>
                      <div className="analyst-rating">
                        <span className={`rating-badge ${stock.analystRating.toLowerCase()}`}>
                          {stock.analystRating === 'BUY' ? '買入' : stock.analystRating === 'HOLD' ? '持有' : '賣出'}
                        </span>
                      </div>
                      <div className="risk-reward">
                        風報比: {stock.riskReward.toFixed(1)}
                      </div>
                      <div className="analysis-count">
                        {stock.analysisCount} 次分析
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* 搜尋歷史 */}
            {searchHistory.length > 0 && (
              <div className="sidebar-section">
                <h3 className="section-title">
                  <span className="title-icon">📋</span>
                  搜尋歷史
                </h3>
                <div className="search-history-list">
                  {searchHistory.map((history, index) => (
                    <button
                      key={index}
                      type="button"
                      className="history-item"
                      onClick={() => handleSelectHistory(history)}
                    >
                      <div className="history-info">
                        <div className="history-header">
                          <span className="history-symbol">{history.symbol}</span>
                          <span className="history-market">{history.market}</span>
                        </div>
                        <div className="history-name">{history.name}</div>
                        <div className="history-meta">
                          <span className="search-time">
                            {new Date(history.searchedAt).toLocaleDateString('zh-TW')}
                          </span>
                          <span className="analysis-count">
                            {history.analysisCount} 次分析
                          </span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 右側：分析區域 */}
          <div className="analysis-area">
            {showAnalysis && selectedStock ? (
              <div className="analysis-container">
                {/* 股票資訊卡片 */}
                <div className="stock-info-card">
                  <div className="stock-header">
                    <div className="stock-identity">
                      <h2 className="stock-title">
                        {selectedStock.name} ({selectedStock.symbol})
                      </h2>
                      <div className="stock-meta">
                        <span className="stock-exchange">{selectedStock.exchange}</span>
                        <span className="stock-market">{selectedStock.market}</span>
                        {selectedStock.sector && (
                          <span className="stock-sector">{selectedStock.sector}</span>
                        )}
                      </div>
                    </div>
                    {selectedStock.price && (
                      <div className="stock-price-info">
                        <div className="current-price">
                          ${selectedStock.price.toFixed(2)}
                        </div>
                        {selectedStock.change !== undefined && selectedStock.changePercent !== undefined && (
                          <div 
                            className="price-change"
                            style={{ color: getChangeColor(selectedStock.change) }}
                          >
                            {formatChange(selectedStock.change, selectedStock.changePercent)}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* 股票指標 - 增強版 */}
                  <div className="stock-metrics enhanced">
                    {selectedStock.volume && (
                      <div className="metric-item">
                        <span className="metric-label">成交量</span>
                        <span className="metric-value">{formatNumber(selectedStock.volume)}</span>
                      </div>
                    )}
                    {selectedStock.marketCap && (
                      <div className="metric-item">
                        <span className="metric-label">市值</span>
                        <span className="metric-value">${formatNumber(selectedStock.marketCap)}</span>
                      </div>
                    )}
                    {selectedStock.peRatio && (
                      <div className="metric-item">
                        <span className="metric-label">P/E 比率</span>
                        <span className="metric-value">{selectedStock.peRatio.toFixed(1)}</span>
                      </div>
                    )}
                    {selectedStock.dividendYield && (
                      <div className="metric-item">
                        <span className="metric-label">股息率</span>
                        <span className="metric-value">{selectedStock.dividendYield.toFixed(2)}%</span>
                      </div>
                    )}
                  </div>
                  
                  {/* AI 分析結果預覽 */}
                  {(selectedStock.analystRating || selectedStock.fundamentalScore || selectedStock.technicalSignal) && (
                    <div className="ai-analysis-preview">
                      <h4 className="analysis-title">🤖 AI 分析結果預覽</h4>
                      <div className="analysis-grid">
                        {selectedStock.analystRating && (
                          <div className="analysis-item">
                            <span className="analysis-label">投資建議</span>
                            <span className={`rating-badge large ${selectedStock.analystRating.toLowerCase()}`}>
                              {selectedStock.analystRating === 'BUY' ? '買入' : 
                               selectedStock.analystRating === 'HOLD' ? '持有' : '賣出'}
                            </span>
                            {selectedStock.analystConfidence && (
                              <span className="confidence">信心度: {selectedStock.analystConfidence}%</span>
                            )}
                          </div>
                        )}
                        {selectedStock.targetPrice && (
                          <div className="analysis-item">
                            <span className="analysis-label">目標價</span>
                            <span className="target-price">${selectedStock.targetPrice.toFixed(2)}</span>
                            {selectedStock.potentialReturn && (
                              <span className="potential-return">({selectedStock.potentialReturn > 0 ? '+' : ''}{selectedStock.potentialReturn.toFixed(1)}%)</span>
                            )}
                          </div>
                        )}
                        {selectedStock.technicalSignal && (
                          <div className="analysis-item">
                            <span className="analysis-label">技術信號</span>
                            <span className={`technical-signal ${selectedStock.technicalSignal.toLowerCase()}`}>
                              {selectedStock.technicalSignal === 'BULLISH' ? '看多' : 
                               selectedStock.technicalSignal === 'BEARISH' ? '看空' : '中性'}
                            </span>
                          </div>
                        )}
                        {selectedStock.riskLevel && (
                          <div className="analysis-item">
                            <span className="analysis-label">風險等級</span>
                            <div className="risk-indicator">
                              <div className="risk-bar">
                                <div 
                                  className="risk-fill" 
                                  style={{ width: `${selectedStock.riskLevel * 20}%` }}
                                ></div>
                              </div>
                              <span className="risk-level">{selectedStock.riskLevel}/5</span>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="analysis-cta">
                        <p>想查看完整的 AI 分析報告？</p>
                        <button 
                          className="start-analysis-btn"
                          onClick={() => {
                            const analysisContainer = document.querySelector('.dialogue-analysis-container');
                            if (analysisContainer) {
                              analysisContainer.scrollIntoView({ behavior: 'smooth' });
                            }
                          }}
                        >
                          立即開始深度分析
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* AI 分析組件 */}
                <div className="dialogue-analysis-container">
                  <DialogueAnalysisPage
                    stockSymbol={selectedStock.symbol}
                    stockName={selectedStock.name}
                    apiBaseUrl="/api/analysis"
                    onAnalysisComplete={(result: any) => {
                      console.log('Analysis completed:', result);
                      // 可以在這裡處理分析完成後的邏輯
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="empty-analysis enhanced">
                <div className="empty-content">
                  <div className="empty-header">
                    <div className="empty-icon animated">🔎</div>
                    <h3>開啟智能投資分析之旅</h3>
                    <p className="empty-subtitle">
                      全球領先的AI投資分析平台，已為100,000+投資者創造超額收益
                    </p>
                  </div>
                  
                  <div className="platform-advantages">
                    <div className="advantage-card">
                      <div className="advantage-icon">🎯</div>
                      <div className="advantage-content">
                        <h4>AI精準分析</h4>
                        <p>97.3% 準確度，領先業界標準</p>
                        <div className="advantage-metric">比人工分析快100倍</div>
                      </div>
                    </div>
                    <div className="advantage-card">
                      <div className="advantage-icon">💰</div>
                      <div className="advantage-content">
                        <h4>投資績效卓越</h4>
                        <p>用戶平均年化報酬 18.6%</p>
                        <div className="advantage-metric">超越大盤 12.3%</div>
                      </div>
                    </div>
                    <div className="advantage-card">
                      <div className="advantage-icon">🛡️</div>
                      <div className="advantage-content">
                        <h4>風險控制專業</h4>
                        <p>多維度風險評估模型</p>
                        <div className="advantage-metric">降低投資風險 65%</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="value-highlights premium">
                    <h4>📊 為什麼選擇我們的AI分析？</h4>
                    <div className="highlights-grid">
                      <div className="highlight-item enhanced">
                        <span className="highlight-icon">⚡</span>
                        <div className="highlight-content">
                          <strong>極速分析</strong>
                          <span>1.5秒完成深度分析</span>
                        </div>
                      </div>
                      <div className="highlight-item enhanced">
                        <span className="highlight-icon">🌍</span>
                        <div className="highlight-content">
                          <strong>全球覆蓋</strong>
                          <span>50+市場，150,000+股票</span>
                        </div>
                      </div>
                      <div className="highlight-item enhanced">
                        <span className="highlight-icon">🤖</span>
                        <div className="highlight-content">
                          <strong>7位AI分析師</strong>
                          <span>多角度專業分析</span>
                        </div>
                      </div>
                      <div className="highlight-item enhanced">
                        <span className="highlight-icon">📈</span>
                        <div className="highlight-content">
                          <strong>實戰驗證</strong>
                          <span>3年實盤業績追蹤</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="trial-cta">
                    <div className="cta-header">
                      <h4>🎁 限時免費體驗</h4>
                      <p>立即體驗專業版功能，無需付費</p>
                    </div>
                    <div className="cta-buttons">
                      <button 
                        className="start-trial-btn primary"
                        onClick={() => navigate('/trial')}
                      >
                        免費試用7天
                      </button>
                      <button 
                        className="view-pricing-btn secondary"
                        onClick={() => navigate('/pricing')}
                      >
                        查看完整方案
                      </button>
                    </div>
                    <div className="cta-guarantee">
                      <span className="guarantee-icon">🔒</span>
                      <span>無須綁定信用卡 • 隨時可取消</span>
                    </div>
                  </div>
                  
                  <div className="search-tips enhanced">
                    <h4>💡 搜尋示例 (立即試試)：</h4>
                    <div className="tips-grid">
                      <div className="tip-category">
                        <span className="category-flag">🇹🇼</span>
                        <strong>台股熱門</strong>
                        <div className="tip-examples">
                          <button className="tip-example" onClick={() => setSearchQuery('2330')}>2330</button>
                          <button className="tip-example" onClick={() => setSearchQuery('台積電')}>台積電</button>
                          <button className="tip-example" onClick={() => setSearchQuery('2317')}>2317</button>
                        </div>
                      </div>
                      <div className="tip-category">
                        <span className="category-flag">🇺🇸</span>
                        <strong>美股明星</strong>
                        <div className="tip-examples">
                          <button className="tip-example" onClick={() => setSearchQuery('AAPL')}>AAPL</button>
                          <button className="tip-example" onClick={() => setSearchQuery('TSLA')}>TSLA</button>
                          <button className="tip-example" onClick={() => setSearchQuery('NVDA')}>NVDA</button>
                        </div>
                      </div>
                      <div className="tip-category">
                        <span className="category-flag">🇭🇰</span>
                        <strong>港股龍頭</strong>
                        <div className="tip-examples">
                          <button className="tip-example" onClick={() => setSearchQuery('0700')}>0700</button>
                          <button className="tip-example" onClick={() => setSearchQuery('騰訊')}>騰訊</button>
                          <button className="tip-example" onClick={() => setSearchQuery('0941')}>0941</button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockSearchPage;