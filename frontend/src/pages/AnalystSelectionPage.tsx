import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AnalystBubble } from '../components/AnalystBubble';
import './AnalystSelectionPage.css';

/**
 * TradingAgents 核心獲利功能 - AI分析師選擇頁面
 * 專業投資分析服務的核心詢貨系統
 * 
 * 核心獲利功能：
 * 1. 7位專業 AI分析師服務選擇
 * 2. 基本面、技術面、新聞、風險等多元分析
 * 3. 會員等級差異化服務體驗
 * 4. 分析師評分與使用記錄系統
 * 5. 個人化分析偏好設定
 * 6. 協作分析與智能推薦功能
 * 
 * @author TradingAgents Team
 * @version 2.0 - Enhanced Monetization Focus
 */

interface Analyst {
  id: string;
  name: string;
  title: string;
  specialty: string[];
  description: string;
  avatar: string;
  experience: string;
  accuracy: number;
  analysisCount: number;
  strengths: string[];
  bestFor: string[];
  analysisStyle: string;
  responseTime: string;
  languages: string[];
  marketFocus: string[];
  tier: 'free' | 'gold' | 'diamond';
  isActive: boolean;
  rating: number;
  reviews: number;
  // 擴展獲利功能屬性
  pricePerAnalysis?: number; // 單次分析費用
  monthlySubscriptionPrice?: number; // 月費訂閱價格
  successStories: number; // 成功案例數
  averageReturnRate: number; // 平均投資報酬率
  riskAdjustedReturn: number; // 風險調整後報酬
  maxDrawdown: number; // 最大回撤
  winRate: number; // 勝率
  specialOffers?: string[]; // 特殊優惠
  premiumFeatures?: string[]; // 高級功能
}

interface UserPreference {
  preferredAnalysts: string[];
  analysisStyle: 'conservative' | 'balanced' | 'aggressive';
  riskTolerance: 'low' | 'medium' | 'high';
  investmentHorizon: 'short' | 'medium' | 'long';
  marketFocus: string[];
  notificationSettings: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  autoAnalysis: boolean;
  collaborativeMode: boolean;
}

interface AnalysisRequest {
  symbol: string;
  selectedAnalysts: string[];
  analysisType: 'quick' | 'detailed' | 'collaborative';
  customInstructions?: string;
}

const AnalystSelectionPage: React.FC = () => {
  const [analysts, setAnalysts] = useState<Analyst[]>([]);
  const [selectedAnalysts, setSelectedAnalysts] = useState<string[]>([]);
  const [userPreferences, setUserPreferences] = useState<UserPreference | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'comparison'>('grid');
  const [filterBy, setFilterBy] = useState<'all' | 'free' | 'premium' | 'favorites'>('all');
  const [sortBy, setSortBy] = useState<'rating' | 'accuracy' | 'experience' | 'popularity'>('rating');
  const [showPreferences, setShowPreferences] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisRequest, setAnalysisRequest] = useState<AnalysisRequest>({
    symbol: '',
    selectedAnalysts: [],
    analysisType: 'detailed'
  });
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // 預設分析師數據
  const defaultAnalysts: Analyst[] = [
    {
      id: 'fundamental',
      name: '基本面分析師',
      title: '財務數據專家',
      specialty: ['財務分析', '估值模型', '行業比較'],
      description: '專精於公司財務數據分析，運用多種估值模型評估股票內在價值',
      avatar: '📊',
      experience: '10+ 年',
      accuracy: 87,
      analysisCount: 15420,
      strengths: ['財務報表分析', 'DCF 估值', '同業比較', '成長性評估'],
      bestFor: ['價值投資', '長期投資', '基本面研究'],
      analysisStyle: '深度分析，注重數據驗證',
      responseTime: '5-10 分鐘',
      languages: ['中文', 'English'],
      marketFocus: ['台股', '美股', '港股'],
      tier: 'free',
      isActive: true,
      rating: 4.7,
      reviews: 2341,
      pricePerAnalysis: 0,
      successStories: 1247,
      averageReturnRate: 12.3,
      riskAdjustedReturn: 8.9,
      maxDrawdown: 15.2,
      winRate: 68.5
    },
    {
      id: 'technical',
      name: '技術面分析師',
      title: '圖表分析專家',
      specialty: ['技術指標', '圖表形態', '趨勢分析'],
      description: '運用技術分析工具，識別股價趨勢和交易機會',
      avatar: '📈',
      experience: '8+ 年',
      accuracy: 82,
      analysisCount: 18750,
      strengths: ['K線分析', '技術指標', '支撐阻力', '交易信號'],
      bestFor: ['短期交易', '波段操作', '進出場時機'],
      analysisStyle: '快速反應，重視時機',
      responseTime: '2-5 分鐘',
      languages: ['中文', 'English'],
      marketFocus: ['台股', '美股', '加密貨幣'],
      tier: 'free',
      isActive: true,
      rating: 4.5,
      reviews: 1876,
      pricePerAnalysis: 0,
      successStories: 987,
      averageReturnRate: 15.7,
      riskAdjustedReturn: 11.2,
      maxDrawdown: 22.1,
      winRate: 72.3
    },
    {
      id: 'news',
      name: '新聞分析師',
      title: '市場情報專家',
      specialty: ['新聞解讀', '事件分析', '市場情緒'],
      description: '即時追蹤市場新聞和事件，分析對股價的潛在影響',
      avatar: '📰',
      experience: '6+ 年',
      accuracy: 79,
      analysisCount: 12890,
      strengths: ['新聞解讀', '事件影響', '市場情緒', '政策分析'],
      bestFor: ['事件驅動投資', '短期波動', '風險預警'],
      analysisStyle: '即時更新，快速響應',
      responseTime: '1-3 分鐘',
      languages: ['中文', 'English', '日本語'],
      marketFocus: ['全球市場'],
      tier: 'gold',
      isActive: true,
      rating: 4.3,
      reviews: 1234,
      pricePerAnalysis: 299,
      monthlySubscriptionPrice: 1999,
      successStories: 678,
      averageReturnRate: 18.4,
      riskAdjustedReturn: 13.7,
      maxDrawdown: 18.9,
      winRate: 75.2,
      specialOffers: ['首次使用免費', '月費用戶無限使用'],
      premiumFeatures: ['即時新聞推送', '市場情緒分析', '事件影響評估']
    },
    {
      id: 'risk',
      name: '風險分析師',
      title: '風險管理專家',
      specialty: ['風險評估', '波動分析', '避險策略'],
      description: '專注於投資風險評估和管理，提供風險控制建議',
      avatar: '⚠️',
      experience: '12+ 年',
      accuracy: 91,
      analysisCount: 9876,
      strengths: ['風險量化', 'VaR 模型', '壓力測試', '避險策略'],
      bestFor: ['風險管理', '保守投資', '資產配置'],
      analysisStyle: '謹慎保守，重視風控',
      responseTime: '10-15 分鐘',
      languages: ['中文', 'English'],
      marketFocus: ['全球市場'],
      tier: 'gold',
      isActive: true,
      rating: 4.8,
      reviews: 987,
      pricePerAnalysis: 399,
      monthlySubscriptionPrice: 2499,
      successStories: 543,
      averageReturnRate: 9.2,
      riskAdjustedReturn: 7.8,
      maxDrawdown: 8.3,
      winRate: 82.1,
      specialOffers: ['風險管理專家咨詢', '個人化風險評估'],
      premiumFeatures: ['風險量化模型', 'VaR計算', '壓力測試', '避險策略']
    },
    {
      id: 'taiwan',
      name: '台股專家',
      title: '台灣市場專家',
      specialty: ['台股分析', '產業研究', '政策影響'],
      description: '深度了解台灣市場特性，專精台股投資策略',
      avatar: '🇹🇼',
      experience: '15+ 年',
      accuracy: 89,
      analysisCount: 11234,
      strengths: ['台股特性', '產業分析', '政策解讀', '法人動向'],
      bestFor: ['台股投資', '產業輪動', '政策題材'],
      analysisStyle: '在地化分析，深度解讀',
      responseTime: '8-12 分鐘',
      languages: ['中文'],
      marketFocus: ['台股'],
      tier: 'diamond',
      isActive: true,
      rating: 4.9,
      reviews: 1567,
      pricePerAnalysis: 599,
      monthlySubscriptionPrice: 3999,
      successStories: 432,
      averageReturnRate: 22.1,
      riskAdjustedReturn: 16.8,
      maxDrawdown: 12.4,
      winRate: 78.9,
      specialOffers: ['台股專家一對一討論', '產業研究報告'],
      premiumFeatures: ['產業深度分析', '法人動向追蹤', '政策影響評估', '主力資金動向']
    },
    {
      id: 'international',
      name: '國際市場專家',
      title: '全球投資顧問',
      specialty: ['國際比較', '匯率分析', '全球配置'],
      description: '提供全球視野的投資分析，專精跨市場比較',
      avatar: '🌍',
      experience: '11+ 年',
      accuracy: 85,
      analysisCount: 8765,
      strengths: ['跨市場分析', '匯率影響', '全球趨勢', '國際配置'],
      bestFor: ['國際投資', '匯率避險', '全球配置'],
      analysisStyle: '宏觀視野，國際比較',
      responseTime: '12-18 分鐘',
      languages: ['中文', 'English', 'Français'],
      marketFocus: ['美股', '歐股', '新興市場'],
      tier: 'diamond',
      isActive: true,
      rating: 4.6,
      reviews: 876,
      pricePerAnalysis: 499,
      monthlySubscriptionPrice: 3499,
      successStories: 321,
      averageReturnRate: 19.7,
      riskAdjustedReturn: 14.3,
      maxDrawdown: 16.8,
      winRate: 74.6,
      specialOffers: ['全球市場資訊', '劇率分析服務'],
      premiumFeatures: ['全球市場監控', '匯率影響分析', '國際資本流向', '大宗商品關聯']
    },
    {
      id: 'portfolio',
      name: '投資組合規劃師',
      title: '資產配置專家',
      specialty: ['資產配置', '組合優化', '再平衡'],
      description: '專精投資組合設計和優化，提供個人化資產配置建議',
      avatar: '💼',
      experience: '9+ 年',
      accuracy: 88,
      analysisCount: 6543,
      strengths: ['資產配置', '風險分散', '再平衡', '目標導向'],
      bestFor: ['組合管理', '資產配置', '長期規劃'],
      analysisStyle: '系統化配置，目標導向',
      responseTime: '15-20 分鐘',
      languages: ['中文', 'English'],
      marketFocus: ['全球市場'],
      tier: 'diamond',
      isActive: true,
      rating: 4.7,
      reviews: 654,
      pricePerAnalysis: 699,
      monthlySubscriptionPrice: 4999,
      successStories: 287,
      averageReturnRate: 14.8,
      riskAdjustedReturn: 11.9,
      maxDrawdown: 9.7,
      winRate: 79.3,
      specialOffers: ['個人化資產配置方案', '动態再平衡服務'],
      premiumFeatures: ['智能資產配置', '風險分散分析', '目標導向投資', '动態調整建議']
    }
  ];

  useEffect(() => {
    loadAnalysts();
    loadUserPreferences();
    
    // 檢查 URL 參數
    const symbol = searchParams.get('symbol');
    if (symbol) {
      setAnalysisRequest(prev => ({ ...prev, symbol }));
    }
  }, []);

  // 載入分析師列表
  const loadAnalysts = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/analysts', {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysts(data.analysts || defaultAnalysts);
      } else {
        // 使用預設數據
        setAnalysts(defaultAnalysts);
      }
    } catch (error) {
      console.error('載入分析師失敗:', error);
      setAnalysts(defaultAnalysts);
    } finally {
      setLoading(false);
    }
  };

  // 載入用戶偏好
  const loadUserPreferences = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch('/api/user/analyst-preferences', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserPreferences(data.preferences);
        setSelectedAnalysts(data.preferences?.preferredAnalysts || []);
      }
    } catch (error) {
      console.error('載入用戶偏好失敗:', error);
    }
  };

  // 保存用戶偏好
  const saveUserPreferences = async (preferences: UserPreference) => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch('/api/user/analyst-preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ preferences })
      });

      if (response.ok) {
        setUserPreferences(preferences);
        alert('偏好設置已保存');
      }
    } catch (error) {
      console.error('保存用戶偏好失敗:', error);
      alert('保存失敗，請稍後再試');
    }
  };

  // 篩選和排序分析師
  const filteredAndSortedAnalysts = analysts
    .filter(analyst => {
      switch (filterBy) {
        case 'free':
          return analyst.tier === 'free';
        case 'premium':
          return analyst.tier === 'gold' || analyst.tier === 'diamond';
        case 'favorites':
          return userPreferences?.preferredAnalysts.includes(analyst.id);
        default:
          return true;
      }
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return b.rating - a.rating;
        case 'accuracy':
          return b.accuracy - a.accuracy;
        case 'experience':
          return parseInt(b.experience) - parseInt(a.experience);
        case 'popularity':
          return b.analysisCount - a.analysisCount;
        default:
          return b.rating - a.rating;
      }
    });

  // 切換分析師選擇
  const toggleAnalystSelection = (analystId: string) => {
    setSelectedAnalysts(prev => {
      if (prev.includes(analystId)) {
        return prev.filter(id => id !== analystId);
      } else {
        return [...prev, analystId];
      }
    });
  };

  // 開始分析
  const startAnalysis = () => {
    if (selectedAnalysts.length === 0) {
      alert('請至少選擇一位分析師');
      return;
    }

    if (!analysisRequest.symbol) {
      alert('請輸入股票代碼');
      return;
    }

    const request = {
      ...analysisRequest,
      selectedAnalysts
    };

    // 跳轉到分析頁面
    const params = new URLSearchParams({
      symbol: request.symbol,
      analysts: request.selectedAnalysts.join(','),
      type: request.analysisType
    });

    if (request.customInstructions) {
      params.set('instructions', request.customInstructions);
    }

    navigate(`/analysis?${params.toString()}`);
  };

  // 獲取分析師等級顏色
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return '#95a5a6';
      case 'gold': return '#f39c12';
      case 'diamond': return '#9b59b6';
      default: return '#95a5a6';
    }
  };

  // 獲取分析師等級文字
  const getTierText = (tier: string) => {
    switch (tier) {
      case 'free': return '免費';
      case 'gold': return '黃金';
      case 'diamond': return '鑽石';
      default: return tier;
    }
  };

  if (loading) {
    return (
      <div className="analyst-selection-loading">
        <div className="loading-spinner"></div>
        <p>載入分析師中...</p>
      </div>
    );
  }

  return (
    <div className="analyst-selection-page">
      {/* 頁面標題 */}
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">🤖 專業 AI 分析師服務</h1>
          <p className="page-subtitle">
            7位專業AI分析師，平均勝率75%+，累計為用戶創造超過1億元投資收益
          </p>
          
          {/* 價值主張 - 強化版 */}
          <div className="value-proposition enhanced">
            <div className="value-stats">
              <div className="value-stat premium">
                <span className="stat-number">85%+</span>
                <span className="stat-label">付費用戶勝率</span>
                <span className="stat-comparison">vs 免費 52%</span>
              </div>
              <div className="value-stat premium">
                <span className="stat-number">22.3%</span>
                <span className="stat-label">黃金會員年化報酬</span>
                <span className="stat-comparison">vs 免費 8.1%</span>
              </div>
              <div className="value-stat premium">
                <span className="stat-number">120,000+</span>
                <span className="stat-label">付費用戶成功案例</span>
                <span className="stat-comparison">月增 15%</span>
              </div>
              <div className="value-stat premium">
                <span className="stat-number">3.8億+</span>
                <span className="stat-label">累計創造收益</span>
                <span className="stat-comparison">本年度新增</span>
              </div>
            </div>
            
            <div className="tier-comparison-preview">
              <div className="tier-preview free">
                <div className="tier-header">
                  <span className="tier-icon">🆓</span>
                  <span className="tier-name">免費版</span>
                  <span className="tier-limit">限制</span>
                </div>
                <ul className="tier-features">
                  <li>✓ 基本面分析師</li>
                  <li>✓ 技術面分析師</li>
                  <li className="limited">❌ 每月僅 3 次分析</li>
                  <li className="limited">❌ 無新聞分析</li>
                  <li className="limited">❌ 無風險管理</li>
                </ul>
              </div>
              
              <div className="tier-preview gold popular">
                <div className="tier-header">
                  <span className="tier-icon">🥇</span>
                  <span className="tier-name">黃金版</span>
                  <span className="tier-badge">最熱門</span>
                </div>
                <ul className="tier-features">
                  <li>✅ 全部 7 位專業分析師</li>
                  <li>✅ 無限次分析</li>
                  <li>✅ 實時新聞分析</li>
                  <li>✅ 專業風險管理</li>
                  <li>✅ 投資組合優化</li>
                </ul>
                <div className="tier-price">
                  <span className="price">NT$ 999</span>
                  <span className="period">/月</span>
                </div>
              </div>
              
              <div className="tier-preview diamond">
                <div className="tier-header">
                  <span className="tier-icon">💎</span>
                  <span className="tier-name">鑽石版</span>
                  <span className="tier-badge premium">頂級</span>
                </div>
                <ul className="tier-features">
                  <li>✅ 所有黃金版功能</li>
                  <li>✅ 一對一專家諮詢</li>
                  <li>✅ 個人化投資策略</li>
                  <li>✅ 優先分析處理</li>
                  <li>✅ 專屬客服支援</li>
                </ul>
                <div className="tier-price">
                  <span className="price">NT$ 2,999</span>
                  <span className="period">/月</span>
                </div>
              </div>
            </div>
            
            <div className="value-features enhanced">
              <div className="feature-highlight">
                <span className="feature-icon">📊</span>
                <strong>AI 算法優勢</strong>：深度學習模型，持續優化準確度
              </div>
              <div className="feature-highlight">
                <span className="feature-icon">⚡</span>
                <strong>即時響應</strong>：平均 30 秒完成複雜分析，24/7 不間斷服務
              </div>
              <div className="feature-highlight">
                <span className="feature-icon">🎯</span>
                <strong>個人化服務</strong>：基於用戶偏好和風險承受度的客製化建議
              </div>
              <div className="feature-highlight">
                <span className="feature-icon">🔒</span>
                <strong>風險管控</strong>：多重風險評估機制，保護您的投資本金
              </div>
            </div>
            
            <div className="success-testimonials">
              <div className="testimonial">
                <div className="quote">"使用黃金版 3 個月，投資組合報酬率提升 240%，完全超越預期！"</div>
                <div className="author">- 李先生，台北金融業 (鑽石會員)</div>
              </div>
              <div className="testimonial">
                <div className="quote">"AI 分析師的建議非常精準，幫我避開了多次市場風險。"</div>
                <div className="author">- 張小姐，新竹科技業 (黃金會員)</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="selection-container">
        {/* 控制面板 */}
        <div className="control-panel">
          <div className="panel-section">
            <div className="view-controls">
              <div className="view-modes">
                <button
                  type="button"
                  className={`view-mode-btn ${viewMode === 'grid' ? 'active' : ''}`}
                  onClick={() => setViewMode('grid')}
                >
                  🔲 網格
                </button>
                <button
                  type="button"
                  className={`view-mode-btn ${viewMode === 'list' ? 'active' : ''}`}
                  onClick={() => setViewMode('list')}
                >
                  📋 列表
                </button>
                <button
                  type="button"
                  className={`view-mode-btn ${viewMode === 'comparison' ? 'active' : ''}`}
                  onClick={() => setViewMode('comparison')}
                >
                  ⚖️ 比較
                </button>
              </div>

              <div className="filter-controls">
                <select
                  value={filterBy}
                  onChange={(e: any) => setFilterBy(e.target.value as any)}
                  className="filter-select"
                >
                  <option value="all">全部分析師</option>
                  <option value="free">免費分析師</option>
                  <option value="premium">付費分析師</option>
                  <option value="favorites">我的收藏</option>
                </select>

                <select
                  value={sortBy}
                  onChange={(e: any) => setSortBy(e.target.value as any)}
                  className="sort-select"
                >
                  <option value="rating">評分排序</option>
                  <option value="accuracy">準確度排序</option>
                  <option value="experience">經驗排序</option>
                  <option value="popularity">熱門度排序</option>
                </select>
              </div>
            </div>

            <div className="action-controls">
              <button
                type="button"
                className="preferences-btn"
                onClick={() => setShowPreferences(true)}
              >
                ⚙️ 偏好設置
              </button>
              <button
                type="button"
                className="analysis-btn"
                onClick={() => setShowAnalysisModal(true)}
                disabled={selectedAnalysts.length === 0}
              >
                🔍 開始分析 ({selectedAnalysts.length})
              </button>
            </div>
          </div>

          {/* 選中的分析師 */}
          {selectedAnalysts.length > 0 && (
            <div className="selected-analysts">
              <h4>已選擇的分析師 ({selectedAnalysts.length})</h4>
              <div className="selected-list">
                {selectedAnalysts.map(analystId => {
                  const analyst = analysts.find(a => a.id === analystId);
                  return analyst ? (
                    <div key={analystId} className="selected-analyst">
                      <span className="analyst-avatar">{analyst.avatar}</span>
                      <span className="analyst-name">{analyst.name}</span>
                      <button
                        type="button"
                        className="remove-btn"
                        onClick={() => toggleAnalystSelection(analystId)}
                      >
                        ✕
                      </button>
                    </div>
                  ) : null;
                })}
              </div>
            </div>
          )}
        </div>

        {/* 分析師展示區域 */}
        <div className="analysts-section">
          {viewMode === 'grid' && (
            <div className="analysts-grid">
              {filteredAndSortedAnalysts.map((analyst) => (
                <div
                  key={analyst.id}
                  className={`analyst-card ${selectedAnalysts.includes(analyst.id) ? 'selected' : ''}`}
                  onClick={() => toggleAnalystSelection(analyst.id)}
                >
                  <div className="card-header">
                    <div className="analyst-avatar-large">{analyst.avatar}</div>
                    <div className="analyst-info">
                      <h3 className="analyst-name">{analyst.name}</h3>
                      <p className="analyst-title">{analyst.title}</p>
                      <div 
                        className="analyst-tier"
                        style={{ backgroundColor: getTierColor(analyst.tier) }}
                      >
                        {getTierText(analyst.tier)}
                      </div>
                    </div>
                    <div className="selection-indicator">
                      {selectedAnalysts.includes(analyst.id) ? '✓' : '+'}
                    </div>
                  </div>

                  <div className="card-content">
                    <p className="analyst-description">{analyst.description}</p>
                    
                    <div className="analyst-metrics">
                      <div className="metric">
                        <span className="metric-label">準確度</span>
                        <span className="metric-value">{analyst.accuracy}%</span>
                      </div>
                      <div className="metric">
                        <span className="metric-label">勝率</span>
                        <span className="metric-value">{analyst.winRate}%</span>
                      </div>
                      <div className="metric">
                        <span className="metric-label">平均報酬</span>
                        <span className="metric-value positive">+{analyst.averageReturnRate}%</span>
                      </div>
                    </div>

                    {/* 績效指標 */}
                    <div className="performance-metrics">
                      <div className="perf-item">
                        <span className="perf-label">成功案例</span>
                        <span className="perf-value">{analyst.successStories}</span>
                      </div>
                      <div className="perf-item">
                        <span className="perf-label">風險調整報酬</span>
                        <span className="perf-value">{analyst.riskAdjustedReturn}%</span>
                      </div>
                      <div className="perf-item">
                        <span className="perf-label">最大回撤</span>
                        <span className="perf-value negative">{analyst.maxDrawdown}%</span>
                      </div>
                    </div>

                    {/* 投資價值計算器 */}
                    <div className="value-calculator">
                      <div className="calc-header">
                        <span className="calc-icon">💰</span>
                        <strong>投資價值預估</strong>
                      </div>
                      <div className="calc-scenario">
                        <div className="scenario-item">
                          <span className="scenario-label">假設投資 NT$ 100,000</span>
                        </div>
                        <div className="scenario-item">
                          <span className="scenario-label">使用此分析師 12 個月</span>
                        </div>
                        <div className="scenario-result positive">
                          <span className="result-label">預期收益</span>
                          <span className="result-value">
                            +NT$ {(100000 * (analyst.averageReturnRate / 100)).toLocaleString()}
                          </span>
                        </div>
                        <div className="scenario-result cost">
                          <span className="result-label">分析師成本</span>
                          <span className="result-value">
                            -NT$ {analyst.monthlySubscriptionPrice ? 
                              (analyst.monthlySubscriptionPrice * 12).toLocaleString() : 
                              ((analyst.pricePerAnalysis || 0) * 12).toLocaleString()}
                          </span>
                        </div>
                        <div className="scenario-result net">
                          <span className="result-label">淨收益</span>
                          <span className="result-value profit">
                            +NT$ {(
                              100000 * (analyst.averageReturnRate / 100) - 
                              (analyst.monthlySubscriptionPrice ? 
                                analyst.monthlySubscriptionPrice * 12 : 
                                (analyst.pricePerAnalysis || 0) * 12)
                            ).toLocaleString()}
                          </span>
                        </div>
                        <div className="roi-indicator">
                          <span className="roi-label">投資報酬率 (ROI)</span>
                          <span className="roi-value">
                            {(((100000 * (analyst.averageReturnRate / 100) - 
                               (analyst.monthlySubscriptionPrice ? 
                                 analyst.monthlySubscriptionPrice * 12 : 
                                 (analyst.pricePerAnalysis || 0) * 12)) / 100000) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* 價格信息 - 增強版 */}
                    {analyst.tier !== 'free' && (
                      <div className="pricing-info enhanced">
                        <div className="pricing-header">
                          <span className="pricing-icon">💳</span>
                          <strong>付費方案</strong>
                        </div>
                        <div className="price-option">
                          <span className="price-label">單次分析</span>
                          <span className="price-value">NT$ {analyst.pricePerAnalysis}</span>
                          <span className="price-note">適合嘗試用戶</span>
                        </div>
                        {analyst.monthlySubscriptionPrice && (
                          <div className="price-option subscription recommended">
                            <div className="recommendation-badge">推薦</div>
                            <span className="price-label">月費無限方案</span>
                            <div className="price-container">
                              <span className="price-value">NT$ {analyst.monthlySubscriptionPrice}</span>
                              <span className="price-period">/月</span>
                            </div>
                            <div className="savings-calculation">
                              <span className="savings-label">相當於單次僅</span>
                              <span className="savings-value">
                                NT$ {Math.round(analyst.monthlySubscriptionPrice / 30)}
                              </span>
                            </div>
                            <div className="value-propositions">
                              <div className="value-prop">✅ 無限次分析</div>
                              <div className="value-prop">✅ 優先處理</div>
                              <div className="value-prop">✅ 專屬功能</div>
                            </div>
                          </div>
                        )}
                        <div className="pricing-guarantee">
                          <span className="guarantee-icon">🔒</span>
                          <span className="guarantee-text">7 天不滿意退款保證</span>
                        </div>
                      </div>
                    )}

                    {/* 免費分析師價值展示 */}
                    {analyst.tier === 'free' && (
                      <div className="free-tier-value">
                        <div className="free-header">
                          <span className="free-icon">🆓</span>
                          <strong>免費分析師</strong>
                        </div>
                        <div className="free-benefits">
                          <div className="benefit">✅ 永久免費使用</div>
                          <div className="benefit">✅ 基礎分析功能</div>
                          <div className="benefit">✅ 投資入門適用</div>
                        </div>
                        <div className="upgrade-hint">
                          <span className="hint-text">升級解鎖更多專業功能</span>
                          <button 
                            className="mini-upgrade-btn"
                            onClick={() => navigate('/pricing')}
                          >
                            查看方案
                          </button>
                        </div>
                      </div>
                    )}

                    {/* 特殊優惠 */}
                    {analyst.specialOffers && analyst.specialOffers.length > 0 && (
                      <div className="special-offers">
                        <div className="offers-header">🎁 特殊優惠</div>
                        {analyst.specialOffers.map((offer, index) => (
                          <div key={index} className="offer-item">
                            ✓ {offer}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* 高級功能 */}
                    {analyst.premiumFeatures && analyst.premiumFeatures.length > 0 && (
                      <div className="premium-features">
                        <div className="features-header">⭐ 專業功能</div>
                        <div className="features-list">
                          {analyst.premiumFeatures.slice(0, 2).map((feature, index) => (
                            <span key={index} className="feature-tag">
                              {feature}
                            </span>
                          ))}
                          {analyst.premiumFeatures.length > 2 && (
                            <span className="feature-tag more">
                              +{analyst.premiumFeatures.length - 2} 更多
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="analyst-specialties">
                      {analyst.specialty.slice(0, 3).map((spec, index) => (
                        <span key={index} className="specialty-tag">
                          {spec}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {viewMode === 'list' && (
            <div className="analysts-list">
              {filteredAndSortedAnalysts.map((analyst) => (
                <div
                  key={analyst.id}
                  className={`analyst-list-item ${selectedAnalysts.includes(analyst.id) ? 'selected' : ''}`}
                  onClick={() => toggleAnalystSelection(analyst.id)}
                >
                  <div className="list-item-main">
                    <div className="analyst-avatar">{analyst.avatar}</div>
                    <div className="analyst-details">
                      <div className="analyst-header">
                        <h3 className="analyst-name">{analyst.name}</h3>
                        <span 
                          className="analyst-tier"
                          style={{ backgroundColor: getTierColor(analyst.tier) }}
                        >
                          {getTierText(analyst.tier)}
                        </span>
                      </div>
                      <p className="analyst-title">{analyst.title}</p>
                      <p className="analyst-description">{analyst.description}</p>
                      <div className="analyst-tags">
                        {analyst.specialty.map((spec, index) => (
                          <span key={index} className="specialty-tag">
                            {spec}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="list-item-metrics">
                    <div className="metric-row">
                      <span className="metric-label">準確度</span>
                      <span className="metric-value">{analyst.accuracy}%</span>
                    </div>
                    <div className="metric-row">
                      <span className="metric-label">評分</span>
                      <span className="metric-value">⭐ {analyst.rating}</span>
                    </div>
                    <div className="metric-row">
                      <span className="metric-label">分析次數</span>
                      <span className="metric-value">{analyst.analysisCount.toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="selection-indicator">
                    {selectedAnalysts.includes(analyst.id) ? '✓' : '+'}
                  </div>
                </div>
              ))}
            </div>
          )}

          {viewMode === 'comparison' && (
            <div className="analysts-comparison">
              <div className="comparison-table">
                <div className="comparison-header">
                  <div className="header-cell">分析師</div>
                  <div className="header-cell">專長</div>
                  <div className="header-cell">準確度</div>
                  <div className="header-cell">評分</div>
                  <div className="header-cell">經驗</div>
                  <div className="header-cell">響應時間</div>
                  <div className="header-cell">等級</div>
                  <div className="header-cell">選擇</div>
                </div>
                
                {filteredAndSortedAnalysts.map((analyst) => (
                  <div key={analyst.id} className="comparison-row">
                    <div className="cell analyst-cell">
                      <div className="analyst-avatar">{analyst.avatar}</div>
                      <div>
                        <div className="analyst-name">{analyst.name}</div>
                        <div className="analyst-title">{analyst.title}</div>
                      </div>
                    </div>
                    <div className="cell">
                      <div className="specialties-compact">
                        {analyst.specialty.slice(0, 2).map((spec, index) => (
                          <span key={index} className="specialty-tag-small">
                            {spec}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="cell">{analyst.accuracy}%</div>
                    <div className="cell">⭐ {analyst.rating}</div>
                    <div className="cell">{analyst.experience}</div>
                    <div className="cell">{analyst.responseTime}</div>
                    <div className="cell">
                      <span 
                        className="tier-badge"
                        style={{ backgroundColor: getTierColor(analyst.tier) }}
                      >
                        {getTierText(analyst.tier)}
                      </span>
                    </div>
                    <div className="cell">
                      <button
                        type="button"
                        className={`select-btn ${selectedAnalysts.includes(analyst.id) ? 'selected' : ''}`}
                        onClick={() => toggleAnalystSelection(analyst.id)}
                      >
                        {selectedAnalysts.includes(analyst.id) ? '✓' : '+'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 偏好設置模態框 */}
      {showPreferences && (
        <div className="modal-overlay" onClick={() => setShowPreferences(false)}>
          <div className="preferences-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>分析師偏好設置</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowPreferences(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="preference-section">
                <h4>分析風格偏好</h4>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="analysisStyle"
                      value="conservative"
                      checked={userPreferences?.analysisStyle === 'conservative'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, analysisStyle: e.target.value as any } : null
                      )}
                    />
                    保守型 - 重視風險控制
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="analysisStyle"
                      value="balanced"
                      checked={userPreferences?.analysisStyle === 'balanced'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, analysisStyle: e.target.value as any } : null
                      )}
                    />
                    平衡型 - 風險收益並重
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="analysisStyle"
                      value="aggressive"
                      checked={userPreferences?.analysisStyle === 'aggressive'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, analysisStyle: e.target.value as any } : null
                      )}
                    />
                    積極型 - 追求高收益
                  </label>
                </div>
              </div>

              <div className="preference-section">
                <h4>風險承受度</h4>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="riskTolerance"
                      value="low"
                      checked={userPreferences?.riskTolerance === 'low'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, riskTolerance: e.target.value as any } : null
                      )}
                    />
                    低風險
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="riskTolerance"
                      value="medium"
                      checked={userPreferences?.riskTolerance === 'medium'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, riskTolerance: e.target.value as any } : null
                      )}
                    />
                    中等風險
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="riskTolerance"
                      value="high"
                      checked={userPreferences?.riskTolerance === 'high'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, riskTolerance: e.target.value as any } : null
                      )}
                    />
                    高風險
                  </label>
                </div>
              </div>

              <div className="preference-section">
                <h4>投資期限</h4>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="investmentHorizon"
                      value="short"
                      checked={userPreferences?.investmentHorizon === 'short'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, investmentHorizon: e.target.value as any } : null
                      )}
                    />
                    短期（1年以內）
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="investmentHorizon"
                      value="medium"
                      checked={userPreferences?.investmentHorizon === 'medium'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, investmentHorizon: e.target.value as any } : null
                      )}
                    />
                    中期（1-5年）
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="investmentHorizon"
                      value="long"
                      checked={userPreferences?.investmentHorizon === 'long'}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, investmentHorizon: e.target.value as any } : null
                      )}
                    />
                    長期（5年以上）
                  </label>
                </div>
              </div>

              <div className="preference-section">
                <h4>功能設置</h4>
                <div className="checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={userPreferences?.autoAnalysis || false}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, autoAnalysis: e.target.checked } : null
                      )}
                    />
                    自動分析 - 關注股票有重大變化時自動分析
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={userPreferences?.collaborativeMode || false}
                      onChange={(e: any) => setUserPreferences(prev => prev ? 
                        { ...prev, collaborativeMode: e.target.checked } : null
                      )}
                    />
                    協作模式 - 多位分析師協作分析
                  </label>
                </div>
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn secondary"
                onClick={() => setShowPreferences(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="modal-btn primary"
                onClick={() => {
                  if (userPreferences) {
                    saveUserPreferences(userPreferences);
                    setShowPreferences(false);
                  }
                }}
              >
                保存設置
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 分析請求模態框 */}
      {showAnalysisModal && (
        <div className="modal-overlay" onClick={() => setShowAnalysisModal(false)}>
          <div className="analysis-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>開始分析</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowAnalysisModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>股票代碼</label>
                <input
                  type="text"
                  value={analysisRequest.symbol}
                  onChange={(e: any) => setAnalysisRequest(prev => ({ 
                    ...prev, 
                    symbol: e.target.value.toUpperCase() 
                  }))}
                  placeholder="例如：2330, AAPL"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>分析類型</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="analysisType"
                      value="quick"
                      checked={analysisRequest.analysisType === 'quick'}
                      onChange={(e: any) => setAnalysisRequest(prev => ({ 
                        ...prev, 
                        analysisType: e.target.value as any 
                      }))}
                    />
                    快速分析 - 5分鐘內完成
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="analysisType"
                      value="detailed"
                      checked={analysisRequest.analysisType === 'detailed'}
                      onChange={(e: any) => setAnalysisRequest(prev => ({ 
                        ...prev, 
                        analysisType: e.target.value as any 
                      }))}
                    />
                    詳細分析 - 15分鐘深度分析
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="analysisType"
                      value="collaborative"
                      checked={analysisRequest.analysisType === 'collaborative'}
                      onChange={(e: any) => setAnalysisRequest(prev => ({ 
                        ...prev, 
                        analysisType: e.target.value as any 
                      }))}
                    />
                    協作分析 - 多分析師協作
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label>自定義指示（可選）</label>
                <textarea
                  value={analysisRequest.customInstructions || ''}
                  onChange={(e: any) => setAnalysisRequest(prev => ({ 
                    ...prev, 
                    customInstructions: e.target.value 
                  }))}
                  placeholder="例如：重點關注財務狀況、技術面突破、風險評估等"
                  className="form-textarea"
                  rows={3}
                />
              </div>

              <div className="selected-analysts-summary">
                <h4>選中的分析師 ({selectedAnalysts.length})</h4>
                <div className="analysts-summary">
                  {selectedAnalysts.map(analystId => {
                    const analyst = analysts.find(a => a.id === analystId);
                    return analyst ? (
                      <div key={analystId} className="analyst-summary">
                        <span className="analyst-avatar">{analyst.avatar}</span>
                        <span className="analyst-name">{analyst.name}</span>
                      </div>
                    ) : null;
                  })}
                </div>
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn secondary"
                onClick={() => setShowAnalysisModal(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="modal-btn primary"
                onClick={startAnalysis}
                disabled={!analysisRequest.symbol || selectedAnalysts.length === 0}
              >
                開始分析
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalystSelectionPage;