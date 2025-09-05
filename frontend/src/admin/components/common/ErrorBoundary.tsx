/**
 * 錯誤邊界組件 - 全局錯誤處理和降級策略
 * 提供生產環境錯誤恢復和用戶友好的錯誤顯示
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;
  
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    retryCount: 0
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
      retryCount: 0
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary 捕獲錯誤:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // 發送錯誤報告到監控系統
    this.reportError(error, errorInfo);
    
    // 調用外部錯誤處理回調
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    try {
      // 錯誤報告數據
      const errorReport = {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        componentStack: errorInfo.componentStack,
        userId: localStorage.getItem('admin_user') ? JSON.parse(localStorage.getItem('admin_user')!).id : 'anonymous'
      };

      // 發送到後端錯誤追蹤服務
      fetch('/admin/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        },
        body: JSON.stringify(errorReport)
      }).catch(reportErr => {
        console.warn('無法發送錯誤報告:', reportErr);
      });

      // 本地儲存錯誤信息供調試使用
      const localErrors = JSON.parse(localStorage.getItem('admin_errors') || '[]');
      localErrors.push(errorReport);
      
      // 只保留最近50個錯誤
      if (localErrors.length > 50) {
        localErrors.splice(0, localErrors.length - 50);
      }
      
      localStorage.setItem('admin_errors', JSON.stringify(localErrors));
    } catch (reportError) {
      console.error('錯誤報告失敗:', reportError);
    }
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    } else {
      // 達到最大重試次數，建議刷新頁面
      if (window.confirm('系統遇到持續錯誤，是否重新載入頁面？')) {
        window.location.reload();
      }
    }
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      // 自定義降級UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默認錯誤UI
      return (
        <div className="error-boundary">
          <div className="error-boundary-container">
            <div className="error-boundary-icon">⚠️</div>
            <h2 className="error-boundary-title">系統發生錯誤</h2>
            <p className="error-boundary-message">
              抱歉，管理系統遇到了意外錯誤。我們已自動記錄此問題。
            </p>
            
            <div className="error-boundary-details">
              <details>
                <summary>技術詳情 (點擊展開)</summary>
                <div className="error-details">
                  <p><strong>錯誤訊息:</strong> {this.state.error?.message}</p>
                  <p><strong>發生時間:</strong> {new Date().toLocaleString()}</p>
                  <p><strong>重試次數:</strong> {this.state.retryCount}/{this.maxRetries}</p>
                  {this.state.error?.stack && (
                    <pre className="error-stack">
                      {this.state.error.stack}
                    </pre>
                  )}
                </div>
              </details>
            </div>

            <div className="error-boundary-actions">
              {this.state.retryCount < this.maxRetries && (
                <button 
                  className="error-action-button retry"
                  onClick={this.handleRetry}
                >
                  重試 ({this.maxRetries - this.state.retryCount} 次剩餘)
                </button>
              )}
              
              <button 
                className="error-action-button reload"
                onClick={this.handleReload}
              >
                重新載入頁面
              </button>
              
              <button 
                className="error-action-button home"
                onClick={() => window.location.href = '/'}
              >
                返回首頁
              </button>
            </div>

            <div className="error-boundary-support">
              <p>如果問題持續存在，請聯繫技術支援：</p>
              <p>📧 support@03king.com | 📞 客服專線</p>
            </div>
          </div>

          <style jsx>{`
            .error-boundary {
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            .error-boundary-container {
              max-width: 600px;
              padding: 2rem;
              background: white;
              border-radius: 12px;
              box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
              text-align: center;
            }

            .error-boundary-icon {
              font-size: 4rem;
              margin-bottom: 1rem;
            }

            .error-boundary-title {
              color: #333;
              margin-bottom: 1rem;
              font-size: 1.8rem;
              font-weight: 600;
            }

            .error-boundary-message {
              color: #666;
              margin-bottom: 2rem;
              line-height: 1.6;
            }

            .error-boundary-details {
              margin: 1.5rem 0;
              text-align: left;
            }

            .error-boundary-details summary {
              cursor: pointer;
              color: #007bff;
              margin-bottom: 1rem;
            }

            .error-details {
              background: #f8f9fa;
              padding: 1rem;
              border-radius: 6px;
              margin-top: 1rem;
            }

            .error-details p {
              margin: 0.5rem 0;
              font-size: 0.9rem;
            }

            .error-stack {
              background: #e9ecef;
              padding: 1rem;
              border-radius: 4px;
              overflow-x: auto;
              font-size: 0.8rem;
              margin-top: 1rem;
            }

            .error-boundary-actions {
              display: flex;
              gap: 1rem;
              justify-content: center;
              flex-wrap: wrap;
              margin: 2rem 0;
            }

            .error-action-button {
              padding: 0.75rem 1.5rem;
              border: none;
              border-radius: 6px;
              cursor: pointer;
              font-weight: 500;
              transition: all 0.2s;
            }

            .error-action-button.retry {
              background: #28a745;
              color: white;
            }

            .error-action-button.retry:hover {
              background: #218838;
            }

            .error-action-button.reload {
              background: #007bff;
              color: white;
            }

            .error-action-button.reload:hover {
              background: #0056b3;
            }

            .error-action-button.home {
              background: #6c757d;
              color: white;
            }

            .error-action-button.home:hover {
              background: #545b62;
            }

            .error-boundary-support {
              margin-top: 2rem;
              padding-top: 1.5rem;
              border-top: 1px solid #dee2e6;
              color: #6c757d;
              font-size: 0.9rem;
            }

            @media (max-width: 768px) {
              .error-boundary-container {
                margin: 1rem;
                padding: 1.5rem;
              }

              .error-boundary-actions {
                flex-direction: column;
              }

              .error-action-button {
                width: 100%;
              }
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;