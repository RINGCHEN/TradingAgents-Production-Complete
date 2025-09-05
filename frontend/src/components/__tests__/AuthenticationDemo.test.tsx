/**
 * AuthenticationDemo 整合測試
 * 測試認證系統的整體功能
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AuthenticationDemo from '../AuthenticationDemo';
import { EnhancedAuthProvider } from '../../contexts/EnhancedAuthContext';
import { ErrorStateProvider } from '../../contexts/ErrorStateContext';

// Mock AuthStateManager
jest.mock('../../utils/AuthStateManager', () => ({
  AuthStateManager: {
    getInstance: jest.fn(() => ({
      initialize: jest.fn().mockResolvedValue({
        isInitialized: true,
        isAuthenticated: false,
        mode: 'guest',
        user: null,
        error: null
      }),
      getState: jest.fn(() => ({
        isInitialized: true,
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null,
        mode: 'guest',
        lastInitAttempt: null,
        initAttempts: 0
      })),
      login: jest.fn().mockResolvedValue({ success: true }),
      logout: jest.fn().mockResolvedValue(undefined),
      forceReinitialize: jest.fn().mockResolvedValue(undefined),
      cleanup: jest.fn()
    }))
  },
  authStateManager: {
    initialize: jest.fn(),
    getState: jest.fn(() => ({
      isInitialized: true,
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,
      mode: 'guest'
    })),
    login: jest.fn(),
    logout: jest.fn(),
    forceReinitialize: jest.fn()
  }
}));

// Mock ErrorDiagnostics
jest.mock('../../utils/ErrorDiagnostics', () => ({
  reportComponentError: jest.fn()
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ErrorStateProvider>
    <EnhancedAuthProvider>
      {children}
    </EnhancedAuthProvider>
  </ErrorStateProvider>
);

describe('AuthenticationDemo', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('應該正確渲染認證演示組件', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 檢查標題
    expect(screen.getByText('認證系統演示')).toBeInTheDocument();
    
    // 檢查系統狀態區域
    expect(screen.getByText('系統狀態')).toBeInTheDocument();
    expect(screen.getByText('用戶資訊')).toBeInTheDocument();
    
    // 檢查測試結果區域
    expect(screen.getByText('測試結果 (最近10條)')).toBeInTheDocument();
  });

  test('應該顯示正確的初始狀態', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    await waitFor(() => {
      // 檢查初始化狀態
      expect(screen.getByText('✅ 已初始化')).toBeInTheDocument();
      
      // 檢查認證狀態
      expect(screen.getByText('❌ 未登錄')).toBeInTheDocument();
      
      // 檢查模式
      expect(screen.getByText('guest')).toBeInTheDocument();
    });
  });

  test('應該能夠顯示登錄表單', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 點擊登錄按鈕
    const loginButton = screen.getByText('登錄');
    fireEvent.click(loginButton);

    // 檢查登錄表單是否顯示
    await waitFor(() => {
      expect(screen.getByText('登錄表單')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('電子信箱')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('密碼')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('姓名 (選填)')).toBeInTheDocument();
    });
  });

  test('應該能夠填寫測試數據', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 顯示登錄表單
    fireEvent.click(screen.getByText('登錄'));

    await waitFor(() => {
      // 點擊填入測試數據按鈕
      const fillTestDataButton = screen.getByText('填入測試數據');
      fireEvent.click(fillTestDataButton);

      // 檢查表單是否被填入
      const emailInput = screen.getByPlaceholderText('電子信箱') as HTMLInputElement;
      const nameInput = screen.getByPlaceholderText('姓名 (選填)') as HTMLInputElement;
      
      expect(emailInput.value).toBe('test@example.com');
      expect(nameInput.value).toBe('測試用戶');
    });
  });

  test('應該能夠執行功能測試', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 點擊測試權限按鈕
    const testPermissionButton = screen.getByText('測試權限');
    fireEvent.click(testPermissionButton);

    // 等待測試結果出現
    await waitFor(() => {
      // 檢查是否有測試結果
      const testResults = screen.getByText(/stock-analysis|advanced-analysis|portfolio-management|real-time-alerts/);
      expect(testResults).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test('應該能夠清除測試結果', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 先執行一個測試產生結果
    fireEvent.click(screen.getByText('測試權限'));

    await waitFor(() => {
      // 點擊清除結果按鈕
      const clearButton = screen.getByText('清除結果');
      fireEvent.click(clearButton);

      // 檢查是否顯示暫無測試結果
      expect(screen.getByText('暫無測試結果')).toBeInTheDocument();
    });
  });

  test('應該正確處理按鈕狀態', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 檢查各種操作按鈕是否存在
    expect(screen.getByText('登錄')).toBeInTheDocument();
    expect(screen.getByText('刷新狀態')).toBeInTheDocument();
    expect(screen.getByText('測試錯誤')).toBeInTheDocument();
    expect(screen.getByText('測試權限')).toBeInTheDocument();
  });

  test('應該能夠處理錯誤狀態', async () => {
    render(
      <TestWrapper>
        <AuthenticationDemo />
      </TestWrapper>
    );

    // 點擊測試錯誤按鈕
    const testErrorButton = screen.getByText('測試錯誤');
    fireEvent.click(testErrorButton);

    // 等待錯誤測試完成
    await waitFor(() => {
      // 檢查測試結果中是否包含錯誤相關信息
      const testResultsSection = screen.getByText('測試結果 (最近10條)').parentElement;
      expect(testResultsSection).toBeInTheDocument();
    });
  });
});