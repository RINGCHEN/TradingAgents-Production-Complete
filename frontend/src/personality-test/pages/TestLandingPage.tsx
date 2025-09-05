import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnalyticsService } from '../services/AnalyticsService';
import { userExperienceService } from '../services/UserExperienceService';
import UXFeedbackWidget from '../components/UXFeedbackWidget';
import { UTMParams } from '../PersonalityTestApp';
import './TestLandingPage.css';

interface TestLandingPageProps {
  analytics: AnalyticsService;
  utm_params?: UTMParams;
}

interface PreviewCardProps {
  icon: string;
  title: string;
  description: string;
}

const PreviewCard: React.FC<PreviewCardProps> = ({ icon, title, description }) => (
  <div className="preview-card">
    <div className="preview-icon">{icon}</div>
    <h3 className="preview-title">{title}</h3>
    <p className="preview-description">{description}</p>
  </div>
);

const TestLandingPage: React.FC<TestLandingPageProps> = ({ analytics, utm_params }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [error, setError] = useState<string>('');
  const [stats] = useState({
    totalTests: 50000,
    averageRating: 4.8,
    completionRate: 92
  });
  const [isStatsAnimated, setIsStatsAnimated] = useState(false);
  const [uxTestActive, setUxTestActive] = useState(false);
  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 追蹤頁面瀏覽
    analytics.trackPageView('test_landing', {
      utm_params,
      referrer: document.referrer
    });

    // 設置 UTM 參數
    if (utm_params) {
      analytics.setUserProperties(utm_params);
    }

    // 載入統計數據
    const loadStats = async () => {
      try {
        // 這裡可以從 API 獲取實際統計數據
        // const response = await fetch('/api/personality-test/stats');
        // const data = await response.json();
        // setStats(data);
        
        // 模擬載入過程
        setLoadingMessage('載入統計數據...');
        await new Promise(resolve => setTimeout(resolve, 500));
        setLoadingMessage('');
      } catch (error) {
        console.error('Failed to load stats:', error);
      }
    };

    // 設置統計數字動畫觸發
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !isStatsAnimated) {
            setIsStatsAnimated(true);
          }
        });
      },
      { threshold: 0.5 }
    );

    if (statsRef.current) {
      observer.observe(statsRef.current);
    }

    loadStats();

    // 啟動用戶體驗測試
    userExperienceService.startRecording();
    setUxTestActive(true);

    // 追蹤頁面載入性能
    userExperienceService.trackMetric('landing_page_load', Date.now(), 'timestamp');

    return () => {
      if (statsRef.current) {
        observer.unobserve(statsRef.current);
      }
      
      // 停止用戶體驗記錄並提交結果
      if (uxTestActive) {
        userExperienceService.stopRecording();
        userExperienceService.submitTestResult();
      }
    };
  }, [analytics, utm_params, isStatsAnimated, uxTestActive]);

  const handleStartTest = async () => {
    setIsLoading(true);
    setError('');
    setLoadingProgress(0);

    try {
      // 追蹤測試開始意圖
      analytics.track('test_start_clicked', {
        utm_params,
        page_location: 'landing_page',
        button_position: 'hero_section'
      });

      // 模擬載入進度
      const loadingSteps = [
        { progress: 20, message: '準備測試環境...' },
        { progress: 50, message: '載入問題庫...' },
        { progress: 80, message: '初始化分析引擎...' },
        { progress: 100, message: '準備完成！' }
      ];

      for (const step of loadingSteps) {
        setLoadingProgress(step.progress);
        setLoadingMessage(step.message);
        await new Promise(resolve => setTimeout(resolve, 300));
      }

      // 導航到測試開始頁面
      navigate('/start');

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '啟動測試時發生錯誤';
      setError(errorMessage);
      
      analytics.trackError(new Error(errorMessage), {
        context: 'test_start',
        utm_params
      });
    } finally {
      setIsLoading(false);
      setLoadingProgress(0);
      setLoadingMessage('');
    }
  };

  const handleLearnMore = () => {
    analytics.track('learn_more_clicked', {
      utm_params,
      page_location: 'landing_page'
    });

    // 追蹤用戶體驗互動
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'learn_more_button',
      timestamp: Date.now()
    });

    // 滾動到功能介紹區域
    const featuresSection = document.getElementById('features-section');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
      
      // 追蹤滾動行為
      userExperienceService.trackMetric('smooth_scroll_triggered', 1, 'count');
    }
  };

  // 追蹤統計數據查看
  const handleStatsView = () => {
    userExperienceService.trackInteraction({
      type: 'hover',
      element: 'hero_stats',
      timestamp: Date.now()
    });
    
    userExperienceService.trackMetric('stats_engagement', 1, 'count');
  };

  return (
    <div className="test-landing-page">
      <div className="page-container">
        <div className="section-container">
          {/* 英雄區域 */}
          <header className="hero-section">
            <div className="hero-content">
              <h1 className="hero-title">
                <span className="title-icon">🧠</span>
                發現你的投資人格
              </h1>
              <p className="hero-subtitle">
                3分鐘科學測試，了解你的投資風格，擊敗90%的投資者！
              </p>
              <div 
                className="hero-stats" 
                ref={statsRef}
                onMouseEnter={handleStatsView}
              >
                <div className="stat-item">
                  <span className={`stat-number ${isStatsAnimated ? 'animated' : ''}`}>
                    {stats.totalTests.toLocaleString()}+
                  </span>
                  <span className="stat-label">已完成測試</span>
                </div>
                <div className="stat-item">
                  <span className={`stat-number ${isStatsAnimated ? 'animated' : ''}`}>
                    {stats.averageRating}/5
                  </span>
                  <span className="stat-label">用戶評分</span>
                </div>
                <div className="stat-item">
                  <span className={`stat-number ${isStatsAnimated ? 'animated' : ''}`}>
                    {stats.completionRate}%
                  </span>
                  <span className="stat-label">完成率</span>
                </div>
              </div>
            </div>

            <div className="hero-actions">
              <button 
                type="button"
                className={`cta-button primary large ${isLoading ? 'loading' : ''}`}
                onClick={handleStartTest}
                disabled={isLoading}
              >
                {isLoading ? '準備中...' : (
                  <>
                    開始免費測試
                    <span className="button-icon">🚀</span>
                  </>
                )}
              </button>

              <button 
                type="button"
                className="cta-button secondary"
                onClick={handleLearnMore}
              >
                了解更多
                <span className="button-icon">📖</span>
              </button>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
          </header>

          {/* 社交證明區域 */}
          <section className="social-proof-section">
            <div className="testimonials">
              <div className="testimonial">
                <div className="testimonial-content">
                  "這個測試幫我認識了自己的投資盲點，現在投資更有信心了！"
                </div>
                <div className="testimonial-author">
                  <span className="author-name">張先生</span>
                  <span className="author-title">資深投資者</span>
                </div>
              </div>
              <div className="testimonial">
                <div className="testimonial-content">
                  "測試結果非常準確，推薦的投資策略很實用。"
                </div>
                <div className="testimonial-author">
                  <span className="author-name">李小姐</span>
                  <span className="author-title">理財新手</span>
                </div>
              </div>
            </div>
          </section>

          {/* 功能介紹區域 */}
          <section id="features-section" className="features-section">
            <h2 className="section-title">你將獲得什麼？</h2>
            <div className="features-grid">
              <PreviewCard 
                icon="🎯"
                title="個人投資風格分析"
                description="深度分析你的風險偏好和投資行為模式"
              />
              <PreviewCard 
                icon="📊"
                title="五維度雷達圖"
                description="視覺化展示你的投資人格特徵"
              />
              <PreviewCard 
                icon="💡"
                title="個性化投資建議"
                description="基於你的人格類型的專業投資策略"
              />
              <PreviewCard 
                icon="🏆"
                title="投資者排名"
                description="了解你在所有投資者中的表現排名"
              />
              <PreviewCard 
                icon="🤝"
                title="名人投資者對比"
                description="看看你和哪位知名投資者最相似"
              />
              <PreviewCard 
                icon="📈"
                title="專業分析師推薦"
                description="獲得適合你人格類型的分析師建議"
              />
            </div>
          </section>

          {/* 測試信息區域 */}
          <section className="test-info-section">
            <div className="test-info-card">
              <h3 className="info-title">
                <span className="info-icon">ℹ️</span>
                測試詳情
              </h3>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-icon">⏱️</span>
                  <div className="info-content">
                    <span className="info-label">測試時間</span>
                    <span className="info-value">約3-5分鐘</span>
                  </div>
                </div>
                <div className="info-item">
                  <span className="info-icon">❓</span>
                  <div className="info-content">
                    <span className="info-label">問題數量</span>
                    <span className="info-value">8個情境問題</span>
                  </div>
                </div>
                <div className="info-item">
                  <span className="info-icon">🎯</span>
                  <div className="info-content">
                    <span className="info-label">結果準確性</span>
                    <span className="info-value">基於心理學原理</span>
                  </div>
                </div>
                <div className="info-item">
                  <span className="info-icon">🔒</span>
                  <div className="info-content">
                    <span className="info-label">隱私保護</span>
                    <span className="info-value">完全匿名安全</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 行動呼籲區域 */}
          <section className="final-cta-section">
            <div className="cta-content">
              <h2 className="cta-title">準備好發現你的投資潛力了嗎？</h2>
              <p className="cta-description">
                加入超過 {stats.totalTests.toLocaleString()} 位投資者的行列，
                開始你的投資人格探索之旅！
              </p>
              <button 
                type="button"
                className={`cta-button primary large ${isLoading ? 'loading' : ''}`}
                onClick={handleStartTest}
                disabled={isLoading}
              >
                {isLoading ? '準備中...' : (
                  <>
                    立即開始測試
                    <span className="button-icon">✨</span>
                  </>
                )}
              </button>
            </div>
          </section>
        </div>
      </div>

      {/* 載入覆蓋層 */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="loading-spinner-large"></div>
            <div className="loading-text">{loadingMessage || '準備中...'}</div>
            <div className="loading-progress">
              {loadingProgress > 0 && `${loadingProgress}%`}
            </div>
          </div>
        </div>
      )}

      {/* 用戶體驗反饋小工具 */}
      <UXFeedbackWidget page="test_landing" position="bottom-right" />
    </div>
  );
};

export default TestLandingPage;