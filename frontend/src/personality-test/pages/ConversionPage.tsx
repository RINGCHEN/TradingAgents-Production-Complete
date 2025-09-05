import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnalyticsService } from '../services/AnalyticsService';
import { UTMParams } from '../PersonalityTestApp';

interface ConversionPageProps {
  analytics: AnalyticsService;
  utm_params?: UTMParams;
}

const ConversionPage: React.FC<ConversionPageProps> = ({ analytics, utm_params }) => {
  const navigate = useNavigate();

  useEffect(() => {
    // 追蹤頁面瀏覽
    analytics.trackPageView('conversion_page', {
      utm_params
    });
  }, [analytics, utm_params]);

  return (
    <div className="conversion-page">
      <div className="page-container">
        <div className="section-container">
          <h1>註冊轉換頁面</h1>
          <p>這裡將顯示註冊表單，包括：</p>
          <ul>
            <li>個性化註冊引導</li>
            <li>測試結果預填</li>
            <li>會員權益說明</li>
            <li>註冊表單</li>
          </ul>
          <button 
            type="button"
            className="cta-button primary"
            onClick={() => navigate('/')}
          >
            返回首頁
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConversionPage;