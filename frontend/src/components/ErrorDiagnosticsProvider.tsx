/**
 * ErrorDiagnosticsProvider - 錯誤診斷提供者組件
 * 整合ErrorDiagnostics系統到React應用中，提供自動錯誤檢測和報告
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { 
  ErrorDiagnostics, 
  DiagnosticReport, 
  DiagnosticResult,
  errorDiagnostics,
  diagnoseHomepageErrors,
  reportComponentError
} from '../utils/ErrorDiagnostics';

interface ErrorDiagnosticsContextType {
  diagnosticReport: DiagnosticReport | null;
  isHealthy: boolean;
  criticalErrors: DiagnosticResult[];
  refreshDiagnostics: () => void;
  reportError: (category: DiagnosticResult['category'], message: string, details?: any) => void;
  clearErrors: () => void;
}

const ErrorDiagnosticsContext = createContext<ErrorDiagnosticsContextType | undefined>(undefined);

interface ErrorDiagnosticsProviderProps {
  children: ReactNode;
  enableAutoRefresh?: boolean;
  refreshInterval?: number;
  showDebugInfo?: boolean;
}

export const ErrorDiagnosticsProvider: React.FC<ErrorDiagnosticsProviderProps> = ({
  children,
  enableAutoRefresh = true,
  refreshInterval = 30000, // 30秒
  showDebugInfo = process.env.NODE_ENV === 'development'
}) => {
  const [diagnosticReport, setDiagnosticReport] = useState<DiagnosticReport | null>(null);
  const [isHealthy, setIsHealthy] = useState(true);
  const [criticalErrors, setCriticalErrors] = useState<DiagnosticResult[]>([]);

  // 刷新診斷報告
  const refreshDiagnostics = () => {
    try {
      const report = diagnoseHomepageErrors();
      setDiagnosticReport(report);
      setIsHealthy(report.overallHealth === 'healthy');
      setCriticalErrors(report.issues.filter(issue => issue.severity === 'critical'));
      
      if (showDebugInfo) {
        console.log('ErrorDiagnostics Report:', report);
      }
    } catch (error) {
      console.error('Failed to generate diagnostic report:', error);
      reportComponentError('render', 'Failed to generate diagnostic report', { error });
    }
  };

  // 報告錯誤
  const reportError = (category: DiagnosticResult['category'], message: string, details?: any) => {
    reportComponentError(category, message, details);
    // 立即刷新診斷以反映新錯誤
    setTimeout(refreshDiagnostics, 100);
  };

  // 清除錯誤
  const clearErrors = () => {
    errorDiagnostics.clearErrors();
    refreshDiagnostics();
  };

  // 初始化和定期刷新
  useEffect(() => {
    // 初始診斷
    refreshDiagnostics();

    // 設置定期刷新
    let intervalId: NodeJS.Timeout | null = null;
    if (enableAutoRefresh) {
      intervalId = setInterval(refreshDiagnostics, refreshInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [enableAutoRefresh, refreshInterval]);

  // 監聽頁面可見性變化，當頁面重新可見時刷新診斷
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        refreshDiagnostics();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const contextValue: ErrorDiagnosticsContextType = {
    diagnosticReport,
    isHealthy,
    criticalErrors,
    refreshDiagnostics,
    reportError,
    clearErrors
  };

  return (
    <ErrorDiagnosticsContext.Provider value={contextValue}>
      {children}
      {showDebugInfo && <ErrorDiagnosticsDebugPanel />}
    </ErrorDiagnosticsContext.Provider>
  );
};

// Debug面板組件（僅在開發環境顯示）
const ErrorDiagnosticsDebugPanel: React.FC = () => {
  const context = useContext(ErrorDiagnosticsContext);
  const [isExpanded, setIsExpanded] = useState(false);

  if (!context || !context.diagnosticReport) {
    return null;
  }

  const { diagnosticReport, isHealthy, criticalErrors } = context;

  const getHealthColor = () => {
    switch (diagnosticReport.overallHealth) {
      case 'healthy': return '#28a745';
      case 'degraded': return '#ffc107';
      case 'critical': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      backgroundColor: 'white',
      border: `2px solid ${getHealthColor()}`,
      borderRadius: '8px',
      padding: '10px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      zIndex: 9999,
      maxWidth: '400px',
      fontSize: '12px'
    }}>
      <div 
        style={{ 
          cursor: 'pointer', 
          fontWeight: 'bold',
          color: getHealthColor(),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span>🔍 錯誤診斷 ({diagnosticReport.overallHealth})</span>
        <span>{isExpanded ? '▼' : '▶'}</span>
      </div>
      
      {isExpanded && (
        <div style={{ marginTop: '10px' }}>
          <div><strong>總體健康:</strong> {diagnosticReport.overallHealth}</div>
          <div><strong>問題數量:</strong> {diagnosticReport.issues.length}</div>
          <div><strong>嚴重問題:</strong> {criticalErrors.length}</div>
          <div><strong>最後更新:</strong> {diagnosticReport.timestamp.toLocaleTimeString()}</div>
          
          {diagnosticReport.issues.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <strong>最近問題:</strong>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {diagnosticReport.issues.slice(0, 5).map((issue, index) => (
                  <div key={index} style={{ 
                    margin: '5px 0', 
                    padding: '5px', 
                    backgroundColor: '#f8f9fa',
                    borderRadius: '4px',
                    borderLeft: `3px solid ${
                      issue.severity === 'critical' ? '#dc3545' :
                      issue.severity === 'high' ? '#fd7e14' :
                      issue.severity === 'medium' ? '#ffc107' : '#28a745'
                    }`
                  }}>
                    <div><strong>{issue.category}</strong> ({issue.severity})</div>
                    <div>{issue.message}</div>
                    {issue.solution && (
                      <div style={{ fontSize: '11px', color: '#6c757d' }}>
                        💡 {issue.solution}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {diagnosticReport.recommendations.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <strong>建議:</strong>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                {diagnosticReport.recommendations.slice(0, 3).map((rec, index) => (
                  <li key={index} style={{ fontSize: '11px' }}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Hook for using error diagnostics
export const useErrorDiagnostics = () => {
  const context = useContext(ErrorDiagnosticsContext);
  if (context === undefined) {
    throw new Error('useErrorDiagnostics must be used within an ErrorDiagnosticsProvider');
  }
  return context;
};

// Higher-order component for automatic error reporting
export const withErrorDiagnostics = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName?: string
) => {
  return React.forwardRef<any, P>((props, ref) => {
    const { reportError } = useErrorDiagnostics();

    // 創建錯誤報告函數
    const reportComponentError = (error: Error, errorInfo?: any) => {
      reportError('render', `Error in ${componentName || WrappedComponent.name}: ${error.message}`, {
        error: error.message,
        stack: error.stack,
        errorInfo,
        componentName: componentName || WrappedComponent.name
      });
    };

    // 使用錯誤邊界包裝組件
    return (
      <ErrorBoundaryWrapper onError={reportComponentError}>
        <WrappedComponent {...props} ref={ref} />
      </ErrorBoundaryWrapper>
    );
  });
};

// 錯誤邊界包裝器
interface ErrorBoundaryWrapperProps {
  children: ReactNode;
  onError: (error: Error, errorInfo: any) => void;
}

interface ErrorBoundaryWrapperState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundaryWrapper extends React.Component<ErrorBoundaryWrapperProps, ErrorBoundaryWrapperState> {
  constructor(props: ErrorBoundaryWrapperProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryWrapperState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          border: '1px solid #dc3545', 
          borderRadius: '4px',
          backgroundColor: '#f8d7da',
          color: '#721c24'
        }}>
          <h4>組件渲染錯誤</h4>
          <p>此組件發生錯誤，已自動報告給診斷系統。</p>
          <button 
            onClick={() => this.setState({ hasError: false })}
            style={{
              padding: '5px 10px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            重試
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorDiagnosticsProvider;