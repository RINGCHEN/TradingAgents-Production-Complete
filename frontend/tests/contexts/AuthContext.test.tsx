/**
 * AuthContext 單元測試
 * 測試認證上下文的狀態管理和操作
 */

import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import {
  AuthProvider,
  useAuthContext,
  useAuthState,
  useAuthActions,
  useAuthCheck,
  AuthContext
} from '../../contexts/AuthContext';
import { authService, AuthUser, LoginCredentials, AuthError } from '../../services/AuthService';

// Mock the auth service
jest.mock('../../services/AuthService');

const mockAuthService = authService as jest.Mocked<typeof authService>;

describe('AuthContext', () => {
  const mockUser: AuthUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    role: 'admin',
    permissions: ['read', 'write'],
    is_admin: true,
    is_active: true
  };

  const mockCredentials: LoginCredentials = {
    username: 'testuser',
    password: 'password123'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    // Mock console methods to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  describe('AuthProvider', () => {
    it('should initialize with loading state', () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(false);
      mockAuthService.getCurrentUser.mockResolvedValue(null);

      // Act
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Assert
      expect(result.current.isLoading).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isInitialized).toBe(false);
    });

    it('should initialize with authenticated user when valid token exists', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      // Act
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle initialization errors gracefully', async () => {
      // Arrange
      const initError = new AuthError('Initialization failed');
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockRejectedValue(initError);

      // Act
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.error).toEqual(expect.any(AuthError));
    });
  });

  describe('login action', () => {
    it('should successfully login user', async () => {
      // Arrange
      mockAuthService.login.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.login(mockCredentials);
      });

      // Assert
      expect(mockAuthService.login).toHaveBeenCalledWith(mockCredentials);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle login failure', async () => {
      // Arrange
      const loginError = new AuthError('Login failed');
      mockAuthService.login.mockRejectedValue(loginError);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act & Assert
      await act(async () => {
        await expect(result.current.login(mockCredentials)).rejects.toThrow(AuthError);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toEqual(expect.any(AuthError));
    });

    it('should set loading state during login', async () => {
      // Arrange
      let resolveLogin: (user: AuthUser) => void;
      const loginPromise = new Promise<AuthUser>(resolve => {
        resolveLogin = resolve;
      });
      mockAuthService.login.mockReturnValue(loginPromise);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act - start login
      act(() => {
        result.current.login(mockCredentials);
      });

      // Assert - should be loading
      expect(result.current.isLoading).toBe(true);

      // Complete login
      act(() => {
        resolveLogin!(mockUser);
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe('logout action', () => {
    it('should successfully logout user', async () => {
      // Arrange
      mockAuthService.logout.mockResolvedValue();
      
      // Start with authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.logout();
      });

      // Assert
      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should clear state even if logout API fails', async () => {
      // Arrange
      mockAuthService.logout.mockRejectedValue(new Error('Logout failed'));
      
      // Start with authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.logout();
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('refreshUser action', () => {
    it('should successfully refresh user data', async () => {
      // Arrange
      const updatedUser = { ...mockUser, email: 'updated@example.com' };
      mockAuthService.getCurrentUser.mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.refreshUser();
      });

      // Assert
      expect(result.current.user).toEqual(updatedUser);
    });

    it('should logout when refresh returns null', async () => {
      // Arrange
      mockAuthService.getCurrentUser.mockResolvedValue(null);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.refreshUser();
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('checkAuthStatus action', () => {
    it('should update state when authenticated', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.checkAuthStatus();
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should logout when not authenticated', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(false);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act
      await act(async () => {
        await result.current.checkAuthStatus();
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('clearError action', () => {
    it('should clear error state', async () => {
      // Arrange
      const loginError = new AuthError('Login failed');
      mockAuthService.login.mockRejectedValue(loginError);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Create error state
      await act(async () => {
        try {
          await result.current.login(mockCredentials);
        } catch (error) {
          // Expected to fail
        }
      });

      expect(result.current.error).not.toBeNull();

      // Act
      act(() => {
        result.current.clearError();
      });

      // Assert
      expect(result.current.error).toBeNull();
    });
  });

  describe('event listeners', () => {
    it('should handle auth-state-change events', async () => {
      // Arrange
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Act
      act(() => {
        window.dispatchEvent(new CustomEvent('auth-state-change', {
          detail: { user: mockUser }
        }));
      });

      // Assert
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should handle auth-error events', async () => {
      // Arrange
      // Start with authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Act
      act(() => {
        window.dispatchEvent(new CustomEvent('auth-error', {
          detail: { type: 'token-refresh-failed' }
        }));
      });

      // Assert
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('periodic auth check', () => {
    it('should check auth status periodically when authenticated', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Clear previous calls
      mockAuthService.getCurrentUser.mockClear();

      // Act - advance timer by 5 minutes
      act(() => {
        jest.advanceTimersByTime(5 * 60 * 1000);
      });

      // Assert
      await waitFor(() => {
        expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      });
    });

    it('should not check auth status when not authenticated', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(false);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Clear previous calls
      mockAuthService.getCurrentUser.mockClear();

      // Act - advance timer by 5 minutes
      act(() => {
        jest.advanceTimersByTime(5 * 60 * 1000);
      });

      // Assert
      expect(mockAuthService.getCurrentUser).not.toHaveBeenCalled();
    });
  });

  describe('visibility change handling', () => {
    it('should check auth status when page becomes visible', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthContext(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Clear previous calls
      mockAuthService.getCurrentUser.mockClear();

      // Act - simulate page becoming visible
      Object.defineProperty(document, 'visibilityState', {
        value: 'visible',
        writable: true
      });

      act(() => {
        document.dispatchEvent(new Event('visibilitychange'));
      });

      // Assert
      await waitFor(() => {
        expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      });
    });
  });

  describe('hook selectors', () => {
    it('useAuthState should return auth state', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthState(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isInitialized).toBe(true);
      });

      // Assert
      expect(result.current).toEqual({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        isInitialized: true
      });
    });

    it('useAuthActions should return auth actions', () => {
      // Act
      const { result } = renderHook(() => useAuthActions(), {
        wrapper: AuthProvider
      });

      // Assert
      expect(typeof result.current.login).toBe('function');
      expect(typeof result.current.logout).toBe('function');
      expect(typeof result.current.refreshUser).toBe('function');
      expect(typeof result.current.clearError).toBe('function');
      expect(typeof result.current.checkAuthStatus).toBe('function');
    });

    it('useAuthCheck should return auth check state', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuthCheck(), {
        wrapper: AuthProvider
      });

      // Wait for initialization
      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      // Assert
      expect(result.current).toEqual({
        isAuthenticated: true,
        isLoading: false,
        isInitialized: true,
        isReady: true
      });
    });
  });

  describe('error handling', () => {
    it('should throw error when useAuthContext is used outside provider', () => {
      // Arrange
      const TestComponent = () => {
        useAuthContext();
        return null;
      };

      // Act & Assert
      expect(() => render(<TestComponent />)).toThrow(
        'useAuthContext must be used within an AuthProvider'
      );
    });
  });

  describe('component integration', () => {
    it('should provide context to child components', async () => {
      // Arrange
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const TestComponent = () => {
        const { user, isAuthenticated } = useAuthContext();
        return (
          <div>
            <span data-testid="authenticated">{isAuthenticated.toString()}</span>
            <span data-testid="username">{user?.username || 'none'}</span>
          </div>
        );
      };

      // Act
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Assert
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('username')).toHaveTextContent('testuser');
      });
    });
  });
});