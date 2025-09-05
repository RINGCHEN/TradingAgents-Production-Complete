import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnalyticsService } from '../services/AnalyticsService';
import { personalityTestAPI, handleAPIError } from '../services/PersonalityTestAPI';
import { UTMParams } from '../PersonalityTestApp';
import './TestStartPage.css';

interface TestStartPageProps {
  analytics: AnalyticsService;
  utm_params?: UTMParams;
}

const TestStartPage: React.FC<TestStartPageProps> = ({ analytics, utm_params }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [userInfo, setUserInfo] = useState({
    name: '',
    email: '',
    agreeToTerms: false
  });

  useEffect(() => {
    // 追蹤頁面瀏覽
    analytics.trackPageView('test_start', {
      utm_params,
      referrer: document.referrer
    });
  }, [analytics, utm_params]);

  const handleInputChange = (field: string, value: string | boolean) => {
    setUserInfo(prev => ({
      ...prev,
      [field]: value
    }));

    // 追蹤用戶輸入行為
    analytics.track('user_input', {
      field,
      has_value: Boolean(value),
      utm_params
    });
  };

  const handleStartTest = async () => {
    // 驗證輸入
    if (!userInfo.name.trim()) {
      setError('請輸入您的姓名');
      return;
    }

    if (!userInfo.agreeToTerms) {
      setError('請同意服務條款和隱私政策');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // 追蹤測試開始
      analytics.track('test_start_initiated', {
        user_name: userInfo.name,
        user_email: userInfo.email,
        utm_params,
        has_email: Boolean(userInfo.email)
      });

      // 開始測試
      const response = await personalityTestAPI.startTest({
        name: userInfo.name,
        utm_params,
        referrer: document.referrer
      });

      // 設置用戶ID到分析服務
      analytics.setUserId(response.session_id);

      // 追蹤測試成功開始
      analytics.track('test_started_successfully', {
        session_id: response.session_id,
        total_questions: response.total_questions,
        first_question_id: response.question.id
      });

      // 導航到第一個問題
      navigate(`/question/${response.question.id}`, {
        state: {
          sessionId: response.session_id,
          currentQuestion: response.question,
          totalQuestions: response.total_questions,
          questionIndex: 0
        }
      });

    } catch (err) {
      const errorMessage = handleAPIError(err);
      setError(errorMessage);
      
      analytics.trackError(new Error(errorMessage), {
        context: 'test_start',
        user_name: userInfo.name,
        utm_params
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipInfo = async () => {
    setIsLoading(true);
    setError('');

    try {
      // 追蹤跳過信息收集
      analytics.track('user_info_skipped', {
        utm_params
      });

      // 使用匿名用戶開始測試
      const response = await personalityTestAPI.startTest({
        name: 'Anonymous User',
        utm_params,
        referrer: document.referrer
      });

      analytics.setUserId(response.session_id);

      analytics.track('test_started_anonymously', {
        session_id: response.session_id,
        total_questions: response.total_questions
      });

      navigate(`/question/${response.question.id}`, {
        state: {
          sessionId: response.session_id,
          currentQuestion: response.question,
          totalQuestions: response.total_questions,
          questionIndex: 0
        }
      });

    } catch (err) {
      const errorMessage = handleAPIError(err);
      setError(errorMessage);
      
      analytics.trackError(new Error(errorMessage), {
        context: 'anonymous_test_start',
        utm_params
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLanding = () => {
    analytics.track('back_to_landing_clicked', {
      utm_params,
      user_name: userInfo.name,
      has_email: Boolean(userInfo.email)
    });

    navigate('/');
  };

  return (
    <div className="test-start-page">
      <div className="page-container">
        <div className="section-container">
          {/* 頁面標題 */}
          <header className="start-header">
            <button 
              type="button"
              className="back-button"
              onClick={handleBackToLanding}
              disabled={isLoading}
            >
              <span className="back-icon">←</span>
              返回
            </button>
            
            <div className="header-content">
              <h1 className="page-title">
                <span className="title-icon">🚀</span>
                開始你的投資人格測試
              </h1>
              <p className="page-subtitle">
                只需要幾分鐘，就能深入了解你的投資風格
              </p>
            </div>
          </header>

          {/* 用戶信息收集 */}
          <section className="user-info-section">
            <div className="info-card">
              <h2 className="card-title">
                <span className="card-icon">👤</span>
                基本信息 (可選)
              </h2>
              <p className="card-description">
                提供基本信息可以獲得更個性化的測試結果和建議
              </p>

              <div className="form-group">
                <label htmlFor="name" className="form-label">
                  姓名 <span className="required">*</span>
                </label>
                <input
                  id="name"
                  type="text"
                  className="form-input"
                  placeholder="請輸入您的姓名"
                  value={userInfo.name}
                  onChange={(e: any) => handleInputChange('name', e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  電子郵件 (可選)
                </label>
                <input
                  id="email"
                  type="email"
                  className="form-input"
                  placeholder="example@email.com"
                  value={userInfo.email}
                  onChange={(e: any) => handleInputChange('email', e.target.value)}
                  disabled={isLoading}
                />
                <p className="form-help">
                  提供郵件地址可以接收個性化的投資建議
                </p>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    className="checkbox-input"
                    checked={userInfo.agreeToTerms}
                    onChange={(e: any) => handleInputChange('agreeToTerms', e.target.checked)}
                    disabled={isLoading}
                  />
                  <span className="checkbox-text">
                    我同意 <a href="/terms" target="_blank" rel="noopener noreferrer">服務條款</a> 和 
                    <a href="/privacy" target="_blank" rel="noopener noreferrer">隱私政策</a>
                    <span className="required">*</span>
                  </span>
                </label>
              </div>
            </div>
          </section>

          {/* 測試說明 */}
          <section className="test-instructions">
            <div className="instructions-card">
              <h3 className="instructions-title">
                <span className="instructions-icon">📋</span>
                測試說明
              </h3>
              <ul className="instructions-list">
                <li>測試包含 8 個投資情境問題</li>
                <li>每個問題都沒有標準答案，請根據直覺選擇</li>
                <li>整個測試大約需要 3-5 分鐘</li>
                <li>測試結果將立即顯示，包含詳細分析</li>
                <li>所有數據都會安全保護，不會外洩</li>
              </ul>
            </div>
          </section>

          {/* 行動按鈕 */}
          <section className="action-section">
            <div className="action-buttons">
              <button 
                type="button"
                className="cta-button primary large"
                onClick={handleStartTest}
                disabled={isLoading || !userInfo.name.trim() || !userInfo.agreeToTerms}
              >
                {isLoading ? (
                  <>
                    <span className="loading-spinner"></span>
                    準備測試中...
                  </>
                ) : (
                  <>
                    開始測試
                    <span className="button-icon">🎯</span>
                  </>
                )}
              </button>

              <button 
                type="button"
                className="cta-button secondary"
                onClick={handleSkipInfo}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="loading-spinner"></span>
                    準備中...
                  </>
                ) : (
                  <>
                    匿名開始測試
                    <span className="button-icon">👤</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
          </section>

          {/* 隱私保證 */}
          <section className="privacy-assurance">
            <div className="assurance-card">
              <div className="assurance-items">
                <div className="assurance-item">
                  <span className="assurance-icon">🔒</span>
                  <span className="assurance-text">數據加密保護</span>
                </div>
                <div className="assurance-item">
                  <span className="assurance-icon">🚫</span>
                  <span className="assurance-text">不會發送垃圾郵件</span>
                </div>
                <div className="assurance-item">
                  <span className="assurance-icon">✅</span>
                  <span className="assurance-text">完全免費使用</span>
                </div>
                <div className="assurance-item">
                  <span className="assurance-icon">⚡</span>
                  <span className="assurance-text">即時獲得結果</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default TestStartPage;