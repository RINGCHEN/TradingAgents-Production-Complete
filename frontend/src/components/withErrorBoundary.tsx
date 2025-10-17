/**
 * withErrorBoundary - 高階組件(HOC)
 * 自動為組件添加錯誤邊界保護，提供錯誤恢復和降級功能
 */

import React, { ComponentType, forwardRef, Ref } from 'react';
import ErrorBoundary, { ErrorBoundaryProps, ErrorFallbackProps } from './ErrorBoundary';
import { attemptErrorRecovery, getRecommendedFallbackMode } from '../utils/ErrorRecoveryManager';

export interface WithErrorBoundaryOptions {
  fallbackComponent?: ComponentType<ErrorFallbackProps>;
  enableRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  enableAutoRecovery?: boolean;
  autoRecoveryDelay?: number;
  fallbackMode?: 'minimal' | 'static' | 'offline';
  enableDegradation?: boolean;
  showErrorDetails?: boolean;
  onError?: (error: Error, errorInfo: React.ErrorInfo, errorId: string) => void;
}

/**
 * 為組件添加錯誤邊界保護的高階組件
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
) {
  const {
    fallbackComponent,
    enableRetry = true,
    maxRetries = 3,
    retryDelay = 1000,
    enableAutoRecovery = true,
    autoRecoveryDelay = 5000,
    fallbackMode = 'minimal',
    enableDegradation = true,
    showErrorDetails = process.env.NODE_ENV === 'development',
    onError
  } = options;

  const componentName = WrappedComponent.displayName || WrappedComponent.name || 'Component';

  const WrappedWithErrorBoundary = forwardRef<any, P>((props, ref: Ref<any>) => {
    const handleError = async (error: Error, errorInfo: React.ErrorInfo, errorId: string) => {
      // 調用外部錯誤處理器
      if (onError) {
        onError(error, errorInfo, errorId);
      }

      // 嘗試自動恢復
      if (enableAutoRecovery) {
        try {
          const recoveryResult = await attemptErrorRecovery(error, componentName);
          console.log(`Recovery result for ${componentName}:`, recoveryResult);
        } catch (recoveryError) {
          console.error(`Recovery failed for ${componentName}:`, recoveryError);
        }
      }
    };

    const recommendedMode = getRecommendedFallbackMode(componentName);
    const validFallbackMode = recommendedMode !== 'none' ? recommendedMode : fallbackMode;

    const errorBoundaryProps: ErrorBoundaryProps = {
      fallbackComponent,
      onError: handleError,
      enableRetry,
      maxRetries,
      retryDelay,
      enableAutoRecovery,
      autoRecoveryDelay,
      fallbackMode: validFallbackMode,
      componentName,
      enableDegradation,
      showErrorDetails
    };

    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <WrappedComponent {...(props as any)} ref={ref} />
      </ErrorBoundary>
    );
  });

  WrappedWithErrorBoundary.displayName = `withErrorBoundary(${componentName})`;

  return WrappedWithErrorBoundary;
}

/**
 * 為頁面組件添加錯誤邊界的專用HOC
 */
export function withPageErrorBoundary<P extends object>(
  PageComponent: ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
) {
  return withErrorBoundary(PageComponent, {
    enableRetry: true,
    maxRetries: 2,
    enableAutoRecovery: true,
    fallbackMode: 'static',
    enableDegradation: true,
    ...options
  });
}

/**
 * 為關鍵組件添加錯誤邊界的專用HOC
 */
export function withCriticalErrorBoundary<P extends object>(
  CriticalComponent: ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
) {
  return withErrorBoundary(CriticalComponent, {
    enableRetry: true,
    maxRetries: 5,
    retryDelay: 2000,
    enableAutoRecovery: true,
    autoRecoveryDelay: 3000,
    fallbackMode: 'minimal',
    enableDegradation: true,
    ...options
  });
}

/**
 * 為API相關組件添加錯誤邊界的專用HOC
 */
export function withApiErrorBoundary<P extends object>(
  ApiComponent: ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
) {
  return withErrorBoundary(ApiComponent, {
    enableRetry: true,
    maxRetries: 3,
    retryDelay: 1500,
    enableAutoRecovery: true,
    fallbackMode: 'static',
    enableDegradation: true,
    ...options
  });
}

/**
 * 錯誤邊界裝飾器 (實驗性功能)
 */
export function ErrorBoundaryDecorator(options: WithErrorBoundaryOptions = {}) {
  return function <P extends object>(target: ComponentType<P>) {
    return withErrorBoundary(target, options);
  };
}

/**
 * React Hook - 使用錯誤邊界狀態
 */
export function useErrorBoundaryState() {
  const [hasError, setHasError] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);
  const [retryCount, setRetryCount] = React.useState(0);

  const resetError = React.useCallback(() => {
    setHasError(false);
    setError(null);
    setRetryCount(0);
  }, []);

  const captureError = React.useCallback((error: Error) => {
    setHasError(true);
    setError(error);
    setRetryCount(prev => prev + 1);
  }, []);

  return {
    hasError,
    error,
    retryCount,
    resetError,
    captureError
  };
}

/**
 * React Hook - 錯誤恢復
 */
export function useErrorRecovery(componentName: string) {
  const [isRecovering, setIsRecovering] = React.useState(false);
  const [recoveryResult, setRecoveryResult] = React.useState<any>(null);

  const recover = React.useCallback(async (error: Error, retryAttempts: number = 0) => {
    setIsRecovering(true);
    try {
      const result = await attemptErrorRecovery(error, componentName, retryAttempts);
      setRecoveryResult(result);
      return result;
    } catch (recoveryError) {
      console.error('Recovery failed:', recoveryError);
      return {
        success: false,
        strategy: 'error',
        message: 'Recovery failed',
        shouldRetry: false
      };
    } finally {
      setIsRecovering(false);
    }
  }, [componentName]);

  return {
    isRecovering,
    recoveryResult,
    recover
  };
}

export default withErrorBoundary;