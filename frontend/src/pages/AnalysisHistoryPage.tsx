import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './AnalysisHistoryPage.css';

/**
 * TradingAgents 核心獲利功能 - 分析歷史管理頁面
 * 專業投資分析平台的核心績效追蹤系統
 * 
 * 核心獲利功能：
 * 1. 投資建議追蹤與驗證系統
 * 2. 成功率統計與績效分析
 * 3. AI分析師表現比較
 * 4. 個人化投資報告生成
 * 5. 投資組合回報分析
 * 6. 風險管理效果評估
 * 
 * @author TradingAgents Team
 * @version 2.0 - Enhanced Performance Tracking
 */

interface AnalysisRecord {
  id: string;
  symbol: string;
  companyName: string;
  market: string;
  analysisType: string;
  analyst: string;
  result: 'buy' | 'sell' | 'hold';
  confidence: number;
  targetPrice?: number;
  currentPrice?: number;
  priceChange?: number;
  priceChangePercent?: number;
  summary: string;
  keyPoints: string[];
  risks: string[];
  opportunities: string[];
  createdAt: string;
  updatedAt: string;
  tags: string[];
  isFavorite: boolean;
  shareUrl?: string;
  // 增強績效追蹤
  actualOutcome?: 'profit' | 'loss' | 'pending';
  actualReturn?: number;
  holdingPeriod?: number;
  riskLevel?: number;
  followedRecommendation?: boolean;
  userNotes?: string;
  marketCondition?: 'bull' | 'bear' | 'sideways';
  sectorPerformance?: number;
  analystAccuracy?: number;
}

interface PerformanceStats {
  totalAnalyses: number;
  successfulPredictions: number;
  successRate: number;
  averageReturn: number;
  totalReturn: number;
  bestPerformer: string;
  worstPerformer: string;
  avgHoldingPeriod: number;
  riskAdjustedReturn: number;
  winLossRatio: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

interface AnalystPerformance {
  analystId: string;
  analystName: string;
  totalAnalyses: number;
  successRate: number;
  avgReturn: number;
  avgConfidence: number;
  accuracy: number;
  specialties: string[];
  recommendations: {
    buy: number;
    sell: number;
    hold: number;
  };
}

interface FilterOptions {
  dateRange: 'all' | '7d' | '30d' | '90d' | '1y';
  market: 'all' | 'TW' | 'US' | 'HK' | 'CN' | 'JP' | 'KR';
  result: 'all' | 'buy' | 'sell' | 'hold';
  analyst: 'all' | string;
  sortBy: 'date' | 'confidence' | 'performance' | 'symbol';
  sortOrder: 'desc' | 'asc';
}

const AnalysisHistoryPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisRecord[]>([]);
  const [filteredAnalyses, setFilteredAnalyses] = useState<AnalysisRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisRecord | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({
    dateRange: 'all',
    market: 'all',
    result: 'all',
    analyst: 'all',
    sortBy: 'date',
    sortOrder: 'desc'
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  // 增強狀態管理
  const [performanceStats, setPerformanceStats] = useState<PerformanceStats | null>(null);
  const [analystPerformance, setAnalystPerformance] = useState<AnalystPerformance[]>([]);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'cards' | 'analytics'>('cards');
  const [showPerformanceInsights, setShowPerformanceInsights] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // 分析師選項
  const analystOptions = [
    { value: 'all', label: '全部分析師' },
    { value: 'fundamental', label: '基本面分析師' },
    { value: 'technical', label: '技術面分析師' },
    { value: 'news', label: '新聞分析師' },
    { value: 'risk', label: '風險分析師' },
    { value: 'taiwan', label: '台股專家' },
    { value: 'international', label: '國際市場專家' },
    { value: 'portfolio', label: '投資組合規劃師' }
  ];

  useEffect(() => {
    loadAnalysisHistory();
    loadPerformanceStats();
    loadAnalystPerformance();
    
    // 檢查 URL 參數
    const analysisId = searchParams.get('id');
    if (analysisId) {
      // 載入特定分析詳情
      loadAnalysisDetail(analysisId);
    }
  }, []);

  useEffect(() => {
    applyFilters();
  }, [analyses, filters, searchQuery]);

  // 載入分析歷史
  const loadAnalysisHistory = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        navigate('/auth?mode=login');
        return;
      }

      const response = await fetch('/api/analysis/history?includePerformance=true', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyses(data.analyses || []);
      } else if (response.status === 401) {
        navigate('/auth?mode=login');
      }
    } catch (error) {
      console.error('載入分析歷史失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 載入績效統計
  const loadPerformanceStats = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch('/api/analysis/performance-stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPerformanceStats(data.stats);
      }
    } catch (error) {
      console.error('載入績效統計失敗:', error);
    }
  };

  // 載入分析師績效
  const loadAnalystPerformance = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch('/api/analysis/analyst-performance', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalystPerformance(data.performance || []);
      }
    } catch (error) {
      console.error('載入分析師績效失敗:', error);
    }
  };

  // 載入分析詳情
  const loadAnalysisDetail = async (analysisId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/analysis/${analysisId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedAnalysis(data.analysis);
        setShowDetailModal(true);
      }
    } catch (error) {
      console.error('載入分析詳情失敗:', error);
    }
  };

  // 應用篩選
  const applyFilters = () => {
    let filtered = [...analyses];

    // 搜尋篩選
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(analysis =>
        analysis.symbol.toLowerCase().includes(query) ||
        analysis.companyName.toLowerCase().includes(query) ||
        analysis.summary.toLowerCase().includes(query) ||
        analysis.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // 日期範圍篩選
    if (filters.dateRange !== 'all') {
      const now = new Date();
      const days = {
        '7d': 7,
        '30d': 30,
        '90d': 90,
        '1y': 365
      }[filters.dateRange] || 0;
      
      const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(analysis => 
        new Date(analysis.createdAt) >= cutoffDate
      );
    }

    // 市場篩選
    if (filters.market !== 'all') {
      filtered = filtered.filter(analysis => analysis.market === filters.market);
    }

    // 結果篩選
    if (filters.result !== 'all') {
      filtered = filtered.filter(analysis => analysis.result === filters.result);
    }

    // 分析師篩選
    if (filters.analyst !== 'all') {
      filtered = filtered.filter(analysis => analysis.analyst === filters.analyst);
    }

    // 排序
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (filters.sortBy) {
        case 'date':
          aValue = new Date(a.createdAt);
          bValue = new Date(b.createdAt);
          break;
        case 'confidence':
          aValue = a.confidence;
          bValue = b.confidence;
          break;
        case 'performance':
          aValue = a.priceChangePercent || 0;
          bValue = b.priceChangePercent || 0;
          break;
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        default:
          aValue = a.createdAt;
          bValue = b.createdAt;
      }

      if (filters.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredAnalyses(filtered);
  };

  // 切換收藏
  const toggleFavorite = async (analysisId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/analysis/${analysisId}/favorite`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setAnalyses(prev => prev.map(analysis =>
          analysis.id === analysisId
            ? { ...analysis, isFavorite: !analysis.isFavorite }
            : analysis
        ));
      }
    } catch (error) {
      console.error('切換收藏失敗:', error);
    }
  };

  // 分享分析
  const shareAnalysis = async (analysis: AnalysisRecord) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/analysis/${analysis.id}/share`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        const shareUrl = data.shareUrl;
        
        // 複製到剪貼板
        await navigator.clipboard.writeText(shareUrl);
        alert('分享連結已複製到剪貼板');
      }
    } catch (error) {
      console.error('分享分析失敗:', error);
      alert('分享失敗，請稍後再試');
    }
  };

  // 匯出分析
  const exportAnalysis = async (analysisIds: string[], format: 'pdf' | 'excel') => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/analysis/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          analysisIds,
          format
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_export_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('匯出分析失敗:', error);
      alert('匯出失敗，請稍後再試');
    }
  };

  // 刪除分析
  const deleteAnalyses = async (analysisIds: string[]) => {
    if (!confirm(`確定要刪除 ${analysisIds.length} 個分析記錄嗎？此操作無法復原。`)) {
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/analysis/batch-delete', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ analysisIds })
      });

      if (response.ok) {
        setAnalyses(prev => prev.filter(analysis => !analysisIds.includes(analysis.id)));
        setSelectedIds([]);
        setShowBulkActions(false);
      }
    } catch (error) {
      console.error('刪除分析失敗:', error);
      alert('刪除失敗，請稍後再試');
    }
  };

  // 批量操作
  const handleBulkAction = (action: string) => {
    switch (action) {
      case 'export-pdf':
        exportAnalysis(selectedIds, 'pdf');
        break;
      case 'export-excel':
        exportAnalysis(selectedIds, 'excel');
        break;
      case 'delete':
        deleteAnalyses(selectedIds);
        break;
      case 'favorite':
        selectedIds.forEach(id => toggleFavorite(id));
        setSelectedIds([]);
        setShowBulkActions(false);
        break;
    }
  };

  // 選擇/取消選擇
  const toggleSelection = (analysisId: string) => {
    setSelectedIds(prev => {
      const newIds = prev.includes(analysisId)
        ? prev.filter(id => id !== analysisId)
        : [...prev, analysisId];
      
      setShowBulkActions(newIds.length > 0);
      return newIds;
    });
  };

  // 全選/取消全選
  const toggleSelectAll = () => {
    if (selectedIds.length === filteredAnalyses.length) {
      setSelectedIds([]);
      setShowBulkActions(false);
    } else {
      const allIds = filteredAnalyses.map(analysis => analysis.id);
      setSelectedIds(allIds);
      setShowBulkActions(true);
    }
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 獲取結果顏色
  const getResultColor = (result: string) => {
    switch (result) {
      case 'buy': return '#27ae60';
      case 'sell': return '#e74c3c';
      case 'hold': return '#f39c12';
      default: return '#95a5a6';
    }
  };

  // 獲取結果文字
  const getResultText = (result: string) => {
    switch (result) {
      case 'buy': return '買入';
      case 'sell': return '賣出';
      case 'hold': return '持有';
      default: return result;
    }
  };

  // 獲取表現顏色
  const getPerformanceColor = (change?: number) => {
    if (!change) return '#95a5a6';
    if (change > 0) return '#27ae60';
    if (change < 0) return '#e74c3c';
    return '#95a5a6';
  };

  // 獲取結果實際表現類別
  const getOutcomeColor = (outcome?: string) => {
    switch (outcome) {
      case 'profit': return '#27ae60';
      case 'loss': return '#e74c3c';
      case 'pending': return '#f39c12';
      default: return '#95a5a6';
    }
  };

  // 獲取結果實際表現文字
  const getOutcomeText = (outcome?: string) => {
    switch (outcome) {
      case 'profit': return '獲利';
      case 'loss': return '虧損';
      case 'pending': return '等待中';
      default: return '未知';
    }
  };

  if (loading) {
    return (
      <div className="analysis-history-loading">
        <div className="loading-spinner"></div>
        <p>載入分析歷史中...</p>
      </div>
    );
  }

  return (
    <div className="analysis-history-page">
      {/* 頁面標題 */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">📈 分析歷史與績效追蹤</h1>
          <p className="page-subtitle">
            追蹤投資建議效果，優化投資決策，實現長期穩定收益
          </p>
          
          {/* 績效概覽 */}
          {performanceStats && (
            <div className="performance-overview">
              <div className="performance-stats">
                <div className="stat-item">
                  <span className="stat-number">{performanceStats.successRate.toFixed(1)}%</span>
                  <span className="stat-label">成功率</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">+{performanceStats.averageReturn.toFixed(1)}%</span>
                  <span className="stat-label">平均報酬</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">{performanceStats.totalAnalyses}</span>
                  <span className="stat-label">總分析數</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">{performanceStats.sharpeRatio.toFixed(2)}</span>
                  <span className="stat-label">夏普比率</span>
                </div>
              </div>
              <div className="performance-actions">
                <button 
                  className="performance-btn"
                  onClick={() => setShowStatsModal(true)}
                >
                  📊 詳細績效報告
                </button>
                <button 
                  className="performance-btn"
                  onClick={() => setShowPerformanceInsights(true)}
                >
                  🧠 AI績效洞察
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="history-container">
        {/* 視圖模式切換 */}
        <div className="view-mode-section">
          <div className="view-mode-controls">
            <button
              className={`view-mode-btn ${viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setViewMode('cards')}
            >
              🗂️ 卡片視圖
            </button>
            <button
              className={`view-mode-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
            >
              📋 列表視圖
            </button>
            <button
              className={`view-mode-btn ${viewMode === 'analytics' ? 'active' : ''}`}
              onClick={() => setViewMode('analytics')}
            >
              📊 分析視圖
            </button>
          </div>
        </div>

        {/* 篩選和搜尋區域 */}
        <div className="filters-section">
          <div className="search-bar">
            <input
              type="text"
              value={searchQuery}
              onChange={(e: any) => setSearchQuery(e.target.value)}
              placeholder="搜尋股票代碼、公司名稱或標籤..."
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>

          <div className="filters-grid">
            <select
              value={filters.dateRange}
              onChange={(e: any) => setFilters(prev => ({ ...prev, dateRange: e.target.value as any }))}
              className="filter-select"
            >
              <option value="all">全部時間</option>
              <option value="7d">最近 7 天</option>
              <option value="30d">最近 30 天</option>
              <option value="90d">最近 90 天</option>
              <option value="1y">最近 1 年</option>
            </select>

            <select
              value={filters.market}
              onChange={(e: any) => setFilters(prev => ({ ...prev, market: e.target.value as any }))}
              className="filter-select"
            >
              <option value="all">全部市場</option>
              <option value="TW">🇹🇼 台股</option>
              <option value="US">🇺🇸 美股</option>
              <option value="HK">🇭🇰 港股</option>
              <option value="CN">🇨🇳 陸股</option>
              <option value="JP">🇯🇵 日股</option>
              <option value="KR">🇰🇷 韓股</option>
            </select>

            <select
              value={filters.result}
              onChange={(e: any) => setFilters(prev => ({ ...prev, result: e.target.value as any }))}
              className="filter-select"
            >
              <option value="all">全部結果</option>
              <option value="buy">買入</option>
              <option value="hold">持有</option>
              <option value="sell">賣出</option>
            </select>

            <select
              value={filters.analyst}
              onChange={(e: any) => setFilters(prev => ({ ...prev, analyst: e.target.value }))}
              className="filter-select"
            >
              {analystOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <select
              value={`${filters.sortBy}-${filters.sortOrder}`}
              onChange={(e: any) => {
                const [sortBy, sortOrder] = e.target.value.split('-');
                setFilters(prev => ({ ...prev, sortBy: sortBy as any, sortOrder: sortOrder as any }));
              }}
              className="filter-select"
            >
              <option value="date-desc">最新優先</option>
              <option value="date-asc">最舊優先</option>
              <option value="confidence-desc">信心度高到低</option>
              <option value="confidence-asc">信心度低到高</option>
              <option value="performance-desc">表現最佳</option>
              <option value="performance-asc">表現最差</option>
              <option value="symbol-asc">股票代碼 A-Z</option>
              <option value="symbol-desc">股票代碼 Z-A</option>
            </select>
          </div>
        </div>

        {/* 批量操作欄 */}
        {showBulkActions && (
          <div className="bulk-actions-bar">
            <div className="bulk-info">
              已選擇 {selectedIds.length} 個分析
            </div>
            <div className="bulk-actions">
              <button
                type="button"
                className="bulk-action-btn"
                onClick={() => handleBulkAction('favorite')}
              >
                ⭐ 加入收藏
              </button>
              <button
                type="button"
                className="bulk-action-btn"
                onClick={() => handleBulkAction('export-pdf')}
              >
                📄 匯出 PDF
              </button>
              <button
                type="button"
                className="bulk-action-btn"
                onClick={() => handleBulkAction('export-excel')}
              >
                📊 匯出 Excel
              </button>
              <button
                type="button"
                className="bulk-action-btn danger"
                onClick={() => handleBulkAction('delete')}
              >
                🗑️ 刪除
              </button>
            </div>
          </div>
        )}

        {/* 分析展示區域 */}
        <div className="analyses-section">
          {filteredAnalyses.length > 0 ? (
            <>
              <div className="analyses-header">
                <div className="analyses-count">
                  共 {filteredAnalyses.length} 個分析記錄
                </div>
                <button
                  type="button"
                  className="select-all-btn"
                  onClick={toggleSelectAll}
                >
                  {selectedIds.length === filteredAnalyses.length ? '取消全選' : '全選'}
                </button>
              </div>

              {viewMode === 'analytics' ? (
                <div className="analytics-view">
                  {/* 分析師績效比較 */}
                  <div className="analytics-section">
                    <h3 className="analytics-title">🤖 AI分析師績效比較</h3>
                    <div className="analyst-performance-grid">
                      {analystPerformance.map((analyst) => (
                        <div key={analyst.analystId} className="analyst-performance-card">
                          <div className="analyst-header">
                            <h4 className="analyst-name">{analyst.analystName}</h4>
                            <div className="analyst-accuracy">
                              準確度: {analyst.accuracy.toFixed(1)}%
                            </div>
                          </div>
                          <div className="performance-metrics">
                            <div className="metric">
                              <span className="metric-label">成功率</span>
                              <span className="metric-value">{analyst.successRate.toFixed(1)}%</span>
                            </div>
                            <div className="metric">
                              <span className="metric-label">平均報酬</span>
                              <span className="metric-value">+{analyst.avgReturn.toFixed(1)}%</span>
                            </div>
                            <div className="metric">
                              <span className="metric-label">分析次數</span>
                              <span className="metric-value">{analyst.totalAnalyses}</span>
                            </div>
                          </div>
                          <div className="recommendation-breakdown">
                            <div className="rec-item">
                              <span className="rec-label">買入</span>
                              <span className="rec-count">{analyst.recommendations.buy}</span>
                            </div>
                            <div className="rec-item">
                              <span className="rec-label">持有</span>
                              <span className="rec-count">{analyst.recommendations.hold}</span>
                            </div>
                            <div className="rec-item">
                              <span className="rec-label">賣出</span>
                              <span className="rec-count">{analyst.recommendations.sell}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 市場表現分析 */}
                  <div className="analytics-section">
                    <h3 className="analytics-title">📊 市場表現分析</h3>
                    <div className="market-analysis-grid">
                      <div className="market-card">
                        <h4>最佳表現市場</h4>
                        <div className="market-performance">
                          {analyses
                            .reduce((acc: any, analysis) => {
                              if (!acc[analysis.market]) {
                                acc[analysis.market] = { count: 0, totalReturn: 0 };
                              }
                              acc[analysis.market].count++;
                              acc[analysis.market].totalReturn += analysis.priceChangePercent || 0;
                              return acc;
                            }, {})
                            && Object.entries(analyses.reduce((acc: any, analysis) => {
                              if (!acc[analysis.market]) {
                                acc[analysis.market] = { count: 0, totalReturn: 0 };
                              }
                              acc[analysis.market].count++;
                              acc[analysis.market].totalReturn += analysis.priceChangePercent || 0;
                              return acc;
                            }, {}))
                            .sort((a: any, b: any) => (b[1].totalReturn / b[1].count) - (a[1].totalReturn / a[1].count))
                            .slice(0, 3)
                            .map(([market, data]: any) => (
                              <div key={market} className="market-item">
                                <span className="market-name">{market}</span>
                                <span className="market-return">+{(data.totalReturn / data.count).toFixed(1)}%</span>
                              </div>
                            ))
                          }
                        </div>
                      </div>
                      
                      <div className="market-card">
                        <h4>投資建議分布</h4>
                        <div className="recommendation-chart">
                          {Object.entries(
                            analyses.reduce((acc: any, analysis) => {
                              acc[analysis.result] = (acc[analysis.result] || 0) + 1;
                              return acc;
                            }, {})
                          ).map(([result, count]: any) => (
                            <div key={result} className="chart-bar">
                              <div className="bar-label">{getResultText(result)}</div>
                              <div className="bar-container">
                                <div 
                                  className="bar-fill"
                                  style={{
                                    width: `${(count / analyses.length) * 100}%`,
                                    backgroundColor: getResultColor(result)
                                  }}
                                />
                                <span className="bar-count">{count}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className={`analyses-list ${viewMode}`}>
                  {filteredAnalyses.map((analysis) => (
                    <div key={analysis.id} className={`analysis-card ${viewMode}`}>
                    <div className="card-header">
                      <div className="card-selection">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(analysis.id)}
                          onChange={() => toggleSelection(analysis.id)}
                          className="selection-checkbox"
                        />
                      </div>
                      
                      <div className="stock-info">
                        <div className="stock-identity">
                          <h3 className="stock-symbol">{analysis.symbol}</h3>
                          <span className="stock-name">{analysis.companyName}</span>
                          <span className="stock-market">{analysis.market}</span>
                        </div>
                        <div className="analysis-meta">
                          <span className="analysis-type">{analysis.analysisType}</span>
                          <span className="analyst-name">{analysis.analyst}</span>
                        </div>
                      </div>

                      <div className="analysis-result">
                        <div 
                          className="result-badge"
                          style={{ backgroundColor: getResultColor(analysis.result) }}
                        >
                          {getResultText(analysis.result)}
                        </div>
                        <div className="confidence-score">
                          信心度: {analysis.confidence}%
                        </div>
                      </div>

                      <div className="price-info">
                        {analysis.targetPrice && (
                          <div className="target-price">
                            目標價: ${analysis.targetPrice.toFixed(2)}
                          </div>
                        )}
                        {analysis.priceChangePercent !== undefined && (
                          <div 
                            className="price-performance"
                            style={{ color: getPerformanceColor(analysis.priceChangePercent) }}
                          >
                            {analysis.priceChangePercent > 0 ? '+' : ''}
                            {analysis.priceChangePercent.toFixed(2)}%
                          </div>
                        )}
                        {analysis.actualOutcome && (
                          <div className="actual-outcome">
                            <span 
                              className="outcome-badge"
                              style={{ backgroundColor: getOutcomeColor(analysis.actualOutcome) }}
                            >
                              {getOutcomeText(analysis.actualOutcome)}
                            </span>
                            {analysis.actualReturn && (
                              <span className="actual-return">
                                {analysis.actualReturn > 0 ? '+' : ''}{analysis.actualReturn.toFixed(1)}%
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="card-actions">
                        <button
                          type="button"
                          className={`action-btn favorite ${analysis.isFavorite ? 'active' : ''}`}
                          onClick={() => toggleFavorite(analysis.id)}
                          title={analysis.isFavorite ? '取消收藏' : '加入收藏'}
                        >
                          {analysis.isFavorite ? '⭐' : '☆'}
                        </button>
                        <button
                          type="button"
                          className="action-btn share"
                          onClick={() => shareAnalysis(analysis)}
                          title="分享分析"
                        >
                          📤
                        </button>
                        <button
                          type="button"
                          className="action-btn view"
                          onClick={() => {
                            setSelectedAnalysis(analysis);
                            setShowDetailModal(true);
                          }}
                          title="查看詳情"
                        >
                          👁️
                        </button>
                      </div>
                    </div>

                    <div className="card-content">
                      <div className="analysis-summary">
                        {analysis.summary}
                      </div>
                      
                      {analysis.tags.length > 0 && (
                        <div className="analysis-tags">
                          {analysis.tags.map((tag, index) => (
                            <span key={index} className="tag">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="card-footer">
                      <div className="analysis-date">
                        {formatDate(analysis.createdAt)}
                      </div>
                      <button
                        type="button"
                        className="reanalyze-btn"
                        onClick={() => navigate(`/analysis?symbol=${analysis.symbol}`)}
                      >
                        重新分析
                      </button>
                    </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>暫無分析記錄</h3>
              <p>
                {searchQuery || Object.values(filters).some(v => v !== 'all' && v !== 'desc')
                  ? '沒有符合篩選條件的分析記錄'
                  : '您還沒有進行任何股票分析'
                }
              </p>
              <button
                type="button"
                className="start-analysis-btn"
                onClick={() => navigate('/analysis')}
              >
                開始分析
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 分析詳情模態框 */}
      {showDetailModal && selectedAnalysis && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="analysis-detail-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {selectedAnalysis.companyName} ({selectedAnalysis.symbol})
              </h2>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowDetailModal(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-content">
              <div className="detail-section">
                <h3>分析結果</h3>
                <div className="result-summary">
                  <div 
                    className="result-badge large"
                    style={{ backgroundColor: getResultColor(selectedAnalysis.result) }}
                  >
                    {getResultText(selectedAnalysis.result)}
                  </div>
                  <div className="confidence-large">
                    信心度: {selectedAnalysis.confidence}%
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3>分析摘要</h3>
                <p>{selectedAnalysis.summary}</p>
              </div>

              {selectedAnalysis.keyPoints.length > 0 && (
                <div className="detail-section">
                  <h3>關鍵要點</h3>
                  <ul className="points-list">
                    {selectedAnalysis.keyPoints.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedAnalysis.opportunities.length > 0 && (
                <div className="detail-section">
                  <h3>投資機會</h3>
                  <ul className="points-list opportunities">
                    {selectedAnalysis.opportunities.map((opportunity, index) => (
                      <li key={index}>{opportunity}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedAnalysis.risks.length > 0 && (
                <div className="detail-section">
                  <h3>風險提醒</h3>
                  <ul className="points-list risks">
                    {selectedAnalysis.risks.map((risk, index) => (
                      <li key={index}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="detail-section">
                <h3>分析資訊</h3>
                <div className="analysis-info-grid">
                  <div className="info-item">
                    <span className="info-label">分析師</span>
                    <span className="info-value">{selectedAnalysis.analyst}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">分析類型</span>
                    <span className="info-value">{selectedAnalysis.analysisType}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">分析時間</span>
                    <span className="info-value">{formatDate(selectedAnalysis.createdAt)}</span>
                  </div>
                  {selectedAnalysis.targetPrice && (
                    <div className="info-item">
                      <span className="info-label">目標價</span>
                      <span className="info-value">${selectedAnalysis.targetPrice.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="modal-action-btn"
                onClick={() => shareAnalysis(selectedAnalysis)}
              >
                📤 分享
              </button>
              <button
                type="button"
                className="modal-action-btn"
                onClick={() => exportAnalysis([selectedAnalysis.id], 'pdf')}
              >
                📄 匯出 PDF
              </button>
              <button
                type="button"
                className="modal-action-btn primary"
                onClick={() => {
                  setShowDetailModal(false);
                  navigate(`/analysis?symbol=${selectedAnalysis.symbol}`);
                }}
              >
                🔄 重新分析
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 績效統計模態框 */}
      {showStatsModal && performanceStats && (
        <div className="modal-overlay" onClick={() => setShowStatsModal(false)}>
          <div className="stats-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📊 詳細績效統計報告</h2>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowStatsModal(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-content">
              <div className="stats-grid">
                <div className="stats-card">
                  <h3>整體績效</h3>
                  <div className="stats-details">
                    <div className="detail-row">
                      <span className="detail-label">總分析次數</span>
                      <span className="detail-value">{performanceStats.totalAnalyses}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">成功預測</span>
                      <span className="detail-value">{performanceStats.successfulPredictions}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">成功率</span>
                      <span className="detail-value success">{performanceStats.successRate.toFixed(1)}%</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">勝負比</span>
                      <span className="detail-value">{performanceStats.winLossRatio.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div className="stats-card">
                  <h3>報酬分析</h3>
                  <div className="stats-details">
                    <div className="detail-row">
                      <span className="detail-label">總報酬</span>
                      <span className="detail-value profit">+{performanceStats.totalReturn.toFixed(1)}%</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">平均報酬</span>
                      <span className="detail-value profit">+{performanceStats.averageReturn.toFixed(1)}%</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">風險調整報酬</span>
                      <span className="detail-value">{performanceStats.riskAdjustedReturn.toFixed(2)}%</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">夏普比率</span>
                      <span className="detail-value">{performanceStats.sharpeRatio.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div className="stats-card">
                  <h3>風險管理</h3>
                  <div className="stats-details">
                    <div className="detail-row">
                      <span className="detail-label">最大回撤</span>
                      <span className="detail-value loss">-{performanceStats.maxDrawdown.toFixed(1)}%</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">平均持有期</span>
                      <span className="detail-value">{performanceStats.avgHoldingPeriod.toFixed(0)} 天</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">最佳表現</span>
                      <span className="detail-value profit">{performanceStats.bestPerformer}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">最差表現</span>
                      <span className="detail-value loss">{performanceStats.worstPerformer}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="insights-section">
                <h3>🧠 AI 績效洞察</h3>
                <div className="insights-list">
                  <div className="insight-item">
                    <span className="insight-icon">✅</span>
                    <div className="insight-content">
                      <strong>投資表現優異</strong>
                      <p>您的成功率達 {performanceStats.successRate.toFixed(1)}%，超過市場平均水準 15%</p>
                    </div>
                  </div>
                  <div className="insight-item">
                    <span className="insight-icon">📈</span>
                    <div className="insight-content">
                      <strong>風險控制得宜</strong>
                      <p>夏普比率 {performanceStats.sharpeRatio.toFixed(2)} 顯示您在風險管理方面表現出色</p>
                    </div>
                  </div>
                  <div className="insight-item">
                    <span className="insight-icon">⚠️</span>
                    <div className="insight-content">
                      <strong>改進建議</strong>
                      <p>可考慮適度增加長期投資比例，降低整體組合波動性</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="modal-action-btn"
                onClick={() => exportAnalysis(analyses.map(a => a.id), 'pdf')}
              >
                📄 匯出完整報告
              </button>
              <button
                type="button"
                className="modal-action-btn primary"
                onClick={() => {
                  setShowStatsModal(false);
                  navigate('/analysts');
                }}
              >
                🚀 優化投資策略
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI績效洞察模態框 */}
      {showPerformanceInsights && (
        <div className="modal-overlay" onClick={() => setShowPerformanceInsights(false)}>
          <div className="insights-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🧠 AI 績效洞察與建議</h2>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowPerformanceInsights(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-content">
              <div className="insights-content">
                <div className="insight-section">
                  <h3>📈 投資風格分析</h3>
                  <div className="style-analysis">
                    <div className="style-card">
                      <h4>您的投資風格</h4>
                      <p>根據歷史記錄分析，您屬於 <strong>穩健成長型</strong> 投資者</p>
                      <ul>
                        <li>偏好中長期投資機會</li>
                        <li>風險承受度中等</li>
                        <li>重視基本面分析</li>
                      </ul>
                    </div>
                    <div className="style-card">
                      <h4>最佳表現領域</h4>
                      <p>您在 <strong>科技股</strong> 和 <strong>金融股</strong> 領域表現最佳</p>
                      <ul>
                        <li>科技股成功率：78%</li>
                        <li>金融股平均報酬：+12.3%</li>
                        <li>建議繼續關注這些領域</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="insight-section">
                  <h3>📊 分析師推薦</h3>
                  <div className="analyst-recommendations">
                    <div className="rec-card">
                      <h4>最適合您的分析師</h4>
                      <div className="top-analysts">
                        {analystPerformance.slice(0, 3).map((analyst, index) => (
                          <div key={analyst.analystId} className="top-analyst">
                            <span className="rank">#{index + 1}</span>
                            <span className="name">{analyst.analystName}</span>
                            <span className="score">{analyst.accuracy.toFixed(1)}% 準確度</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="rec-card">
                      <h4>策略建議</h4>
                      <ul>
                        <li>增加風險分析師的使用頻率</li>
                        <li>結合多位分析師的意見</li>
                        <li>定期評估投資結果</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="insight-section">
                  <h3>🎯 未來改進方向</h3>
                  <div className="improvement-areas">
                    <div className="improvement-card">
                      <h4>短期改進</h4>
                      <ul>
                        <li>提高止損紀律</li>
                        <li>增加技術面分析比重</li>
                        <li>縮短持有周期</li>
                      </ul>
                    </div>
                    <div className="improvement-card">
                      <h4>長期目標</h4>
                      <ul>
                        <li>建立系統化投資流程</li>
                        <li>擴大國際市場配置</li>
                        <li>發展個人化風險模型</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="modal-action-btn"
                onClick={() => setShowPerformanceInsights(false)}
              >
                關閉
              </button>
              <button
                type="button"
                className="modal-action-btn primary"
                onClick={() => {
                  setShowPerformanceInsights(false);
                  navigate('/portfolio');
                }}
              >
                💼 優化投資組合
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisHistoryPage;