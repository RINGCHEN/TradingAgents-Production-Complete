import React, { useState, useEffect, Suspense, lazy } from 'react';
import { useUser, useLogout } from '../hooks/useAuth';
import { adminApiClient } from '../services/AdminApiClient';
import { performanceOptimizer, usePerformanceOptimizer } from '../services/PerformanceOptimizer';
import './AdminDashboard.css';

// 懶載入的子組件
const SystemOverview = lazy(() => import('../components/admin/SystemOverview'));
const UserManagement = lazy(() => import('../components/admin/UserManagement'));
const ConfigManagement = lazy(() => import('../components/admin/ConfigManagement'));
const PerformanceMonitor = lazy(() => import('../components/admin/PerformanceMonitor'));

// 優化的管理後台主頁面
// 實現懶載入、記憶化和性能監控

interface SystemStatus {
  status: string;
  timestamp: string;
  version: string;
  database: string;
  services: {
    api: string;
    database: string;
  };
}

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

interface ConfigItem {
  id: number;
  config_key: string;
  config_value: string;
  description: string;
  created_at: string;
  updated_at: string;
}

interface TabData {
  systemStatus: SystemStatus | null;
  users: User[];
  configs: ConfigItem[];
  lastRefresh: Date;
}

const OptimizedAdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tabData, setTabData] = useState<TabData>({
    systemStatus: null,
    users: [],
    configs: [],
    lastRefresh: new Date()
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 使用性能優化器
  const {
    optimizedMemo,
    optimizedCallback,
    debounce,
    throttle,
    getMetrics
  } = usePerformanceOptimizer('OptimizedAdminDashboard');

  // 使用認證Hook
  const { user, isAuthenticated, refresh: refreshUser } = useUser();
  const { logout, isLoggingOut } = useLogout();

  // 優化的數據獲取函數
  const fetchSystemStatus = optimizedCallback(async () => {
    try {
      const response = await adminApiClient.get('/admin/system/health', { useCache: true });
      return response.data;
    } catch (error) {
      console.error('獲取系統狀態失敗:', error);
      throw error;
    }
  }, []);

  const fetchUsers = optimizedCallback(async () => {
    try {
      const response = await adminApiClient.get('/admin/users', { useCache: true });
      return response.data;
    } catch (error) {
      console.error('獲取用戶列表失敗:', error);
      throw error;
    }
  }, []);

  const fetchConfigs = optimizedCallback(async () => {
    try {
      const response = await adminApiClient.get('/admin/configs', { useCache: true });
      return response.data;
    } catch (error) {
      console.error('獲取配置列表失敗:', error);
      throw error;
    }
  }, []);

  // 批量數據獲取
  const fetchAllData = optimizedCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // 使用批量請求優化
      const [systemStatus, users, configs] = await adminApiClient.batchRequests([
        { method: 'GET', url: '/admin/system/health', config: { useCache: true } },
        { method: 'GET', url: '/admin/users', config: { useCache: true } },
        { method: 'GET', url: '/admin/configs', config: { useCache: true } }
      ]);

      setTabData({
        systemStatus: systemStatus.data,
        users: users.data,
        configs: configs.data,
        lastRefresh: new Date()
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : '數據獲取失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  // 防抖的刷新函數
  const debouncedRefresh = debounce(fetchAllData, 300);

  // 節流的標籤切換
  const throttledTabChange = throttle((tab: string) => {
    setActiveTab(tab);
    
    // 預加載相關數據
    if (tab === 'users' && tabData.users.length === 0) {
      fetchUsers().then(users => {
        setTabData(prev => ({ ...prev, users }));
      }).catch(console.error);
    } else if (tab === 'configs' && tabData.configs.length === 0) {
      fetchConfigs().then(configs => {
        setTabData(prev => ({ ...prev, configs }));
      }).catch(console.error);
    }
  }, 100);

  // 優化的登出處理
  const handleLogout = optimizedCallback(async () => {
    try {
      await logout();
      // 清理緩存
      adminApiClient.clearCache();
      performanceOptimizer.clearMetrics('OptimizedAdminDashboard');
    } catch (error) {
      console.error('登出失敗:', error);
    }
  }, [logout]);

  // 記憶化的標籤配置
  const tabConfig = optimizedMemo(() => [
    { id: 'dashboard', label: '系統概覽', icon: '📊' },
    { id: 'users', label: '用戶管理', icon: '👥' },
    { id: 'configs', label: '配置管理', icon: '⚙️' },
    { id: 'performance', label: '性能監控', icon: '📈' }
  ], []);

  // 記憶化的用戶信息
  const userInfo = optimizedMemo(() => ({
    username: user?.username || 'Unknown',
    email: user?.email || '',
    isAdmin: user?.is_admin || false
  }), [user]);

  // 初始化數據獲取
  useEffect(() => {
    if (isAuthenticated) {
      // 預加載常用數據
      adminApiClient.preloadData([
        '/admin/system/health',
        '/admin/users',
        '/admin/configs'
      ]);
      
      fetchAllData();
    }
  }, [isAuthenticated, fetchAllData]);

  // 定期刷新系統狀態
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(() => {
      fetchSystemStatus().then(systemStatus => {
        setTabData(prev => ({ ...prev, systemStatus, lastRefresh: new Date() }));
      }).catch(console.error);
    }, 30000); // 30秒刷新一次

    return () => clearInterval(interval);
  }, [isAuthenticated, fetchSystemStatus]);

  // 記憶化的渲染內容
  const renderTabContent = optimizedMemo(() => {
    const LoadingSpinner = () => (
      <div className="loading-spinner">
        <div className="spinner"></div>
        <span>載入中...</span>
      </div>
    );

    const ErrorMessage = ({ message }: { message: string }) => (
      <div className="error-message">
        <span className="error-icon">⚠️</span>
        <span>{message}</span>
        <button onClick={debouncedRefresh} className="retry-button">
          重試
        </button>
      </div>
    );

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage message={error} />;

    switch (activeTab) {
      case 'dashboard':
        return (
          <Suspense fallback={<LoadingSpinner />}>
            <SystemOverview 
              systemStatus={tabData.systemStatus}
              lastRefresh={tabData.lastRefresh}
              onRefresh={debouncedRefresh}
            />
          </Suspense>
        );
      case 'users':
        return (
          <Suspense fallback={<LoadingSpinner />}>
            <UserManagement 
              users={tabData.users}
              onRefresh={debouncedRefresh}
            />
          </Suspense>
        );
      case 'configs':
        return (
          <Suspense fallback={<LoadingSpinner />}>
            <ConfigManagement 
              configs={tabData.configs}
              onRefresh={debouncedRefresh}
            />
          </Suspense>
        );
      case 'performance':
        return (
          <Suspense fallback={<LoadingSpinner />}>
            <PerformanceMonitor 
              metrics={getMetrics()}
              apiStats={adminApiClient.getStats()}
            />
          </Suspense>
        );
      default:
        return <div>未知標籤</div>;
    }
  }, [activeTab, tabData, loading, error, debouncedRefresh, getMetrics]);

  // 記憶化的標籤導航
  const renderTabNavigation = optimizedMemo(() => (
    <nav className="admin-nav">
      {tabConfig.map(tab => (
        <button
          key={tab.id}
          className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => throttledTabChange(tab.id)}
          aria-selected={activeTab === tab.id}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  ), [tabConfig, activeTab, throttledTabChange]);

  // 記憶化的頭部
  const renderHeader = optimizedMemo(() => (
    <header className="admin-header">
      <div className="header-left">
        <h1 className="admin-title">TradingAgents 管理後台</h1>
        <span className="last-refresh">
          最後更新: {tabData.lastRefresh.toLocaleTimeString()}
        </span>
      </div>
      <div className="header-right">
        <div className="user-info">
          <span className="user-name">{userInfo.username}</span>
          <span className="user-email">{userInfo.email}</span>
          {userInfo.isAdmin && <span className="admin-badge">管理員</span>}
        </div>
        <button 
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="logout-button"
        >
          {isLoggingOut ? '登出中...' : '登出'}
        </button>
      </div>
    </header>
  ), [userInfo, tabData.lastRefresh, handleLogout, isLoggingOut]);

  if (!isAuthenticated) {
    return (
      <div className="auth-required">
        <h2>需要認證</h2>
        <p>請先登錄以訪問管理後台</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard optimized">
      {renderHeader}
      {renderTabNavigation}
      <main className="admin-content">
        {renderTabContent}
      </main>
    </div>
  );
};

// 使用性能優化器記憶化整個組件
export default performanceOptimizer.memoizeComponent(
  OptimizedAdminDashboard,
  'OptimizedAdminDashboard'
);