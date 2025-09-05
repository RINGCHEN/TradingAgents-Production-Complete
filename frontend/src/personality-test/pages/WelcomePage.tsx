import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { userExperienceService } from '../services/UserExperienceService';
import './WelcomePage.css';

interface WelcomePageProps {
  // 可以通過props或location state傳入數據
}

interface WelcomeData {
  userId: string;
  nextSteps: string[];
  personalityType?: any;
}

const WelcomePage: React.FC<WelcomePageProps> = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const { userId, nextSteps, personalityType } = location.state as WelcomeData || {};
  
  const [currentStep, setCurrentStep] = useState(0);
  const [showNextSteps, setShowNextSteps] = useState(false);
  
  useEffect(() => {
    // 追蹤歡迎頁面訪問
    userExperienceService.trackInteraction({
      type: 'focus',
      element: 'welcome_page',
      timestamp: Date.now()
    });
    
    // 如果沒有必要數據，跳轉回首頁
    if (!userId) {
      navigate('/personality-test');
      return;
    }
    
    // 延遲顯示下一步驟
    setTimeout(() => {
      setShowNextSteps(true);
    }, 3000);
  }, [userId, navigate]);
  
  const handleStepClick = (stepIndex: number) => {
    setCurrentStep(stepIndex);
    
    userExperienceService.trackInteraction({
      type: 'click',
      element: `welcome_step_${stepIndex}`,
      timestamp: Date.now()
    });
  };
  
  const handleGetStarted = () => {
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'welcome_get_started',
      timestamp: Date.now()
    });
    
    // 跳轉到主系統或儀表板
    window.location.href = '/dashboard';
  };
  
  const handleExploreMore = () => {
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'welcome_explore_more',
      timestamp: Date.now()
    });
    
    // 跳轉到功能介紹頁面
    navigate('/personality-test/features');
  };
  
  if (!userId) {
    return (
      <div className="welcome-page loading">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>載入中...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="welcome-page">
      <div className="welcome-container">
        
        {/* 歡迎標題 */}
        <header className="welcome-header">
          <div className="welcome-animation">
            <div className="success-icon">🎉</div>
            <h1 className="welcome-title">歡迎加入 TradingAgents！</h1>
            <p className="welcome-subtitle">
              您的投資之旅從這裡開始
            </p>
          </div>
          
          {personalityType && (
            <div className="personality-reminder">
              <div className="reminder-badge">
                <span className="badge-icon">{personalityType.icon || '🧠'}</span>
                <div className="badge-content">
                  <span className="badge-title">您的投資人格</span>
                  <span className="badge-type">{personalityType.display_name}</span>
                </div>
              </div>
            </div>
          )}
        </header>
        
        {/* 歡迎內容 */}
        <div className="welcome-content">
          
          {/* 成功確認 */}
          <section className="confirmation-section">
            <div className="confirmation-card">
              <div className="confirmation-icon">✅</div>
              <div className="confirmation-content">
                <h3>註冊成功！</h3>
                <p>我們已經為您發送了歡迎郵件，請查收您的郵箱。</p>
                <div className="email-note">
                  <span className="note-icon">📧</span>
                  <span className="note-text">
                    如果沒有收到郵件，請檢查垃圾郵件資料夾
                  </span>
                </div>
              </div>
            </div>
          </section>
          
          {/* 下一步驟 */}
          {showNextSteps && nextSteps && nextSteps.length > 0 && (
            <section className="next-steps-section">
              <h2 className="section-title">您的下一步</h2>
              <p className="section-subtitle">
                我們為您準備了個性化的入門指南
              </p>
              
              <div className="steps-container">
                <div className="steps-list">
                  {nextSteps.map((step, index) => (
                    <div
                      key={index}
                      className={`step-item ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
                      onClick={() => handleStepClick(index)}
                    >
                      <div className="step-number">
                        {index < currentStep ? '✓' : index + 1}
                      </div>
                      <div className="step-content">
                        <h4 className="step-title">{step}</h4>
                        {index === currentStep && (
                          <p className="step-description">
                            {getStepDescription(step)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="step-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${((currentStep + 1) / nextSteps.length) * 100}%` }}
                    ></div>
                  </div>
                  <span className="progress-text">
                    {currentStep + 1} / {nextSteps.length}
                  </span>
                </div>
              </div>
            </section>
          )}
          
          {/* 功能亮點 */}
          <section className="features-section">
            <h2 className="section-title">探索 TradingAgents 的強大功能</h2>
            
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">📊</div>
                <h3 className="feature-title">專業分析</h3>
                <p className="feature-description">
                  獲得專業分析師的深度市場分析和投資建議
                </p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3 className="feature-title">實時警報</h3>
                <p className="feature-description">
                  第一時間獲得重要市場動態和投資機會提醒
                </p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">🎯</div>
                <h3 className="feature-title">個性化推薦</h3>
                <p className="feature-description">
                  基於您的投資人格提供量身定制的投資策略
                </p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">📱</div>
                <h3 className="feature-title">隨時隨地</h3>
                <p className="feature-description">
                  通過手機和電腦隨時管理您的投資組合
                </p>
              </div>
            </div>
          </section>
          
          {/* 行動按鈕 */}
          <section className="action-section">
            <div className="action-buttons">
              <button 
                className="primary-button"
                onClick={handleGetStarted}
              >
                開始投資之旅
              </button>
              
              <button 
                className="secondary-button"
                onClick={handleExploreMore}
              >
                了解更多功能
              </button>
            </div>
            
            <div className="support-info">
              <p className="support-text">
                需要幫助？我們的客服團隊隨時為您服務
              </p>
              <div className="support-contacts">
                <a href="mailto:support@tradingagents.com" className="support-link">
                  <span className="contact-icon">📧</span>
                  support@tradingagents.com
                </a>
                <a href="tel:+886-2-1234-5678" className="support-link">
                  <span className="contact-icon">📞</span>
                  +886-2-1234-5678
                </a>
              </div>
            </div>
          </section>
          
        </div>
        
      </div>
    </div>
  );
};

// 輔助函數：獲取步驟描述
const getStepDescription = (step: string): string => {
  const descriptions: Record<string, string> = {
    '完善您的風險偏好設定': '設置您的投資風險承受度，幫助我們為您推薦合適的投資產品。',
    '瀏覽穩健型投資組合推薦': '查看專為保守型投資者設計的投資組合，穩健增長您的財富。',
    '設置投資目標和時間範圍': '明確您的投資目標，制定合理的投資時間規劃。',
    '訂閱市場分析報告': '獲得專業的市場分析和投資建議，掌握市場動態。',
    '聯繫專屬投資顧問': '與我們的專業投資顧問一對一諮詢，獲得個性化建議。',
    '設置高收益投資警報': '及時獲得高潛力投資機會提醒，不錯過任何機會。',
    '瀏覽積極型投資機會': '探索高收益投資產品，實現財富快速增長。',
    '學習進階交易策略': '掌握專業的交易技巧和策略，提升投資技能。',
    '加入投資者社群': '與其他投資者交流經驗，分享投資心得。',
    '開始模擬交易練習': '在無風險環境中練習交易，提升投資技能。',
    '建立多元化投資組合': '構建平衡的投資組合，分散風險並優化收益。',
    '設置平衡型資產配置': '根據您的風險偏好配置不同類型的投資資產。',
    '學習投資組合管理': '掌握投資組合管理的基本原理和實踐技巧。',
    '設置定期投資計劃': '制定定期投資計劃，實現財富的穩定增長。',
    '獲得專業投資建議': '獲得我們專業團隊的投資建議和市場分析。'
  };
  
  return descriptions[step] || '點擊開始這個步驟，我們將為您提供詳細指導。';
};

export default WelcomePage;