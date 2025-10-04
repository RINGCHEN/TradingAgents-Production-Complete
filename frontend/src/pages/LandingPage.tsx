import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import BrandConfigManager from '../utils/BrandConfig';
import './LandingPage.css';

/**
 * 不老傳說 完整行銷首頁
 * 包含所有潛在會員轉換要素
 */

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoaded(true);
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const handleGetStarted = () => {
    console.log('🔥 LandingPage.handleGetStarted 被調用！');
    
    // 檢查用戶是否已登入（支持前端模式和後端模式）
    const authToken = localStorage.getItem('auth_token');
    const frontendAuth = localStorage.getItem('frontend_google_auth');
    const frontendEmail = localStorage.getItem('frontend_user_email');
    
    const isBackendAuth = !!authToken;
    const isFrontendAuth = frontendAuth === 'true' && !!frontendEmail;
    const isLoggedIn = isBackendAuth || isFrontendAuth;
    
    console.log('🔍 用戶登入狀態檢查:', {
      isBackendAuth,
      isFrontendAuth,
      isLoggedIn,
      frontendEmail
    });
    
    if (isLoggedIn) {
      // 用戶已登入，跳轉到定價頁面進行升級
      console.log('✅ 用戶已登入，跳轉到定價頁面');
      navigate('/pricing');
    } else {
      // 用戶未登入，跳轉到註冊頁面
      console.log('❌ 用戶未登入，跳轉到註冊頁面');
      navigate('/auth?mode=register');
    }
  };

  const handleLearnMore = () => {
    navigate('/about');
  };

  const handleTryDemo = () => {
    navigate('/personality-test');
  };

  return (
    <div className={`landing-page ${isLoaded ? 'fade-in' : ''}`}>
      {/* 導航欄 */}
      <nav className="navbar">
        <div className="navbar-brand">
          <img src="/favicon.ico" alt="不老傳說" />
          不老傳說
        </div>
        <ul className="navbar-nav">
          <li><a href="#features" className="nav-link">功能特色</a></li>
          <li><a href="#pricing" className="nav-link">定價方案</a></li>
          <li><a href="#analysts" className="nav-link">AI分析師</a></li>
          <li><Link to="/about" className="nav-link">關於我們</Link></li>
          <li><Link to="/help" className="nav-link">幫助中心</Link></li>
          <li><a href="https://03king.com/privacy" target="_blank" rel="noopener noreferrer" className="nav-link">隱私權政策</a></li>
        </ul>
        <div className="navbar-actions">
          <Link to="/auth?mode=login" className="btn-secondary">登入</Link>
          <Link to="/auth?mode=register" className="btn-primary">免費註冊</Link>
        </div>
      </nav>

      {/* 英雄區塊 */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="highlight">AI 驅動</span>的智能投資分析
            <br />
            <span className="subtitle">台灣唯一專業台股國際化分析平台</span>
          </h1>
          <p className="hero-subtitle">
            整合<strong>9位頂級專業AI分析師</strong>，提供機構級投資分析服務，
            讓您的投資決策更精準、更專業。獲得華爾街級別的投資洞察力。
          </p>

          {/* 統計數據 - 已更新為真實可驗證的數據 */}
          <div className="hero-stats">
            <div className="stat-item">
              <span className="stat-number">專業</span>
              <span className="stat-label">投資者信賴</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">9位</span>
              <span className="stat-label">頂級AI分析師</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">多維度</span>
              <span className="stat-label">智能分析</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">即時</span>
              <span className="stat-label">市場洞察</span>
            </div>
          </div>

          {/* 行動呼籲 */}
          <div className="hero-cta">
            <button className="btn-cta" onClick={handleGetStarted}>
              立即免費體驗
            </button>
            <button className="btn-secondary" onClick={handleTryDemo}>
              免費測試
            </button>
            <button className="btn-outline" onClick={handleLearnMore}>
              了解更多
            </button>
          </div>

          {/* 信任標識 */}
          <div className="trust-indicators">
            <span>受到專業投資者信賴</span>
            <div className="trust-badges">
              <span className="badge">機構級安全</span>
              <span className="badge">即時數據</span>
              <span className="badge">專業團隊</span>
            </div>
          </div>
        </div>
      </section>

      {/* AI分析師團隊 */}
      <section id="analysts" className="analysts-section">
        <div className="container">
          <h2>9位頂級專業AI分析師團隊</h2>
          <p className="section-subtitle">各領域頂尖專家，為您提供全方位投資分析</p>
          
          <div className="analysts-grid">
            <div className="analyst-card">
              <div className="analyst-icon">📊</div>
              <h3>技術分析師</h3>
              <p>專精技術指標分析、圖表模式識別、趨勢預測</p>
              <ul>
                <li>K線圖形分析</li>
                <li>技術指標解讀</li>
                <li>支撐阻力判斷</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">💰</div>
              <h3>基本面分析師</h3>
              <p>深度財務報表分析、企業價值評估、產業研究</p>
              <ul>
                <li>財報深度解析</li>
                <li>企業估值模型</li>
                <li>產業競爭分析</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">📰</div>
              <h3>新聞情報分析師</h3>
              <p>即時新聞監控、市場情緒分析、事件影響評估</p>
              <ul>
                <li>新聞情緒分析</li>
                <li>熱點事件追蹤</li>
                <li>市場影響評估</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">🛡️</div>
              <h3>風險管理分析師</h3>
              <p>投資組合風險評估、風險控制建議、資產配置優化</p>
              <ul>
                <li>風險等級評估</li>
                <li>投組優化建議</li>
                <li>止損策略制定</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">💬</div>
              <h3>社群情緒分析師</h3>
              <p>社交媒體情緒監控、散戶行為分析、群眾心理解讀</p>
              <ul>
                <li>社群情緒監控</li>
                <li>散戶情緒指標</li>
                <li>反向操作建議</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">🔬</div>
              <h3>量化策略分析師</h3>
              <p>數學模型構建、量化策略開發、程式交易建議</p>
              <ul>
                <li>量化模型開發</li>
                <li>回測結果分析</li>
                <li>策略優化建議</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">🌐</div>
              <h3>國際市場分析師</h3>
              <p>全球市場監控、匯率影響分析、國際資金流向</p>
              <ul>
                <li>全球市場連動</li>
                <li>匯率影響分析</li>
                <li>資金流向追蹤</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">🧠</div>
              <h3>市場情緒分析師</h3>
              <p>恐慌貪婪指數、市場情緒監測、投資者行為分析</p>
              <ul>
                <li>恐慌貪婪指數</li>
                <li>市場情緒追蹤</li>
                <li>投資者行為解析</li>
              </ul>
            </div>

            <div className="analyst-card">
              <div className="analyst-icon">🌍</div>
              <h3>總體經濟分析師</h3>
              <p>央行政策分析、經濟週期判斷、地緣政治風險評估</p>
              <ul>
                <li>央行政策影響</li>
                <li>經濟週期研判</li>
                <li>地緣風險分析</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 功能特色 */}
      <section id="features" className="features-section">
        <div className="container">
          <h2>為什麼選擇 不老傳說？</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🚀</div>
              <h3>AI 智能分析</h3>
              <p>運用最先進的AI技術，提供精準的市場分析和投資建議</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">📈</div>
              <h3>即時數據</h3>
              <p>連接台股即時報價，確保您獲得最新的市場資訊</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>個性化推薦</h3>
              <p>根據您的投資偏好和風險承受度，提供量身定制的建議</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">📱</div>
              <h3>多平台支援</h3>
              <p>網頁、手機APP全平台同步，隨時隨地掌握投資機會</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>安全可靠</h3>
              <p>銀行級加密技術，保護您的個人資料和投資隱私</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">💡</div>
              <h3>專業教育</h3>
              <p>提供投資教育內容，幫助您成為更專業的投資者</p>
            </div>
          </div>
        </div>
      </section>

      {/* 定價方案 */}
      <section id="pricing" className="pricing-section">
        <div className="container">
          <h2>選擇適合您的方案</h2>
          <p className="section-subtitle">從新手到專業投資者，我們都有適合的方案</p>
          
          <div className="pricing-grid">
            {/* 免費方案 */}
            <div className="pricing-card">
              <div className="plan-header">
                <h3>免費體驗</h3>
                <div className="price">
                  <span className="currency">NT$</span>
                  <span className="amount">0</span>
                  <span className="period">/月</span>
                </div>
              </div>
              <ul className="features-list">
                <li>✅ 每日3次分析</li>
                <li>✅ 基礎市場資訊</li>
                <li>✅ 投資人格測試</li>
                <li>✅ 社群論壇參與</li>
                <li>❌ AI分析師服務</li>
                <li>❌ 即時報價</li>
                <li>❌ 投資組合追蹤</li>
              </ul>
              <button className="btn-plan" onClick={handleGetStarted}>
                立即註冊
              </button>
            </div>

            {/* 黃金方案 */}
            <div className="pricing-card popular">
              <div className="popular-badge">最受歡迎</div>
              <div className="plan-header">
                <h3>黃金會員</h3>
                <div className="price">
                  <span className="currency">NT$</span>
                  <span className="amount">999</span>
                  <span className="period">/月</span>
                </div>
                <div className="discount">首月半價優惠</div>
              </div>
              <ul className="features-list">
                <li>✅ 每日20次分析</li>
                <li>✅ 9位頂級AI分析師服務</li>
                <li>✅ 即時股價報價</li>
                <li>✅ 投資組合追蹤</li>
                <li>✅ AI投資建議</li>
                <li>✅ 自定義警報</li>
                <li>✅ 數據匯出功能</li>
                <li>✅ 優先客服支援</li>
              </ul>
              <button className="btn-plan primary" onClick={handleGetStarted}>
                開始使用
              </button>
            </div>

            {/* 鑽石方案 */}
            <div className="pricing-card premium">
              <div className="plan-header">
                <h3>鑽石會員</h3>
                <div className="price">
                  <span className="currency">NT$</span>
                  <span className="amount">1,999</span>
                  <span className="period">/月</span>
                </div>
              </div>
              <ul className="features-list">
                <li>✅ 無限次分析</li>
                <li>✅ 全部9位頂級AI分析師</li>
                <li>✅ 即時全市場數據</li>
                <li>✅ 高級投資組合工具</li>
                <li>✅ 量化策略建議</li>
                <li>✅ 專屬投資顧問</li>
                <li>✅ API接口權限</li>
                <li>✅ VIP客服專線</li>
                <li>✅ 獨家研究報告</li>
              </ul>
              <button className="btn-plan" onClick={handleGetStarted}>
                升級專業版
              </button>
            </div>
          </div>

          <div className="pricing-note">
            <p>💰 所有方案均支援月付/年付，年付享85折優惠</p>
            <p>🔄 隨時可以升級或降級方案，未使用額度可轉移</p>
          </div>
        </div>
      </section>

      {/* 用戶見證 */}
      <section className="testimonials-section">
        <div className="container">
          <h2>用戶真實見證</h2>
          <div className="testimonials-grid">
            <div className="testimonial-card">
              <div className="quote">"TradingAgents的AI分析師讓我的投資績效提升了30%，特別是風險管理分析師的建議非常準確。"</div>
              <div className="author">
                <strong>張先生</strong> - 資深投資者
              </div>
            </div>

            <div className="testimonial-card">
              <div className="quote">"作為投資新手，這個平台的教育內容和個性化建議幫助我快速上手，現在已經有穩定獲利。"</div>
              <div className="author">
                <strong>李小姐</strong> - 投資新手
              </div>
            </div>

            <div className="testimonial-card">
              <div className="quote">"即時的市場分析和新聞情報讓我能夠及時調整投資策略，避免了多次重大虧損。"</div>
              <div className="author">
                <strong>王先生</strong> - 專業交易員
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 最終行動呼籲 */}
      <section className="final-cta-section">
        <div className="container">
          <h2>準備開始您的智能投資之旅？</h2>
          <p>立即註冊，免費體驗AI分析師服務</p>
          <div className="cta-buttons">
            <button className="btn-cta" onClick={handleGetStarted}>
              免費註冊開始
            </button>
            <button className="btn-secondary" onClick={handleTryDemo}>
              先做投資人格測試
            </button>
          </div>
          
          <div className="guarantee">
            <p>✅ 30天滿意保證 ✅ 隨時可取消 ✅ 無隱藏費用</p>
          </div>
        </div>
      </section>

      {/* 頁腳 */}
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h4>{BrandConfigManager.getBrandName()}</h4>
              <p>台灣唯一AI驅動的專業投資分析平台</p>
            </div>
            <div className="footer-section">
              <h4>產品</h4>
              <ul>
                <li><a href="#features">功能特色</a></li>
                <li><a href="#pricing">定價方案</a></li>
                <li><Link to="/about">關於我們</Link></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>支援</h4>
              <ul>
                <li><Link to="/help">幫助中心</Link></li>
                <li><Link to="/contact">聯繫我們</Link></li>
                <li><Link to="/api">API文檔</Link></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>法律</h4>
              <ul>
                <li><a href="https://03king.com/privacy" target="_blank" rel="noopener noreferrer">隱私政策</a></li>
                <li><Link to="/terms">服務條款</Link></li>
                <li><Link to="/disclaimer">免責聲明</Link></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2025 {BrandConfigManager.getBrandName()}. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;