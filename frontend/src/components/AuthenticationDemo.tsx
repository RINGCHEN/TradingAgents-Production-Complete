/**
 * AuthenticationDemo - 認證系統演示組件
 * 展示修復後的認證系統功能，包括錯誤處理和訪客模式降級
 */

import React, { useState, useEffect } from 'react';
import { useEnhancedAuth, useAuthError, useGuestMode } from '../contexts/EnhancedAuthContext';
import { AuthErrorHandler, formatAuthErrorMessage } from '../utils/AuthErrors';

interface AuthenticationDemoProps {
  className?: string;
}

const AuthenticationDemo: React.FC<AuthenticationDemoProps> = ({ className = '' }) => {
  const {
    user,
    isAuthenticated,
    isLoading,
    isInitialized,
    mode,
    login,
    logout,
    refresh,
    membershipStatus,
    canAccessFeature
  } = useEnhancedAuth();

  const { error, clearError, retryInitialization, hasRecoverableError } = useAuthError();
  const { isGuestMode, switchToGuest } = useGuestMode();

  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [testResults, setTestResults] = useState<string[]>([]);

  // 添加測試結果
  const addTestResult = (result: string) => {
    setTestResults(prev => [...prev.slice(-9), `${new Date().toLocaleTimeString()}: ${result}`]);
  };

  // 處理登錄
  const handleLogin = async () => {
    try {
      addTestResult('嘗試登錄...');
      const result = await login(loginForm);
      
      if (result.success) {
        addTestResult('✅ 登錄成功');
        setShowLoginForm(false);
        setLoginForm({ email: '', password: '', name: '' });
      } else {
        const errorMsg = result.error ? formatAuthErrorMessage(result.error) : null;
        addTestResult(`❌ 登錄失敗: ${errorMsg?.message || '未知錯誤'}`);
      }
    } catch (error) {
      addTestResult(`❌ 登錄異常: ${error instanceof Error ? error.message : '未知錯誤'}`);
    }
  };

  // 處理登出
  const handleLogout = async () => {
    try {
      addTestResult('嘗試登出...');
      await logout();
      addTestResult('✅ 登出成功');
    } catch (error) {
      addTestResult(`❌ 登出失敗: ${error instanceof Error ? error.message : '未知錯誤'}`);
    }
  };

  // 測試錯誤處理
  const testErrorHandling = async () => {
    try {
      addTestResult('測試錯誤處理...');
      const result = await login({ email: 'error@test.com', password: 'test' });
      
      if (!result.success && result.error) {
        const errorInfo = AuthErrorHandler.handleAuthError(result.error);
        const userMessage = formatAuthErrorMessage(errorInfo);
        addTestResult(`✅ 錯誤處理正常: ${userMessage.title}`);
      }
    } catch (error) {
      addTestResult(`❌ 錯誤處理測試失敗: ${error instanceof Error ? error.message : '未知錯誤'}`);
    }
  };

  // 測試功能訪問
  const testFeatureAccess = () => {
    const features = ['stock-analysis', 'advanced-analysis', 'portfolio-management', 'real-time-alerts'];
    
    features.forEach(feature => {
      const access = canAccessFeature(feature);
      const status = access.allowed ? '✅' : '❌';
      const reason = access.reason ? ` (${access.reason})` : '';
      addTestResult(`${status} ${feature}${reason}`);
    });
  };

  // 刷新認證狀態
  const handleRefresh = async () => {
    try {
      addTestResult('刷新認證狀態...');
      await refresh();
      addTestResult('✅ 刷新成功');
    } catch (error) {
      addTestResult(`❌ 刷新失敗: ${error instanceof Error ? error.message : '未知錯誤'}`);
    }
  };

  // 重試初始化
  const handleRetryInit = async () => {
    try {
      addTestResult('重試初始化...');
      await retryInitialization();
      addTestResult('✅ 重試成功');
    } catch (error) {
      addTestResult(`❌ 重試失敗: ${error instanceof Error ? error.message : '未知錯誤'}`);
    }
  };

  // 切換到訪客模式
  const handleSwitchToGuest = () => {
    addTestResult('切換到訪客模式...');
    switchToGuest();
    addTestResult('✅ 已切換到訪客模式');
  };

  // 監聽認證狀態變化
  useEffect(() => {
    if (isInitialized) {
      addTestResult(`🔄 認證狀態: ${mode} (已初始化)`);
    }
  }, [isInitialized, mode]);

  // 監聽錯誤變化
  useEffect(() => {
    if (error) {
      const errorMsg = formatAuthErrorMessage(error);
      addTestResult(`⚠️ 認證錯誤: ${errorMsg.title} - ${errorMsg.message}`);
    }
  }, [error]);

  return (
    <div className={`auth-demo p-6 bg-white rounded-lg shadow-lg ${className}`}>
      <h2 className="text-2xl font-bold mb-6 text-gray-800">認證系統演示</h2>
      
      {/* 系統狀態顯示 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold mb-2 text-gray-700">系統狀態</h3>
          <div className="space-y-1 text-sm">
            <div>初始化: <span className={isInitialized ? 'text-green-600' : 'text-red-600'}>
              {isInitialized ? '✅ 已初始化' : '❌ 未初始化'}
            </span></div>
            <div>認證狀態: <span className={isAuthenticated ? 'text-green-600' : 'text-gray-600'}>
              {isAuthenticated ? '✅ 已登錄' : '❌ 未登錄'}
            </span></div>
            <div>載入中: <span className={isLoading ? 'text-yellow-600' : 'text-gray-600'}>
              {isLoading ? '⏳ 載入中' : '✅ 就緒'}
            </span></div>
            <div>模式: <span className="font-medium">{mode}</span></div>
            <div>訪客模式: <span className={isGuestMode ? 'text-blue-600' : 'text-gray-600'}>
              {isGuestMode ? '👤 訪客' : '👤 會員'}
            </span></div>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold mb-2 text-gray-700">用戶資訊</h3>
          {user ? (
            <div className="space-y-1 text-sm">
              <div>姓名: {user.name || '未設定'}</div>
              <div>信箱: {user.email}</div>
              <div>等級: <span className="font-medium">{user.tier}</span></div>
              <div>分析次數: {membershipStatus.analysisCount}/{membershipStatus.analysisLimit}</div>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">未登錄</div>
          )}
        </div>
      </div>

      {/* 錯誤顯示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-red-800">認證錯誤</h4>
              <p className="text-red-600 text-sm mt-1">{error.message}</p>
              <p className="text-red-500 text-xs mt-1">
                類型: {error.type} | 時間: {error.timestamp.toLocaleTimeString()}
              </p>
            </div>
            <div className="flex space-x-2">
              {hasRecoverableError && (
                <button
                  onClick={handleRetryInit}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                >
                  重試
                </button>
              )}
              <button
                onClick={clearError}
                className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
              >
                清除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 操作按鈕 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {!isAuthenticated ? (
          <button
            onClick={() => setShowLoginForm(!showLoginForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            {showLoginForm ? '取消登錄' : '登錄'}
          </button>
        ) : (
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            登出
          </button>
        )}
        
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
        >
          刷新狀態
        </button>
        
        <button
          onClick={testErrorHandling}
          className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
        >
          測試錯誤
        </button>
        
        <button
          onClick={testFeatureAccess}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
        >
          測試權限
        </button>
        
        {!isGuestMode && (
          <button
            onClick={handleSwitchToGuest}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
          >
            訪客模式
          </button>
        )}
      </div>

      {/* 登錄表單 */}
      {showLoginForm && (
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h3 className="font-semibold mb-3 text-gray-700">登錄表單</h3>
          <div className="space-y-3">
            <input
              type="email"
              placeholder="電子信箱"
              value={loginForm.email}
              onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              placeholder="密碼"
              value={loginForm.password}
              onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="text"
              placeholder="姓名 (選填)"
              value={loginForm.name}
              onChange={(e) => setLoginForm(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex space-x-2">
              <button
                onClick={handleLogin}
                disabled={!loginForm.email || isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                {isLoading ? '登錄中...' : '登錄'}
              </button>
              <button
                onClick={() => setLoginForm({ email: 'test@example.com', password: 'test123', name: '測試用戶' })}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                填入測試數據
              </button>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            <p>測試提示:</p>
            <p>• 使用 error@test.com 測試錯誤處理</p>
            <p>• 使用其他信箱測試正常登錄</p>
          </div>
        </div>
      )}

      {/* 測試結果 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold mb-3 text-gray-700">測試結果 (最近10條)</h3>
        <div className="space-y-1 text-sm font-mono">
          {testResults.length === 0 ? (
            <div className="text-gray-500">暫無測試結果</div>
          ) : (
            testResults.map((result, index) => (
              <div key={index} className="text-gray-700">
                {result}
              </div>
            ))
          )}
        </div>
        <button
          onClick={() => setTestResults([])}
          className="mt-3 px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
        >
          清除結果
        </button>
      </div>
    </div>
  );
};

export default AuthenticationDemo;