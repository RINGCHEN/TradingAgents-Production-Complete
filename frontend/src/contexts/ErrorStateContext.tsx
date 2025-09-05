/**
 * ErrorStateContext - 錯誤狀態管理上下文
 * 提供全局錯誤狀態管理和降級渲染邏輯
 */

import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import { errorRecoveryManager } from '../utils/ErrorRecoveryManager';

export interface ErrorState {
  globalErrors: ComponentError[];
  componentStates: Record<string, ComponentErrorState>;
  systemHealth: 'healthy' | 'degraded' | 'critical';
  fallbackMode: 'none' | 'minimal' | 'static' | 'offline';
  isRecovering: boolean;
  lastRecoveryAttempt: Date | null;
}

export interface ComponentError {
  id: string;
  componentName: string;
  error: Error;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recovered: boolean;
  retryCount: number;
}

export interface ComponentErrorState {
  hasError: boolean;
  errorCount: number;
  lastError: Error | null;
  lastErrorTime: Date | null;
  retryCount: number;
  fallbackMode: 'none' | 'minimal' | 'static' | 'offline';
  isRecovering: boolean;
}

type ErrorAction =
  | { type: 'ADD_ERROR'; payload: { componentName: string; error: Error; severity?: 'low' | 'medium' | 'high' | 'critical' } }
  | { type: 'REMOVE_ERROR'; payload: { errorId: string } }
  | { type: 'CLEAR_COMPONENT_ERRORS'; payload: { componentName: string } }
  | { type: 'CLEAR_ALL_ERRORS' }
  | { type: 'SET_COMPONENT_STATE'; payload: { componentName: string; state: Partial<ComponentErrorState> } }
  | { type: 'SET_RECOVERY_STATE'; payload: { isRecovering: boolean } }
  | { type: 'SET_FALLBACK_MODE'; payload: { mode: 'none' | 'minimal' | 'static' | 'offline' } }
  | { type: 'UPDATE_SYSTEM_HEALTH' };

const initialState: ErrorState = {
  globalErrors: [],
  componentStates: {},
  systemHealth: 'healthy',
  fallbackMode: 'none',
  isRecovering: false,
  lastRecoveryAttempt: null
};

function errorStateReducer(state: ErrorState, action: ErrorAction): ErrorState {
  switch (action.type) {
    case 'ADD_ERROR': {
      const { componentName, error, severity = 'medium' } = action.payload;
      const errorId = `${componentName}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      const newError: ComponentError = {
        id: errorId,
        componentName,
        error,
        timestamp: new Date(),
        severity,
        recovered: false,
        retryCount: 0
      };

      const currentComponentState = state.componentStates[componentName] || {
        hasError: false,
        errorCount: 0,
        lastError: null,
        lastErrorTime: null,
        retryCount: 0,
        fallbackMode: 'none',
        isRecovering: false
      };

      const updatedComponentState: ComponentErrorState = {
        ...currentComponentState,
        hasError: true,
        errorCount: currentComponentState.errorCount + 1,
        lastError: error,
        lastErrorTime: new Date(),
        fallbackMode: determineFallbackMode(currentComponentState.errorCount + 1)
      };

      return {
        ...state,
        globalErrors: [...state.globalErrors, newError].slice(-50), // 保持最近50個錯誤
        componentStates: {
          ...state.componentStates,
          [componentName]: updatedComponentState
        }
      };
    }

    case 'REMOVE_ERROR': {
      const { errorId } = action.payload;
      return {
        ...state,
        globalErrors: state.globalErrors.filter(error => error.id !== errorId)
      };
    }

    case 'CLEAR_COMPONENT_ERRORS': {
      const { componentName } = action.payload;
      return {
        ...state,
        globalErrors: state.globalErrors.filter(error => error.componentName !== componentName),
        componentStates: {
          ...state.componentStates,
          [componentName]: {
            hasError: false,
            errorCount: 0,
            lastError: null,
            lastErrorTime: null,
            retryCount: 0,
            fallbackMode: 'none',
            isRecovering: false
          }
        }
      };
    }

    case 'CLEAR_ALL_ERRORS': {
      return {
        ...state,
        globalErrors: [],
        componentStates: {}
      };
    }

    case 'SET_COMPONENT_STATE': {
      const { componentName, state: componentState } = action.payload;
      const currentState = state.componentStates[componentName] || {
        hasError: false,
        errorCount: 0,
        lastError: null,
        lastErrorTime: null,
        retryCount: 0,
        fallbackMode: 'none',
        isRecovering: false
      };

      return {
        ...state,
        componentStates: {
          ...state.componentStates,
          [componentName]: {
            ...currentState,
            ...componentState
          }
        }
      };
    }

    case 'SET_RECOVERY_STATE': {
      return {
        ...state,
        isRecovering: action.payload.isRecovering,
        lastRecoveryAttempt: action.payload.isRecovering ? new Date() : state.lastRecoveryAttempt
      };
    }

    case 'SET_FALLBACK_MODE': {
      return {
        ...state,
        fallbackMode: action.payload.mode
      };
    }

    case 'UPDATE_SYSTEM_HEALTH': {
      const criticalErrors = state.globalErrors.filter(error => error.severity === 'critical').length;
      const highErrors = state.globalErrors.filter(error => error.severity === 'high').length;
      const totalErrors = state.globalErrors.length;

      let systemHealth: 'healthy' | 'degraded' | 'critical' = 'healthy';
      
      if (criticalErrors > 0 || totalErrors > 10) {
        systemHealth = 'critical';
      } else if (highErrors > 2 || totalErrors > 5) {
        systemHealth = 'degraded';
      }

      return {
        ...state,
        systemHealth
      };
    }

    default:
      return state;
  }
}

function determineFallbackMode(errorCount: number): 'none' | 'minimal' | 'static' | 'offline' {
  if (errorCount >= 5) {
    return 'offline';
  } else if (errorCount >= 3) {
    return 'static';
  } else if (errorCount >= 1) {
    return 'minimal';
  } else {
    return 'none';
  }
}

interface ErrorStateContextType {
  state: ErrorState;
  addError: (componentName: string, error: Error, severity?: 'low' | 'medium' | 'high' | 'critical') => void;
  removeError: (errorId: string) => void;
  clearComponentErrors: (componentName: string) => void;
  clearAllErrors: () => void;
  setComponentState: (componentName: string, state: Partial<ComponentErrorState>) => void;
  setRecoveryState: (isRecovering: boolean) => void;
  setFallbackMode: (mode: 'none' | 'minimal' | 'static' | 'offline') => void;
  getComponentState: (componentName: string) => ComponentErrorState;
  isComponentInError: (componentName: string) => boolean;
  getSystemHealth: () => 'healthy' | 'degraded' | 'critical';
  attemptRecovery: (componentName: string, error: Error) => Promise<void>;
}

const ErrorStateContext = createContext<ErrorStateContextType | undefined>(undefined);

interface ErrorStateProviderProps {
  children: ReactNode;
  enableAutoRecovery?: boolean;
  maxGlobalErrors?: number;
}

export const ErrorStateProvider: React.FC<ErrorStateProviderProps> = ({
  children,
  enableAutoRecovery = true,
  maxGlobalErrors = 50
}) => {
  const [state, dispatch] = useReducer(errorStateReducer, initialState);

  // 自動更新系統健康狀態
  useEffect(() => {
    dispatch({ type: 'UPDATE_SYSTEM_HEALTH' });
  }, [state.globalErrors]);

  // 自動清理過期錯誤
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      const now = Date.now();
      const expiredErrors = state.globalErrors.filter(error => 
        now - error.timestamp.getTime() > 300000 // 5分鐘
      );

      expiredErrors.forEach(error => {
        dispatch({ type: 'REMOVE_ERROR', payload: { errorId: error.id } });
      });
    }, 60000); // 每分鐘檢查一次

    return () => clearInterval(cleanupInterval);
  }, [state.globalErrors]);

  const addError = (componentName: string, error: Error, severity: 'low' | 'medium' | 'high' | 'critical' = 'medium') => {
    dispatch({ type: 'ADD_ERROR', payload: { componentName, error, severity } });
  };

  const removeError = (errorId: string) => {
    dispatch({ type: 'REMOVE_ERROR', payload: { errorId } });
  };

  const clearComponentErrors = (componentName: string) => {
    dispatch({ type: 'CLEAR_COMPONENT_ERRORS', payload: { componentName } });
  };

  const clearAllErrors = () => {
    dispatch({ type: 'CLEAR_ALL_ERRORS' });
  };

  const setComponentState = (componentName: string, componentState: Partial<ComponentErrorState>) => {
    dispatch({ type: 'SET_COMPONENT_STATE', payload: { componentName, state: componentState } });
  };

  const setRecoveryState = (isRecovering: boolean) => {
    dispatch({ type: 'SET_RECOVERY_STATE', payload: { isRecovering } });
  };

  const setFallbackMode = (mode: 'none' | 'minimal' | 'static' | 'offline') => {
    dispatch({ type: 'SET_FALLBACK_MODE', payload: { mode } });
  };

  const getComponentState = (componentName: string): ComponentErrorState => {
    return state.componentStates[componentName] || {
      hasError: false,
      errorCount: 0,
      lastError: null,
      lastErrorTime: null,
      retryCount: 0,
      fallbackMode: 'none',
      isRecovering: false
    };
  };

  const isComponentInError = (componentName: string): boolean => {
    const componentState = getComponentState(componentName);
    return componentState.hasError;
  };

  const getSystemHealth = (): 'healthy' | 'degraded' | 'critical' => {
    return state.systemHealth;
  };

  const attemptRecovery = async (componentName: string, error: Error) => {
    if (!enableAutoRecovery) return;

    setRecoveryState(true);
    setComponentState(componentName, { isRecovering: true });

    try {
      const componentState = getComponentState(componentName);
      const result = await errorRecoveryManager.attemptRecovery(
        error,
        componentName,
        componentState.retryCount
      );

      if (result.success) {
        // 恢復成功，清理錯誤狀態
        clearComponentErrors(componentName);
        
        if (result.fallbackMode) {
          setComponentState(componentName, { 
            fallbackMode: result.fallbackMode,
            isRecovering: false
          });
        }
      } else {
        // 恢復失敗，更新重試計數
        setComponentState(componentName, { 
          retryCount: componentState.retryCount + 1,
          isRecovering: false
        });
      }
    } catch (recoveryError) {
      console.error('Recovery attempt failed:', recoveryError);
      setComponentState(componentName, { isRecovering: false });
    } finally {
      setRecoveryState(false);
    }
  };

  const contextValue: ErrorStateContextType = {
    state,
    addError,
    removeError,
    clearComponentErrors,
    clearAllErrors,
    setComponentState,
    setRecoveryState,
    setFallbackMode,
    getComponentState,
    isComponentInError,
    getSystemHealth,
    attemptRecovery
  };

  return (
    <ErrorStateContext.Provider value={contextValue}>
      {children}
    </ErrorStateContext.Provider>
  );
};

export const useErrorState = (): ErrorStateContextType => {
  const context = useContext(ErrorStateContext);
  if (context === undefined) {
    throw new Error('useErrorState must be used within an ErrorStateProvider');
  }
  return context;
};

// 便利Hook - 組件錯誤狀態
export const useComponentErrorState = (componentName: string) => {
  const { getComponentState, addError, clearComponentErrors, setComponentState, attemptRecovery } = useErrorState();
  
  const componentState = getComponentState(componentName);
  
  const reportError = (error: Error, severity: 'low' | 'medium' | 'high' | 'critical' = 'medium') => {
    addError(componentName, error, severity);
  };

  const clearErrors = () => {
    clearComponentErrors(componentName);
  };

  const updateState = (state: Partial<ComponentErrorState>) => {
    setComponentState(componentName, state);
  };

  const recover = (error: Error) => {
    return attemptRecovery(componentName, error);
  };

  return {
    ...componentState,
    reportError,
    clearErrors,
    updateState,
    recover
  };
};

export default ErrorStateProvider;