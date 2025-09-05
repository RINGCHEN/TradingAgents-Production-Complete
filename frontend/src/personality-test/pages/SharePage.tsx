import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PersonalityTestAPI } from '../services/PersonalityTestAPI';
import { userExperienceService } from '../services/UserExperienceService';
import SocialShareButtons from '../components/SocialShareButtons';
import './SharePage.css';

interface SharePageProps {
  // 可以通過props傳入數據
}

interface ShareData {
  share_image: {
    image_url: string;
    share_text: string;
    share_url: string;
    template_id: string;
  };
  result: {
    id: string;
    personality_type: string;
    percentile: number;
    description: string;
    dimension_scores: Record<string, number>;
  };
  meta_tags: {
    title: string;
    description: string;
    image: string;
    url: string;
  };
}

const SharePage: React.FC<SharePageProps> = () => {
  const { resultId } = useParams<{ resultId: string }>();
  const navigate = useNavigate();
  
  const [shareData, setShareData] = useState<ShareData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (resultId) {
      loadShareData();
      trackSharePageView();
    }
  }, [resultId]);

  useEffect(() => {
    // 動態更新頁面meta標籤
    if (shareData) {
      updateMetaTags(shareData.meta_tags);
    }
  }, [shareData]);

  const loadShareData = async () => {
    if (!resultId) return;

    try {
      const api = new PersonalityTestAPI();
      const response = await api.request(`/api/share/result/${resultId}`, 'GET');
      
      if (response.success) {
        setShareData(response.data);
      } else {
        throw new Error('分享內容不存在或已過期');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '載入分享內容時發生錯誤';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const trackSharePageView = () => {
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'share_page_view',
      timestamp: Date.now(),
      value: resultId
    });

    // 追蹤分享點擊（有人通過分享鏈接訪問）
    userExperienceService.trackMetric('share_click_through', 1, 'count');
  };

  const updateMetaTags = (metaTags: ShareData['meta_tags']) => {
    // 更新頁面標題
    document.title = metaTags.title;

    // 更新或創建meta標籤
    const updateMetaTag = (property: string, content: string) => {
      let meta = document.querySelector(`meta[property="${property}"]`) as HTMLMetaElement;
      if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute('property', property);
        document.head.appendChild(meta);
      }
      meta.content = content;
    };

    // Open Graph標籤
    updateMetaTag('og:title', metaTags.title);
    updateMetaTag('og:description', metaTags.description);
    updateMetaTag('og:image', `${window.location.origin}${metaTags.image}`);
    updateMetaTag('og:url', `${window.location.origin}${metaTags.url}`);
    updateMetaTag('og:type', 'website');

    // Twitter Card標籤
    updateMetaTag('twitter:card', 'summary_large_image');
    updateMetaTag('twitter:title', metaTags.title);
    updateMetaTag('twitter:description', metaTags.description);
    updateMetaTag('twitter:image', `${window.location.origin}${metaTags.image}`);
  };

  const handleTakeTest = () => {
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'take_test_from_share',
      timestamp: Date.now()
    });

    navigate('/personality-test');
  };

  const handleShareComplete = (platform: string, success: boolean) => {
    if (success) {
      userExperienceService.trackInteraction({
        type: 'click',
        element: `reshare_${platform}`,
        timestamp: Date.now()
      });
    }
  };

  if (isLoading) {
    return (
      <div className="share-page loading">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">載入分享內容中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="share-page error">
        <div className="error-container">
          <div className="error-icon">😕</div>
          <h2 className="error-title">分享內容不存在</h2>
          <p className="error-message">{error}</p>
          <button 
            className="take-test-button"
            onClick={handleTakeTest}
          >
            開始我的測試
          </button>
        </div>
      </div>
    );
  }

  if (!shareData) {
    return (
      <div className="share-page no-data">
        <div className="no-data-container">
          <div className="no-data-icon">🤔</div>
          <h2 className="no-data-title">找不到分享內容</h2>
          <p className="no-data-message">
            這個分享鏈接可能已過期或不存在。
          </p>
          <button 
            className="take-test-button"
            onClick={handleTakeTest}
          >
            開始我的測試
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="share-page">
      <div className="share-container">
        
        {/* 分享標題 */}
        <header className="share-header">
          <h1 className="share-title">朋友分享了他們的投資人格測試結果</h1>
          <p className="share-subtitle">看看他們的投資風格，也來測測你的吧！</p>
        </header>

        {/* 分享內容展示 */}
        <section className="shared-result-section">
          <div className="shared-result-card">
            
            {/* 分享圖片 */}
            <div className="shared-image-container">
              <img 
                src={shareData.share_image.image_url} 
                alt={`${shareData.result.personality_type}的投資人格測試結果`}
                className="shared-image"
              />
            </div>

            {/* 結果摘要 */}
            <div className="result-summary">
              <div className="personality-badge">
                <span className="personality-type">{shareData.result.personality_type}</span>
                <span className="percentile-text">擊敗了 {shareData.result.percentile}% 的投資者</span>
              </div>
              
              <p className="result-description">
                {shareData.result.description.substring(0, 150)}...
              </p>

              {/* 維度分數預覽 */}
              <div className="dimensions-preview">
                <h3 className="dimensions-title">投資特徵分析</h3>
                <div className="dimensions-bars">
                  {Object.entries(shareData.result.dimension_scores).map(([dimension, score]) => (
                    <div key={dimension} className="dimension-bar">
                      <span className="dimension-name">{dimension}</span>
                      <div className="bar-container">
                        <div 
                          className="bar-fill"
                          style={{ width: `${score}%` }}
                        ></div>
                        <span className="score-text">{score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 行動呼籲 */}
        <section className="cta-section">
          <div className="cta-card">
            <h2 className="cta-title">你的投資人格是什麼？</h2>
            <p className="cta-description">
              只需3分鐘，發現你的投資風格，獲得個性化的投資建議！
            </p>
            
            <div className="cta-features">
              <div className="feature-item">
                <span className="feature-icon">🎯</span>
                <span className="feature-text">個人投資風格分析</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📊</span>
                <span className="feature-text">五維度雷達圖</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">💡</span>
                <span className="feature-text">個性化投資建議</span>
              </div>
            </div>

            <button 
              className="take-test-button primary"
              onClick={handleTakeTest}
            >
              開始我的免費測試
            </button>
          </div>
        </section>

        {/* 重新分享區域 */}
        <section className="reshare-section">
          <h3 className="reshare-title">覺得有趣嗎？分享給更多朋友！</h3>
          <div className="reshare-buttons">
            <SocialShareButtons
              shareData={{
                image_url: shareData.share_image.image_url,
                share_text: shareData.share_image.share_text,
                share_url: shareData.share_image.share_url,
                result_id: shareData.result.id
              }}
              onShareComplete={handleShareComplete}
              showLabels={true}
              size="medium"
              layout="horizontal"
            />
          </div>
        </section>

        {/* 頁腳信息 */}
        <footer className="share-footer">
          <p className="footer-text">
            TradingAgents - 專業的AI投資分析平台
          </p>
          <p className="footer-link">
            <a href="/personality-test" onClick={handleTakeTest}>
              開始你的投資人格測試 →
            </a>
          </p>
        </footer>
      </div>
    </div>
  );
};

export default SharePage;