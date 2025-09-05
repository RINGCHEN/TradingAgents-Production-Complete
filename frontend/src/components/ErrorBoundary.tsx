/**
 * ErrorBoundary - React錯誤邊界組件
 * 捕獲React渲染錯誤，實施錯誤狀態管理和降級渲染邏輯
 * 建立錯誤恢復和重試機制
 */

import React, { Component, ReactNode, ErrorInfo } from 'react';
import { reportComponentError } from '../utils/ErrorDiagnostics';

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRecovering: boolean;
  fallbackMode: 'minimal' | 'static' | 'offline' | 'none';
}

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackComponent?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo, errorId: string) => void;
  enableRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  enableAutoRecovery?: boolean;
  autoRecoveryDelay?: number;
  fallbackMode?: 'minimal' | 'static' | 'offline';
  componentName?: string;
  enableDegradation?: boolean;
  showErrorDetails?: boolean;
}

export interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  onRetry: () => void;
  onReset: () => void;
  canRetry: boolean;
  fallbackMode: 'minimal' | 'static' | 'offline' | 'none';
  componentName?: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;
  private autoRecoveryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRecovering: false,
      fallbackMode: 'none'
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // 生成唯一的錯誤ID
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId,
      fallbackMode: 'minimal'
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { onError, componentName = 'Unknown' } = this.props;
    const errorId = this.state.errorId || `error-${Date.now()}`;

    // 更新狀態以包含錯誤信息
    this.setState({
      errorInfo,
      error
    });

    // 報告錯誤到診斷系統
    this.reportErrorToDiagnostics(error, errorInfo, errorId);

    // 調用外部錯誤處理器
    if (onError) {
      onError(error, errorInfo, errorId);
    }

    // 記錄詳細錯誤信息
    console.error(`ErrorBoundary caught an error in ${componentName}:`, {
      error,
      errorInfo,
      errorId,
      componentStack: errorInfo.componentStack,
      errorBoundary: this.constructor.name
    });

    // 啟動自動恢復機制
    if (this.props.enableAutoRecovery) {
      this.scheduleAutoRecovery();
    }
  }

  componentWillUnmount() {
    // 清理定時器
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
    if (this.autoRecoveryTimeoutId) {
      clearTimeout(this.autoRecoveryTimeoutId);
    }
  }

  /**
   * 報告錯誤到診斷系統
   */
  private reportErrorToDiagnostics(error: Error, errorInfo: ErrorInfo, errorId: string) {
    const { componentName = 'Unknown' } = this.props;
    
    reportComponentError(
      'render',
      `React Error Boundary caught error in ${componentName}: ${error.message}`,
      {
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack
        },
        errorInfo: {
          componentStack: errorInfo.componentStack
        },
        errorId,
        componentName,
        retryCount: this.state.retryCount,
        timestamp: new Date().toISOString()
      }
    );
  }

  /**
   * 重試渲染
   */
  private handleRetry = () => {
    const { maxRetries = 3, retryDelay = 1000 } = this.props;
    
    if (this.state.retryCount >= maxRetries) {
      console.warn('Maximum retry attempts reached');
      return;
    }

    this.setState({
      isRecovering: true
    });

    // 延遲重試以避免立即失敗
    this.retryTimeoutId = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prevState.retryCount + 1,
        isRecovering: false,
        fallbackMode: 'none'
      }));
    }, retryDelay);
  };

  /**
   * 重置錯誤狀態
   */
  private handleReset = () => {
    // 清理定時器
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
      this.retryTimeoutId = null;
    }
    if (this.autoRecoveryTimeoutId) {
      clearTimeout(this.autoRecoveryTimeoutId);
      this.autoRecoveryTimeoutId = null;
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRecovering: false,
      fallbackMode: 'none'
    });
  };

  /**
   * 安排自動恢復
   */
  private scheduleAutoRecovery() {
    const { autoRecoveryDelay = 5000 } = this.props;
    
    this.autoRecoveryTimeoutId = setTimeout(() => {
      if (this.state.hasError && this.state.retryCount === 0) {
        console.log('Attempting auto-recovery...');
        this.handleRetry();
      }
    }, autoRecoveryDelay);
  }

  /**
   * 確定降級模式
   */
  private determineFallbackMode(): 'minimal' | 'static' | 'offline' | 'none' {
    const { fallbackMode = 'minimal', enableDegradation = true } = this.props;
    
    if (!enableDegradation) {
      return 'none';
    }

    // 根據重試次數決定降級程度
    if (this.state.retryCount >= 2) {
      return 'offline';
    } else if (this.state.retryCount >= 1) {
      return 'static';
    } else {
      return fallbackMode;
    }
  }

  render() {
    const { 
      children, 
      fallbackComponent: FallbackComponent,
      enableRetry = true,
      maxRetries = 3,
      componentName = 'Component'
    } = this.props;

    if (this.state.hasError) {
      const canRetry = enableRetry && this.state.retryCount < maxRetries;
      const currentFallbackMode = this.determineFallbackMode();

      // 如果提供了自定義降級組件，使用它
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            errorId={this.state.errorId}
            retryCount={this.state.retryCount}
            onRetry={this.handleRetry}
            onReset={this.handleReset}
            canRetry={canRetry}
            fallbackMode={currentFallbackMode}
            componentName={componentName}
          />
        );
      }

      // 使用默認降級UI
      return (
        <DefaultErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorId={this.state.errorId}
          retryCount={this.state.retryCount}
          onRetry={this.handleRetry}
          onReset={this.handleReset}
          canRetry={canRetry}
          fallbackMode={currentFallbackMode}
          componentName={componentName}
          isRecovering={this.state.isRecovering}
          showErrorDetails={this.props.showErrorDetails}
        />
      );
    }

    return children;
  }
}

/**
 * 默認錯誤降級組件
 */
interface DefaultErrorFallbackProps extends ErrorFallbackProps {
  isRecovering: boolean;
  showErrorDetails?: boolean;
}

const DefaultErrorFallback: React.FC<DefaultErrorFallbackProps> = ({
  error,
  errorInfo,
  errorId,
  retryCount,
  onRetry,
  onReset,
  canRetry,
  fallbackMode,
  componentName,
  isRecovering,
  showErrorDetails = process.env.NODE_ENV === 'development'
}) => {
  const getFallbackContent = () => {
    switch (fallbackMode) {
      case 'offline':
        return (
          <div className="error-fallback offline-mode">
            <div className="error-icon">📱</div>
            <h3>離線模式</h3>
            <p>系統暫時無法正常運行，已切換到離線模式。</p>
            <p>您可以瀏覽基本功能，或稍後重試。</p>
            <div className="offline-features">
              <ul>
                <li>✓ 查看已緩存的內容</li>
                <li>✓ 基本導航功能</li>
                <li>✗ 實時數據更新</li>
                <li>✗ 互動功能</li>
              </ul>
            </div>
          </div>
        );

      case 'static':
        return (
          <div className="error-fallback static-mode">
            <div className="error-icon">🔧</div>
            <h3>靜態模式</h3>
            <p>部分功能暫時不可用，已切換到靜態模式。</p>
            <p>基本功能仍然可用，動態內容可能無法顯示。</p>
          </div>
        );

      case 'minimal':
      default:
        return (
          <div className="error-fallback minimal-mode">
            <div className="error-icon">⚠️</div>
            <h3>組件載入失敗</h3>
            <p>{componentName} 組件發生錯誤，無法正常顯示。</p>
            {retryCount > 0 && (
              <p className="retry-info">
                已重試 {retryCount} 次
              </p>
            )}
          </div>
        );
    }
  };

  return (
    <div className="error-boundary-container">
      <style jsx>{`
        .error-boundary-container {
          padding: 20px;
          margin: 10px;
          border: 1px solid #e1e5e9;
          border-radius: 8px;
          background-color: #f8f9fa;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .error-fallback {
          text-align: center;
          padding: 20px;
        }

        .error-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .error-fallback h3 {
          color: #495057;
          margin-bottom: 12px;
          font-size: 18px;
        }

        .error-fallback p {
          color: #6c757d;
          margin-bottom: 8px;
          line-height: 1.5;
        }

        .retry-info {
          font-size: 14px;
          color: #868e96;
        }

        .offline-features {
          margin-top: 16px;
          text-align: left;
          display: inline-block;
        }

        .offline-features ul {
          list-style: none;
          padding: 0;
        }

        .offline-features li {
          padding: 4px 0;
          font-size: 14px;
        }

        .error-actions {
          margin-top: 20px;
          display: flex;
          gap: 12px;
          justify-content: center;
          flex-wrap: wrap;
        }

        .error-button {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.2s;
        }

        .retry-button {
          background-color: #007bff;
          color: white;
        }

        .retry-button:hover:not(:disabled) {
          background-color: #0056b3;
        }

        .retry-button:disabled {
          background-color: #6c757d;
          cursor: not-allowed;
        }

        .reset-button {
          background-color: #6c757d;
          color: white;
        }

        .reset-button:hover {
          background-color: #545b62;
        }

        .recovering {
          opacity: 0.7;
        }

        .error-details {
          margin-top: 20px;
          padding: 16px;
          background-color: #f1f3f4;
          border-radius: 4px;
          text-align: left;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          color: #495057;
          max-height: 200px;
          overflow-y: auto;
        }

        .error-details summary {
          cursor: pointer;
          font-weight: bold;
          margin-bottom: 8px;
        }

        .error-id {
          font-size: 12px;
          color: #868e96;
          margin-top: 12px;
        }
      `}</style>

      <div className={isRecovering ? 'recovering' : ''}>
        {getFallbackContent()}

        <div className="error-actions">
          {canRetry && onRetry && (
            <button
              className="error-button retry-button"
              onClick={onRetry}
              disabled={isRecovering}
            >
              {isRecovering ? '恢復中...' : '重試'}
            </button>
          )}
          
          <button
            className="error-button reset-button"
            onClick={onReset}
            disabled={isRecovering}
          >
            重置
          </button>
        </div>

        {showErrorDetails && error && (
          <details className="error-details">
            <summary>錯誤詳情 (開發模式)</summary>
            <div>
              <strong>錯誤:</strong> {error.name}: {error.message}
            </div>
            {error.stack && (
              <div>
                <strong>堆棧:</strong>
                <pre>{error.stack}</pre>
              </div>
            )}
            {errorInfo?.componentStack && (
              <div>
                <strong>組件堆棧:</strong>
                <pre>{errorInfo.componentStack}</pre>
              </div>
            )}
          </details>
        )}

        {errorId && (
          <div className="error-id">
            錯誤ID: {errorId}
          </div>
        )}
      </div>
    </div>
  );
};

export default ErrorBoundary;