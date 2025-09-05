/**
 * AdminDashboard 組件測試
 * 天工(TianGong) - 管理後台主界面測試
 * 
 * 測試範圍:
 * - 組件渲染
 * - 標籤切換功能
 * - 數據載入狀態
 * - 權限控制
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import AdminDashboard from '../pages/AdminDashboard';

// 模擬認證服務
const mockAuthService = {
  getCurrentUser: jest.fn(),
  authenticatedRequest: jest.fn(),
  logout: jest.fn()
};

// 模擬用戶數據
const mockAdminUser = {
  user_id: 'admin_123',
  username: 'admin',
  role: 'admin',
  membership_tier: 'premium',
  permissions: ['ADMIN_ACCESS', 'USER_MANAGEMENT', 'SYSTEM_CONFIG']
};

const mockModeratorUser = {
  user_id: 'mod_456', 
  username: 'moderator',
  role: 'moderator',
  membership_tier: 'premium',
  permissions: ['USER_MANAGEMENT', 'SECURITY_MONITOR']
};

// 包裝組件用於測試
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

// 模擬 authService
jest.mock('../services/authService', () => ({
  getCurrentUser: () => mockAdminUser,
  authenticatedRequest: jest.fn(),
  logout: jest.fn()
}));

describe('AdminDashboard Component', () => {
  
  beforeEach(() => {
    // 重置所有模擬
    jest.clearAllMocks();
    
    // 設置預設的API響應
    mockAuthService.authenticatedRequest.mockImplementation((url: string) => {
      if (url.includes('/admin/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            total_users: 150,
            active_users: 125,
            system_health: 'good',
            security_alerts: 3
          })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  test('should render admin dashboard with correct title', () => {
    renderWithRouter(<AdminDashboard />);
    
    // 檢查標題是否正確渲染
    expect(screen.getByText('管理後台')).toBeInTheDocument();
    expect(screen.getByText('系統管理和監控中心')).toBeInTheDocument();
  });

  test('should render all navigation tabs', () => {
    renderWithRouter(<AdminDashboard />);
    
    // 檢查所有標籤是否存在
    expect(screen.getByText('概覽')).toBeInTheDocument();
    expect(screen.getByText('用戶管理')).toBeInTheDocument();
    expect(screen.getByText('安全監控')).toBeInTheDocument();
    expect(screen.getByText('系統配置')).toBeInTheDocument();
  });

  test('should switch tabs correctly', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 預設應該顯示概覽標籤
    const overviewTab = screen.getByText('概覽');
    expect(overviewTab.closest('.tab')).toHaveClass('active');
    
    // 點擊用戶管理標籤
    const userManagementTab = screen.getByText('用戶管理');
    fireEvent.click(userManagementTab);
    
    // 檢查標籤切換
    await waitFor(() => {
      expect(userManagementTab.closest('.tab')).toHaveClass('active');
      expect(overviewTab.closest('.tab')).not.toHaveClass('active');
    });
  });

  test('should display loading state initially', () => {
    renderWithRouter(<AdminDashboard />);
    
    // 檢查載入狀態
    expect(screen.getByText('載入中...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('should display system statistics after loading', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 等待數據載入完成
    await waitFor(() => {
      expect(screen.getByText('系統統計')).toBeInTheDocument();
    });
    
    // 檢查統計數據
    expect(screen.getByText('150')).toBeInTheDocument(); // 總用戶數
    expect(screen.getByText('125')).toBeInTheDocument(); // 活躍用戶數
    expect(screen.getByText('3')).toBeInTheDocument();   // 安全告警
  });

  test('should handle API error gracefully', async () => {
    // 模擬API錯誤
    mockAuthService.authenticatedRequest.mockRejectedValue(new Error('API Error'));
    
    renderWithRouter(<AdminDashboard />);
    
    // 等待錯誤狀態顯示
    await waitFor(() => {
      expect(screen.getByText('載入失敗')).toBeInTheDocument();
      expect(screen.getByText('重新載入')).toBeInTheDocument();
    });
  });

  test('should retry loading when retry button is clicked', async () => {
    // 首次API調用失敗
    mockAuthService.authenticatedRequest
      .mockRejectedValueOnce(new Error('API Error'))
      .mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          total_users: 200,
          active_users: 180,
          system_health: 'excellent',
          security_alerts: 0
        })
      });
    
    renderWithRouter(<AdminDashboard />);
    
    // 等待錯誤狀態
    await waitFor(() => {
      expect(screen.getByText('載入失敗')).toBeInTheDocument();
    });
    
    // 點擊重新載入按鈕
    const retryButton = screen.getByText('重新載入');
    fireEvent.click(retryButton);
    
    // 檢查重新載入成功
    await waitFor(() => {
      expect(screen.getByText('200')).toBeInTheDocument();
    });
  });

  test('should display user management interface when tab is selected', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 等待初始載入完成
    await waitFor(() => {
      expect(screen.getByText('概覽')).toBeInTheDocument();
    });
    
    // 點擊用戶管理標籤
    const userTab = screen.getByText('用戶管理');
    fireEvent.click(userTab);
    
    // 檢查用戶管理界面元素
    await waitFor(() => {
      expect(screen.getByText('用戶列表')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('搜索用戶...')).toBeInTheDocument();
    });
  });

  test('should display security monitoring interface when tab is selected', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 等待初始載入完成
    await waitFor(() => {
      expect(screen.getByText('概覽')).toBeInTheDocument();
    });
    
    // 點擊安全監控標籤
    const securityTab = screen.getByText('安全監控');
    fireEvent.click(securityTab);
    
    // 檢查安全監控界面元素
    await waitFor(() => {
      expect(screen.getByText('安全告警')).toBeInTheDocument();
      expect(screen.getByText('威脅監控')).toBeInTheDocument();
    });
  });

  test('should display system configuration interface when tab is selected', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 等待初始載入完成
    await waitFor(() => {
      expect(screen.getByText('概覽')).toBeInTheDocument();
    });
    
    // 點擊系統配置標籤
    const configTab = screen.getByText('系統配置');
    fireEvent.click(configTab);
    
    // 檢查系統配置界面元素
    await waitFor(() => {
      expect(screen.getByText('系統設定')).toBeInTheDocument();
      expect(screen.getByText('配置管理')).toBeInTheDocument();
    });
  });

  test('should show logout button and handle logout', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 檢查登出按鈕存在
    const logoutButton = screen.getByText('登出');
    expect(logoutButton).toBeInTheDocument();
    
    // 點擊登出按鈕
    fireEvent.click(logoutButton);
    
    // 檢查是否調用登出函數
    expect(mockAuthService.logout).toHaveBeenCalled();
  });

  test('should display user info correctly', () => {
    renderWithRouter(<AdminDashboard />);
    
    // 檢查用戶信息顯示
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('管理員')).toBeInTheDocument();
  });

  test('should handle responsive design', () => {
    // 模擬移動端視窗大小
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });
    
    renderWithRouter(<AdminDashboard />);
    
    // 檢查移動端導航是否正確顯示
    const mobileMenu = screen.getByTestId('mobile-menu');
    expect(mobileMenu).toBeInTheDocument();
  });

});

describe('AdminDashboard Permission Tests', () => {

  test('should show all features for admin user', () => {
    // 使用管理員用戶
    jest.doMock('../services/authService', () => ({
      getCurrentUser: () => mockAdminUser,
      authenticatedRequest: jest.fn(),
      logout: jest.fn()
    }));
    
    renderWithRouter(<AdminDashboard />);
    
    // 管理員應該能看到所有標籤
    expect(screen.getByText('概覽')).toBeInTheDocument();
    expect(screen.getByText('用戶管理')).toBeInTheDocument();
    expect(screen.getByText('安全監控')).toBeInTheDocument();
    expect(screen.getByText('系統配置')).toBeInTheDocument();
  });

  test('should hide restricted features for moderator user', () => {
    // 使用版主用戶
    jest.doMock('../services/authService', () => ({
      getCurrentUser: () => mockModeratorUser,
      authenticatedRequest: jest.fn(),
      logout: jest.fn()
    }));
    
    renderWithRouter(<AdminDashboard />);
    
    // 版主應該看不到系統配置標籤
    expect(screen.getByText('概覽')).toBeInTheDocument();
    expect(screen.getByText('用戶管理')).toBeInTheDocument();
    expect(screen.getByText('安全監控')).toBeInTheDocument();
    expect(screen.queryByText('系統配置')).not.toBeInTheDocument();
  });

});

describe('AdminDashboard Integration Tests', () => {

  test('should handle real-time data updates', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 模擬實時數據更新
    const updateButton = screen.getByText('刷新數據');
    fireEvent.click(updateButton);
    
    // 檢查載入狀態
    expect(screen.getByTestId('updating-spinner')).toBeInTheDocument();
    
    // 等待更新完成
    await waitFor(() => {
      expect(screen.queryByTestId('updating-spinner')).not.toBeInTheDocument();
    });
  });

  test('should maintain state across tab switches', async () => {
    renderWithRouter(<AdminDashboard />);
    
    // 等待初始載入
    await waitFor(() => {
      expect(screen.getByText('概覽')).toBeInTheDocument();
    });
    
    // 在用戶管理標籤中進行搜索
    fireEvent.click(screen.getByText('用戶管理'));
    await waitFor(() => {
      expect(screen.getByPlaceholderText('搜索用戶...')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('搜索用戶...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    // 切換到其他標籤再切回來
    fireEvent.click(screen.getByText('概覽'));
    fireEvent.click(screen.getByText('用戶管理'));
    
    // 檢查搜索狀態是否保持
    await waitFor(() => {
      expect(searchInput).toHaveValue('test');
    });
  });

});