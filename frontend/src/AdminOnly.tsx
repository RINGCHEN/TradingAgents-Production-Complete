/**
 * 專用管理後台應用入口
 * 只顯示管理後台，不包含主網站內容
 */

import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ErrorStateProvider } from './contexts/ErrorStateContext';
import ErrorBoundary from './components/ErrorBoundary';
import ErrorDiagnosticsProvider from './components/ErrorDiagnosticsProvider';

// 管理後台組件
import AdminApp from './admin/AdminApp_Ultimate';

const AdminOnly: React.FC = () => {
  return (
    <ErrorStateProvider>
      <ErrorBoundary>
        <ErrorDiagnosticsProvider>
          <Router>
            {/* 直接顯示管理後台，不需要路由匹配 */}
            <AdminApp />
          </Router>
        </ErrorDiagnosticsProvider>
      </ErrorBoundary>
    </ErrorStateProvider>
  );
};

export default AdminOnly;