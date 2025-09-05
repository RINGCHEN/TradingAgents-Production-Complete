/**
 * FallbackRenderer - 降級渲染器
 * 根據錯誤嚴重程度和系統狀態提供不同級別的降級渲染
 */

import React, { ReactNode, useMemo } from 'react';
import { useErrorState } from '../contexts/ErrorStateContext';

export interface FallbackRendererProps {
  children: ReactNode;
  componentName: string;
  fallbackMode?: 'auto' | 'minimal' | 'static' | 'offline';
  minimalFallback?: ReactNode;
  staticFallback?: ReactNode;
  offlineFallback?: ReactNode;
  enableGracefulDegradation?: boolean;
  showLoadingState?: boolean;
}

export interface FallbackContentProps {
  mode: 'minimal' | 'static' | 'offline';
  componentName: string;
  errorCount: number;
  onRetry?: () => void;
  onReset?: () => void;
}

const FallbackRenderer: React.FC<FallbackRendererProps> = ({
  children,
  componentName,
  fallbackMode = 'auto',
  minimalFallback,
  staticFallback,
  offlineFallback,
  enableGracefulDegradation = true,
  showLoadingState = true
}) => {
  const { getComponentState, getSystemHealth } = useErrorState();
  const componentState = getComponentState(componentName);
  const systemHealth = getSystemHealth();

  // 確定當前應該使用的降級模式
  const currentFallbackMode = useMemo(() => {
    if (fallbackMode !== 'auto') {
      return fallbackMode;
    }

    // 自動模式：根據組件狀態和系統健康狀況決定
    if (componentState.hasError) {
      return componentState.fallbackMode;
    }

    // 根據系統健康狀況決定預防性降級
    if (enableGracefulDegradation) {
      switch (systemHealth) {
        case 'critical':
          return 'static';
        case 'degraded':
          return 'minimal';
        default:
          return 'none';
      }
    }

    return 'none';
  }, [fallbackMode, componentState, systemHealth, enableGracefulDegradation]);

  // 如果組件正在恢復中，顯示載入狀態
  if (componentState.isRecovering && showLoadingState) {
    return <RecoveryLoadingState componentName={componentName} />;
  }

  // 根據降級模式渲染內容
  switch (currentFallbackMode) {
    case 'minimal':
      return minimalFallback ? (
        <>{minimalFallback}</>
      ) : (
        <MinimalFallback 
          componentName={componentName}
          errorCount={componentState.errorCount}
        />
      );

    case 'static':
      return staticFallback ? (
        <>{staticFallback}</>
      ) : (
        <StaticFallback 
          componentName={componentName}
          errorCount={componentState.errorCount}
        />
      );

    case 'offline':
      return offlineFallback ? (
        <>{offlineFallback}</>
      ) : (
        <OfflineFallback 
          componentName={componentName}
          errorCount={componentState.errorCount}
        />
      );

    case 'none':
    default:
      return <>{children}</>;
  }
};

/**
 * 恢復載入狀態組件
 */
const RecoveryLoadingState: React.FC<{ componentName: string }> = ({ componentName }) => (
  <div className="recovery-loading">
    <style jsx>{`
      .recovery-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        margin: 10px;
      }

      .loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid #e9ecef;
        border-top: 3px solid #007bff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 12px;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .loading-text {
        color: #6c757d;
        font-size: 14px;
        text-align: center;
      }
    `}</style>
    
    <div className="loading-spinner"></div>
    <div className="loading-text">
      正在恢復 {componentName}...
    </div>
  </div>
);

/**
 * 最小降級組件
 */
const MinimalFallback: React.FC<FallbackContentProps> = ({ 
  componentName, 
  errorCount,
  onRetry,
  onReset 
}) => (
  <div className="minimal-fallback">
    <style jsx>{`
      .minimal-fallback {
        padding: 16px;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        margin: 8px;
        text-align: center;
      }

      .fallback-icon {
        font-size: 24px;
        margin-bottom: 8px;
      }

      .fallback-title {
        font-size: 16px;
        font-weight: 600;
        color: #856404;
        margin-bottom: 4px;
      }

      .fallback-message {
        font-size: 14px;
        color: #856404;
        margin-bottom: 12px;
      }

      .fallback-actions {
        display: flex;
        gap: 8px;
        justify-content: center;
      }

      .fallback-button {
        padding: 6px 12px;
        border: none;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        transition: background-color 0.2s;
      }

      .retry-button {
        background-color: #ffc107;
        color: #212529;
      }

      .retry-button:hover {
        background-color: #e0a800;
      }
    `}</style>

    <div className="fallback-icon">⚠️</div>
    <div className="fallback-title">功能暫時不可用</div>
    <div className="fallback-message">
      {componentName} 遇到問題，已切換到簡化模式
      {errorCount > 1 && ` (錯誤次數: ${errorCount})`}
    </div>
    
    {onRetry && (
      <div className="fallback-actions">
        <button className="fallback-button retry-button" onClick={onRetry}>
          重試
        </button>
      </div>
    )}
  </div>
);

/**
 * 靜態降級組件
 */
const StaticFallback: React.FC<FallbackContentProps> = ({ 
  componentName, 
  errorCount,
  onReset 
}) => (
  <div className="static-fallback">
    <style jsx>{`
      .static-fallback {
        padding: 20px;
        background-color: #e2e3e5;
        border: 1px solid #d6d8db;
        border-radius: 8px;
        margin: 10px;
        text-align: center;
      }

      .fallback-icon {
        font-size: 32px;
        margin-bottom: 12px;
      }

      .fallback-title {
        font-size: 18px;
        font-weight: 600;
        color: #495057;
        margin-bottom: 8px;
      }

      .fallback-message {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 16px;
        line-height: 1.5;
      }

      .static-features {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 16px;
      }

      .features-title {
        font-size: 14px;
        font-weight: 600;
        color: #495057;
        margin-bottom: 8px;
      }

      .features-list {
        font-size: 12px;
        color: #6c757d;
        text-align: left;
      }

      .features-list ul {
        margin: 0;
        padding-left: 20px;
      }

      .features-list li {
        margin-bottom: 4px;
      }

      .reset-button {
        padding: 8px 16px;
        background-color: #6c757d;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s;
      }

      .reset-button:hover {
        background-color: #545b62;
      }
    `}</style>

    <div className="fallback-icon">🔧</div>
    <div className="fallback-title">靜態模式</div>
    <div className="fallback-message">
      {componentName} 已切換到靜態模式以確保基本功能可用。
      動態功能暫時不可用，但您仍可以瀏覽基本內容。
    </div>

    <div className="static-features">
      <div className="features-title">可用功能:</div>
      <div className="features-list">
        <ul>
          <li>✓ 基本內容瀏覽</li>
          <li>✓ 靜態信息顯示</li>
          <li>✗ 實時數據更新</li>
          <li>✗ 互動功能</li>
        </ul>
      </div>
    </div>

    {onReset && (
      <button className="reset-button" onClick={onReset}>
        嘗試恢復完整功能
      </button>
    )}
  </div>
);

/**
 * 離線降級組件
 */
const OfflineFallback: React.FC<FallbackContentProps> = ({ 
  componentName, 
  errorCount,
  onReset 
}) => (
  <div className="offline-fallback">
    <style jsx>{`
      .offline-fallback {
        padding: 24px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        margin: 10px;
        text-align: center;
      }

      .fallback-icon {
        font-size: 48px;
        margin-bottom: 16px;
      }

      .fallback-title {
        font-size: 20px;
        font-weight: 600;
        color: #721c24;
        margin-bottom: 12px;
      }

      .fallback-message {
        font-size: 16px;
        color: #721c24;
        margin-bottom: 20px;
        line-height: 1.5;
      }

      .offline-info {
        background-color: #f1b0b7;
        padding: 16px;
        border-radius: 6px;
        margin-bottom: 20px;
      }

      .info-title {
        font-size: 14px;
        font-weight: 600;
        color: #721c24;
        margin-bottom: 8px;
      }

      .info-text {
        font-size: 13px;
        color: #721c24;
        line-height: 1.4;
      }

      .offline-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-items: center;
      }

      .action-button {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s;
        min-width: 120px;
      }

      .primary-button {
        background-color: #dc3545;
        color: white;
      }

      .primary-button:hover {
        background-color: #c82333;
      }

      .secondary-button {
        background-color: #6c757d;
        color: white;
      }

      .secondary-button:hover {
        background-color: #545b62;
      }
    `}</style>

    <div className="fallback-icon">📱</div>
    <div className="fallback-title">離線模式</div>
    <div className="fallback-message">
      {componentName} 無法正常運行，已切換到離線模式。
      系統將提供基本的離線功能。
    </div>

    <div className="offline-info">
      <div className="info-title">離線模式說明:</div>
      <div className="info-text">
        在離線模式下，您可以瀏覽已緩存的內容和使用基本功能。
        實時數據和互動功能將不可用，直到系統恢復正常。
      </div>
    </div>

    <div className="offline-actions">
      {onReset && (
        <button className="action-button primary-button" onClick={onReset}>
          嘗試重新連接
        </button>
      )}
      <button 
        className="action-button secondary-button"
        onClick={() => window.location.reload()}
      >
        重新載入頁面
      </button>
    </div>
  </div>
);

/**
 * 智能降級包裝器 - 自動根據錯誤狀態選擇降級策略
 */
export const SmartFallbackWrapper: React.FC<{
  children: ReactNode;
  componentName: string;
  customFallbacks?: {
    minimal?: ReactNode;
    static?: ReactNode;
    offline?: ReactNode;
  };
}> = ({ children, componentName, customFallbacks = {} }) => {
  return (
    <FallbackRenderer
      componentName={componentName}
      fallbackMode="auto"
      enableGracefulDegradation={true}
      minimalFallback={customFallbacks.minimal}
      staticFallback={customFallbacks.static}
      offlineFallback={customFallbacks.offline}
    >
      {children}
    </FallbackRenderer>
  );
};

export default FallbackRenderer;