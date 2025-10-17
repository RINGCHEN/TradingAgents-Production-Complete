/**
 * 網絡連接失敗降級組件
 * 當 API 連接失敗時提供離線模式和降級功能
 */

import React, { useState, useEffect } from 'react';

interface NetworkFallbackProps {
  children: React.ReactNode;
  onRetry?: () => void;
  retryInterval?: number;
  maxRetries?: number;
  fallbackContent?: React.ReactNode;
}

export const NetworkFallback: React.FC<NetworkFallbackProps> = ({
  children,
  onRetry,
  retryInterval = 5000,
  maxRetries = 10,
  fallbackContent
}): React.ReactElement => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionFailed, setConnectionFailed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastAttempt, setLastAttempt] = useState<Date | null>(null);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setConnectionFailed(false);
      setRetryCount(0);
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      setConnectionFailed(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (connectionFailed && retryCount < maxRetries && isOnline) {
      const timer = setTimeout(() => {
        handleRetryConnection();
      }, retryInterval);

      return () => clearTimeout(timer);
    }
  }, [connectionFailed, retryCount, maxRetries, retryInterval, isOnline]);

  const handleRetryConnection = async () => {
    try {
      setLastAttempt(new Date());
      
      // 測試連接到後端
      const response = await fetch('/health', {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache'
        }
      });

      if (response.ok) {
        setConnectionFailed(false);
        setRetryCount(0);
        if (onRetry) {
          onRetry();
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.warn(`連接重試失敗 (${retryCount + 1}/${maxRetries}):`, error);
      setRetryCount(prev => prev + 1);
      
      if (retryCount + 1 >= maxRetries) {
        console.error('已達到最大重試次數，切換到離線模式');
      }
    }
  };

  const renderOfflineMode = (): React.ReactElement => {
    if (fallbackContent) {
      return <>{fallbackContent}</>;
    }

    return (
      <div className="network-fallback">
        <div className="network-fallback-container">
          <div className="network-status">
            {!isOnline ? (
              <>
                <div className="status-icon offline">📡</div>
                <h3>網絡連接中斷</h3>
                <p>檢測到您的設備已離線，請檢查網絡連接</p>
              </>
            ) : (
              <>
                <div className="status-icon error">⚠️</div>
                <h3>無法連接到服務器</h3>
                <p>服務器暫時無法訪問，正在嘗試重新連接...</p>
              </>
            )}
          </div>

          <div className="connection-info">
            <div className="retry-info">
              <p>重試進度: {retryCount}/{maxRetries}</p>
              {lastAttempt && (
                <p>最後嘗試: {lastAttempt.toLocaleTimeString()}</p>
              )}
            </div>

            <div className="offline-features">
              <h4>離線可用功能:</h4>
              <ul>
                <li>📊 查看本地緩存的數據</li>
                <li>📝 離線編輯內容（將在連接恢復後同步）</li>
                <li>💾 本地數據備份</li>
                <li>🔍 瀏覽歷史記錄</li>
              </ul>
            </div>

            <div className="action-buttons">
              {retryCount < maxRetries && (
                <button 
                  className="retry-button"
                  onClick={handleRetryConnection}
                  disabled={!isOnline}
                >
                  立即重試
                </button>
              )}
              
              <button 
                className="offline-button"
                onClick={() => setConnectionFailed(false)}
              >
                進入離線模式
              </button>
              
              <button 
                className="refresh-button"
                onClick={() => window.location.reload()}
              >
                刷新頁面
              </button>
            </div>
          </div>

          <div className="network-tips">
            <h4>網絡問題排除建議:</h4>
            <ol>
              <li>檢查您的網絡連接是否正常</li>
              <li>確認防火牆沒有阻止應用訪問</li>
              <li>嘗試刷新頁面或重新登錄</li>
              <li>如問題持續，請聯繫技術支援</li>
            </ol>
          </div>
        </div>

        <style jsx>{`
          .network-fallback {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 1rem;
          }

          .network-fallback-container {
            max-width: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
          }

          .network-status {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
          }

          .status-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
          }

          .status-icon.offline {
            animation: pulse 2s infinite;
          }

          .status-icon.error {
            animation: shake 0.5s ease-in-out infinite alternate;
          }

          @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
          }

          @keyframes shake {
            0% { transform: translateX(0); }
            100% { transform: translateX(2px); }
          }

          .network-status h3 {
            margin: 0 0 1rem 0;
            font-size: 1.5rem;
          }

          .network-status p {
            margin: 0;
            opacity: 0.9;
          }

          .connection-info {
            padding: 2rem;
          }

          .retry-info {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            text-align: center;
          }

          .retry-info p {
            margin: 0.25rem 0;
            color: #6c757d;
          }

          .offline-features {
            margin-bottom: 1.5rem;
          }

          .offline-features h4 {
            color: #495057;
            margin-bottom: 1rem;
          }

          .offline-features ul {
            list-style: none;
            padding: 0;
          }

          .offline-features li {
            padding: 0.5rem 0;
            border-bottom: 1px solid #e9ecef;
          }

          .offline-features li:last-child {
            border-bottom: none;
          }

          .action-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 1.5rem;
          }

          .action-buttons button {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
            flex: 1;
            min-width: 120px;
          }

          .retry-button {
            background: #28a745;
            color: white;
          }

          .retry-button:hover:not(:disabled) {
            background: #218838;
          }

          .retry-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
          }

          .offline-button {
            background: #17a2b8;
            color: white;
          }

          .offline-button:hover {
            background: #138496;
          }

          .refresh-button {
            background: #ffc107;
            color: #212529;
          }

          .refresh-button:hover {
            background: #e0a800;
          }

          .network-tips {
            background: #f8f9fa;
            padding: 1.5rem;
            border-top: 1px solid #e9ecef;
          }

          .network-tips h4 {
            color: #495057;
            margin-bottom: 1rem;
          }

          .network-tips ol {
            color: #6c757d;
            padding-left: 1.5rem;
          }

          .network-tips li {
            margin-bottom: 0.5rem;
          }

          @media (max-width: 768px) {
            .network-fallback-container {
              margin: 1rem;
            }

            .network-status,
            .connection-info {
              padding: 1.5rem;
            }

            .action-buttons {
              flex-direction: column;
            }

            .action-buttons button {
              width: 100%;
            }
          }
        `}</style>
      </div>
    );
  };

  // 如果檢測到網絡問題，顯示降級界面
  if (connectionFailed && retryCount >= maxRetries) {
    return renderOfflineMode();
  }

  // 正常渲染子組件
  return <>{children}</>;
};

export default NetworkFallback;