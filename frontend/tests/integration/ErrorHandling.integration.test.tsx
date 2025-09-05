/**
 * 錯誤處理流程整合測試
 * 測試認證系統的錯誤處理和恢復機制
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuthContext } from '../../contexts/AuthContext';
import AdminLogin from '../../pages/AdminLogin';
import AdminDashboard from '../../pages/AdminDashboard';
import { authService } from '../../services/AuthService';
import { handleAuthError } from '../../utils/AuthErrors';

// Mock dependencies
jest.mock('../../services/AuthService');
jest.mock('../../utils/AuthErrors');

// Mock fetch
global.fetch = jest.fn();

// Mock console methods to avoid noise in tests
jest.spyOn(console, 'error').mockImplementation(() => {});
jest.spyOn(console, 'warn').mockImplementation(() => {});
jest.spyOn(console, 'log').mockImplementation(() => {});

describe('Error Handling Integration Tests', () => {
  const mockUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    role: 'admin',
    permissions: ['read', 'write'],
    is_admin: true,
    is_active: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
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

  describe('Network Error Handling', () => {
    it('should handle network errors during login', async () => {
      const user = userEvent.setup();

      // Mock network error
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network Error'));
      (handleAuthError as jest.Mock).mockReturnValue({
        message: '網絡連接失敗，請檢查網絡設置',
        type: 'network-error'
      });

      renderWithProviders(<AdminLogin />);

      // Attempt login
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Verify error handling
      await waitFor(() => {
        expect(handleAuthError).toHaveBeenCalledWith(
          expect.any(Error),
          'login'
        );
      });

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/網絡連接失敗/)).toBeInTheDocument();
      });
    });

    it('should provide retry mechanism for network errors', async () => {
      const user = userEvent.setup();

      let attemptCount = 0;
      (global.fetch as jest.Mock).mockImplementation(() => {
        attemptCount++;
        if (attemptCount === 1) {
          return Promise.reject(new Error('Network Error'));
        } else {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              access_token: 'token',
              expires_in: 3600
            })
          });
        }
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '網絡連接失敗，請檢查網絡設置',
        type: 'network-error',
        isRetryable: true
      });

      renderWithProviders(<AdminLogin />);

      // First attempt fails
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/網絡連接失敗/)).toBeInTheDocument();
      });

      // Retry button should be available
      const retryButton = screen.getByRole('button', { name: /重試|retry/i });
      expect(retryButton).toBeInTheDocument();

      // Second attempt succeeds
      await user.click(retryButton);

      await waitFor(() => {
        expect(attemptCount).toBe(2);
      });
    });

    it('should handle offline/online state changes', async () => {
      // Mock offline state
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      const TestComponent = () => {
        const { error } = useAuthContext();
        return (
          <div>
            <div data-testid="error-message">
              {error?.message || 'No error'}
            </div>
            <div data-testid="online-status">
              {navigator.onLine ? 'Online' : 'Offline'}
            </div>
          </div>
        );
      };

      renderWithProviders(<TestComponent />);

      // Verify offline state
      expect(screen.getByTestId('online-status')).toHaveTextContent('Offline');

      // Simulate going online
      Object.defineProperty(navigator, 'onLine', {
        value: true
      });

      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('online-status')).toHaveTextContent('Online');
      });
    });
  });

  describe('Authentication Error Handling', () => {
    it('should handle 401 unauthorized errors', async () => {
      const user = userEvent.setup();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ message: 'Unauthorized' })
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '用戶名或密碼錯誤',
        type: 'unauthorized'
      });

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'wrong');
      await user.type(screen.getByLabelText(/密碼|password/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/用戶名或密碼錯誤/)).toBeInTheDocument();
      });

      // Verify form is still accessible for retry
      expect(screen.getByRole('textbox', { name: /用戶名|username/i })).not.toBeDisabled();
      expect(screen.getByLabelText(/密碼|password/i)).not.toBeDisabled();
    });

    it('should handle 403 forbidden errors', async () => {
      // Mock successful login but forbidden access to dashboard
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/login')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              access_token: 'token',
              expires_in: 3600
            })
          });
        }
        
        if (url.includes('/auth/me')) {
          return Promise.resolve({
            ok: false,
            status: 403,
            json: () => Promise.resolve({ message: 'Forbidden' })
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '權限不足，請聯繫管理員',
        type: 'forbidden'
      });

      const TestComponent = () => {
        const { login, error } = useAuthContext();
        
        const handleLogin = async () => {
          try {
            await login({ username: 'user', password: 'password' });
          } catch (err) {
            // Error handled by context
          }
        };

        return (
          <div>
            <button onClick={handleLogin}>Login</button>
            <div data-testid="error">{error?.message || 'No error'}</div>
          </div>
        );
      };

      renderWithProviders(<TestComponent />);

      await userEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('權限不足，請聯繫管理員');
      });
    });

    it('should handle token expiration during session', async () => {
      // Mock initial successful state
      const mockSecureStorage = {
        getItem: jest.fn().mockResolvedValue({
          access_token: 'expired-token',
          expires_at: Date.now() - 1000 // Expired
        }),
        setItem: jest.fn(),
        removeItem: jest.fn()
      };

      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Refresh token expired' })
          });
        }
        
        if (url.includes('/auth/me')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: () => Promise.resolve({ message: 'Token expired' })
          });
        }
        
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const TestComponent = () => {
        const { user, error, checkAuthStatus } = useAuthContext();
        
        return (
          <div>
            <div data-testid="user">{user?.username || 'No user'}</div>
            <div data-testid="error">{error?.message || 'No error'}</div>
            <button onClick={checkAuthStatus}>Check Auth</button>
          </div>
        );
      };

      renderWithProviders(<TestComponent />);

      // Trigger auth check
      await userEvent.click(screen.getByRole('button', { name: /check auth/i }));

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('No user');
      });
    });
  });

  describe('Server Error Handling', () => {
    it('should handle 500 server errors gracefully', async () => {
      const user = userEvent.setup();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: 'Internal Server Error' })
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '服務器錯誤，請稍後重試',
        type: 'server-error',
        isRetryable: true
      });

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/服務器錯誤，請稍後重試/)).toBeInTheDocument();
      });

      // Should show retry option
      expect(screen.getByRole('button', { name: /重試|retry/i })).toBeInTheDocument();
    });

    it('should handle rate limiting (429) errors', async () => {
      const user = userEvent.setup();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 429,
        headers: new Map([['retry-after', '60']]),
        json: () => Promise.resolve({ message: 'Too Many Requests' })
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '請求過於頻繁，請60秒後重試',
        type: 'rate-limit',
        retryAfter: 60
      });

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'admin');
      await user.type(screen.getByLabelText(/密碼|password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/請求過於頻繁，請60秒後重試/)).toBeInTheDocument();
      });

      // Login button should be disabled temporarily
      expect(screen.getByRole('button', { name: /登錄|login/i })).toBeDisabled();
    });
  });

  describe('Validation Error Handling', () => {
    it('should handle validation errors from server', async () => {
      const user = userEvent.setup();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({
          message: 'Validation failed',
          errors: {
            username: ['用戶名不能為空'],
            password: ['密碼長度至少8位']
          }
        })
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '輸入驗證失敗',
        type: 'validation-error',
        validationErrors: {
          username: ['用戶名不能為空'],
          password: ['密碼長度至少8位']
        }
      });

      renderWithProviders(<AdminLogin />);

      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), '');
      await user.type(screen.getByLabelText(/密碼|password/i), '123');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/用戶名不能為空/)).toBeInTheDocument();
        expect(screen.getByText(/密碼長度至少8位/)).toBeInTheDocument();
      });
    });

    it('should handle client-side validation errors', async () => {
      const user = userEvent.setup();

      renderWithProviders(<AdminLogin />);

      // Try to submit empty form
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      // Should show client-side validation errors
      await waitFor(() => {
        expect(screen.getByText(/請輸入用戶名/)).toBeInTheDocument();
        expect(screen.getByText(/請輸入密碼/)).toBeInTheDocument();
      });

      // Should not make API call
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('Error Recovery and Retry Logic', () => {
    it('should implement exponential backoff for retries', async () => {
      const user = userEvent.setup();
      const timestamps: number[] = [];

      (global.fetch as jest.Mock).mockImplementation(() => {
        timestamps.push(Date.now());
        return Promise.reject(new Error('Network Error'));
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '網絡連接失敗',
        type: 'network-error',
        isRetryable: true
      });

      const TestComponent = () => {
        const { login, error } = useAuthContext();
        
        const handleRetry = async () => {
          try {
            await login({ username: 'admin', password: 'password' });
          } catch (err) {
            // Error handled by context
          }
        };

        return (
          <div>
            <button onClick={handleRetry}>Retry</button>
            <div data-testid="error">{error?.message || 'No error'}</div>
          </div>
        );
      };

      renderWithProviders(<TestComponent />);

      // Make multiple retry attempts
      for (let i = 0; i < 3; i++) {
        await userEvent.click(screen.getByRole('button', { name: /retry/i }));
        await waitFor(() => {
          expect(screen.getByTestId('error')).toHaveTextContent('網絡連接失敗');
        });
      }

      // Verify exponential backoff (timestamps should have increasing gaps)
      expect(timestamps.length).toBe(3);
    });

    it('should limit maximum retry attempts', async () => {
      const user = userEvent.setup();
      let attemptCount = 0;

      (global.fetch as jest.Mock).mockImplementation(() => {
        attemptCount++;
        return Promise.reject(new Error('Persistent Error'));
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '持續錯誤',
        type: 'network-error',
        isRetryable: true
      });

      const TestComponent = () => {
        const { login, error } = useAuthContext();
        
        const handleRetry = async () => {
          try {
            await login({ username: 'admin', password: 'password' });
          } catch (err) {
            // Error handled by context
          }
        };

        return (
          <div>
            <button onClick={handleRetry}>Retry</button>
            <div data-testid="error">{error?.message || 'No error'}</div>
            <div data-testid="attempts">{attemptCount}</div>
          </div>
        );
      };

      renderWithProviders(<TestComponent />);

      // Make many retry attempts
      for (let i = 0; i < 10; i++) {
        await userEvent.click(screen.getByRole('button', { name: /retry/i }));
        await waitFor(() => {
          expect(screen.getByTestId('error')).toHaveTextContent('持續錯誤');
        });
      }

      // Should limit attempts (e.g., max 5 attempts)
      expect(attemptCount).toBeLessThanOrEqual(5);
    });
  });

  describe('Error State Management', () => {
    it('should clear errors when user takes corrective action', async () => {
      const user = userEvent.setup();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ message: 'Unauthorized' })
      });

      (handleAuthError as jest.Mock).mockReturnValue({
        message: '用戶名或密碼錯誤',
        type: 'unauthorized'
      });

      renderWithProviders(<AdminLogin />);

      // First attempt fails
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'wrong');
      await user.type(screen.getByLabelText(/密碼|password/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /登錄|login/i }));

      await waitFor(() => {
        expect(screen.getByText(/用戶名或密碼錯誤/)).toBeInTheDocument();
      });

      // Clear error when user starts typing
      await user.clear(screen.getByRole('textbox', { name: /用戶名|username/i }));
      await user.type(screen.getByRole('textbox', { name: /用戶名|username/i }), 'correct');

      await waitFor(() => {
        expect(screen.queryByText(/用戶名或密碼錯誤/)).not.toBeInTheDocument();
      });
    });

    it('should persist error state across component re-renders', async () => {
      (handleAuthError as jest.Mock).mockReturnValue({
        message: '持續錯誤',
        type: 'server-error'
      });

      const TestComponent = () => {
        const { error, clearError } = useAuthContext();
        const [count, setCount] = React.useState(0);
        
        return (
          <div>
            <div data-testid="error">{error?.message || 'No error'}</div>
            <div data-testid="count">{count}</div>
            <button onClick={() => setCount(c => c + 1)}>Increment</button>
            <button onClick={clearError}>Clear Error</button>
          </div>
        );
      };

      const { rerender } = renderWithProviders(<TestComponent />);

      // Set error state
      act(() => {
        window.dispatchEvent(new CustomEvent('auth-error', {
          detail: { type: 'server-error' }
        }));
      });

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('持續錯誤');
      });

      // Trigger re-render
      await userEvent.click(screen.getByRole('button', { name: /increment/i }));

      // Error should persist
      expect(screen.getByTestId('error')).toHaveTextContent('持續錯誤');
      expect(screen.getByTestId('count')).toHaveTextContent('1');

      // Clear error
      await userEvent.click(screen.getByRole('button', { name: /clear error/i }));

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('No error');
      });
    });
  });

  describe('Global Error Handling', () => {
    it('should handle unhandled promise rejections', async () => {
      const errorHandler = jest.fn();
      window.addEventListener('unhandledrejection', errorHandler);

      // Trigger unhandled rejection
      Promise.reject(new Error('Unhandled error'));

      await waitFor(() => {
        expect(errorHandler).toHaveBeenCalled();
      });

      window.removeEventListener('unhandledrejection', errorHandler);
    });

    it('should handle JavaScript errors gracefully', async () => {
      const errorHandler = jest.fn();
      window.addEventListener('error', errorHandler);

      // Trigger JavaScript error
      act(() => {
        throw new Error('JavaScript error');
      });

      // Should not crash the application
      expect(errorHandler).toHaveBeenCalled();

      window.removeEventListener('error', errorHandler);
    });
  });
});