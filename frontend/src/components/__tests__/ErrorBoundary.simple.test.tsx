/**
 * ErrorBoundary 簡化測試套件
 * 基本功能測試，避免複雜的記憶體問題
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../ErrorBoundary';
import { ErrorStateProvider } from '../../contexts/ErrorStateContext';

// Mock 錯誤診斷系統
jest.mock('../../utils/ErrorDiagnostics', () => ({
  reportComponentError: jest.fn()
}));

// Mock 錯誤恢復管理器
jest.mock('../../utils/ErrorRecoveryManager', () => ({
  errorRecoveryManager: {
    attemptRecovery: jest.fn().mockResolvedValue({
      success: true,
      strategy: 'test-strategy',
      message: 'Recovery successful',
      shouldRetry: true
    })
  },
  attemptErrorRecovery: jest.fn().mockResolvedValue({
    success: true,
    strategy: 'test-strategy',
    message: 'Recovery successful',
    shouldRetry: true
  })
}));

// 測試組件
const NormalComponent: React.FC = () => <div>Normal Component</div>;
const ErrorComponent: React.FC = () => {
  throw new Error('Test error');
};

// 測試包裝器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ErrorStateProvider>
    {children}
  </ErrorStateProvider>
);

describe('ErrorBoundary - 基本功能', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('正常渲染子組件', () => {
    render(
      <TestWrapper>
        <ErrorBoundary componentName="TestComponent">
          <NormalComponent />
        </ErrorBoundary>
      </TestWrapper>
    );

    expect(screen.getByText('Normal Component')).toBeInTheDocument();
  });

  test('捕獲並顯示錯誤', () => {
    render(
      <TestWrapper>
        <ErrorBoundary componentName="TestComponent">
          <ErrorComponent />
        </ErrorBoundary>
      </TestWrapper>
    );

    expect(screen.getByText(/組件載入失敗/)).toBeInTheDocument();
    expect(screen.getByText(/TestComponent 組件發生錯誤/)).toBeInTheDocument();
  });

  test('顯示重試和重置按鈕', () => {
    render(
      <TestWrapper>
        <ErrorBoundary componentName="TestComponent" enableRetry={true}>
          <ErrorComponent />
        </ErrorBoundary>
      </TestWrapper>
    );

    expect(screen.getByText('重試')).toBeInTheDocument();
    expect(screen.getByText('重置')).toBeInTheDocument();
  });

  test('禁用重試時不顯示重試按鈕', () => {
    render(
      <TestWrapper>
        <ErrorBoundary componentName="TestComponent" enableRetry={false}>
          <ErrorComponent />
        </ErrorBoundary>
      </TestWrapper>
    );

    expect(screen.queryByText('重試')).not.toBeInTheDocument();
    expect(screen.getByText('重置')).toBeInTheDocument();
  });

  test('重置按鈕可以點擊', () => {
    render(
      <TestWrapper>
        <ErrorBoundary componentName="TestComponent">
          <ErrorComponent />
        </ErrorBoundary>
      </TestWrapper>
    );

    const resetButton = screen.getByText('重置');
    expect(resetButton).not.toBeDisabled();
    
    // 點擊不應該拋出錯誤
    fireEvent.click(resetButton);
  });

  test('顯示錯誤ID', () => {
    render(
      <TestWrapper>
        <ErrorBoundary componentName="TestComponent">
          <ErrorComponent />
        </ErrorBoundary>
      </TestWrapper>
    );

    expect(screen.getByText(/錯誤ID:/)).toBeInTheDocument();
  });
});