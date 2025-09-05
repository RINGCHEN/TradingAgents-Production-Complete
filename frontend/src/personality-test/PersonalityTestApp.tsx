import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './PersonalityTestApp.css';

// 獨立測試應用組件
import TestLandingPage from './pages/TestLandingPage';
import TestStartPage from './pages/TestStartPage';
import TestQuestionPage from './pages/TestQuestionPage';
import TestResultPage from './pages/TestResultPage';
import SharePage from './pages/SharePage';
import RegistrationPage from './pages/RegistrationPage';
import WelcomePage from './pages/WelcomePage';

// 分析服務
import { AnalyticsService } from './services/AnalyticsService';

// 類型定義
export interface UTMParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

export interface PersonalityTestAppProps {
  mode?: 'standalone' | 'embedded';
  theme?: 'light' | 'dark';
  utm_params?: UTMParams;
}

// URL參數解析工具
const useURLParams = () => {
  const location = useLocation();
  
  const getUTMParams = (): UTMParams => {
    const searchParams = new URLSearchParams(location.search);
    return {
      utm_source: searchParams.get('utm_source') || undefined,
      utm_medium: searchParams.get('utm_medium') || undefined,
      utm_campaign: searchParams.get('utm_campaign') || undefined,
      utm_term: searchParams.get('utm_term') || undefined,
      utm_content: searchParams.get('utm_content') || undefined,
    };
  };

  const getReferrer = (): string => {
    return document.referrer || 'direct';
  };

  return { getUTMParams, getReferrer };
};

// 主應用組件
const PersonalityTestApp: React.FC<PersonalityTestAppProps> = ({
  mode = 'standalone',
  theme = 'light',
  utm_params
}) => {
  const [analytics] = useState(() => new AnalyticsService());
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // 初始化分析服務
    const initializeApp = async () => {
      try {
        await analytics.initialize();
        
        // 追蹤應用啟動
        analytics.track('app_initialized', {
          mode,
          theme,
          utm_params,
          timestamp: new Date().toISOString(),
          user_agent: navigator.userAgent,
          screen_resolution: `${window.screen.width}x${window.screen.height}`,
          viewport_size: `${window.innerWidth}x${window.innerHeight}`
        });

        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize personality test app:', error);
        setIsInitialized(true); // 即使初始化失敗也要繼續
      }
    };

    initializeApp();
  }, [analytics, mode, theme, utm_params]);

  // 載入中狀態
  if (!isInitialized) {
    return (
      <div className={`personality-test-app ${mode} ${theme} loading`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">正在準備您的投資人格測試...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`personality-test-app ${mode} ${theme}`}>
      <Router basename="/personality-test">
        <Routes>
          {/* 測試首頁 */}
          <Route 
            path="/" 
            element={
              <TestLandingPage 
                analytics={analytics}
                utm_params={utm_params}
              />
            } 
          />
          
          {/* 開始測試 */}
          <Route 
            path="/start" 
            element={
              <TestStartPage 
                analytics={analytics}
                utm_params={utm_params}
              />
            } 
          />
          
          {/* 測試問題頁面 */}
          <Route 
            path="/question/:questionId" 
            element={
              <TestQuestionPage 
                analytics={analytics}
                utm_params={utm_params}
              />
            } 
          />
          
          {/* 結果頁面 */}
          <Route 
            path="/result/:sessionId" 
            element={<TestResultPage />} 
          />
          
          {/* 分享頁面 */}
          <Route 
            path="/share/:resultId" 
            element={<SharePage />} 
          />
          
          {/* 註冊轉換頁面 */}
          <Route 
            path="/register" 
            element={<RegistrationPage />} 
          />
          
          {/* 歡迎頁面 */}
          <Route 
            path="/welcome" 
            element={<WelcomePage />} 
          />
          
          {/* 默認重定向到首頁 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </div>
  );
};

// 帶有URL參數解析的包裝組件
const PersonalityTestAppWrapper: React.FC<Omit<PersonalityTestAppProps, 'utm_params'>> = (props) => {
  const { getUTMParams } = useURLParams();
  const utm_params = getUTMParams();

  return <PersonalityTestApp {...props} utm_params={utm_params} />;
};

export default PersonalityTestApp;
export { PersonalityTestAppWrapper };