import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import { EnhancedAuthProvider } from './contexts/EnhancedAuthContext';
import { SimpleAuthProvider } from './contexts/SimpleAuthContext';

// 錯誤診斷系統
import ErrorDiagnosticsProvider from './components/ErrorDiagnosticsProvider';
import HomepageErrorDetector from './components/HomepageErrorDetector';

// 錯誤邊界系統
import ErrorBoundary from './components/ErrorBoundary';
import { ErrorStateProvider } from './contexts/ErrorStateContext';
import { withPageErrorBoundary } from './components/withErrorBoundary';

// 路由保護系統
import { ProtectedRoute, MembershipRoute } from './components/ProtectedRoute';

// 頁面組件 (使用錯誤邊界保護)
import LandingPageComponent from './pages/LandingPage';
import AuthenticationPageComponent from './pages/AuthenticationPage';
import UserDashboardComponent from './pages/UserDashboard';
import AnalystSelectionPageComponent from './pages/AnalystSelectionPage';
import StockSearchPageComponent from './pages/StockSearchPage';
import IntegratedPortfolioPageComponent from './pages/IntegratedPortfolioPage';
import AnalysisHistoryPageComponent from './pages/AnalysisHistoryPage';
import MarketMonitorPageComponent from './pages/MarketMonitorPage';
import AboutPageComponent from './pages/AboutPage';
import HelpCenterPageComponent from './pages/HelpCenterPage';
import PersonalityTestPageComponent from './pages/PersonalityTestPage';
import SubscriptionManagementPageComponent from './pages/SubscriptionManagementPage';
import PaymentHistoryPageComponent from './pages/PaymentHistoryPage';
import AuthTestPageComponent from './pages/AuthTestPage';
import ContactPageComponent from './pages/ContactPage';
import PrivacyPageComponent from './pages/PrivacyPage';
import TermsPageComponent from './pages/TermsPage';
import DisclaimerPageComponent from './pages/DisclaimerPage';
import ApiPageComponent from './pages/ApiPage';

// PayUni定價頁面
import ProfessionalPricingPageComponent from './pages/ProfessionalPricingPage';
import SimplePricingPageComponent from './pages/SimplePricingPage';
import SimplePricingPageSimpleComponent from './pages/SimplePricingPageSimple';

// PayUni支付頁面
import PayUniPaymentPageComponent from './pages/PayUniPaymentPage';
// import PaymentSuccessPageComponent from './pages/PaymentSuccessPage'; // 臨時註釋掉以避免構建錯誤

// 管理後台組件
import AdminApp from './admin/AdminApp_Ultimate';

// 為頁面組件添加錯誤邊界保護
const LandingPage = withPageErrorBoundary(LandingPageComponent);
const AuthenticationPage = withPageErrorBoundary(AuthenticationPageComponent);
const UserDashboard = withPageErrorBoundary(UserDashboardComponent);
const AnalystSelectionPage = withPageErrorBoundary(AnalystSelectionPageComponent);
const StockSearchPage = withPageErrorBoundary(StockSearchPageComponent);
const PortfolioPage = withPageErrorBoundary(IntegratedPortfolioPageComponent);
const AnalysisHistoryPage = withPageErrorBoundary(AnalysisHistoryPageComponent);
const MarketMonitorPage = withPageErrorBoundary(MarketMonitorPageComponent);
const AboutPage = withPageErrorBoundary(AboutPageComponent);
const HelpCenterPage = withPageErrorBoundary(HelpCenterPageComponent);
const PersonalityTestPage = withPageErrorBoundary(PersonalityTestPageComponent);
const SubscriptionManagementPage = withPageErrorBoundary(SubscriptionManagementPageComponent);
const PaymentHistoryPage = withPageErrorBoundary(PaymentHistoryPageComponent);
const AuthTestPage = withPageErrorBoundary(AuthTestPageComponent);
const ContactPage = withPageErrorBoundary(ContactPageComponent);
const PrivacyPage = withPageErrorBoundary(PrivacyPageComponent);
const TermsPage = withPageErrorBoundary(TermsPageComponent);
const DisclaimerPage = withPageErrorBoundary(DisclaimerPageComponent);
const ApiPage = withPageErrorBoundary(ApiPageComponent);

// PayUni定價頁面（錯誤邊界保護）
const ProfessionalPricingPage = withPageErrorBoundary(ProfessionalPricingPageComponent);
const SimplePricingPage = withPageErrorBoundary(SimplePricingPageComponent);
const SimplePricingPageSimple = withPageErrorBoundary(SimplePricingPageSimpleComponent);

// PayUni支付頁面（錯誤邊界保護）
const PayUniPaymentPage = withPageErrorBoundary(PayUniPaymentPageComponent);
// 臨時支付成功頁面組件
const PaymentSuccessPage = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const orderNumber = urlParams.get('order_number') || 'N/A';
  const amount = urlParams.get('amount') || '0';
  const tierType = urlParams.get('tier') || 'gold';
  const isTestMode = urlParams.get('test_mode') === 'true';

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      color: 'white'
    }}>
      <div style={{
        background: 'white',
        color: 'black',
        padding: '40px',
        borderRadius: '20px',
        textAlign: 'center',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.1)',
        maxWidth: '500px',
        width: '90%'
      }}>
        <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🎉</div>
        <h1 style={{ color: '#28a745', marginBottom: '20px' }}>
          {isTestMode ? '測試支付成功！' : '支付成功！'}
        </h1>
        <div style={{ marginBottom: '30px', lineHeight: '1.6' }}>
          <p><strong>訂單號碼:</strong> {orderNumber}</p>
          <p><strong>支付金額:</strong> NT$ {parseInt(amount).toLocaleString()}</p>
          <p><strong>會員方案:</strong> {tierType === 'gold' ? '黃金方案' : '鑽石方案'}</p>
          {isTestMode && (
            <p style={{ color: '#ff6b6b', fontSize: '0.9rem', marginTop: '15px' }}>
              ⚠️ 這是測試模式，實際未扣款
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
          <button
            onClick={() => window.location.href = '/'}
            style={{
              background: '#28a745',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500'
            }}
          >
            返回首頁
          </button>
          <button
            onClick={() => window.location.href = '/auth'}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500'
            }}
          >
            會員中心
          </button>
        </div>
        <p style={{ marginTop: '20px', fontSize: '0.85rem', color: '#666' }}>
          會員權益將在5分鐘內生效，感謝您的支持！
        </p>
      </div>
    </div>
  );
};

// 樣式
import './App.css';

const App: React.FC = () => {
  const handleCriticalError = (errors: any[]) => {
    console.error('Critical homepage errors detected:', errors);
    // 可以在這裡添加用戶通知或自動重定向邏輯
  };

  const handleAppError = (error: Error, errorInfo: React.ErrorInfo, errorId: string) => {
    console.error('App-level error caught:', { error, errorInfo, errorId });
    // 可以在這裡添加全局錯誤處理邏輯
  };

  // 檢測是否為管理後台域名或使用管理後台參數
  // 支援多種管理後台進入方式：
  // 1. admin.03king.com 域名
  // 2. twstock-admin 域名
  // 3. /admin 路徑
  // 4. ?admin=true 參數
  const urlParams = new URLSearchParams(window.location.search);
  const isAdminParam = urlParams.get('admin') === 'true';
  
  const isAdminDomain = window.location.hostname === 'admin.03king.com' || 
                       window.location.hostname.includes('twstock-admin') ||
                       window.location.pathname.startsWith('/admin') ||
                       isAdminParam;
  
  console.log('🔍 Domain check:', window.location.hostname, 'pathname:', window.location.pathname, 'isAdmin:', isAdminDomain);
  
  // 如果是管理後台域名，直接顯示管理後台
  if (isAdminDomain) {
    console.log('🔧 Loading TradingAgents Ultimate Admin Backend - All 15+ Modules with Auth');
    return (
      <ErrorBoundary
        componentName="AdminApp"
        enableRetry={true}
        maxRetries={2}
        enableAutoRecovery={true}
        fallbackMode="static"
        onError={handleAppError}
      >
        <ErrorStateProvider enableAutoRecovery={true}>
          <ErrorDiagnosticsProvider 
            enableAutoRefresh={true}
            refreshInterval={30000}
            showDebugInfo={process.env.NODE_ENV === 'development'}
          >
            <Router>
              <AdminApp />
            </Router>
          </ErrorDiagnosticsProvider>
        </ErrorStateProvider>
      </ErrorBoundary>
    );
  }
  
  console.log('🌟 Loading TradingAgents Main Website');

  return (
    <ErrorBoundary
      componentName="App"
      enableRetry={true}
      maxRetries={2}
      enableAutoRecovery={true}
      fallbackMode="static"
      onError={handleAppError}
    >
      <ErrorStateProvider enableAutoRecovery={true}>
        <ErrorDiagnosticsProvider 
          enableAutoRefresh={true}
          refreshInterval={30000}
          showDebugInfo={process.env.NODE_ENV === 'development'}
        >
          <SimpleAuthProvider>
            <Router>
              <div className="App" data-testid="app-root">
                <HomepageErrorDetector 
                  onCriticalError={handleCriticalError}
                  enableAutoFix={true}
                />
                
                <ErrorBoundary
                  componentName="Router"
                  enableRetry={true}
                  maxRetries={3}
                  fallbackMode="minimal"
                >
                  <Routes>
                    {/* 公開頁面 */}
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/auth" element={<AuthenticationPage />} />
                    <Route path="/about" element={<AboutPage />} />
                    <Route path="/help" element={<HelpCenterPage />} />
                    <Route path="/personality-test" element={<PersonalityTestPage />} />
                    <Route path="/auth-test" element={<AuthTestPage />} />
                    <Route path="/contact" element={<ContactPage />} />
                    <Route path="/privacy" element={<PrivacyPage />} />
                    <Route path="/terms" element={<TermsPage />} />
                    <Route path="/disclaimer" element={<DisclaimerPage />} />
                    <Route path="/api" element={<ApiPage />} />
                    
                    {/* PayUni定價頁面 */}
                    <Route path="/pricing" element={<ProfessionalPricingPage />} />
                    <Route path="/pricing-full" element={<SimplePricingPage />} />
                    <Route path="/pricing-simple" element={<SimplePricingPageSimple />} />
                    
                    {/* PayUni支付頁面 */}
                    <Route path="/payuni/payment-page/:orderNumber" element={<PayUniPaymentPage />} />
                    
                    {/* PayUni支付成功頁面 */}
                    <Route path="/payment/success" element={<PaymentSuccessPage />} />
                    
                    {/* PayUni測試路由 */}
                    <Route path="/payuni-test" element={
                      <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        minHeight: '100vh',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        fontFamily: 'Arial, sans-serif'
                      }}>
                        <div style={{
                          background: 'white',
                          color: 'black',
                          padding: '40px',
                          borderRadius: '20px',
                          textAlign: 'center',
                          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.1)'
                        }}>
                          <h1 style={{fontSize: '48px', margin: '20px 0'}}>🎉</h1>
                          <h2>PayUni 路由測試成功！</h2>
                          <p>App.tsx 路由修復完成！</p>
                          <button 
                            onClick={() => window.location.href = '/pricing'}
                            style={{
                              padding: '10px 20px',
                              fontSize: '16px',
                              marginTop: '20px',
                              background: '#28a745',
                              color: 'white',
                              border: 'none',
                              borderRadius: '5px',
                              cursor: 'pointer'
                            }}
                          >
                            返回定價頁面
                          </button>
                        </div>
                      </div>
                    } />
                    
                    {/* 管理後台 */}
                    <Route path="/admin/*" element={<AdminApp />} />
                    
                    {/* 會員專屬頁面 - 使用路由保護 */}
                    <Route path="/dashboard" element={
                      <ProtectedRoute requireAuth={true}>
                        <UserDashboard />
                      </ProtectedRoute>
                    } />
                    <Route path="/analysts" element={
                      <MembershipRoute>
                        <AnalystSelectionPage />
                      </MembershipRoute>
                    } />
                    <Route path="/search" element={
                      <ProtectedRoute requireAuth={true}>
                        <StockSearchPage />
                      </ProtectedRoute>
                    } />
                    <Route path="/portfolio" element={
                      <MembershipRoute>
                        <PortfolioPage />
                      </MembershipRoute>
                    } />
                    <Route path="/history" element={
                      <ProtectedRoute requireAuth={true}>
                        <AnalysisHistoryPage />
                      </ProtectedRoute>
                    } />
                    <Route path="/monitor" element={
                      <MembershipRoute>
                        <MarketMonitorPage />
                      </MembershipRoute>
                    } />
                    <Route path="/subscription" element={
                      <ProtectedRoute requireAuth={true}>
                        <SubscriptionManagementPage />
                      </ProtectedRoute>
                    } />
                    <Route path="/payments" element={
                      <ProtectedRoute requireAuth={true}>
                        <PaymentHistoryPage />
                      </ProtectedRoute>
                    } />
                    
                    {/* 404頁面 */}
                    <Route path="*" element={<LandingPage />} />
                  </Routes>
                </ErrorBoundary>
              </div>
            </Router>
          </SimpleAuthProvider>
        </ErrorDiagnosticsProvider>
      </ErrorStateProvider>
    </ErrorBoundary>
  );
};

export default App;