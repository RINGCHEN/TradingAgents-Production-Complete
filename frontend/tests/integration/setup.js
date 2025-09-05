/**
 * 整合測試設置文件
 * 為整合測試提供特殊的環境配置和工具函數
 */

import '@testing-library/jest-dom';

// 整合測試專用的環境變量
process.env.NODE_ENV = 'test';
process.env.REACT_APP_API_BASE_URL = 'http://localhost:3000/api';

// 擴展的超時時間用於整合測試
jest.setTimeout(30000);

// Mock window.location for navigation tests
delete window.location;
window.location = {
  href: 'http://localhost:3000',
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  pathname: '/',
  search: '',
  hash: '',
  assign: jest.fn(),
  replace: jest.fn(),
  reload: jest.fn()
};

// Mock window.history for routing tests
Object.defineProperty(window, 'history', {
  value: {
    pushState: jest.fn(),
    replaceState: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    go: jest.fn(),
    length: 1,
    state: null
  },
  writable: true
});

// Enhanced localStorage mock for integration tests
const createLocalStorageMock = () => {
  let store = {};
  
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: jest.fn((index) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    })
  };
};

global.localStorage = createLocalStorageMock();
global.sessionStorage = createLocalStorageMock();

// Mock crypto for secure operations
Object.defineProperty(global, 'crypto', {
  value: {
    getRandomValues: jest.fn((arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }),
    randomUUID: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9))
  }
});

// Mock performance API
Object.defineProperty(global, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByName: jest.fn(() => []),
    getEntriesByType: jest.fn(() => [])
  }
});

// Enhanced fetch mock for integration tests
const createFetchMock = () => {
  const fetchMock = jest.fn();
  
  // Default successful response
  fetchMock.mockResolvedValue({
    ok: true,
    status: 200,
    statusText: 'OK',
    headers: new Map(),
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0))
  });
  
  return fetchMock;
};

global.fetch = createFetchMock();

// Mock IntersectionObserver for component visibility tests
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback, options) {
    this.callback = callback;
    this.options = options;
  }
  
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver for responsive tests
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {
    this.callback = callback;
  }
  
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock MutationObserver for DOM change tests
global.MutationObserver = class MutationObserver {
  constructor(callback) {
    this.callback = callback;
  }
  
  observe() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
};

// Mock requestAnimationFrame for animation tests
global.requestAnimationFrame = jest.fn((callback) => {
  return setTimeout(callback, 16);
});

global.cancelAnimationFrame = jest.fn((id) => {
  clearTimeout(id);
});

// Mock requestIdleCallback for performance tests
global.requestIdleCallback = jest.fn((callback) => {
  return setTimeout(() => callback({ didTimeout: false, timeRemaining: () => 50 }), 1);
});

global.cancelIdleCallback = jest.fn((id) => {
  clearTimeout(id);
});

// Enhanced console mocking with categorization
const originalConsole = { ...console };

const createConsoleMock = (level) => {
  const mock = jest.fn();
  mock.originalMethod = originalConsole[level];
  return mock;
};

global.console = {
  ...originalConsole,
  log: createConsoleMock('log'),
  info: createConsoleMock('info'),
  warn: createConsoleMock('warn'),
  error: createConsoleMock('error'),
  debug: createConsoleMock('debug')
};

// Mock navigator properties for various tests
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true
});

Object.defineProperty(navigator, 'language', {
  writable: true,
  value: 'en-US'
});

Object.defineProperty(navigator, 'languages', {
  writable: true,
  value: ['en-US', 'en']
});

Object.defineProperty(navigator, 'userAgent', {
  writable: true,
  value: 'Mozilla/5.0 (Test Environment) Jest/Integration'
});

// Mock clipboard API
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn(() => Promise.resolve()),
    readText: jest.fn(() => Promise.resolve(''))
  }
});

// Mock geolocation API
Object.defineProperty(navigator, 'geolocation', {
  value: {
    getCurrentPosition: jest.fn(),
    watchPosition: jest.fn(),
    clearWatch: jest.fn()
  }
});

// Mock media devices for camera/microphone tests
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: jest.fn(() => Promise.resolve({
      getTracks: () => [],
      getVideoTracks: () => [],
      getAudioTracks: () => []
    })),
    enumerateDevices: jest.fn(() => Promise.resolve([]))
  }
});

// Mock service worker for PWA tests
Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    register: jest.fn(() => Promise.resolve({
      installing: null,
      waiting: null,
      active: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    })),
    ready: Promise.resolve({
      installing: null,
      waiting: null,
      active: null
    })
  }
});

// Global test utilities for integration tests
global.testUtils = {
  // Wait for async operations to complete
  waitForAsync: (ms = 0) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Create mock user data
  createMockUser: (overrides = {}) => ({
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    role: 'admin',
    permissions: ['read', 'write'],
    is_admin: true,
    is_active: true,
    ...overrides
  }),
  
  // Create mock token data
  createMockTokens: (overrides = {}) => ({
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    expires_at: Date.now() + 3600000,
    ...overrides
  }),
  
  // Create mock API response
  createMockResponse: (data, options = {}) => ({
    ok: true,
    status: 200,
    statusText: 'OK',
    headers: new Map(),
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    ...options
  }),
  
  // Create mock error response
  createMockErrorResponse: (status, message, options = {}) => ({
    ok: false,
    status,
    statusText: message,
    headers: new Map(),
    json: () => Promise.resolve({ message }),
    text: () => Promise.resolve(JSON.stringify({ message })),
    ...options
  })
};

// Setup and teardown hooks for integration tests
beforeEach(() => {
  // Reset all mocks before each test
  jest.clearAllMocks();
  
  // Reset localStorage
  global.localStorage.clear();
  global.sessionStorage.clear();
  
  // Reset fetch mock
  global.fetch.mockClear();
  
  // Reset console mocks
  Object.keys(global.console).forEach(level => {
    if (typeof global.console[level].mockClear === 'function') {
      global.console[level].mockClear();
    }
  });
  
  // Reset window location
  window.location.href = 'http://localhost:3000';
  window.location.pathname = '/';
  window.location.search = '';
  window.location.hash = '';
});

afterEach(() => {
  // Clean up any remaining timers
  jest.clearAllTimers();
  
  // Clean up any event listeners
  const events = ['auth-state-change', 'auth-error', 'online', 'offline'];
  events.forEach(event => {
    window.removeAllListeners?.(event);
  });
});

// Global error handler for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Suppress specific warnings in test environment
const originalWarn = console.warn;
console.warn = (...args) => {
  const message = args[0];
  
  // Suppress known warnings that are expected in test environment
  const suppressedWarnings = [
    'Warning: ReactDOM.render is deprecated',
    'Warning: componentWillReceiveProps has been renamed',
    'Warning: componentWillMount has been renamed'
  ];
  
  if (suppressedWarnings.some(warning => message?.includes?.(warning))) {
    return;
  }
  
  originalWarn.apply(console, args);
};