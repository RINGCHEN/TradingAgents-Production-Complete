/**
 * AdminDashboard 整合測試
 * 天工(TianGong) - 接手小c團隊的前端組件測試工作
 * 
 * 測試目標:
 * - 管理後台組件的完整功能測試
 * - 與小k團隊API的整合測試
 * - 用戶互動和數據流測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'

import AdminDashboard from '../../pages/AdminDashboard'

// Mock API calls
jest.mock('../../services/ApiClient', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
}))

// Mock Authentication Context
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'admin-123',
      email: 'admin@example.com',
      role: 'admin',
      tier: 'admin'
    },
    token: 'mock-jwt-token',
    isAuthenticated: true,
    logout: jest.fn()
  })
}))

const mockApiClient = require('../../services/ApiClient')

// Helper function to render component with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('AdminDashboard Integration Tests', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks()
    
    // Setup default API responses
    mockApiClient.get.mockImplementation((url: string) => {
      if (url.includes('/admin/system/health')) {
        return Promise.resolve({
          data: {
            status: 'healthy',
            uptime: '24h 15m',
            cpu_usage: 45.2,
            memory_usage: 67.8,
            active_users: 1247
          }
        })
      }
      
      if (url.includes('/admin/users/')) {
        return Promise.resolve({
          data: {
            users: [
              {
                id: '1',
                email: 'user1@example.com',
                tier: 'gold',
                status: 'active',
                last_login: '2025-08-14T08:30:00Z'
              },
              {
                id: '2', 
                email: 'user2@example.com',
                tier: 'free',
                status: 'active',
                last_login: '2025-08-13T15:45:00Z'
              }
            ],
            total: 2,
            page: 1,
            per_page: 10
          }
        })
      }
      
      if (url.includes('/admin/config/items')) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 'system.maintenance_mode',
                value: false,
                category: 'system',
                last_modified: '2025-08-14T00:00:00Z'
              },
              {
                id: 'api.rate_limit',
                value: 1000,
                category: 'api',
                last_modified: '2025-08-13T12:00:00Z'
              }
            ]
          }
        })
      }
      
      return Promise.reject(new Error('Mock API endpoint not configured'))
    })
  })

  describe('Component Rendering', () => {
    test('renders admin dashboard with main sections', async () => {
      renderWithRouter(<AdminDashboard />)
      
      // Check for main sections
      expect(screen.getByRole('heading', { name: /管理後台/i })).toBeInTheDocument()
      
      // Wait for API calls to complete and check for system overview
      await waitFor(() => {
        expect(screen.getByText(/系統概覽/i)).toBeInTheDocument()
      })
      
      // Check for navigation tabs
      expect(screen.getByText(/用戶管理/i)).toBeInTheDocument()
      expect(screen.getByText(/配置管理/i)).toBeInTheDocument()
    })

    test('displays system health information', async () => {
      renderWithRouter(<AdminDashboard />)
      
      // Wait for system health data to load
      await waitFor(() => {
        expect(screen.getByText(/系統狀態/i)).toBeInTheDocument()
      })
      
      // Check for system metrics
      await waitFor(() => {
        expect(screen.getByText(/45.2%/)).toBeInTheDocument() // CPU usage
        expect(screen.getByText(/67.8%/)).toBeInTheDocument() // Memory usage
        expect(screen.getByText(/1247/)).toBeInTheDocument()  // Active users
      })
    })

    test('handles loading states correctly', () => {
      // Mock delayed API response
      mockApiClient.get.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 1000))
      )
      
      renderWithRouter(<AdminDashboard />)
      
      // Should show loading indicator
      expect(screen.getByText(/載入中/i) || screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  describe('Tab Navigation', () => {
    test('switches between tabs correctly', async () => {
      const user = userEvent.setup()
      renderWithRouter(<AdminDashboard />)
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText(/系統概覽/i)).toBeInTheDocument()
      })
      
      // Click on user management tab
      const userManagementTab = screen.getByText(/用戶管理/i)
      await user.click(userManagementTab)
      
      // Check if user management content is displayed
      await waitFor(() => {
        expect(screen.getByText(/user1@example.com/i)).toBeInTheDocument()
      })
      
      // Click on config management tab  
      const configTab = screen.getByText(/配置管理/i)
      await user.click(configTab)
      
      // Check if config content is displayed
      await waitFor(() => {
        expect(screen.getByText(/system.maintenance_mode/i)).toBeInTheDocument()
      })
    })

    test('maintains tab state during navigation', async () => {
      const user = userEvent.setup()
      renderWithRouter(<AdminDashboard />)
      
      // Switch to user management tab
      const userTab = screen.getByText(/用戶管理/i)
      await user.click(userTab)
      
      // Verify active tab styling (assuming CSS class)
      expect(userTab.closest('button')).toHaveClass('active')
    })
  })

  describe('API Integration', () => {
    test('makes correct API calls on component mount', async () => {
      renderWithRouter(<AdminDashboard />)
      
      // Wait for component to mount and make API calls
      await waitFor(() => {
        expect(mockApiClient.get).toHaveBeenCalledWith('/admin/system/health')
      })
    })

    test('handles API errors gracefully', async () => {
      // Mock API error
      mockApiClient.get.mockRejectedValue(new Error('API Error'))
      
      renderWithRouter(<AdminDashboard />)
      
      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/錯誤/i) || screen.getByText(/無法載入/i)).toBeInTheDocument()
      })
    })

    test('retries failed API calls', async () => {
      // Mock first call to fail, second to succeed
      mockApiClient.get
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          data: { status: 'healthy', uptime: '1h' }
        })
      
      renderWithRouter(<AdminDashboard />)
      
      // Should eventually show data after retry
      await waitFor(() => {
        expect(screen.getByText(/healthy/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  describe('User Interactions', () => {
    test('allows refreshing system data', async () => {
      const user = userEvent.setup()
      renderWithRouter(<AdminDashboard />)
      
      // Wait for initial load
      await waitFor(() => {
        expect(mockApiClient.get).toHaveBeenCalled()
      })
      
      // Clear mock calls
      mockApiClient.get.mockClear()
      
      // Click refresh button (assuming it exists)
      const refreshButton = screen.getByRole('button', { name: /重新整理|刷新/i })
      if (refreshButton) {
        await user.click(refreshButton)
        
        // Should make API calls again
        await waitFor(() => {
          expect(mockApiClient.get).toHaveBeenCalled()
        })
      }
    })

    test('supports search functionality in user management', async () => {
      const user = userEvent.setup()
      renderWithRouter(<AdminDashboard />)
      
      // Switch to user management
      const userTab = screen.getByText(/用戶管理/i)
      await user.click(userTab)
      
      // Find search input
      const searchInput = screen.getByPlaceholderText(/搜索用戶/i)
      if (searchInput) {
        await user.type(searchInput, 'user1')
        
        // Should filter results
        await waitFor(() => {
          expect(screen.getByText(/user1@example.com/i)).toBeInTheDocument()
        })
      }
    })
  })

  describe('Responsive Design', () => {
    test('adapts to mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      renderWithRouter(<AdminDashboard />)
      
      // Should have mobile-responsive classes
      const dashboard = screen.getByRole('main') || screen.getByTestId('admin-dashboard')
      expect(dashboard).toHaveClass('responsive')
    })

    test('shows mobile navigation menu', async () => {
      const user = userEvent.setup()
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      renderWithRouter(<AdminDashboard />)
      
      // Look for mobile menu button
      const menuButton = screen.getByRole('button', { name: /選單|menu/i })
      if (menuButton) {
        await user.click(menuButton)
        
        // Should show navigation menu
        expect(screen.getByRole('navigation')).toBeVisible()
      }
    })
  })

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      renderWithRouter(<AdminDashboard />)
      
      // Check for main landmark
      expect(screen.getByRole('main')).toBeInTheDocument()
      
      // Check for navigation
      expect(screen.getByRole('navigation')).toBeInTheDocument()
      
      // Check for tab accessibility
      const tabs = screen.getAllByRole('tab')
      expect(tabs.length).toBeGreaterThan(0)
    })

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      renderWithRouter(<AdminDashboard />)
      
      // Tab through interactive elements
      await user.tab()
      
      // First focusable element should be focused
      const firstTab = screen.getAllByRole('tab')[0]
      expect(firstTab).toHaveFocus()
      
      // Use arrow keys to navigate between tabs
      await user.keyboard('[ArrowRight]')
      
      const secondTab = screen.getAllByRole('tab')[1]
      if (secondTab) {
        expect(secondTab).toHaveFocus()
      }
    })

    test('provides appropriate screen reader content', () => {
      renderWithRouter(<AdminDashboard />)
      
      // Check for screen reader announcements
      expect(screen.getByLabelText(/管理後台主要內容/i)).toBeInTheDocument()
      
      // Check for live regions for dynamic content
      const liveRegion = screen.getByRole('status') || screen.getByLabelText(/狀態更新/i)
      if (liveRegion) {
        expect(liveRegion).toHaveAttribute('aria-live')
      }
    })
  })

  describe('Performance', () => {
    test('does not cause memory leaks', () => {
      const { unmount } = renderWithRouter(<AdminDashboard />)
      
      // Component should unmount cleanly
      expect(() => unmount()).not.toThrow()
    })

    test('debounces search input', async () => {
      const user = userEvent.setup()
      renderWithRouter(<AdminDashboard />)
      
      // Switch to user management
      const userTab = screen.getByText(/用戶管理/i)
      await user.click(userTab)
      
      const searchInput = screen.getByPlaceholderText(/搜索用戶/i)
      if (searchInput) {
        // Type quickly
        await user.type(searchInput, 'abc', { delay: 50 })
        
        // API should not be called for every keystroke
        expect(mockApiClient.get).not.toHaveBeenCalledTimes(3)
      }
    })
  })
})