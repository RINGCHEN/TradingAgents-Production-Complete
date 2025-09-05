/**
 * Navigation 組件增強測試
 * 天工(TianGong) - 接手小c團隊的前端組件測試工作
 * 
 * 測試目標:
 * - Navigation組件的完整功能測試
 * - 響應式設計測試
 * - 用戶權限和角色測試
 * - 無障礙性測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import { axe, toHaveNoViolations } from 'jest-axe'

import Navigation from '../../components/Navigation'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

// Mock AuthContext
const mockAuthContext = {
  user: null,
  isAuthenticated: false,
  logout: jest.fn(),
  login: jest.fn()
}

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

// Helper function to render with router
const renderWithRouter = (component: React.ReactElement, initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      {component}
    </MemoryRouter>
  )
}

describe('Navigation Component Enhanced Tests', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()
    
    // Reset auth context
    mockAuthContext.user = null
    mockAuthContext.isAuthenticated = false
  })

  describe('Component Rendering', () => {
    test('renders basic navigation structure', () => {
      renderWithRouter(<Navigation />)
      
      // Should have navigation role
      expect(screen.getByRole('navigation')).toBeInTheDocument()
      
      // Should have brand/logo
      expect(screen.getByText(/TradingAgents/i)).toBeInTheDocument()
    })

    test('renders navigation items based on authentication state', () => {
      renderWithRouter(<Navigation />)
      
      // Unauthenticated state - should show login/register links
      expect(screen.getByText(/登入/i) || screen.getByText(/登錄/i)).toBeInTheDocument()
      expect(screen.getByText(/註冊/i)).toBeInTheDocument()
    })

    test('renders user-specific navigation when authenticated', () => {
      // Set authenticated state
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'gold',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      // Should show user-specific links
      expect(screen.getByText(/儀表板|Dashboard/i)).toBeInTheDocument()
      expect(screen.getByText(/分析|Analysis/i)).toBeInTheDocument()
      expect(screen.getByText(/登出|Logout/i)).toBeInTheDocument()
    })

    test('shows admin navigation for admin users', () => {
      // Set admin user
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: 'admin-123',
        email: 'admin@example.com',
        tier: 'admin',
        role: 'admin'
      }
      
      renderWithRouter(<Navigation />)
      
      // Should show admin link
      expect(screen.getByText(/管理後台|Admin/i)).toBeInTheDocument()
    })
  })

  describe('User Tier-based Navigation', () => {
    test('shows appropriate navigation for free tier users', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'free',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      // Free tier should have limited navigation
      expect(screen.getByText(/基礎分析/i)).toBeInTheDocument()
      expect(screen.getByText(/升級/i)).toBeInTheDocument()
    })

    test('shows premium features for gold tier users', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'gold',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      // Gold tier should have more features
      expect(screen.getByText(/高級分析/i)).toBeInTheDocument()
      expect(screen.getByText(/投資組合/i)).toBeInTheDocument()
    })

    test('shows all features for diamond tier users', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'diamond',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      // Diamond tier should have all features
      expect(screen.getByText(/專業分析/i)).toBeInTheDocument()
      expect(screen.getByText(/AI對話/i)).toBeInTheDocument()
      expect(screen.getByText(/客製化/i)).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    test('shows mobile menu button on small screens', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      // Trigger resize event
      window.dispatchEvent(new Event('resize'))
      
      renderWithRouter(<Navigation />)
      
      // Should show hamburger menu button
      const menuButton = screen.getByRole('button', { name: /選單|menu/i })
      expect(menuButton).toBeInTheDocument()
    })

    test('toggles mobile menu correctly', async () => {
      const user = userEvent.setup()
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      renderWithRouter(<Navigation />)
      
      const menuButton = screen.getByRole('button', { name: /選單|menu/i })
      
      // Menu should be hidden initially
      const navMenu = screen.getByRole('list') || screen.getByTestId('nav-menu')
      expect(navMenu).not.toBeVisible()
      
      // Click to open menu
      await user.click(menuButton)
      
      // Menu should be visible
      expect(navMenu).toBeVisible()
      
      // Click to close menu
      await user.click(menuButton)
      
      // Menu should be hidden again
      expect(navMenu).not.toBeVisible()
    })

    test('closes mobile menu when clicking outside', async () => {
      const user = userEvent.setup()
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      renderWithRouter(<Navigation />)
      
      const menuButton = screen.getByRole('button', { name: /選單|menu/i })
      
      // Open menu
      await user.click(menuButton)
      
      const navMenu = screen.getByRole('list') || screen.getByTestId('nav-menu')
      expect(navMenu).toBeVisible()
      
      // Click outside
      await user.click(document.body)
      
      // Menu should close
      expect(navMenu).not.toBeVisible()
    })
  })

  describe('User Interactions', () => {
    test('handles logout correctly', async () => {
      const user = userEvent.setup()
      
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'gold',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      const logoutButton = screen.getByText(/登出|Logout/i)
      await user.click(logoutButton)
      
      // Should call logout function
      expect(mockAuthContext.logout).toHaveBeenCalled()
    })

    test('navigates to correct routes when links are clicked', async () => {
      const user = userEvent.setup()
      
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'gold',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />, ['/'])
      
      // Click on dashboard link
      const dashboardLink = screen.getByText(/儀表板|Dashboard/i)
      await user.click(dashboardLink)
      
      // Should navigate to dashboard (check URL or router state)
      expect(dashboardLink.closest('a')).toHaveAttribute('href', '/dashboard')
    })

    test('shows active navigation state', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'gold',
        role: 'user'
      }
      
      // Render with dashboard route active
      renderWithRouter(<Navigation />, ['/dashboard'])
      
      // Dashboard link should have active styling
      const dashboardLink = screen.getByText(/儀表板|Dashboard/i)
      expect(dashboardLink.closest('a')).toHaveClass('active')
    })
  })

  describe('Accessibility', () => {
    test('has no accessibility violations', async () => {
      const { container } = renderWithRouter(<Navigation />)
      
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'gold',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      // Tab through navigation links
      await user.tab()
      
      // First link should be focused
      const firstLink = screen.getAllByRole('link')[0]
      expect(firstLink).toHaveFocus()
      
      // Continue tabbing
      await user.tab()
      const secondLink = screen.getAllByRole('link')[1]
      expect(secondLink).toHaveFocus()
    })

    test('has proper ARIA labels and roles', () => {
      renderWithRouter(<Navigation />)
      
      // Navigation should have proper role
      const nav = screen.getByRole('navigation')
      expect(nav).toHaveAttribute('aria-label', expect.stringMatching(/主要導航|main navigation/i))
      
      // Mobile menu button should have proper labels
      const menuButton = screen.getByRole('button', { name: /選單|menu/i })
      if (menuButton) {
        expect(menuButton).toHaveAttribute('aria-expanded')
        expect(menuButton).toHaveAttribute('aria-controls')
      }
    })

    test('announces navigation state changes to screen readers', async () => {
      const user = userEvent.setup()
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      renderWithRouter(<Navigation />)
      
      const menuButton = screen.getByRole('button', { name: /選單|menu/i })
      
      // Check initial aria-expanded state
      expect(menuButton).toHaveAttribute('aria-expanded', 'false')
      
      // Open menu
      await user.click(menuButton)
      
      // Check updated aria-expanded state
      expect(menuButton).toHaveAttribute('aria-expanded', 'true')
    })
  })

  describe('Theme and Styling', () => {
    test('applies correct tier-based styling', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'diamond',
        role: 'user'
      }
      
      renderWithRouter(<Navigation />)
      
      // Navigation should have tier-specific styling
      const nav = screen.getByRole('navigation')
      expect(nav).toHaveClass('tier-diamond')
    })

    test('supports dark mode', () => {
      // Mock dark mode preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      })
      
      renderWithRouter(<Navigation />)
      
      const nav = screen.getByRole('navigation')
      expect(nav).toHaveClass('dark-mode')
    })
  })

  describe('Performance', () => {
    test('does not re-render unnecessarily', () => {
      const renderSpy = jest.fn()
      
      // Mock component with render tracking
      const NavigationWithSpy = () => {
        renderSpy()
        return <Navigation />
      }
      
      const { rerender } = renderWithRouter(<NavigationWithSpy />)
      
      // Initial render
      expect(renderSpy).toHaveBeenCalledTimes(1)
      
      // Re-render with same props
      rerender(<NavigationWithSpy />)
      
      // Should not re-render if props haven't changed
      expect(renderSpy).toHaveBeenCalledTimes(1)
    })

    test('cleans up event listeners on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener')
      
      const { unmount } = renderWithRouter(<Navigation />)
      
      unmount()
      
      // Should clean up resize listener
      expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))
      
      removeEventListenerSpy.mockRestore()
    })
  })

  describe('Error Handling', () => {
    test('handles missing user data gracefully', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = null // Missing user data
      
      expect(() => {
        renderWithRouter(<Navigation />)
      }).not.toThrow()
      
      // Should fall back to unauthenticated state
      expect(screen.getByText(/登入/i)).toBeInTheDocument()
    })

    test('handles invalid tier gracefully', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '123',
        email: 'user@example.com',
        tier: 'invalid_tier', // Invalid tier
        role: 'user'
      }
      
      expect(() => {
        renderWithRouter(<Navigation />)
      }).not.toThrow()
      
      // Should default to free tier behavior
      expect(screen.getByText(/基礎分析/i)).toBeInTheDocument()
    })
  })
})