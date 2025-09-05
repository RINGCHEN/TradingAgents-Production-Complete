/**
 * ApiClientDemo 測試套件
 * 測試API客戶端演示組件的基本功能
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ApiClientDemo from '../ApiClientDemo';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('ApiClientDemo', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('應該渲染演示組件', () => {
    render(<ApiClientDemo />);
    
    expect(screen.getByText('API客戶端演示 - 響應格式驗證與錯誤處理')).toBeInTheDocument();
    expect(screen.getByText('測試正常JSON響應')).toBeInTheDocument();
    expect(screen.getByText('測試HTML格式錯誤')).toBeInTheDocument();
    expect(screen.getByText('測試網路錯誤')).toBeInTheDocument();
    expect(screen.getByText('測試404錯誤')).toBeInTheDocument();
  });

  it('應該顯示測試結果', async () => {
    render(<ApiClientDemo />);
    
    // 點擊測試按鈕
    fireEvent.click(screen.getByText('測試正常JSON響應'));
    
    // 等待測試結果出現
    await waitFor(() => {
      expect(screen.getByText(/JSON響應/)).toBeInTheDocument();
    });
  });

  it('應該能夠清除測試結果', async () => {
    render(<ApiClientDemo />);
    
    // 先執行一個測試
    fireEvent.click(screen.getByText('測試正常JSON響應'));
    
    await waitFor(() => {
      expect(screen.getByText(/JSON響應/)).toBeInTheDocument();
    });
    
    // 清除結果
    fireEvent.click(screen.getByText('清除測試結果'));
    
    // 檢查是否顯示暫無測試結果
    expect(screen.getByText('暫無測試結果')).toBeInTheDocument();
  });

  it('應該顯示載入狀態', () => {
    render(<ApiClientDemo />);
    
    // 點擊測試按鈕
    fireEvent.click(screen.getByText('測試正常JSON響應'));
    
    // 檢查載入狀態
    expect(screen.getByText('測試中...')).toBeInTheDocument();
  });

  it('應該顯示功能說明', () => {
    render(<ApiClientDemo />);
    
    expect(screen.getByText('功能說明:')).toBeInTheDocument();
    expect(screen.getByText(/自動檢測API響應格式/)).toBeInTheDocument();
    expect(screen.getByText(/智能錯誤分類和處理策略/)).toBeInTheDocument();
    expect(screen.getByText(/網路錯誤自動重試機制/)).toBeInTheDocument();
  });
});