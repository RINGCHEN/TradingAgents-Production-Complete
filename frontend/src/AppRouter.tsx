import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// 主網站頁面
import LandingPage from './pages/LandingPage';
import AuthenticationPage from './pages/AuthenticationPage';
import PersonalityTestPage from './pages/PersonalityTestPage';
import AboutPage from './pages/AboutPage';
import HelpCenterPage from './pages/HelpCenterPage';

// 會員專區頁面
import UserDashboard from './pages/UserDashboard';
// import PortfolioPage from './pages/PortfolioPage';  // 舊的投資組合頁面
// import EmergencyPortfolioPage from './pages/EmergencyPortfolioPage';  // 舊的投資組合頁面
import SimplePortfolioPage from './pages/SimplePortfolioPage';  // 🔄 修復版投資組合頁面 (2025-09-10)
import AnalysisHistoryPage from './pages/AnalysisHistoryPage';
import AnalystSelectionPage from './pages/AnalystSelectionPage';
import StockSearchPage from './pages/StockSearchPage';
import MarketMonitorPage from './pages/MarketMonitorPage';
import NewsPage from './pages/NewsPage';

// 會員管理頁面
import SubscriptionManagementPage from './pages/SubscriptionManagementPage';
import PaymentHistoryPage from './pages/PaymentHistoryPage';

// 會員功能頁面
import PricingStrategyDemo from './pages/PricingStrategyDemo';
import ABTestingDemo from './pages/ABTestingDemo';

// PayUni支付相關頁面
import PaymentSuccessPage from './pages/PaymentSuccessPage';
import PaymentCancelPage from './pages/PaymentCancelPage';
import SimplePricingPage from './pages/SimplePricingPage';
import SimplePricingPageSimple from './pages/SimplePricingPageSimple';
import UltraSimplePage from './pages/UltraSimplePage';
import TestSimplePage from './pages/TestSimplePage';

// 管理後台頁面
import OptimizedAdminDashboard from './pages/OptimizedAdminDashboard';
import SecurityMonitorDashboard from './pages/SecurityMonitorDashboard';
import SystemMonitorDashboard from './pages/SystemMonitorDashboard';
import SystemConfigurationManagement from './pages/SystemConfigurationManagement';
import UserDetailsManagement from './pages/UserDetailsManagement';

// 保護路由組件
import { ProtectedRoute, MembershipRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

// 導航組件
import Navigation from './components/Navigation';

const AppRouter: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="app-container">
          <Navigation />
          <main className="main-content">
            <Routes>
              {/* 公開路由 */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/help" element={<HelpCenterPage />} />
              <Route path="/auth" element={<AuthenticationPage />} />
              <Route path="/login" element={<AuthenticationPage />} />
              <Route path="/register" element={<AuthenticationPage />} />
              <Route path="/pricing" element={<UltraSimplePage />} />
              <Route path="/pricing-simple" element={<SimplePricingPageSimple />} />
              <Route path="/pricing-full" element={<SimplePricingPage />} />
              <Route path="/test" element={<TestSimplePage />} />
              
              {/* PayUni支付相關路由 */}
              <Route path="/payment/success" element={<PaymentSuccessPage />} />
              <Route path="/payment/cancel" element={<PaymentCancelPage />} />
              <Route path="/payment/result" element={<PaymentSuccessPage />} />
              
              {/* 投資人格測試 */}
              <Route path="/personality-test" element={<PersonalityTestPage />} />
              
              {/* 會員專區路由 - 需要認證 */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <UserDashboard />
                  </ProtectedRoute>
                } 
              />
              
              {/* 基礎分析功能 - 免費會員可用 */}
              <Route 
                path="/stock-search" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <StockSearchPage />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/analyst-selection" 
                element={
                  <ProtectedRoute>
                    <AnalystSelectionPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* 進階功能 - 黃金會員以上 */}
              <Route 
                path="/portfolio" 
                element={
                  <MembershipRoute>
                    <SimplePortfolioPage />
                  </MembershipRoute>
                } 
              />
              
              <Route 
                path="/market-monitor" 
                element={
                  <ProtectedRoute>
                    <MarketMonitorPage />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/analysis-history" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <AnalysisHistoryPage />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/news" 
                element={
                  <ProtectedRoute>
                    <NewsPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* A/B 測試頁面 - 鑽石會員專享 */}
              <Route 
                path="/ab-testing" 
                element={
                  <MembershipRoute>
                    <ABTestingDemo />
                  </MembershipRoute>
                } 
              />
              
              {/* 會員管理路由 - 需要認證 */}
              <Route 
                path="/subscription" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <SubscriptionManagementPage />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/billing" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <PaymentHistoryPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* 會員升級頁面 */}
              <Route 
                path="/upgrade" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <SubscriptionManagementPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* 管理後台路由 - 需要管理員權限 */}
              <Route 
                path="/admin" 
                element={
                  <ProtectedRoute>
                    <OptimizedAdminDashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/admin/security" 
                element={
                  <ProtectedRoute>
                    <SecurityMonitorDashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/admin/system" 
                element={
                  <ProtectedRoute>
                    <SystemMonitorDashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/admin/config" 
                element={
                  <ProtectedRoute>
                    <SystemConfigurationManagement />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/admin/users" 
                element={
                  <ProtectedRoute>
                    <UserDetailsManagement />
                  </ProtectedRoute>
                } 
              />
              
              {/* 試用和升級路由 */}
              <Route 
                path="/trial" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <div style={{ padding: '40px', textAlign: 'center' }}>
                      <h1>🎯 免費試用</h1>
                      <p>7天免費試用黃金會員功能</p>
                      <button 
                        style={{ 
                          background: '#667eea', 
                          color: 'white', 
                          border: 'none', 
                          padding: '10px 20px', 
                          borderRadius: '5px',
                          cursor: 'pointer'
                        }}
                        onClick={() => window.location.href = '/pricing'}
                      >
                        開始試用
                      </button>
                    </div>
                  </ProtectedRoute>
                } 
              />
              
              {/* 外部連結重定向 */}
              <Route 
                path="/admin-external" 
                element={
                  <div style={{ padding: '40px', textAlign: 'center' }}>
                    <h1>🔧 管理後台</h1>
                    <p>正在重定向到外部管理後台...</p>
                    <p>如果沒有自動跳轉，請點擊 <a href="https://admin.03king.com" style={{ color: '#667eea' }}>這裡</a></p>
                  </div>
                } 
              />
              
              {/* 404 重定向 */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default AppRouter;