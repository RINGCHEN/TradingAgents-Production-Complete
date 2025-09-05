import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { personalityTestAPI, PersonalityTestResult } from '../services/PersonalityTestAPI';
import { userExperienceService } from '../services/UserExperienceService';
import ShareImagePreview from '../components/ShareImagePreview';
import SocialShareButtons from '../components/SocialShareButtons';
import PersonalityRadarChart from '../components/PersonalityRadarChart';
import ConversionCTA from '../components/ConversionCTA';
import './TestResultPage.css';

interface TestResultPageProps {
  // 可以通過props傳入結果數據，或通過URL參數獲取
  resultData?: PersonalityTestResult;
}

interface ConversionMetrics {
  pageViewTime: number;
  scrollDepth: number;
  ctaViews: number;
  ctaClicks: number;
  shareClicks: number;
}

interface ShareData {
  image_url: string;
  share_text: string;
  share_url: string;
  result_id: string;
}

const TestResultPage: React.FC<TestResultPageProps> = ({ resultData }) => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  
  const [result, setResult] = useState<PersonalityTestResult | null>(resultData || null);
  const [shareData, setShareData] = useState<ShareData | null>(null);
  const [isLoading, setIsLoading] = useState(!resultData);
  const [error, setError] = useState<string>('');
  const [showShareSection, setShowShareSection] = useState(false);
  const [showConversionSection, setShowConversionSection] = useState(false);
  const [conversionMetrics, setConversionMetrics] = useState<ConversionMetrics>({
    pageViewTime: 0,
    scrollDepth: 0,
    ctaViews: 0,
    ctaClicks: 0,
    shareClicks: 0
  });
  
  // A/B測試變體
  const [abTestVariant, setAbTestVariant] = useState<'A' | 'B'>('A');
  
  // 引用元素用於追蹤
  const pageRef = useRef<HTMLDivElement>(null);
  const ctaSectionRef = useRef<HTMLDivElement>(null);
  const startTimeRef = useRef<number>(Date.now());

  useEffect(() => {
    if (!resultData && sessionId) {
      loadTestResult();
    } else if (resultData) {
      setResult(resultData);
      setIsLoading(false);
    }

    // 設置A/B測試變體
    setAbTestVariant(Math.random() > 0.5 ? 'A' : 'B');

    // 追蹤結果頁面瀏覽
    userExperienceService.trackInteraction({
      type: 'focus',
      element: 'test_result_page',
      timestamp: Date.now()
    });

    // 追蹤轉換步驟
    if (sessionId) {
      personalityTestAPI.trackConversionStep({
        session_id: sessionId,
        step: 'result_view',
        action: 'page_loaded',
        data: { ab_variant: abTestVariant }
      });
    }
  }, [sessionId, resultData]);

  useEffect(() => {
    if (result) {
      // 延遲顯示分享區域，增加戲劇效果
      setTimeout(() => {
        setShowShareSection(true);
      }, 2000);

      // 延遲顯示轉換區域，讓用戶先消化結果
      setTimeout(() => {
        setShowConversionSection(true);
      }, 4000);
    }
  }, [result]);

  // 追蹤頁面停留時間和滾動深度
  useEffect(() => {
    const handleScroll = () => {
      if (pageRef.current) {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = Math.round((scrollTop / docHeight) * 100);
        
        setConversionMetrics(prev => ({
          ...prev,
          scrollDepth: Math.max(prev.scrollDepth, scrollPercent)
        }));
      }
    };

    const handleBeforeUnload = () => {
      const timeSpent = Date.now() - startTimeRef.current;
      setConversionMetrics(prev => ({ ...prev, pageViewTime: timeSpent }));
      
      // 發送轉換指標
      if (sessionId) {
        personalityTestAPI.trackConversionStep({
          session_id: sessionId,
          step: 'result_engagement',
          action: 'page_exit',
          data: {
            time_spent: timeSpent,
            scroll_depth: conversionMetrics.scrollDepth,
            cta_views: conversionMetrics.ctaViews,
            cta_clicks: conversionMetrics.ctaClicks,
            share_clicks: conversionMetrics.shareClicks
          }
        });
      }
    };

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [sessionId, conversionMetrics]);

  // 追蹤CTA區域可見性
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.target === ctaSectionRef.current) {
            setConversionMetrics(prev => ({ ...prev, ctaViews: prev.ctaViews + 1 }));
            
            if (sessionId) {
              personalityTestAPI.trackConversionStep({
                session_id: sessionId,
                step: 'cta_view',
                action: 'section_visible',
                data: { ab_variant: abTestVariant }
              });
            }
          }
        });
      },
      { threshold: 0.5 }
    );

    if (ctaSectionRef.current) {
      observer.observe(ctaSectionRef.current);
    }

    return () => observer.disconnect();
  }, [sessionId, abTestVariant]);

  const loadTestResult = async () => {
    if (!sessionId) return;

    try {
      const result = await personalityTestAPI.getTestResult(sessionId);
      setResult(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '載入測試結果時發生錯誤';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleShareImageGenerated = (imageData: any) => {
    setShareData({
      image_url: imageData.image_url,
      share_text: imageData.share_text,
      share_url: imageData.share_url,
      result_id: result?.id || ''
    });
  };

  const handleShareComplete = (platform: string, success: boolean) => {
    setConversionMetrics(prev => ({ ...prev, shareClicks: prev.shareClicks + 1 }));
    
    if (success) {
      userExperienceService.trackInteraction({
        type: 'click',
        element: `share_success_${platform}`,
        timestamp: Date.now()
      });
      
      // 追蹤分享成功
      if (sessionId && result) {
        personalityTestAPI.trackConversionStep({
          session_id: sessionId,
          step: 'share_success',
          action: `shared_to_${platform}`,
          data: { 
            personality_type: result.personality_type.type,
            percentile: result.percentile 
          }
        });
      }
    } else {
      userExperienceService.trackInteraction({
        type: 'click',
        element: `share_failed_${platform}`,
        timestamp: Date.now()
      });
    }
  };

  const handleRegisterClick = () => {
    setConversionMetrics(prev => ({ ...prev, ctaClicks: prev.ctaClicks + 1 }));
    
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'register_from_result',
      timestamp: Date.now()
    });

    // 追蹤轉換點擊
    if (sessionId && result) {
      personalityTestAPI.trackConversionStep({
        session_id: sessionId,
        step: 'register_click',
        action: 'cta_clicked',
        data: { 
          ab_variant: abTestVariant,
          personality_type: result.personality_type.type,
          time_to_click: Date.now() - startTimeRef.current,
          scroll_depth: conversionMetrics.scrollDepth
        }
      });
    }

    // 導航到註冊頁面，帶上結果數據
    navigate('/personality-test/register', {
      state: { 
        resultId: result?.id,
        personalityType: result?.personality_type,
        sessionId: sessionId,
        abVariant: abTestVariant
      }
    });
  };

  const handleRetakeTest = () => {
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'retake_test',
      timestamp: Date.now()
    });

    navigate('/personality-test/start');
  };

  if (isLoading) {
    return (
      <div className="test-result-page loading">
        <div className="loading-container">
          <div className="loading-spinner-large"></div>
          <p className="loading-text">正在分析你的投資人格...</p>
          <div className="loading-progress">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="test-result-page error">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2 className="error-title">載入失敗</h2>
          <p className="error-message">{error}</p>
          <div className="error-actions">
            <button 
              className="retry-button"
              onClick={() => window.location.reload()}
            >
              重新載入
            </button>
            <button 
              className="home-button"
              onClick={() => navigate('/personality-test')}
            >
              返回首頁
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="test-result-page no-result">
        <div className="no-result-container">
          <div className="no-result-icon">🤔</div>
          <h2 className="no-result-title">找不到測試結果</h2>
          <p className="no-result-message">
            測試結果可能已過期或不存在，請重新進行測試。
          </p>
          <button 
            className="start-test-button"
            onClick={() => navigate('/personality-test')}
          >
            開始新測試
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="test-result-page" ref={pageRef}>
      <div className="result-container">
        
        {/* 結果標題區域 */}
        <header className="result-header">
          <div className="result-badge">
            <div className="badge-icon">{result.personality_type.icon || '🧠'}</div>
            <div className="badge-content">
              <h1 className="result-title">你的投資人格是</h1>
              <div className="personality-type">
                <span className="type-name">{result.personality_type.display_name}</span>
                <span className="type-subtitle">{result.personality_type.title}</span>
              </div>
            </div>
          </div>
          
          <div className="percentile-highlight">
            <div className="percentile-circle">
              <div className="percentile-number">{result.percentile}%</div>
              <div className="percentile-label">擊敗</div>
            </div>
            <p className="percentile-text">
              恭喜！你擊敗了 <strong>{result.percentile}%</strong> 的投資者！
            </p>
            {result.share_content?.celebrity_comparison && (
              <p className="celebrity-comparison">
                🌟 {result.share_content.celebrity_comparison}
              </p>
            )}
          </div>
        </header>

        {/* 維度分析雷達圖 */}
        <section className="dimensions-section">
          <h2 className="section-title">你的投資特徵分析</h2>
          <PersonalityRadarChart 
            scores={result.dimension_scores}
            size={320}
            animated={true}
            showLabels={true}
            showValues={true}
          />
        </section>

        {/* 詳細描述 */}
        <section className="description-section">
          <h2 className="section-title">詳細分析</h2>
          <div className="description-content">
            <div className="personality-description">
              <p className="description-text">{result.personality_type.description}</p>
            </div>
            
            {result.personality_type.characteristics && (
              <div className="characteristics-section">
                <h3 className="characteristics-title">你的投資特徵：</h3>
                <ul className="characteristics-list">
                  {result.personality_type.characteristics.map((characteristic, index) => (
                    <li key={index} className="characteristic-item">
                      <span className="characteristic-icon">✨</span>
                      <span className="characteristic-text">{characteristic}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.personality_type.investment_style && (
              <div className="investment-style-section">
                <h3 className="investment-style-title">你的投資風格：</h3>
                <p className="investment-style-text">{result.personality_type.investment_style}</p>
              </div>
            )}

            {result.recommendations && result.recommendations.length > 0 && (
              <div className="recommendations-section">
                <h3 className="recommendations-title">專業建議：</h3>
                <ul className="recommendations-list">
                  {result.recommendations.map((recommendation, index) => (
                    <li key={index} className="recommendation-item">
                      <span className="recommendation-icon">💡</span>
                      <span className="recommendation-text">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>

        {/* 分享區域 */}
        {showShareSection && (
          <section className="share-section">
            <h2 className="section-title">分享你的結果</h2>
            <p className="share-subtitle">
              讓朋友也來測試他們的投資人格吧！
            </p>
            
            {/* 分享圖片預覽 */}
            <div className="share-preview-container">
              <ShareImagePreview
                resultId={result.id}
                onImageGenerated={handleShareImageGenerated}
                onError={(error: any) => console.error('Share image error:', error)}
              />
            </div>

            {/* 社交分享按鈕 */}
            {shareData && (
              <div className="social-share-container">
                <SocialShareButtons
                  shareData={shareData}
                  onShareComplete={handleShareComplete}
                  showLabels={true}
                  size="large"
                  layout="horizontal"
                />
              </div>
            )}
          </section>
        )}

        {/* 轉換CTA區域 */}
        {showConversionSection && (
          <section className="conversion-section" ref={ctaSectionRef}>
            <ConversionCTA
              result={result}
              variant={abTestVariant}
              onRegisterClick={handleRegisterClick}
              onSecondaryAction={() => {
                // 可以添加更多詳情的處理
                console.log('Show more details clicked');
              }}
            />
          </section>
        )}

        {/* 測試信息 */}
        <footer className="result-footer">
          <div className="test-info">
            <span className="test-date">
              測試完成時間: {new Date(result.completed_at).toLocaleString()}
            </span>
            <span className="test-id">
              結果ID: {result.id}
            </span>
            <span className="completion-time">
              完成時間: {Math.round(result.completion_time / 60)}分鐘
            </span>
          </div>
          
          <div className="secondary-actions">
            <button 
              type="button"
              className="retake-button"
              onClick={handleRetakeTest}
            >
              重新測試
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default TestResultPage;