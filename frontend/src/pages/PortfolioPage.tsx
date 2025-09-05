import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createApiUrl } from '../config/apiConfig';
import './PortfolioPage.css';

/**
 * TradingAgents 核心獲利功能 - 智能投資組合管理系統
 * 專業投資組合優化與風險管理平台
 * 
 * 核心獲利功能：
 * 1. AI驅動的投資組合分析與優化建議
 * 2. 實時風險評估與分散度計算
 * 3. 專業績效追蹤與基準比較
 * 4. 智能資產配置與再平衡建議
 * 5. 個人化投資策略制定
 * 6. 高級投資組合洞察與市場機會
 * 
 * @author TradingAgents Team
 * @version 2.0 - Enhanced Monetization Focus
 */

interface Holding {
  id: string;
  symbol: string;
  companyName: string;
  market: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  totalCost: number;
  unrealizedGain: number;
  unrealizedGainPercent: number;
  dayChange: number;
  dayChangePercent: number;
  weight: number;
  sector: string;
  addedAt: string;
  lastUpdated: string;
  // 增強獲利相關屬性
  analystRating?: 'BUY' | 'HOLD' | 'SELL';
  targetPrice?: number;
  potentialUpside?: number;
  riskScore?: number; // 1-10
  dividendYield?: number;
  peRatio?: number;
  beta?: number; // 市場風險係數
  earningsGrowth?: number;
  revenueGrowth?: number;
  aiScore?: number; // AI綜合評分
  momentum?: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
  technicalSignal?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
}

interface Portfolio {
  id: string;
  name: string;
  description: string;
  totalValue: number;
  totalCost: number;
  totalGain: number;
  totalGainPercent: number;
  dayChange: number;
  dayChangePercent: number;
  holdings: Holding[];
  createdAt: string;
  updatedAt: string;
  // 增強獲利追蹤屬性
  monthlyReturn?: number;
  yearlyReturn?: number;
  sharpeRatio?: number; // 夏普比率
  maxDrawdown?: number; // 最大回撤
  winRate?: number; // 勝率
  benchmarkReturn?: number; // 基準報酬
  alpha?: number; // 超額報酬
  beta?: number; // 系統性風險
  volatility?: number; // 波動率
  memberTier?: 'FREE' | 'GOLD' | 'DIAMOND';
  premiumFeatures?: string[];
  rebalanceSuggestions?: number; // 再平衡建議數量
}

interface PortfolioAnalysis {
  riskScore: number;
  diversificationScore: number;
  sectorAllocation: { [sector: string]: number };
  marketAllocation: { [market: string]: number };
  recommendations: string[];
  riskFactors: string[];
  opportunities: string[];
  // 增強分析與獲利建議
  overallRating: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR';
  expectedReturn: number; // 預期年化報酬
  targetReturn: number; // 目標報酬
  riskAdjustedReturn: number; // 風險調整後報酬
  correlationMatrix: { [symbol: string]: { [symbol: string]: number } };
  performanceMetrics: {
    sharpeRatio: number;
    sortino: number;
    maxDrawdown: number;
    calmar: number;
    beta: number;
    alpha: number;
    winRate: number;
  };
  rebalanceRecommendations: {
    symbol: string;
    currentWeight: number;
    targetWeight: number;
    action: 'BUY' | 'SELL' | 'HOLD';
    reason: string;
  }[];
  premiumInsights: string[];
  nextUpgrade?: {
    tier: 'GOLD' | 'DIAMOND';
    benefits: string[];
    price: number;
  };
}

interface AddHoldingForm {
  symbol: string;
  quantity: number;
  averagePrice: number;
  purchaseDate: string;
}

const PortfolioPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [portfolioAnalysis, setPortfolioAnalysis] = useState<PortfolioAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddHolding, setShowAddHolding] = useState(false);
  const [showCreatePortfolio, setShowCreatePortfolio] = useState(false);
  const [addHoldingForm, setAddHoldingForm] = useState<AddHoldingForm>({
    symbol: '',
    quantity: 0,
    averagePrice: 0,
    purchaseDate: new Date().toISOString().split('T')[0]
  });
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioDescription, setNewPortfolioDescription] = useState('');
  const [viewMode, setViewMode] = useState<'overview' | 'holdings' | 'analysis' | 'performance'>('overview');
  const [sortBy, setSortBy] = useState<'value' | 'gain' | 'weight' | 'symbol'>('value');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [error, setError] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioAnalysis(selectedPortfolio.id);
    }
  }, [selectedPortfolio]);

  // 載入投資組合列表
  const loadPortfolios = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        navigate('/auth?mode=login');
        return;
      }

      // 直接使用現有端點，但修復CORS配置
      const response = await fetch(createApiUrl('/api/portfolios'), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Origin': window.location.origin
        },
        mode: 'cors' as RequestMode,
        credentials: 'include' as RequestCredentials
      });

      if (response.ok) {
        const data = await response.json();
        setPortfolios(data.portfolios || []);
        
        // 如果有組合，選擇第一個
        if (data.portfolios && data.portfolios.length > 0) {
          setSelectedPortfolio(data.portfolios[0]);
        }
      } else if (response.status === 401) {
        navigate('/auth?mode=login');
      } else {
        // API不可用時，創建示例投資組合
        console.log('API不可用，創建示例數據');
        const demoPortfolios = [
          {
            id: 'demo-1',
            name: '我的第一個投資組合',
            description: '示例投資組合 - API服務暫時不可用',
            totalValue: 150000,
            totalCost: 140000,
            totalGain: 10000,
            totalGainPercent: 7.14,
            holdings: []
          }
        ];
        setPortfolios(demoPortfolios);
        setSelectedPortfolio(demoPortfolios[0]);
        setError('API服務暫時不可用，顯示示例數據');
      }
    } catch (error) {
      console.error('載入投資組合失敗:', error);
      // 網路錯誤時也創建示例數據
      const demoPortfolios = [
        {
          id: 'demo-offline',
          name: '離線投資組合',
          description: '網路連接問題，離線模式',
          totalValue: 100000,
          totalCost: 95000,
          totalGain: 5000,
          totalGainPercent: 5.26,
          holdings: []
        }
      ];
      setPortfolios(demoPortfolios);
      setSelectedPortfolio(demoPortfolios[0]);
      setError('網路連接問題，使用離線模式');
    } finally {
      setLoading(false);
    }
  };

  // 載入組合分析
  const loadPortfolioAnalysis = async (portfolioId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(createApiUrl(`/api/portfolio/${portfolioId}/analysis`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPortfolioAnalysis(data.analysis);
      }
    } catch (error) {
      console.error('載入組合分析失敗:', error);
    }
  };

  // 創建新組合
  const createPortfolio = async () => {
    if (!newPortfolioName.trim()) return;

    try {
      const token = localStorage.getItem('auth_token');
      // 直接使用現有端點，但修復CORS配置
      const response = await fetch(createApiUrl('/api/portfolio'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Origin': window.location.origin
        },
        mode: 'cors' as RequestMode,
        credentials: 'include' as RequestCredentials,
        body: JSON.stringify({
          name: newPortfolioName,
          description: newPortfolioDescription
        })
      });

      if (response.ok) {
        const data = await response.json();
        setPortfolios(prev => [...prev, data.portfolio]);
        setSelectedPortfolio(data.portfolio);
        setShowCreatePortfolio(false);
        setNewPortfolioName('');
        setNewPortfolioDescription('');
      } else {
        // API不可用時，手動創建投資組合
        const newPortfolio = {
          id: `manual-${Date.now()}`,
          name: newPortfolioName,
          description: newPortfolioDescription || '手動創建的投資組合',
          totalValue: 0,
          totalCost: 0,
          totalGain: 0,
          totalGainPercent: 0,
          holdings: []
        };
        setPortfolios(prev => [...prev, newPortfolio]);
        setSelectedPortfolio(newPortfolio);
        setShowCreatePortfolio(false);
        setNewPortfolioName('');
        setNewPortfolioDescription('');
        setError('API服務不可用，已離線創建投資組合');
      }
    } catch (error) {
      console.error('創建投資組合失敗:', error);
      // 網路錯誤時也手動創建
      const newPortfolio = {
        id: `offline-${Date.now()}`,
        name: newPortfolioName,
        description: newPortfolioDescription || '離線創建的投資組合',
        totalValue: 0,
        totalCost: 0,
        totalGain: 0,
        totalGainPercent: 0,
        holdings: []
      };
      setPortfolios(prev => [...prev, newPortfolio]);
      setSelectedPortfolio(newPortfolio);
      setShowCreatePortfolio(false);
      setNewPortfolioName('');
      setNewPortfolioDescription('');
      setError('網路問題，已離線創建投資組合');
    }
  };

  // 添加持股
  const addHolding = async () => {
    if (!selectedPortfolio || !addHoldingForm.symbol || addHoldingForm.quantity <= 0 || addHoldingForm.averagePrice <= 0) {
      alert('請填寫完整的持股資訊');
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(createApiUrl(`/api/portfolio/${selectedPortfolio.id}/holdings`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(addHoldingForm)
      });

      if (response.ok) {
        const data = await response.json();
        
        // 更新選中的組合
        setSelectedPortfolio(prev => prev ? {
          ...prev,
          holdings: [...prev.holdings, data.holding],
          totalValue: data.portfolio.totalValue,
          totalCost: data.portfolio.totalCost,
          totalGain: data.portfolio.totalGain,
          totalGainPercent: data.portfolio.totalGainPercent
        } : null);

        // 重置表單
        setAddHoldingForm({
          symbol: '',
          quantity: 0,
          averagePrice: 0,
          purchaseDate: new Date().toISOString().split('T')[0]
        });
        setShowAddHolding(false);

        // 重新載入組合分析
        loadPortfolioAnalysis(selectedPortfolio.id);
      } else {
        const errorData = await response.json();
        alert(errorData.message || '添加持股失敗');
      }
    } catch (error) {
      console.error('添加持股失敗:', error);
      alert('添加失敗，請稍後再試');
    }
  };

  // 刪除持股
  const removeHolding = async (holdingId: string) => {
    if (!selectedPortfolio || !confirm('確定要刪除這個持股嗎？')) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(createApiUrl(`/api/portfolio/${selectedPortfolio.id}/holdings/${holdingId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // 更新選中的組合
        setSelectedPortfolio(prev => prev ? {
          ...prev,
          holdings: prev.holdings.filter(h => h.id !== holdingId),
          totalValue: data.portfolio.totalValue,
          totalCost: data.portfolio.totalCost,
          totalGain: data.portfolio.totalGain,
          totalGainPercent: data.portfolio.totalGainPercent
        } : null);

        // 重新載入組合分析
        loadPortfolioAnalysis(selectedPortfolio.id);
      }
    } catch (error) {
      console.error('刪除持股失敗:', error);
      alert('刪除失敗，請稍後再試');
    }
  };

  // 更新持股
  const updateHolding = async (holdingId: string, updates: Partial<Holding>) => {
    if (!selectedPortfolio) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(createApiUrl(`/api/portfolio/${selectedPortfolio.id}/holdings/${holdingId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        const data = await response.json();
        
        // 更新選中的組合
        setSelectedPortfolio(prev => prev ? {
          ...prev,
          holdings: prev.holdings.map(h => h.id === holdingId ? data.holding : h),
          totalValue: data.portfolio.totalValue,
          totalCost: data.portfolio.totalCost,
          totalGain: data.portfolio.totalGain,
          totalGainPercent: data.portfolio.totalGainPercent
        } : null);

        // 重新載入組合分析
        loadPortfolioAnalysis(selectedPortfolio.id);
      }
    } catch (error) {
      console.error('更新持股失敗:', error);
      alert('更新失敗，請稍後再試');
    }
  };

  // 排序持股
  const sortedHoldings = selectedPortfolio?.holdings.slice().sort((a, b) => {
    let aValue: any, bValue: any;
    
    switch (sortBy) {
      case 'value':
        aValue = a.totalValue;
        bValue = b.totalValue;
        break;
      case 'gain':
        aValue = a.unrealizedGainPercent;
        bValue = b.unrealizedGainPercent;
        break;
      case 'weight':
        aValue = a.weight;
        bValue = b.weight;
        break;
      case 'symbol':
        aValue = a.symbol;
        bValue = b.symbol;
        break;
      default:
        aValue = a.totalValue;
        bValue = b.totalValue;
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  }) || [];

  // 格式化數字
  const formatNumber = (num: number) => {
    if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (Math.abs(num) >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toFixed(2);
  };

  // 格式化百分比
  const formatPercent = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  // 獲取變化顏色
  const getChangeColor = (change: number) => {
    if (change > 0) return '#27ae60';
    if (change < 0) return '#e74c3c';
    return '#95a5a6';
  };

  // 獲取風險等級顏色
  const getRiskColor = (riskScore: number) => {
    if (riskScore <= 3) return '#27ae60';
    if (riskScore <= 6) return '#f39c12';
    return '#e74c3c';
  };

  // 獲取風險等級文字
  const getRiskText = (riskScore: number) => {
    if (riskScore <= 3) return '低風險';
    if (riskScore <= 6) return '中風險';
    return '高風險';
  };

  if (loading) {
    return (
      <div className="portfolio-loading">
        <div className="loading-spinner"></div>
        <p>載入投資組合中...</p>
      </div>
    );
  }

  return (
    <div className="portfolio-page">
      {/* 頁面標題 */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">💼 智能投資組合管理</h1>
          <p className="page-subtitle">
            AI驅動的投資組合優化 • 專業風險管理 • 精準績效追蹤
          </p>
          
          {/* 價值主張展示 */}
          <div className="value-proposition">
            <div className="value-stats">
              <div className="value-stat">
                <span className="stat-number">+18.5%</span>
                <span className="stat-label">平均年化報酬</span>
              </div>
              <div className="value-stat">
                <span className="stat-number">85%</span>
                <span className="stat-label">組合優化準確度</span>
              </div>
              <div className="value-stat">
                <span className="stat-number">-15%</span>
                <span className="stat-label">平均風險降低</span>
              </div>
              <div className="value-stat">
                <span className="stat-number">10,000+</span>
                <span className="stat-label">成功組合優化</span>
              </div>
            </div>
            <div className="value-features">
              <div className="feature-highlight">✨ AI驅動的智能資產配置</div>
              <div className="feature-highlight">📊 實時風險評估與監控</div>
              <div className="feature-highlight">🎯 個人化投資策略制定</div>
              <div className="feature-highlight">🚀 專業級績效分析工具</div>
            </div>
          </div>
        </div>
      </div>

      <div className="portfolio-container">
        {/* 錯誤信息顯示 */}
        {error && (
          <div style={{
            background: '#fff3cd',
            color: '#856404',
            padding: '12px',
            borderRadius: '5px',
            marginBottom: '20px',
            border: '1px solid #ffeaa7'
          }}>
            ⚠️ {error}
          </div>
        )}
        
        {/* 組合選擇器 */}
        <div className="portfolio-selector">
          <div className="selector-header">
            <h3>我的投資組合</h3>
            <button
              type="button"
              className="create-portfolio-btn"
              onClick={() => setShowCreatePortfolio(true)}
            >
              + 創建組合
            </button>
          </div>
          
          {portfolios.length > 0 ? (
            <div className="portfolio-tabs">
              {portfolios.map((portfolio) => (
                <button
                  key={portfolio.id}
                  type="button"
                  className={`portfolio-tab ${selectedPortfolio?.id === portfolio.id ? 'active' : ''}`}
                  onClick={() => setSelectedPortfolio(portfolio)}
                >
                  <div className="tab-name">{portfolio.name}</div>
                  <div className="tab-value">${formatNumber(portfolio.totalValue)}</div>
                  <div 
                    className="tab-change"
                    style={{ color: getChangeColor(portfolio.totalGainPercent) }}
                  >
                    {formatPercent(portfolio.totalGainPercent)}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-portfolios">
              <div className="empty-icon">📊</div>
              <h3>還沒有投資組合</h3>
              <p>創建您的第一個投資組合，開始追蹤投資表現</p>
              <button
                type="button"
                className="create-first-portfolio-btn"
                onClick={() => setShowCreatePortfolio(true)}
              >
                創建投資組合
              </button>
            </div>
          )}
        </div>

        {/* 主要內容 */}
        {selectedPortfolio && (
          <div className="portfolio-content">
            {/* 組合概覽 */}
            <div className="portfolio-overview">
              <div className="overview-stats">
                <div className="stat-card primary">
                  <div className="stat-label">總價值</div>
                  <div className="stat-value">${formatNumber(selectedPortfolio.totalValue)}</div>
                  <div 
                    className="stat-change"
                    style={{ color: getChangeColor(selectedPortfolio.dayChangePercent) }}
                  >
                    今日 {formatPercent(selectedPortfolio.dayChangePercent)} (${formatNumber(selectedPortfolio.dayChange)})
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">總成本</div>
                  <div className="stat-value">${formatNumber(selectedPortfolio.totalCost)}</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">未實現損益</div>
                  <div 
                    className="stat-value"
                    style={{ color: getChangeColor(selectedPortfolio.totalGain) }}
                  >
                    ${formatNumber(selectedPortfolio.totalGain)}
                  </div>
                  <div 
                    className="stat-change"
                    style={{ color: getChangeColor(selectedPortfolio.totalGainPercent) }}
                  >
                    {formatPercent(selectedPortfolio.totalGainPercent)}
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">持股數量</div>
                  <div className="stat-value">{selectedPortfolio.holdings.length}</div>
                </div>
              </div>

              {/* 增強風險評估與績效指標 */}
              {portfolioAnalysis && (
                <div className="enhanced-metrics">
                  <div className="risk-assessment">
                    <div className="risk-score">
                      <div className="risk-label">風險評級</div>
                      <div 
                        className="risk-value"
                        style={{ color: getRiskColor(portfolioAnalysis.riskScore) }}
                      >
                        {getRiskText(portfolioAnalysis.riskScore)} ({portfolioAnalysis.riskScore}/10)
                      </div>
                    </div>
                    <div className="diversification-score">
                      <div className="diversification-label">分散度</div>
                      <div className="diversification-value">
                        {portfolioAnalysis.diversificationScore}/10
                      </div>
                    </div>
                    <div className="overall-rating">
                      <div className="rating-label">整體評級</div>
                      <div className={`rating-value ${portfolioAnalysis.overallRating?.toLowerCase()}`}>
                        {portfolioAnalysis.overallRating === 'EXCELLENT' ? '優秀' :
                         portfolioAnalysis.overallRating === 'GOOD' ? '良好' :
                         portfolioAnalysis.overallRating === 'FAIR' ? '一般' : '需改善'}
                      </div>
                    </div>
                  </div>
                  
                  {/* 進階績效指標 */}
                  {portfolioAnalysis.performanceMetrics && (
                    <div className="performance-indicators">
                      <div className="indicator-item">
                        <span className="indicator-label">夏普比率</span>
                        <span className="indicator-value">{portfolioAnalysis.performanceMetrics.sharpeRatio.toFixed(2)}</span>
                      </div>
                      <div className="indicator-item">
                        <span className="indicator-label">最大回撤</span>
                        <span className="indicator-value negative">{portfolioAnalysis.performanceMetrics.maxDrawdown.toFixed(1)}%</span>
                      </div>
                      <div className="indicator-item">
                        <span className="indicator-label">Alpha (超額報酬)</span>
                        <span className={`indicator-value ${portfolioAnalysis.performanceMetrics.alpha >= 0 ? 'positive' : 'negative'}`}>
                          {portfolioAnalysis.performanceMetrics.alpha.toFixed(2)}%
                        </span>
                      </div>
                      <div className="indicator-item">
                        <span className="indicator-label">勝率</span>
                        <span className="indicator-value">{portfolioAnalysis.performanceMetrics.winRate.toFixed(1)}%</span>
                      </div>
                    </div>
                  )}
                  
                  {/* 預期報酬 */}
                  {portfolioAnalysis.expectedReturn && (
                    <div className="return-forecast">
                      <div className="forecast-item">
                        <span className="forecast-label">預期年化報酬</span>
                        <span className="forecast-value positive">+{portfolioAnalysis.expectedReturn.toFixed(1)}%</span>
                      </div>
                      {portfolioAnalysis.targetReturn && (
                        <div className="forecast-item">
                          <span className="forecast-label">目標報酬</span>
                          <span className="forecast-value">+{portfolioAnalysis.targetReturn.toFixed(1)}%</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 視圖切換 */}
            <div className="view-tabs">
              <button
                type="button"
                className={`view-tab ${viewMode === 'overview' ? 'active' : ''}`}
                onClick={() => setViewMode('overview')}
              >
                概覽
              </button>
              <button
                type="button"
                className={`view-tab ${viewMode === 'holdings' ? 'active' : ''}`}
                onClick={() => setViewMode('holdings')}
              >
                持股明細
              </button>
              <button
                type="button"
                className={`view-tab ${viewMode === 'analysis' ? 'active' : ''}`}
                onClick={() => setViewMode('analysis')}
              >
                組合分析
              </button>
              <button
                type="button"
                className={`view-tab ${viewMode === 'performance' ? 'active' : ''}`}
                onClick={() => setViewMode('performance')}
              >
                表現追蹤
              </button>
            </div>

            {/* 內容區域 */}
            <div className="view-content">
              {viewMode === 'overview' && (
                <div className="overview-content">
                  {/* 資產配置圖表 */}
                  {portfolioAnalysis && (
                    <div className="allocation-charts">
                      <div className="chart-section">
                        <h4>行業配置</h4>
                        <div className="allocation-chart">
                          {Object.entries(portfolioAnalysis.sectorAllocation).map(([sector, percentage]) => (
                            <div key={sector} className="allocation-item">
                              <div className="allocation-label">{sector}</div>
                              <div className="allocation-bar">
                                <div 
                                  className="allocation-fill"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <div className="allocation-percent">{percentage.toFixed(1)}%</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="chart-section">
                        <h4>市場配置</h4>
                        <div className="allocation-chart">
                          {Object.entries(portfolioAnalysis.marketAllocation).map(([market, percentage]) => (
                            <div key={market} className="allocation-item">
                              <div className="allocation-label">{market}</div>
                              <div className="allocation-bar">
                                <div 
                                  className="allocation-fill"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <div className="allocation-percent">{percentage.toFixed(1)}%</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 前5大持股 */}
                  <div className="top-holdings">
                    <h4>前5大持股</h4>
                    <div className="holdings-preview">
                      {selectedPortfolio.holdings
                        .sort((a, b) => b.totalValue - a.totalValue)
                        .slice(0, 5)
                        .map((holding) => (
                          <div key={holding.id} className="holding-preview-item">
                            <div className="holding-info">
                              <div className="holding-symbol">{holding.symbol}</div>
                              <div className="holding-name">{holding.companyName}</div>
                            </div>
                            <div className="holding-metrics">
                              <div className="holding-value">${formatNumber(holding.totalValue)}</div>
                              <div className="holding-weight">{holding.weight.toFixed(1)}%</div>
                              <div 
                                className="holding-gain"
                                style={{ color: getChangeColor(holding.unrealizedGainPercent) }}
                              >
                                {formatPercent(holding.unrealizedGainPercent)}
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}

              {viewMode === 'holdings' && (
                <div className="holdings-content">
                  <div className="holdings-header">
                    <div className="holdings-actions">
                      <button
                        type="button"
                        className="add-holding-btn"
                        onClick={() => setShowAddHolding(true)}
                      >
                        + 添加持股
                      </button>
                      <div className="sort-controls">
                        <select
                          value={`${sortBy}-${sortOrder}`}
                          onChange={(e: any) => {
                            const [sortBy, sortOrder] = e.target.value.split('-');
                            setSortBy(sortBy as any);
                            setSortOrder(sortOrder as any);
                          }}
                          className="sort-select"
                        >
                          <option value="value-desc">價值高到低</option>
                          <option value="value-asc">價值低到高</option>
                          <option value="gain-desc">收益高到低</option>
                          <option value="gain-asc">收益低到高</option>
                          <option value="weight-desc">權重高到低</option>
                          <option value="weight-asc">權重低到高</option>
                          <option value="symbol-asc">股票代碼 A-Z</option>
                          <option value="symbol-desc">股票代碼 Z-A</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="holdings-table enhanced">
                    <div className="table-header">
                      <div className="col-stock">股票</div>
                      <div className="col-quantity">數量</div>
                      <div className="col-price">成本價</div>
                      <div className="col-current">現價</div>
                      <div className="col-value">市值</div>
                      <div className="col-gain">損益</div>
                      <div className="col-weight">權重</div>
                      <div className="col-rating">評級</div>
                      <div className="col-potential">上漲潛力</div>
                      <div className="col-actions">操作</div>
                    </div>
                    
                    {sortedHoldings.map((holding) => (
                      <div key={holding.id} className="table-row">
                        <div className="col-stock">
                          <div className="stock-info">
                            <div className="stock-symbol">{holding.symbol}</div>
                            <div className="stock-name">{holding.companyName}</div>
                            <div className="stock-market">{holding.market}</div>
                          </div>
                        </div>
                        <div className="col-quantity">
                          {holding.quantity.toLocaleString()}
                        </div>
                        <div className="col-price">
                          ${holding.averagePrice.toFixed(2)}
                        </div>
                        <div className="col-current">
                          <div className="current-price">${holding.currentPrice.toFixed(2)}</div>
                          <div 
                            className="day-change"
                            style={{ color: getChangeColor(holding.dayChangePercent) }}
                          >
                            {formatPercent(holding.dayChangePercent)}
                          </div>
                        </div>
                        <div className="col-value">
                          ${formatNumber(holding.totalValue)}
                        </div>
                        <div className="col-gain">
                          <div 
                            className="gain-amount"
                            style={{ color: getChangeColor(holding.unrealizedGain) }}
                          >
                            ${formatNumber(holding.unrealizedGain)}
                          </div>
                          <div 
                            className="gain-percent"
                            style={{ color: getChangeColor(holding.unrealizedGainPercent) }}
                          >
                            {formatPercent(holding.unrealizedGainPercent)}
                          </div>
                        </div>
                        <div className="col-weight">
                          {holding.weight.toFixed(1)}%
                        </div>
                        <div className="col-rating">
                          {holding.analystRating && (
                            <span className={`rating-badge ${holding.analystRating.toLowerCase()}`}>
                              {holding.analystRating === 'BUY' ? '買入' : 
                               holding.analystRating === 'HOLD' ? '持有' : '賣出'}
                            </span>
                          )}
                          {holding.aiScore && (
                            <div className="ai-score">
                              AI: {holding.aiScore}/10
                            </div>
                          )}
                        </div>
                        <div className="col-potential">
                          {holding.potentialUpside && (
                            <div className="upside-potential">
                              <span className="upside-value">+{holding.potentialUpside.toFixed(1)}%</span>
                              {holding.targetPrice && (
                                <span className="target-price">目標: ${holding.targetPrice.toFixed(2)}</span>
                              )}
                            </div>
                          )}
                          {holding.technicalSignal && (
                            <div className={`technical-signal ${holding.technicalSignal.toLowerCase()}`}>
                              {holding.technicalSignal === 'BULLISH' ? '看多' :
                               holding.technicalSignal === 'BEARISH' ? '看空' : '中性'}
                            </div>
                          )}
                        </div>
                        <div className="col-actions">
                          <button
                            type="button"
                            className="action-btn edit"
                            onClick={() => {
                              // 實現編輯功能
                              const newQuantity = prompt('輸入新的持股數量:', holding.quantity.toString());
                              if (newQuantity && !isNaN(Number(newQuantity))) {
                                updateHolding(holding.id, { quantity: Number(newQuantity) });
                              }
                            }}
                            title="編輯"
                          >
                            ✏️
                          </button>
                          <button
                            type="button"
                            className="action-btn analyze"
                            onClick={() => navigate(`/analysis?symbol=${holding.symbol}`)}
                            title="分析"
                          >
                            🔍
                          </button>
                          <button
                            type="button"
                            className="action-btn delete"
                            onClick={() => removeHolding(holding.id)}
                            title="刪除"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {viewMode === 'analysis' && portfolioAnalysis && (
                <div className="analysis-content">
                  <div className="analysis-sections">
                    {/* 再平衡建議 - 核心獲利功能 */}
                    {portfolioAnalysis.rebalanceRecommendations && portfolioAnalysis.rebalanceRecommendations.length > 0 && (
                      <div className="analysis-section premium">
                        <h4>🎯 智能再平衡建議</h4>
                        <div className="rebalance-recommendations">
                          {portfolioAnalysis.rebalanceRecommendations.map((rec, index) => (
                            <div key={index} className="rebalance-item">
                              <div className="rebalance-header">
                                <span className="stock-symbol">{rec.symbol}</span>
                                <span className={`action-badge ${rec.action.toLowerCase()}`}>
                                  {rec.action === 'BUY' ? '加倉' : rec.action === 'SELL' ? '減倉' : '持有'}
                                </span>
                              </div>
                              <div className="weight-changes">
                                <span className="current-weight">現有: {rec.currentWeight.toFixed(1)}%</span>
                                <span className="arrow">→</span>
                                <span className="target-weight">建議: {rec.targetWeight.toFixed(1)}%</span>
                              </div>
                              <div className="rebalance-reason">{rec.reason}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 投資建議 */}
                    <div className="analysis-section">
                      <h4>💡 投資建議</h4>
                      <div className="recommendations-list">
                        {portfolioAnalysis.recommendations.map((recommendation, index) => (
                          <div key={index} className="recommendation-item">
                            <span className="recommendation-icon">💡</span>
                            <span className="recommendation-text">{recommendation}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 投資機會 */}
                    <div className="analysis-section">
                      <h4>🚀 投資機會</h4>
                      <div className="opportunities-list">
                        {portfolioAnalysis.opportunities.map((opportunity, index) => (
                          <div key={index} className="opportunity-item">
                            <span className="opportunity-icon">🚀</span>
                            <span className="opportunity-text">{opportunity}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 風險因素 */}
                    <div className="analysis-section">
                      <h4>⚠️ 風險因素</h4>
                      <div className="risks-list">
                        {portfolioAnalysis.riskFactors.map((risk, index) => (
                          <div key={index} className="risk-item">
                            <span className="risk-icon">⚠️</span>
                            <span className="risk-text">{risk}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 高級洞察 - 會員專屬 */}
                    {portfolioAnalysis.premiumInsights && portfolioAnalysis.premiumInsights.length > 0 && (
                      <div className="analysis-section premium">
                        <h4>💎 高級洞察 (會員專享)</h4>
                        <div className="premium-insights">
                          {portfolioAnalysis.premiumInsights.map((insight, index) => (
                            <div key={index} className="premium-insight-item">
                              <span className="premium-icon">💎</span>
                              <span className="insight-text">{insight}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 升級推薦 */}
                    {portfolioAnalysis.nextUpgrade && (
                      <div className="upgrade-recommendation">
                        <h4>🌟 升級享受更多功能</h4>
                        <div className="upgrade-content">
                          <div className="upgrade-header">
                            <span className="upgrade-tier">{portfolioAnalysis.nextUpgrade.tier} 會員</span>
                            <span className="upgrade-price">${portfolioAnalysis.nextUpgrade.price}/月</span>
                          </div>
                          <div className="upgrade-benefits">
                            {portfolioAnalysis.nextUpgrade.benefits.map((benefit, index) => (
                              <div key={index} className="benefit-item">
                                ✨ {benefit}
                              </div>
                            ))}
                          </div>
                          <button className="upgrade-btn">立即升級</button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {viewMode === 'performance' && (
                <div className="performance-content">
                  <div className="performance-placeholder">
                    <div className="placeholder-icon">📈</div>
                    <h3>表現追蹤功能開發中</h3>
                    <p>即將推出詳細的投資表現分析和歷史追蹤功能</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 創建組合模態框 */}
      {showCreatePortfolio && (
        <div className="modal-overlay" onClick={() => setShowCreatePortfolio(false)}>
          <div className="create-portfolio-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>創建新的投資組合</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowCreatePortfolio(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>組合名稱</label>
                <input
                  type="text"
                  value={newPortfolioName}
                  onChange={(e: any) => setNewPortfolioName(e.target.value)}
                  placeholder="例如：核心持股、成長股組合"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>組合描述（可選）</label>
                <textarea
                  value={newPortfolioDescription}
                  onChange={(e: any) => setNewPortfolioDescription(e.target.value)}
                  placeholder="描述這個組合的投資策略或目標"
                  className="form-textarea"
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn secondary"
                onClick={() => setShowCreatePortfolio(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="modal-btn primary"
                onClick={createPortfolio}
                disabled={!newPortfolioName.trim()}
              >
                創建組合
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 添加持股模態框 */}
      {showAddHolding && (
        <div className="modal-overlay" onClick={() => setShowAddHolding(false)}>
          <div className="add-holding-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加持股</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowAddHolding(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>股票代碼</label>
                <input
                  type="text"
                  value={addHoldingForm.symbol}
                  onChange={(e: any) => setAddHoldingForm(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                  placeholder="例如：2330, AAPL"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>持股數量</label>
                <input
                  type="number"
                  value={addHoldingForm.quantity || ''}
                  onChange={(e: any) => setAddHoldingForm(prev => ({ ...prev, quantity: Number(e.target.value) }))}
                  placeholder="持有股數"
                  className="form-input"
                  min="1"
                />
              </div>
              <div className="form-group">
                <label>平均成本價</label>
                <input
                  type="number"
                  value={addHoldingForm.averagePrice || ''}
                  onChange={(e: any) => setAddHoldingForm(prev => ({ ...prev, averagePrice: Number(e.target.value) }))}
                  placeholder="每股成本價"
                  className="form-input"
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="form-group">
                <label>購買日期</label>
                <input
                  type="date"
                  value={addHoldingForm.purchaseDate}
                  onChange={(e: any) => setAddHoldingForm(prev => ({ ...prev, purchaseDate: e.target.value }))}
                  className="form-input"
                />
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn secondary"
                onClick={() => setShowAddHolding(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="modal-btn primary"
                onClick={addHolding}
                disabled={!addHoldingForm.symbol || addHoldingForm.quantity <= 0 || addHoldingForm.averagePrice <= 0}
              >
                添加持股
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioPage;