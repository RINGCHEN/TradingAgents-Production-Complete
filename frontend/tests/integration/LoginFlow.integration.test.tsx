/**
 * 完整登錄流程整合測試
 * 測試從用戶輸入到認證完成的整個流程
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import AdminLogin from '../../pages/AdminLogin';
import AdminDashboard from '../../pages/AdminDashboard';
import { authService } from '../../services/AuthService';

// Mock the auth service
jest.mock('../../services/AuthService');

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

describe('Login Flow Integration Tests', () => {
  const mockUser = {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    permissions: ['read', 'write', 'admin'],
    is_admin: true,
    is_active: true
  };

  const mockTokens = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    
    // Mock successful API responses
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/auth/login')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTokens)
        });
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUser)
        });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <AuthProvider>
          {component}
        </AuthProvider>
      </BrowserRouter>
    );
  };

  describe('Successful Login Flow', () => {
    it('should complete full login flow from form submission to dashboard access', async () => {
      const user = userEvent.setup();

      // Render login page
      renderWithProviders(<AdminLogin />);

      // Verify login form is displayed
      expect(screen.getByRole('textbox', { name: /用戶名|username/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/密碼|password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /登錄|login/i })).toBeInTheDocument();

      // Fill in login form
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');

      // Submit form
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Wait for login to complete
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/login'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              username: 'admin',
              password: 'password123'
            })
          })
        );
      });

      // Verify user info is fetched
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/me'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': `Bearer ${mockTokens.access_token}`
            })
          })
        );
      });

      // Verify tokens are stored
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'admin_auth_tokens',
        expect.stringContaining(mockTokens.access_token)
      );
    });

    it('should maintain authentication state across component re-renders', async () => {
      const user = userEvent.setup();

      // Start with login page
      const { rerender } = renderWithProviders(<AdminLogin />);

      // Complete login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/login'),
          expect.any(Object)
        );
      });

      // Mock localStorage to return stored tokens
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockTokens));

      // Re-render with dashboard
      rerender(
        <BrowserRouter>
          <AuthProvider>
            <AdminDashboard />
          </AuthProvider>
        </BrowserRouter>
      );

      // Verify dashboard loads with user data
      await waitFor(() => {
        expect(screen.getByText(/歡迎|welcome/i)).toBeInTheDocument();
      });
    });
  });

  describe('Login Error Handling', () => {
    it('should handle invalid credentials gracefully', async () => {
      const user = userEvent.setup();

      // Mock failed login
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ message: 'Invalid credentials' })
        })
      );

      renderWithProviders(<AdminLogin />);

      // Fill in invalid credentials
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'invalid');
      await user.type(screen.getByLabelText(/密碼|password/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/用戶名或密碼錯誤|invalid credentials/i)).toBeInTheDocument();
      });

      // Verify no tokens are stored
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    it('should handle network errors during login', async () => {
      const user = userEvent.setup();

      // Mock network error
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.reject(new Error('Network Error'))
      );

      renderWithProviders(<AdminLogin />);

      // Attempt login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify network error message
      await waitFor(() => {
        expect(screen.getByText(/網絡連接失敗|network error/i)).toBeInTheDocument();
      });
    });

    it('should handle server errors during login', async () => {
      const user = userEvent.setup();

      // Mock server error
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ message: 'Internal Server Error' })
        })
      );

      renderWithProviders(<AdminLogin />);

      // Attempt login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify server error message
      await waitFor(() => {
        expect(screen.getByText(/服務器錯誤|server error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during login process', async () => {
      const user = userEvent.setup();

      // Mock delayed response
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(mockTokens)
          }), 100)
        )
      );

      renderWithProviders(<AdminLogin />);

      // Start login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify loading state
      expect(screen.getByText(/登錄中|logging in/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /登錄|login/i })).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByText(/登錄中|logging in/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const user = userEvent.setup();

      renderWithProviders(<AdminLogin />);

      // Try to submit empty form
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify validation messages
      await waitFor(() => {
        expect(screen.getByText(/請輸入用戶名|username required/i)).toBeInTheDocument();
        expect(screen.getByText(/請輸入密碼|password required/i)).toBeInTheDocument();
      });

      // Verify no API call is made
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should validate minimum password length', async () => {
      const user = userEvent.setup();

      renderWithProviders(<AdminLogin />);

      // Enter short password
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), '123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify validation message
      await waitFor(() => {
        expect(screen.getByText(/密碼長度至少|password too short/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authentication State Persistence', () => {
    it('should restore authentication state on page reload', async () => {
      // Mock existing tokens in localStorage
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockTokens));

      // Mock user info API call
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUser)
        })
      );

      // Render dashboard (simulating page reload)
      renderWithProviders(<AdminDashboard />);

      // Verify user info is fetched
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/me'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': `Bearer ${mockTokens.access_token}`
            })
          })
        );
      });

      // Verify dashboard shows user data
      await waitFor(() => {
        expect(screen.getByText(mockUser.username)).toBeInTheDocument();
      });
    });

    it('should handle expired tokens on page reload', async () => {
      // Mock expired tokens
      const expiredTokens = {
        ...mockTokens,
        expires_at: Date.now() - 1000 // Expired 1 second ago
      };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(expiredTokens));

      // Mock token refresh failure
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ message: 'Token expired' })
        })
      );

      renderWithProviders(<AdminDashboard />);

      // Verify tokens are cleared
      await waitFor(() => {
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('admin_auth_tokens');
      });

      // Verify user is redirected to login
      await waitFor(() => {
        expect(screen.getByText(/請登錄|please login/i)).toBeInTheDocument();
      });
    });
  });

  describe('Cross-Component Communication', () => {
    it('should update all components when authentication state changes', async () => {
      const user = userEvent.setup();

      // Create a test component that shows auth state
      const AuthStateDisplay = () => {
        const { isAuthenticated, user: currentUser } = useAuthContext();
        return (
          <div>
            <div data-testid="auth-status">
              {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
            </div>
            <div data-testid="user-name">
              {currentUser?.username || 'No User'}
            </div>
          </div>
        );
      };

      renderWithProviders(
        <div>
          <AdminLogin />
          <AuthStateDisplay />
        </div>
      );

      // Initially not authenticated
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
      expect(screen.getByTestId('user-name')).toHaveTextContent('No User');

      // Complete login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify state updates across components
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('admin');
      });
    });
  });

  describe('Memory and Performance', () => {
    it('should not cause memory leaks during login flow', async () => {
      const user = userEvent.setup();

      // Track event listeners
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = renderWithProviders(<AdminLogin />);

      // Complete login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });

      // Unmount component
      unmount();

      // Verify event listeners are cleaned up
      expect(removeEventListenerSpy).toHaveBeenCalled();

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });

    it('should handle rapid successive login attempts', async () => {
      const user = userEvent.setup();

      renderWithProviders(<AdminLogin />);

      // Fill form
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');

      // Click login button multiple times rapidly
      const loginButton = screen.getByRole('button', { name: /登錄|login/i });
      await user.click(loginButton);
      await user.click(loginButton);
      await user.click(loginButton);

      // Verify only one API call is made
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });
    });
  });
});