import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DialogueContainer } from '../components/DialogueContainer';
import SubscriptionPlanCard from '../components/SubscriptionPlanCard';
import { UserPreferencesPanel } from '../components/UserPreferencesPanel';
import './UserDashboard.css';

/**
 * TradingAgents 核心獲利功能 - 會員儀表板
 * 專業投資分析平台的核心會員體驗頁面
 * 
 * 核心獲利功能：
 * 1. 個人化投資概覽與智能推薦
 * 2. 會員等級權益展示與升級引導
 * 3. AI分析師服務使用統計
 * 4. 投資組合績效追蹤
 * 5. 市場機會實時推送
 * 6. 專業分析工具快速入口
 * 
 * @author TradingAgents Team
 * @version 2.0 - Enhanced Monetization Focus
 */

interface User {
  id: string;
  name: string;
  email: string;
  tier: 'free' | 'gold' | 'diamond';
  avatar?: string;
  joinDate: string;
  analysisCount: number;
  analysisLimit: number;
  // 擴展會員價值追蹤
  totalValue: number; // 投資組合總價值
  monthlyReturn: number; // 月回報率
  successRate: number; // AI建議成功率
  premiumFeatures: string[]; // 已解鎖功能
  nextUpgrade?: {
    tier: string;
    benefits: string[];
    price: number;
  };
}

interface RecentAnalysis {
  id: string;
  symbol: string;
  companyName: string;
  analysisType: string;
  result: 'buy' | 'sell' | 'hold';
  confidence: number;
  createdAt: string;
}

interface MarketAlert {
  id: string;
  type: 'price' | 'technical' | 'news' | 'ai_insight' | 'opportunity';
  symbol: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'urgent';
  createdAt: string;
  // 增強市場洞察
  actionable: boolean; // 是否可操作
  potentialReturn?: number; // 潜在回報
  riskLevel?: number; // 風險等級
  analystRecommendation?: string; // AI分析師建議
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: string;
  action: () => void;
  disabled?: boolean;
}

const UserDashboard: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>([]);
  const [marketAlerts, setMarketAlerts] = useState<MarketAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showSubscriptionPrompt, setShowSubscriptionPrompt] = useState(true);
  // 擴展狀態管理
  const [portfolioStats, setPortfolioStats] = useState<any>(null);
  const [marketOpportunities, setMarketOpportunities] = useState<any[]>([]);
  const [aiInsights, setAiInsights] = useState<any[]>([]);
  const [upgradePrompt, setUpgradePrompt] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const isGuestMode = searchParams.get('mode') === 'guest';

  useEffect(() => {
    loadUserData();
    loadRecentAnalyses();
    loadMarketAlerts();
    loadPortfolioStats();
    loadMarketOpportunities();
    loadAiInsights();
    
    // 設置實時更新
    const interval = setInterval(() => {
      loadMarketAlerts();
      loadAiInsights();
    }, 30000); // 30秒更新一次
    
    return () => clearInterval(interval);
  }, []);

  const loadUserData = async () => {
    try {
      if (isGuestMode) {
        // 訪客模式數據
        setUser({
          id: 'guest',
          name: '訪客用戶',
          email: 'guest@example.com',
          tier: 'free',
          joinDate: new Date().toISOString(),
          analysisCount: 0,
          analysisLimit: 3,
          totalValue: 0,
          monthlyReturn: 0,
          successRate: 0,
          premiumFeatures: [],
          nextUpgrade: {
            tier: 'gold',
            benefits: ['無限分析次數', '高級分析師', '實時警示', '投資組合建議'],
            price: 999
          }
        });
      } else {
        // 從 localStorage 獲取用戶數據 - 支持前端模式和後端模式
        const userInfo = localStorage.getItem('user_info');
        const authToken = localStorage.getItem('auth_token');
        
        // 檢查前端模式認證
        const frontendAuth = localStorage.getItem('frontend_google_auth');
        const frontendEmail = localStorage.getItem('frontend_user_email');
        const frontendName = localStorage.getItem('frontend_user_name');
        
        console.log('🔍 UserDashboard 認證檢查:', {
          hasUserInfo: !!userInfo,
          hasAuthToken: !!authToken,
          hasFrontendAuth: frontendAuth === 'true',
          frontendEmail,
          frontendName
        });
        
        if (userInfo && authToken) {
          // 後端模式：使用完整的用戶數據
          const userData = JSON.parse(userInfo);
          setUser({
            ...userData,
            totalValue: userData.totalValue || 0,
            monthlyReturn: userData.monthlyReturn || 0,
            successRate: userData.successRate || 0,
            premiumFeatures: userData.premiumFeatures || [],
            nextUpgrade: userData.tier === 'free' ? {
              tier: 'gold',
              benefits: ['無限分析次數', '高級分析師', '實時警示', '投資組合建議'],
              price: 999
            } : undefined
          });
          console.log('✅ 後端模式用戶數據載入成功');
        } else if (frontendAuth === 'true' && frontendEmail && frontendName) {
          // 前端模式：創建基本用戶數據
          const frontendUser = {
            id: 'frontend_user',
            name: frontendName,
            email: frontendEmail,
            tier: 'free',
            joinDate: new Date().toISOString(),
            analysisCount: 0,
            analysisLimit: 5,
            totalValue: 0,
            monthlyReturn: 0,
            successRate: 0,
            premiumFeatures: [],
            nextUpgrade: {
              tier: 'gold',
              benefits: ['無限分析次數', '高級分析師', '實時警示', '投資組合建議'],
              price: 1999
            }
          };
          setUser(frontendUser);
          console.log('✅ 前端模式用戶數據載入成功:', frontendUser);
        } else {
          // 沒有有效的登入信息，跳轉到登入頁
          console.log('❌ 無有效認證信息，跳轉到登入頁');
          navigate('/auth?mode=login');
        }
      }
    } catch (error) {
      console.error('載入用戶數據失敗:', error);
      // 如果數據載入失敗，跳轉到登入頁
      navigate('/auth?mode=login');
    } finally {
      setLoading(false);
    }
  };

  // 加載投資組合統計 - 使用模擬數據
  const loadPortfolioStats = async () => {
    try {
      // 模擬投資組合統計數據
      const mockPortfolioStats = {
        totalValue: 1250000,
        totalReturn: 8.5,
        monthlyReturn: 2.3,
        winRate: 73.2,
        positions: 8,
        lastUpdated: new Date().toISOString()
      };
      
      setPortfolioStats(mockPortfolioStats);
    } catch (error) {
      console.error('載入投資組合統計失敗:', error);
    }
  };

  // 加載市場機會 - 使用模擬數據
  const loadMarketOpportunities = async () => {
    try {
      // 模擬市場機會數據
      const mockOpportunities = [
        {
          id: '1',
          symbol: '2330',
          title: '台積電技術突破機會',
          description: '3奈米製程領先優勢擴大，AI晶片需求暴增',
          type: '技術分析',
          potentialReturn: 15.8,
          riskLevel: 2,
          confidence: 87
        },
        {
          id: '2',
          symbol: '2454',
          title: '聯發科5G晶片回升',
          description: '中階5G手機市場復甦，營收成長看好',
          type: '基本面分析',
          potentialReturn: 22.3,
          riskLevel: 3,
          confidence: 74
        },
        {
          id: '3',
          symbol: '2317',
          title: '鴻海電動車轉型',
          description: 'MIH平台發展順利，電動車代工訂單增加',
          type: '產業分析',
          potentialReturn: 18.5,
          riskLevel: 4,
          confidence: 69
        }
      ];
      
      setMarketOpportunities(mockOpportunities);
    } catch (error) {
      console.error('載入市場機會失敗:', error);
    }
  };

  // 加載AI洞察 - 使用模擬數據
  const loadAiInsights = async () => {
    try {
      // 模擬AI洞察數據
      const mockInsights = [
        {
          id: '1',
          analystType: 'fundamental',
          analystName: '基本面分析師 Alex',
          title: '台股科技股估值修正完成',
          content: '經過Q2財報季調整，台股科技股PE ratio已回到合理區間，建議關注AI供應鏈龍頭股',
          confidence: 85,
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2小時前
          actionable: true
        },
        {
          id: '2',
          analystType: 'technical',
          analystName: '技術分析師 Sarah',
          title: '大盤突破季線壓力',
          content: '加權指數成功突破季線並站穩，成交量配合良好，短期多頭格局確立',
          confidence: 78,
          createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4小時前
          actionable: true
        },
        {
          id: '3',
          analystType: 'news',
          analystName: '新聞分析師 Mike',
          title: '美國降息預期升溫',
          content: 'Fed官員鴿派發言，市場預期年底前降息機率達75%，有利資金回流新興市場',
          confidence: 72,
          createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6小時前
          actionable: false
        }
      ];
      
      setAiInsights(mockInsights);
    } catch (error) {
      console.error('載入AI洞察失敗:', error);
    }
  };

  const loadRecentAnalyses = async () => {
    try {
      // 從 localStorage 讀取分析歷史，如果沒有則使用模擬數據
      const storedAnalyses = localStorage.getItem('recent_analyses');
      
      if (storedAnalyses) {
        const analyses = JSON.parse(storedAnalyses);
        setRecentAnalyses(analyses.slice(0, 5)); // 只顯示前5筆
      } else {
        // 模擬分析記錄數據（新用戶）
        const mockAnalyses = [
          {
            id: '1',
            symbol: '2330',
            companyName: '台灣積體電路',
            analysisType: '綜合分析',
            result: 'buy',
            confidence: 87,
            createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() // 1天前
          },
          {
            id: '2',
            symbol: '2454',
            companyName: '聯發科技',
            analysisType: '技術分析',
            result: 'hold',
            confidence: 72,
            createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() // 2天前
          }
        ];
        setRecentAnalyses(mockAnalyses);
      }
    } catch (error) {
      console.error('載入分析記錄失敗:', error);
      setRecentAnalyses([]); // 如果出錯就設為空陣列
    }
  };

  const loadMarketAlerts = async () => {
    try {
      // 模擬市場預警數據
      const mockAlerts = [
        {
          id: '1',
          type: 'price',
          symbol: '2330',
          message: '台積電股價突破600元，創近期新高',
          severity: 'medium',
          createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30分鐘前
          actionable: true,
          potentialReturn: 5.2,
          riskLevel: 2
        },
        {
          id: '2',
          type: 'technical',
          symbol: '2454',
          message: '聯發科出現黃金交叉訊號，建議關注',
          severity: 'high',
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2小時前
          actionable: true,
          potentialReturn: 8.7,
          riskLevel: 3
        },
        {
          id: '3',
          type: 'news',
          symbol: '2317',
          message: '鴻海公布電動車新訂單，股價有望上漲',
          severity: 'low',
          createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4小時前
          actionable: false,
          riskLevel: 4
        }
      ];
      
      setMarketAlerts(mockAlerts);
    } catch (error) {
      console.error('載入市場預警失敗:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('guest_session');
    navigate('/');
  };

  const handleUpgrade = () => {
    console.log('🔥 UserDashboard.handleUpgrade 被調用！即將跳轉到 /pricing');
    try {
      navigate('/pricing');
      console.log('✅ navigate("/pricing") 調用成功');
    } catch (error) {
      console.error('❌ navigate 調用失敗:', error);
    }
  };

  const handleStartAnalysis = () => {
    navigate('/analysis');
  };

  const handleViewHistory = () => {
    navigate('/analysis/history');
  };

  const handlePortfolio = () => {
    navigate('/portfolio');
  };

  const handleAnalystSelection = () => {
    navigate('/analysts');
  };

  const handleMarketMonitor = () => {
    navigate('/market-monitor');
  };

  const handleStockSearch = () => {
    navigate('/stock-search');
  };

  const handleSettings = () => {
    setShowPreferences(true);
  };

  // 快速操作按鈕 - 核心獲利功能入口
  const quickActions: QuickAction[] = [
    {
      id: 'stock-search',
      title: '智能股票搜尋',
      description: '台股國際同業比較分析',
      icon: '🔎',
      action: handleStockSearch
    },
    {
      id: 'analyst-selection',
      title: 'AI分析師',
      description: '7位專業分析師服務',
      icon: '🤖',
      action: handleAnalystSelection,
      disabled: user?.tier === 'free' && user?.analysisCount >= user?.analysisLimit
    },
    {
      id: 'portfolio',
      title: '投資組合',
      description: '組合管理與風險評估',
      icon: '📊',
      action: handlePortfolio
    },
    {
      id: 'market-monitor',
      title: '市場監控',
      description: '實時市場監控儀表板',
      icon: '💹',
      action: handleMarketMonitor
    },
    {
      id: 'history',
      title: '分析歷史',
      description: '成功率統計與投資追蹤',
      icon: '📋',
      action: handleViewHistory
    },
    {
      id: 'analysis',
      title: '快速分析',
      description: '一鍵分析任意股票',
      icon: '⚡',
      action: handleStartAnalysis,
      disabled: user?.analysisCount >= user?.analysisLimit && user?.tier === 'free'
    }
  ];

  const getTierDisplayName = (tier: string) => {
    switch (tier) {
      case 'free': return '免費版';
      case 'gold': return '黃金版';
      case 'diamond': return '鑽石版';
      default: return tier;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return '#95a5a6';
      case 'gold': return '#f39c12';
      case 'diamond': return '#9b59b6';
      default: return '#95a5a6';
    }
  };

  const getResultColor = (result: string) => {
    switch (result) {
      case 'buy': return '#27ae60';
      case 'sell': return '#e74c3c';
      case 'hold': return '#f39c12';
      default: return '#95a5a6';
    }
  };

  const getAlertSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent': return '#c0392b';
      case 'high': return '#e74c3c';
      case 'medium': return '#f39c12';
      case 'low': return '#3498db';
      default: return '#95a5a6';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>載入中...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="dashboard-error">
        <h2>載入失敗</h2>
        <p>無法載入用戶資料，請重新登入</p>
        <button type="button" onClick={() => navigate('/auth?mode=login')}>
          重新登入
        </button>
      </div>
    );
  }

  return (
    <div className="user-dashboard">
      {/* 頂部導航 */}
      <header className="dashboard-header">
        <div className="header-container">
          <div className="header-brand">
            <span className="brand-icon">🤖</span>
            <span className="brand-text">TradingAgents</span>
          </div>
          
          <div className="header-actions">
            <button type="button" className="header-button" onClick={handleSettings}>
              <span className="button-icon">⚙️</span>
              設置
            </button>
            <button type="button" className="header-button" onClick={handleLogout}>
              <span className="button-icon">🚪</span>
              登出
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard-container">
        {/* 側邊欄 */}
        <aside className="dashboard-sidebar">
          <div className="user-profile">
            <div className="profile-avatar">
              {user.avatar ? (
                <img src={user.avatar} alt={user.name} />
              ) : (
                <span className="avatar-placeholder">
                  {user.name.charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            <div className="profile-info">
              <h3 className="profile-name">{user.name}</h3>
              <p className="profile-email">{user.email}</p>
              <div className="profile-tier">
                <span 
                  className="tier-badge"
                  style={{ backgroundColor: getTierColor(user.tier) }}
                >
                  {getTierDisplayName(user.tier)}
                </span>
              </div>
            </div>
          </div>

          {/* 會員價值與使用統計 */}
          <div className="member-value-stats">
            <h4>投資成果</h4>
            {user.totalValue > 0 && (
              <>
                <div className="stat-item">
                  <span className="stat-label">組合價值</span>
                  <span className="stat-value">{formatCurrency(user.totalValue)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">月回報率</span>
                  <span 
                    className="stat-value"
                    style={{ color: user.monthlyReturn >= 0 ? '#27ae60' : '#e74c3c' }}
                  >
                    {formatPercentage(user.monthlyReturn)}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">AI成功率</span>
                  <span className="stat-value">{user.successRate.toFixed(1)}%</span>
                </div>
              </>
            )}
            <div className="stat-item">
              <span className="stat-label">分析次數</span>
              <span className="stat-value">
                {user.analysisCount} / {user.analysisLimit === -1 ? '無限' : user.analysisLimit}
              </span>
            </div>
            <div className="usage-progress">
              <div 
                className="progress-bar"
                style={{ 
                  width: user.analysisLimit === -1 ? '100%' : 
                    `${Math.min((user.analysisCount / user.analysisLimit) * 100, 100)}%` 
                }}
              ></div>
            </div>
            {user.tier === 'free' && user?.analysisCount >= user?.analysisLimit && (
              <button type="button" className="upgrade-button" onClick={handleUpgrade}>
                升級解鎖更多分析
              </button>
            )}
            
            {/* 會員等級升級提示 */}
            {user.nextUpgrade && user.tier === 'free' && (
              <div className="upgrade-incentive">
                <div className="upgrade-header">
                  <span className="upgrade-icon">✨</span>
                  <strong>升級至{user.nextUpgrade.tier.toUpperCase()}</strong>
                </div>
                <ul className="upgrade-benefits">
                  {(user.nextUpgrade.benefits || []).slice(0, 2).map((benefit, index) => (
                    <li key={index}>{benefit}</li>
                  ))}
                </ul>
                <div className="upgrade-price">
                  月費 {formatCurrency(user.nextUpgrade.price)}
                </div>
              </div>
            )}
          </div>

          {/* 導航菜單 */}
          <nav className="dashboard-nav">
            <a href="/dashboard" className="nav-item active">
              <span className="nav-icon">🏠</span>
              儀表板
            </a>
            <a href="/stock-search" className="nav-item">
              <span className="nav-icon">🔎</span>
              股票搜尋
            </a>
            <a href="/analysts" className="nav-item">
              <span className="nav-icon">🤖</span>
              AI分析師
            </a>
            <a href="/portfolio" className="nav-item">
              <span className="nav-icon">📊</span>
              投資組合
            </a>
            <a href="/analysis/history" className="nav-item">
              <span className="nav-icon">📋</span>
              分析歷史
            </a>
            <a href="/market-monitor" className="nav-item">
              <span className="nav-icon">💹</span>
              市場監控
            </a>
          </nav>
        </aside>

        {/* 主要內容 */}
        <main className="dashboard-main">
          {/* 歡迎區塊 */}
          <section className="welcome-section">
            <div className="welcome-content">
              <h1 className="welcome-title">
                {isGuestMode ? '歡迎體驗 TradingAgents' : `歡迎回來，${user.name}`}
              </h1>
              <p className="welcome-subtitle">
                {isGuestMode 
                  ? '您有 3 次免費分析機會，立即開始探索 AI 投資分析的強大功能'
                  : '準備好開始今天的投資分析了嗎？'
                }
              </p>
            </div>
            
            {isGuestMode && (
              <div className="guest-notice">
                <div className="notice-content">
                  <span className="notice-icon">🎯</span>
                  <div className="notice-text">
                    <strong>免費體驗模式</strong>
                    <p>剩餘 {user.analysisLimit - user.analysisCount} 次分析機會</p>
                  </div>
                </div>
                <button type="button" className="upgrade-cta" onClick={() => navigate('/auth?mode=register')}>
                  註冊解鎖完整功能
                </button>
              </div>
            )}
          </section>

          {/* 快速操作 */}
          <section className="quick-actions-section">
            <h2 className="section-title">快速操作</h2>
            <div className="quick-actions-grid">
              {(quickActions || []).map((action) => (
                <button
                  key={action.id}
                  type="button"
                  className={`quick-action-card ${action.disabled ? 'disabled' : ''}`}
                  onClick={action.action}
                  disabled={action.disabled}
                >
                  <div className="action-icon">{action.icon}</div>
                  <div className="action-content">
                    <h3 className="action-title">{action.title}</h3>
                    <p className="action-description">{action.description}</p>
                  </div>
                  {action.disabled && (
                    <div className="action-overlay">
                      <span>需要升級</span>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </section>

          {/* 最近分析 */}
          <section className="recent-analyses-section">
            <div className="section-header">
              <h2 className="section-title">最近分析</h2>
              <button type="button" className="view-all-button" onClick={handleViewHistory}>
                查看全部
              </button>
            </div>
            
            {recentAnalyses.length > 0 ? (
              <div className="analyses-list">
                {(recentAnalyses || []).map((analysis) => (
                  <div key={analysis.id} className="analysis-item">
                    <div className="analysis-symbol">
                      <strong>{analysis.symbol}</strong>
                      <span className="company-name">{analysis.companyName}</span>
                    </div>
                    <div className="analysis-type">{analysis.analysisType}</div>
                    <div 
                      className="analysis-result"
                      style={{ color: getResultColor(analysis.result) }}
                    >
                      {analysis.result.toUpperCase()}
                    </div>
                    <div className="analysis-confidence">
                      信心度: {analysis.confidence}%
                    </div>
                    <div className="analysis-date">
                      {formatDate(analysis.createdAt)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📊</div>
                <h3>還沒有分析記錄</h3>
                <p>開始您的第一次股票分析吧！</p>
                <button type="button" className="start-analysis-button" onClick={handleStartAnalysis}>
                  開始分析
                </button>
              </div>
            )}
          </section>

          {/* 市場預警 */}
          <section className="market-alerts-section">
            <div className="section-header">
              <h2 className="section-title">市場預警</h2>
              <button type="button" className="view-all-button" onClick={() => navigate('/market')}>
                查看全部
              </button>
            </div>
            
            {marketAlerts.length > 0 ? (
              <div className="alerts-list">
                {(marketAlerts || []).map((alert) => (
                  <div key={alert.id} className="alert-item">
                    <div 
                      className="alert-indicator"
                      style={{ backgroundColor: getAlertSeverityColor(alert.severity) }}
                    ></div>
                    <div className="alert-content">
                      <div className="alert-header">
                        <span className="alert-symbol">{alert.symbol}</span>
                        <span className="alert-type">{alert.type}</span>
                      </div>
                      <p className="alert-message">{alert.message}</p>
                      <span className="alert-time">{formatDate(alert.createdAt)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🔔</div>
                <h3>暫無市場預警</h3>
                <p>我們會在重要市場事件發生時通知您</p>
              </div>
            )}
          </section>

          {/* 市場機會 - 核心獲利功能 */}
          {marketOpportunities.length > 0 && (
            <section className="market-opportunities-section">
              <div className="section-header">
                <h2 className="section-title">
                  <span className="section-icon">💡</span>
                  市場機會
                </h2>
                <button type="button" className="view-all-button" onClick={() => navigate('/market-monitor')}>
                  查看全部
                </button>
              </div>
              
              <div className="opportunities-grid">
                {(marketOpportunities || []).map((opportunity, index) => (
                  <div key={index} className="opportunity-card">
                    <div className="opportunity-header">
                      <span className="opportunity-symbol">{opportunity.symbol}</span>
                      <span className="opportunity-type">{opportunity.type}</span>
                    </div>
                    <h4 className="opportunity-title">{opportunity.title}</h4>
                    <p className="opportunity-description">{opportunity.description}</p>
                    <div className="opportunity-metrics">
                      <div className="metric">
                        <span className="metric-label">潛在回報</span>
                        <span className="metric-value positive">+{opportunity.potentialReturn}%</span>
                      </div>
                      <div className="metric">
                        <span className="metric-label">風險等級</span>
                        <span className={`metric-value risk-${opportunity.riskLevel}`}>
                          {opportunity.riskLevel}/5
                        </span>
                      </div>
                    </div>
                    <button 
                      type="button" 
                      className="opportunity-action"
                      onClick={() => navigate(`/stock-search?symbol=${opportunity.symbol}`)}
                    >
                      立即分析
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* AI洞察 - 專業投資建議 */}
          {aiInsights.length > 0 && (
            <section className="ai-insights-section">
              <div className="section-header">
                <h2 className="section-title">
                  <span className="section-icon">🧠</span>
                  AI投資洞察
                </h2>
                <button type="button" className="view-all-button" onClick={() => navigate('/analysts')}>
                  更多洞察
                </button>
              </div>
              
              <div className="insights-list">
                {(aiInsights || []).map((insight, index) => (
                  <div key={index} className="insight-item">
                    <div className="insight-header">
                      <div className="insight-analyst">
                        <span className="analyst-avatar">{insight.analystType === 'fundamental' ? '📊' : insight.analystType === 'technical' ? '📈' : '📰'}</span>
                        <span className="analyst-name">{insight.analystName}</span>
                      </div>
                      <span className="insight-confidence">
                        信心度: {insight.confidence}%
                      </span>
                    </div>
                    <h4 className="insight-title">{insight.title}</h4>
                    <p className="insight-content">{insight.content}</p>
                    <div className="insight-actions">
                      <span className="insight-time">{formatDate(insight.createdAt)}</span>
                      <button 
                        type="button" 
                        className="insight-action"
                        onClick={() => navigate(`/analysts?type=${insight.analystType}`)}
                      >
                        查看詳情
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 會員升級CTA - 強化版本 */}
          {user.tier === 'free' && (
            <section className="premium-cta-section enhanced">
              <div className="premium-cta-card">
                <div className="premium-icon-section">
                  <div className="premium-icon">👑</div>
                  <div className="value-highlights">
                    <div className="highlight-badge success">平均年化報酬 +15.8%</div>
                    <div className="highlight-badge roi">已為用戶創造 1億+ 投資收益</div>
                  </div>
                </div>
                <div className="premium-content">
                  <h3>解鎖專業投資功能，提升投資績效</h3>
                  <p>升級用戶平均投資回報率比免費用戶高出 240%，立即加入 10,000+ 成功投資者行列</p>
                  
                  <div className="comparison-grid">
                    <div className="comparison-column current">
                      <h4>目前免費版</h4>
                      <ul className="feature-list">
                        <li className="limited">每月 {user.analysisLimit} 次分析</li>
                        <li className="limited">僅基本分析師</li>
                        <li className="limited">無投資組合管理</li>
                        <li className="limited">無實時警報</li>
                      </ul>
                    </div>
                    <div className="comparison-column upgrade">
                      <h4>升級後黃金版 <span className="savings">節省 60%</span></h4>
                      <ul className="feature-list">
                        <li>✅ 無限次股票分析</li>
                        <li>✅ 7位專業AI分析師</li>
                        <li>✅ 智能投資組合優化</li>
                        <li>✅ 實時市場監控警報</li>
                        <li>✅ 專業風險管理工具</li>
                        <li>✅ 國際市場分析</li>
                        <li>✅ 優先客服支援</li>
                        <li>✅ 高級技術指標</li>
                      </ul>
                    </div>
                  </div>
                  
                  <div className="success-metrics">
                    <div className="metric-item">
                      <span className="metric-number">75%+</span>
                      <span className="metric-label">用戶獲利比例</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-number">2.4x</span>
                      <span className="metric-label">投資回報提升</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-number">30天</span>
                      <span className="metric-label">平均回本週期</span>
                    </div>
                  </div>
                </div>
                <div className="premium-action">
                  <div className="pricing-options">
                    <div className="price-option recommended">
                      <div className="price-header">
                        <span className="price-tag">推薦</span>
                        <span className="price-amount">NT$ 999</span>
                        <span className="price-period">/月</span>
                      </div>
                      <div className="price-savings">年付可享 8 折優惠</div>
                    </div>
                  </div>
                  <div className="cta-buttons">
                    <button 
                      type="button" 
                      className="premium-upgrade-button primary"
                      onClick={handleUpgrade}
                    >
                      立即升級黃金版
                    </button>
                    <button 
                      type="button" 
                      className="trial-button"
                      onClick={() => navigate('/trial')}
                    >
                      免費試用 7 天
                    </button>
                  </div>
                  <div className="guarantee">
                    <span className="guarantee-icon">🔒</span>
                    <span>30天不滿意退款保證</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* 鑽石版用戶專屬價值展示 */}
          {user.tier === 'diamond' && (
            <section className="diamond-exclusive-section">
              <div className="diamond-card">
                <div className="diamond-header">
                  <div className="diamond-icon">💎</div>
                  <div className="diamond-title">
                    <h3>鑽石會員專屬價值</h3>
                    <p>您正在享受我們最頂級的投資分析服務</p>
                  </div>
                </div>
                <div className="diamond-benefits">
                  <div className="benefit-item">
                    <span className="benefit-icon">🎯</span>
                    <div className="benefit-text">
                      <strong>一對一專家諮詢</strong>
                      <p>每月 2 小時專業投資顧問服務</p>
                    </div>
                  </div>
                  <div className="benefit-item">
                    <span className="benefit-icon">📊</span>
                    <div className="benefit-text">
                      <strong>個人化投資策略</strong>
                      <p>基於您的風險偏好定制投資組合</p>
                    </div>
                  </div>
                  <div className="benefit-item">
                    <span className="benefit-icon">⚡</span>
                    <div className="benefit-text">
                      <strong>優先分析處理</strong>
                      <p>分析請求優先處理，平均響應時間 &lt; 30秒</p>
                    </div>
                  </div>
                </div>
                <div className="diamond-stats">
                  <div className="stat">
                    <span className="stat-value">{user.totalValue > 0 ? formatCurrency(user.totalValue) : 'NT$ 2,580,000'}</span>
                    <span className="stat-label">平均組合價值</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{user.monthlyReturn > 0 ? formatPercentage(user.monthlyReturn) : '+18.6%'}</span>
                    <span className="stat-label">平均年化報酬</span>
                  </div>
                </div>
              </div>
            </section>
          )}
        </main>
      </div>

      {/* 對話分析容器 */}
      {user.analysisCount < user.analysisLimit && (
        <div className="floating-analysis">
          <DialogueContainer
            apiBaseUrl="/api/analysis"
            onAnalysisComplete={(result: any) => {
              console.log('Analysis completed:', result);
              loadRecentAnalyses();
              setUser(prev => prev ? { ...prev, analysisCount: prev.analysisCount + 1 } : null);
            }}
          />
        </div>
      )}

      {/* 用戶偏好設置面板 */}
      {showPreferences && (
        <div className="preferences-overlay">
          <div className="preferences-modal">
            <div className="modal-header">
              <h2>個人設置</h2>
              <button 
                type="button" 
                className="close-button" 
                onClick={() => setShowPreferences(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <UserPreferencesPanel
                userId={user.id}
                onSave={(preferences: any) => {
                  console.log('Preferences saved:', preferences);
                  setShowPreferences(false);
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* 訂閱方案橫幅（免費用戶） */}
      {user.tier === 'free' && !isGuestMode && showSubscriptionPrompt && (
        <div className="subscription-prompt">
          <div className="container">
            <div className="header">
              <h3 className="title">升級到黃金會員 - 解鎖完整AI分析功能</h3>
              <button 
                className="close-btn"
                onClick={() => setShowSubscriptionPrompt(false)}
                aria-label="關閉"
              >
                ✕
              </button>
            </div>
            <div className="features-list">
              <div className="feature-item">
                <span>🚀</span>
                完整基本面分析
              </div>
              <div className="feature-item">
                <span>📊</span>
                每日50次查詢
              </div>
              <div className="feature-item">
                <span>📈</span>
                進階技術分析
              </div>
              <div className="feature-item">
                <span>💡</span>
                個人化投資建議
              </div>
              <div className="feature-item">
                <span>🤖</span>
                AI智能學習
              </div>
              <div className="feature-item">
                <span>💬</span>
                優先客服支援
              </div>
            </div>
            <button 
              className="upgrade-btn"
              onClick={handleUpgrade}
            >
              立即升級 NT$ 1,999/月
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserDashboard;