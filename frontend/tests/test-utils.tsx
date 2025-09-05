import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';

// Mock AuthService for testing
const mockAuthService = {
  login: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
  refreshToken: jest.fn(),
  isAuthenticated: jest.fn(),
  onAuthStateChange: jest.fn(),
  initializeAuth: jest.fn(),
};

// Test wrapper component
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <BrowserRouter>
      <AuthProvider authService={mockAuthService}>
        {children}
      </AuthProvider>
    </BrowserRouter>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Test utilities for security testing
export const testSecurityHeaders = (response: Response) => {
  const headers = response.headers;
  expect(headers.get('X-Content-Type-Options')).toBe('nosniff');
  expect(headers.get('X-Frame-Options')).toBe('DENY');
  expect(headers.get('X-XSS-Protection')).toBe('1; mode=block');
};

// Performance testing utilities
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

// Mock data generators
export const createMockUser = (overrides = {}) => ({
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  isActive: true,
  ...overrides,
});

export const createMockAuthState = (overrides = {}) => ({
  user: createMockUser(),
  isAuthenticated: true,
  isLoading: false,
  ...overrides,
});

// API response mocks
export const createMockApiResponse = (data: any, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {},
});

export const createMockApiError = (status = 500, message = 'Server Error') => ({
  response: {
    status,
    data: { message },
    statusText: message,
  },
  message,
});

// Test environment helpers
export const setupTestEnvironment = () => {
  // Mock localStorage
  const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
  });

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock,
  });

  // Mock window.location
  delete (window as any).location;
  window.location = {
    ...window.location,
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
  };

  return {
    localStorage: localStorageMock,
    sessionStorage: sessionStorageMock,
  };
};

// Cleanup function
export const cleanupTestEnvironment = () => {
  jest.clearAllMocks();
  jest.restoreAllMocks();
};

// Async testing helpers
export const waitForAsyncUpdates = () => new Promise(resolve => setTimeout(resolve, 0));

// Form testing utilities
export const fillForm = async (form: HTMLFormElement, data: Record<string, string>) => {
  const { fireEvent } = await import('@testing-library/react');
  Object.entries(data).forEach(([name, value]) => {
    const input = form.querySelector(`[name="${name}"]`) as HTMLInputElement;
    if (input) {
      fireEvent.change(input, { target: { value } });
    }
  });
};

// Security testing helpers
export const testXSSPrevention = (component: ReactElement, maliciousInput: string) => {
  const { container } = customRender(component);
  // Check that malicious scripts are not executed
  expect(container.innerHTML).not.toContain('<script>');
  expect(container.innerHTML).not.toContain('javascript:');
  expect(container.innerHTML).not.toContain('onerror=');
  expect(container.innerHTML).not.toContain('onload=');
};

// Accessibility testing helpers
export const testAccessibility = async (component: ReactElement) => {
  const { axe } = await import('jest-axe');
  const { container } = customRender(component);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
};

// Export mock auth service for use in tests
export { mockAuthService };