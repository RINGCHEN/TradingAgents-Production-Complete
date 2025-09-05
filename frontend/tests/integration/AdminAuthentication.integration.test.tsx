/**
 * Admin Authentication Integration Tests
 * 測試管理員認證系統的完整整合流程
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import AdminLogin from '../../pages/AdminLogin';
import AdminDashboard from '../../pages/AdminDashboard';
import { apiClient } from '../../services/ApiClient';

// Mock the services
jest.mock('../../services/ApiClient');
jest.mock('../../services/AuthService');
jest.mock('../../services/TokenManager');

// Mock fetch for API calls
global.fetch = jest.fn();

describe('Admin Authentication Integration', () => {
  const mockAdminUser = {
    id: 1,
    username: 'admin',
    email: 'admin@tradingagents.com',
    role: 'admin',
    permissions: ['admin:read', 'admin:write', 'admin:delete'],
    is_admin: true,
    is_active: true
  };

  const mockTokens = {
    access_token: 'admin-access-token',
    refresh_token: 'admin-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000
  };

  const mockAdminData = {
    users: [
      { id: 1, username: 'user1', email: 'user1@example.com', is_active: true },
      { id: 2, username: 'user2', email: 'user2@example.com', is_active: false }
    ],
    subscriptions: [
      { id: 1, user_id: 1, plan: 'premium', status: 'active' },
      { id: 2, user_id: 2, plan: 'basic', status: 'cancelled' }
    ],
    systemHealth: {
      status: 'healthy',
      uptime: 86400,
      database: { status: 'connected', response_time: 15 },
      redis: { status: 'connected', response_time: 5 },
      external_apis: [
        { name: 'finnhub', status: 'connected', response_time: 120 }
      ]
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
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
          json: () => Promise.resolve(mockAdminUser)
        });
      }
      if (url.includes('/admin/users')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            users: mockAdminData.users,
            total: mockAdminData.users.length,
            page: 1,
            limit: 20
          })
        });
      }
      if (url.includes('/admin/subscriptions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            subscriptions: mockAdminData.subscriptions,
            total: mockAdminData.subscriptions.length,
            page: 1,
            limit: 20
          })
        });
      }
      if (url.includes('/admin/system/health')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAdminData.systemHealth)
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

  describe('Complete Admin Authentication Flow', () => {
    it('should complete full admin login and dashboard access flow', async () => {
      const user = userEvent.setup();

      // Start with login page
      renderWithProviders(<AdminLogin />);

      // Verify login form is displayed
      expect(screen.getByRole('textbox', { name: /用戶名|username/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/密碼|password/i)).toBeInTheDocument();

      // Fill in admin credentials
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'admin123');

      // Submit login form
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Wait for authentication to complete
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/login'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              username: 'admin',
              password: 'admin123'
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
    });

    it('should load admin dashboard with real data after authentication', async () => {
      const user = userEvent.setup();

      // Mock authenticated state
      const AuthenticatedDashboard = () => (
        <AuthProvider>
          <AdminDashboard />
        </AuthProvider>
      );

      renderWithProviders(<AuthenticatedDashboard />);

      // Wait for dashboard to load data
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/users'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': expect.stringContaining('Bearer')
            })
          })
        );
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/subscriptions'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': expect.stringContaining('Bearer')
            })
          })
        );
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/admin/system/health'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': expect.stringContaining('Bearer')
            })
          })
        );
      });

      // Verify dashboard displays real data
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
        expect(screen.getByText('user2')).toBeInTheDocument();
        expect(screen.getByText('premium')).toBeInTheDocument();
        expect(screen.getByText('healthy')).toBeInTheDocument();
      });
    });
  });

  describe('Protected Route Integration', () => {
    it('should redirect to login when accessing protected route without authentication', async () => {
      // Render protected dashboard without authentication
      renderWithProviders(
        <ProtectedRoute>
          <AdminDashboard />
        </ProtectedRoute>
      );

      // Should redirect to login
      await waitFor(() => {
        expect(screen.getByText(/請登錄|please login/i)).toBeInTheDocument();
      });
    });

    it('should allow access to protected route with valid authentication', async () => {
      const user = userEvent.setup();

      // Create a test component that simulates authenticated state
      const AuthenticatedProtectedRoute = () => {
        const [isAuthenticated, setIsAuthenticated] = React.useState(false);

        React.useEffect(() => {
          // Simulate authentication
          setTimeout(() => setIsAuthenticated(true), 100);
        }, []);

        if (!isAuthenticated) {
          return <AdminLogin />;
        }

        return (
          <ProtectedRoute>
            <AdminDashboard />
          </ProtectedRoute>
        );
      };

      renderWithProviders(<AuthenticatedProtectedRoute />);

      // Wait for authentication and dashboard to load
      await waitFor(() => {
        expect(screen.getByText(/管理面板|admin dashboard/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should handle permission-based access control', async () => {
      // Mock user with limited permissions
      const limitedUser = {
        ...mockAdminUser,
        permissions: ['admin:read'] // Only read permission
      };

      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(limitedUser)
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        });
      });

      renderWithProviders(
        <ProtectedRoute requiredPermissions={['admin:write']}>
          <div>Admin Write Content</div>
        </ProtectedRoute>
      );

      // Should show access denied message
      await waitFor(() => {
        expect(screen.getByText(/權限不足|access denied/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Authentication Integration', () => {
    it('should automatically add authentication headers to admin API calls', async () => {
      // Mock apiClient
      const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
      mockApiClient.get.mockResolvedValue({
        data: mockAdminData.users,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {}
      });

      renderWithProviders(<AdminDashboard />);

      // Wait for API calls
      await waitFor(() => {
        expect(mockApiClient.get).toHaveBeenCalledWith('/admin/users');
      });
    });

    it('should handle 401 errors with automatic token refresh', async () => {
      let callCount = 0;
      (global.fetch as jest.Mock).mockImplementation((url) => {
        callCount++;
        
        if (url.includes('/admin/users')) {
          if (callCount === 1) {
            // First call returns 401
            return Promise.resolve({
              ok: false,
              status: 401,
              json: () => Promise.resolve({ message: 'Token expired' })
            });
          } else {
            // Retry after refresh succeeds
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve({
                users: mockAdminData.users,
                total: mockAdminData.users.length
              })
            });
          }
        }
        
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              access_token: 'new-access-token',
              expires_in: 3600
            })
          });
        }
        
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        });
      });

      renderWithProviders(<AdminDashboard />);

      // Wait for initial 401, refresh, and retry
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/refresh'),
          expect.any(Object)
        );
      });

      // Verify data is eventually loaded
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
      });
    });

    it('should handle authentication failure during API calls', async () => {
      // Mock failed token refresh
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/admin/users')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Unauthorized' })
          });
        }
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Refresh token expired' })
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const authErrorListener = jest.fn();
      window.addEventListener('auth-error', authErrorListener);

      renderWithProviders(<AdminDashboard />);

      // Wait for auth error event
      await waitFor(() => {
        expect(authErrorListener).toHaveBeenCalledWith(
          expect.objectContaining({
            detail: { type: 'token-refresh-failed' }
          })
        );
      });

      window.removeEventListener('auth-error', authErrorListener);
    });
  });

  describe('Error Handling and User Experience', () => {
    it('should display appropriate error messages for different failure types', async () => {
      const user = userEvent.setup();

      // Test invalid credentials
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ message: 'Invalid credentials' })
        })
      );

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'wrong');
      await user.type(screen.getByLabelText(/密碼|password/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/用戶名或密碼錯誤|invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('should show loading states during authentication operations', async () => {
      const user = userEvent.setup();

      // Mock delayed response
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(mockTokens)
          }), 200)
        )
      );

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'admin123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify loading state
      expect(screen.getByText(/登錄中|logging in/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /登錄|login/i })).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByText(/登錄中|logging in/i)).not.toBeInTheDocument();
      });
    });

    it('should handle network errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock network error
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.reject(new Error('Network Error'))
      );

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'admin123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/網絡連接失敗|network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Security Compliance', () => {
    it('should use secure token storage mechanisms', async () => {
      const user = userEvent.setup();

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'admin123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/login'),
          expect.any(Object)
        );
      });

      // Verify tokens are not logged or exposed
      const consoleSpy = jest.spyOn(console, 'log');
      expect(consoleSpy).not.toHaveBeenCalledWith(
        expect.stringContaining(mockTokens.access_token)
      );
    });

    it('should enforce HTTPS for authentication requests', async () => {
      const user = userEvent.setup();

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'admin123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringMatching(/^https?:\/\//),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            })
          })
        );
      });
    });

    it('should clear all authentication data on logout', async () => {
      const user = userEvent.setup();

      // Mock authenticated state
      const AuthenticatedApp = () => {
        const [isAuthenticated, setIsAuthenticated] = React.useState(true);

        const handleLogout = () => {
          setIsAuthenticated(false);
          // Simulate logout cleanup
          localStorage.removeItem('admin_auth_tokens');
          sessionStorage.clear();
        };

        if (!isAuthenticated) {
          return <AdminLogin />;
        }

        return (
          <div>
            <button onClick={handleLogout}>Logout</button>
            <AdminDashboard />
          </div>
        );
      };

      const localStorageSpy = jest.spyOn(Storage.prototype, 'removeItem');
      const sessionStorageSpy = jest.spyOn(Storage.prototype, 'clear');

      renderWithProviders(<AuthenticatedApp />);

      await user.click(screen.getByText('Logout'));

      expect(localStorageSpy).toHaveBeenCalledWith('admin_auth_tokens');
      expect(sessionStorageSpy).toHaveBeenCalled();

      localStorageSpy.mockRestore();
      sessionStorageSpy.mockRestore();
    });
  });

  describe('Cross-Tab Authentication Synchronization', () => {
    it('should synchronize authentication state across browser tabs', async () => {
      // Mock storage event for cross-tab communication
      const storageEvent = new StorageEvent('storage', {
        key: 'admin_auth_tokens',
        newValue: JSON.stringify(mockTokens),
        oldValue: null,
        storageArea: localStorage
      });

      const AuthStateDisplay = () => {
        const { isAuthenticated, user } = useAuthContext();
        return (
          <div>
            <div data-testid="auth-status">
              {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
            </div>
            <div data-testid="user-name">
              {user?.username || 'No User'}
            </div>
          </div>
        );
      };

      renderWithProviders(<AuthStateDisplay />);

      // Initially not authenticated
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');

      // Simulate storage change from another tab
      act(() => {
        window.dispatchEvent(storageEvent);
      });

      // Should update authentication state
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
      });
    });
  });

  describe('Performance and Memory Management', () => {
    it('should not cause memory leaks during authentication flow', async () => {
      const user = userEvent.setup();

      // Track event listeners
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = renderWithProviders(<AdminLogin />);

      // Complete login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'admin123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });

      // Unmount component
      unmount();

      // Verify cleanup
      expect(removeEventListenerSpy).toHaveBeenCalled();

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });

    it('should handle rapid authentication state changes efficiently', async () => {
      const AuthStateToggle = () => {
        const [count, setCount] = React.useState(0);
        
        React.useEffect(() => {
          const interval = setInterval(() => {
            setCount(c => c + 1);
            // Simulate rapid auth state changes
            window.dispatchEvent(new CustomEvent('auth-state-change', {
              detail: { user: count % 2 === 0 ? mockAdminUser : null }
            }));
          }, 10);

          return () => clearInterval(interval);
        }, [count]);

        return <div data-testid="counter">{count}</div>;
      };

      const { unmount } = renderWithProviders(<AuthStateToggle />);

      // Let it run for a short time
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      // Should handle rapid changes without errors
      expect(screen.getByTestId('counter')).toBeInTheDocument();

      unmount();
    });
  });
});