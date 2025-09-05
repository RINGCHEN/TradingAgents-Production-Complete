import React from 'react';
import BrandConfigManager from '../utils/BrandConfig';
import './BrandChangeInfoPage.css';

/**
 * 品牌變更詳細信息頁面
 * 提供完整的品牌更名說明和FAQ
 */
const BrandChangeInfoPage: React.FC = () => {
  return (
    <div className="brand-change-info-page">
      <header className="page-header">
        <div className="container">
          <div className="header-content">
            <div className="brand-evolution">
              <div className="old-logo">TradingAgents</div>
              <div className="evolution-arrow">→</div>
              <div className="new-logo">{BrandConfigManager.getBrandName()}</div>
            </div>
            <h1>品牌全新升級</h1>
            <p className="subtitle">從 TradingAgents 到不老傳說的華麗轉身</p>
          </div>
        </div>
      </header>

      <main className="page-content">
        <div className="container">
          {/* 品牌更名說明 */}
          <section className="section brand-announcement">
            <h2>品牌更名公告</h2>
            <div className="announcement-content">
              <p>
                親愛的用戶，我們懷著激動的心情向您宣布一個重要消息：
                <strong>TradingAgents</strong> 正式更名為 <strong>「不老傳說」</strong>！
              </p>
              
              <div className="highlight-box">
                <h3>🎉 全新品牌，不變承諾</h3>
                <p>
                  雖然名稱變了，但我們對提供卓越AI投資分析服務的承諾永遠不變。
                  不老傳說代表著我們對永續經營和傳奇成就的追求。
                </p>
              </div>
              
              <div className="date-info">
                <strong>生效日期：</strong>2025年8月19日
              </div>
            </div>
          </section>

          {/* 品牌理念 */}
          <section className="section brand-philosophy">
            <h2>品牌理念與願景</h2>
            <div className="philosophy-grid">
              <div className="philosophy-card">
                <div className="card-icon">🏛️</div>
                <h3>不老</h3>
                <p>象徵永恆的智慧與不朽的價值，我們致力於為您提供經得起時間考驗的投資策略</p>
              </div>
              <div className="philosophy-card">
                <div className="card-icon">⚡</div>
                <h3>傳說</h3>
                <p>代表卓越的成就與非凡的表現，每一次投資分析都力求成為行業典範</p>
              </div>
              <div className="philosophy-card">
                <div className="card-icon">🎯</div>
                <h3>AI智能</h3>
                <p>結合人工智能與金融專業，為您打造個人專屬的投資傳奇故事</p>
              </div>
            </div>
          </section>

          {/* 常見問題 */}
          <section className="section faq-section">
            <h2>常見問題解答</h2>
            <div className="faq-list">
              <div className="faq-item">
                <h3>Q: 品牌更名會影響我的帳戶嗎？</h3>
                <p>A: 完全不會！您的帳戶資訊、投資記錄、設定偏好等所有數據都完全保持不變。您可以使用相同的帳號密碼繼續登入。</p>
              </div>
              
              <div className="faq-item">
                <h3>Q: 原有的功能服務會改變嗎？</h3>
                <p>A: 所有原有功能完全保持不變，包括7位專業AI分析師、投資組合管理、市場監控等服務。我們只是換了個更好聽的名字！</p>
              </div>
              
              <div className="faq-item">
                <h3>Q: 會有額外費用嗎？</h3>
                <p>A: 絕對不會！品牌更名是我們的內部升級，不會產生任何額外費用。您的訂閱方案和價格完全不受影響。</p>
              </div>
              
              <div className="faq-item">
                <h3>Q: 我需要重新註冊或下載新的應用嗎？</h3>
                <p>A: 不需要！系統會自動更新品牌標識，您無需進行任何操作。只要照常使用即可。</p>
              </div>
              
              <div className="faq-item">
                <h3>Q: 安全性和隱私保護會受影響嗎？</h3>
                <p>A: 絕對不會！我們的安全措施、隱私政策和數據保護標準完全保持不變，繼續為您提供最高級別的安全保障。</p>
              </div>
              
              <div className="faq-item">
                <h3>Q: 客服聯絡方式有變更嗎？</h3>
                <p>A: 客服團隊保持不變，但聯絡郵箱已更新為 <a href="mailto:support@bulao-chuanshuo.com">support@bulao-chuanshuo.com</a>。原郵箱仍可正常使用。</p>
              </div>
            </div>
          </section>

          {/* 服務保證 */}
          <section className="section service-guarantee">
            <h2>服務保證</h2>
            <div className="guarantee-grid">
              <div className="guarantee-item">
                <div className="guarantee-icon">✓</div>
                <h3>相同團隊</h3>
                <p>原班人馬繼續為您服務</p>
              </div>
              <div className="guarantee-item">
                <div className="guarantee-icon">✓</div>
                <h3>相同品質</h3>
                <p>維持一貫的高品質服務</p>
              </div>
              <div className="guarantee-item">
                <div className="guarantee-icon">✓</div>
                <h3>升級體驗</h3>
                <p>更好的用戶界面和體驗</p>
              </div>
              <div className="guarantee-item">
                <div className="guarantee-icon">✓</div>
                <h3>持續創新</h3>
                <p>不斷推出新功能和改進</p>
              </div>
            </div>
          </section>

          {/* 聯絡資訊 */}
          <section className="section contact-section">
            <h2>聯絡我們</h2>
            <div className="contact-content">
              <p>如果您對品牌更名有任何疑問或需要協助，請隨時聯絡我們：</p>
              
              <div className="contact-methods">
                <div className="contact-method">
                  <strong>客服信箱：</strong>
                  <a href="mailto:support@bulao-chuanshuo.com">support@bulao-chuanshuo.com</a>
                </div>
                <div className="contact-method">
                  <strong>回應時間：</strong>
                  24小時內回覆（工作日）
                </div>
                <div className="contact-method">
                  <strong>服務時間：</strong>
                  週一至週五 09:00-18:00 (台北時間)
                </div>
              </div>
              
              <div className="thank-you-message">
                <h3>感謝您的支持</h3>
                <p>
                  感謝您一直以來對我們的信任與支持。不老傳說將繼續致力於為您創造投資奇蹟，
                  讓我們一起書寫屬於您的投資傳奇故事！
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>

      <footer className="page-footer">
        <div className="container">
          <p>&copy; 2025 {BrandConfigManager.getBrandName()}. 版權所有.</p>
          <p>原 TradingAgents | 現 不老傳說 - 傳承經典，開創未來</p>
        </div>
      </footer>
    </div>
  );
};

export default BrandChangeInfoPage;