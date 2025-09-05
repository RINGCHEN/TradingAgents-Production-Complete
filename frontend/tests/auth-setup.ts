/**
 * Authentication Test Setup
 * 認證測試的全局設置和配置
 */

import '@testing-library/jest-dom';
import 'jest-localstorage-mock';

// Mock console methods to reduce noise in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleLog = console.log;

beforeAll(() => {
  // Mock console methods but allow important messages through
  console.error = jest.fn((message, ...args) => {
    // Allow through actual test failures and important errors
    if (typeof message === 'string' && (
      message.includes('Error:') ||
      message.includes('Failed') ||
      message.includes('Warning:')
    )) {
      originalConsoleError(message, ...args);
    }
  });

  console.warn = jest.fn((message, ...args) => {
    // Allow through important warnings
    if (typeof message === 'string' && message.includes('Warning:')) {
      originalConsoleWarn(message, ...args);
    }
  });

  console.log = jest.fn((message, ...args) => {
    // Suppress most console.log calls in tests
    if (process.env.DEBUG_TESTS === 'true') {
      originalConsoleLog(message, ...args);
    }
  });
});

afterAll(() => {
  // Restore original console methods
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
  console.log = originalConsoleLog;
});

// Global test setup
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  
  // Clear localStorage
  localStorage.clear();
  sessionStorage.clear();
  
  // Reset fetch mock
  if (global.fetch) {
    (global.fetch as jest.Mock).mockClear();
  }
  
  // Clear any existing timers
  jest.clearAllTimers();
  
  // Reset DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
});

afterEach(() => {
  // Clean up any remaining timers
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
  
  // Clean up any event listeners
  window.removeAllListeners?.();
  
  // Clear any remaining mocks
  jest.restoreAllMocks();
});

// Mock global objects and APIs
Object.defineProperty(window, 'location', {
  value: {
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
  },
  writable: true
});

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

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByType: jest.fn(() => []),
    getEntriesByName: jest.fn(() => []),
    clearMarks: jest.fn(),
    clearMeasures: jest.fn(),
    memory: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000
    }
  },
  writable: true
});

// Mock crypto API for secure random generation
Object.defineProperty(window, 'crypto', {
  value: {
    getRandomValues: jest.fn((arr: any) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }),
    randomUUID: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9))
  },
  writable: true
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock fetch globally
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    headers: new Headers(),
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    clone: jest.fn()
  } as Response)
);

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor(url: string) {}
  close() {}
  send() {}
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true; }
  
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  
  readyState = WebSocket.CONNECTING;
  url = '';
  protocol = '';
  extensions = '';
  bufferedAmount = 0;
  binaryType: BinaryType = 'blob';
  
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
};

// Mock File and FileReader
global.File = class File {
  constructor(
    public bits: BlobPart[],
    public name: string,
    public options?: FilePropertyBag
  ) {}
  
  size = 0;
  type = '';
  lastModified = Date.now();
  
  arrayBuffer(): Promise<ArrayBuffer> {
    return Promise.resolve(new ArrayBuffer(0));
  }
  
  slice(): Blob {
    return new Blob();
  }
  
  stream(): ReadableStream {
    return new ReadableStream();
  }
  
  text(): Promise<string> {
    return Promise.resolve('');
  }
};

global.FileReader = class FileReader {
  result: string | ArrayBuffer | null = null;
  error: DOMException | null = null;
  readyState = 0;
  
  onabort: ((event: ProgressEvent) => void) | null = null;
  onerror: ((event: ProgressEvent) => void) | null = null;
  onload: ((event: ProgressEvent) => void) | null = null;
  onloadend: ((event: ProgressEvent) => void) | null = null;
  onloadstart: ((event: ProgressEvent) => void) | null = null;
  onprogress: ((event: ProgressEvent) => void) | null = null;
  
  abort() {}
  readAsArrayBuffer(file: Blob) {}
  readAsBinaryString(file: Blob) {}
  readAsDataURL(file: Blob) {}
  readAsText(file: Blob, encoding?: string) {}
  
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true; }
  
  static EMPTY = 0;
  static LOADING = 1;
  static DONE = 2;
};

// Mock URL
global.URL = class URL {
  constructor(public href: string, base?: string) {}
  
  hash = '';
  host = '';
  hostname = '';
  origin = '';
  pathname = '';
  port = '';
  protocol = '';
  search = '';
  searchParams = new URLSearchParams();
  username = '';
  password = '';
  
  toString() {
    return this.href;
  }
  
  toJSON() {
    return this.href;
  }
  
  static createObjectURL(object: any): string {
    return 'mock-object-url';
  }
  
  static revokeObjectURL(url: string): void {}
};

// Mock Blob
global.Blob = class Blob {
  constructor(
    public blobParts?: BlobPart[],
    public options?: BlobPropertyBag
  ) {}
  
  size = 0;
  type = '';
  
  arrayBuffer(): Promise<ArrayBuffer> {
    return Promise.resolve(new ArrayBuffer(0));
  }
  
  slice(): Blob {
    return new Blob();
  }
  
  stream(): ReadableStream {
    return new ReadableStream();
  }
  
  text(): Promise<string> {
    return Promise.resolve('');
  }
};

// Authentication-specific test utilities
export const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  permissions: ['read', 'write'],
  is_admin: true,
  is_active: true,
  ...overrides
});

export const createMockTokens = (overrides = {}) => ({
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'Bearer',
  expires_in: 3600,
  expires_at: Date.now() + 3600000,
  ...overrides
});

export const createMockApiResponse = (data: any, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  statusText: status === 200 ? 'OK' : 'Error',
  headers: new Headers(),
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
  clone: jest.fn()
});

// Test helpers for async operations
export const waitForAsync = (ms = 0) => new Promise(resolve => setTimeout(resolve, ms));

export const flushPromises = () => new Promise(resolve => setImmediate(resolve));

// Mock storage events for cross-tab testing
export const triggerStorageEvent = (key: string, newValue: string | null, oldValue: string | null = null) => {
  const event = new StorageEvent('storage', {
    key,
    newValue,
    oldValue,
    storageArea: localStorage
  });
  window.dispatchEvent(event);
};

// Mock visibility change events
export const triggerVisibilityChange = (hidden: boolean) => {
  Object.defineProperty(document, 'hidden', {
    value: hidden,
    writable: true
  });
  
  Object.defineProperty(document, 'visibilityState', {
    value: hidden ? 'hidden' : 'visible',
    writable: true
  });
  
  document.dispatchEvent(new Event('visibilitychange'));
};

// Mock network conditions
export const mockNetworkError = () => {
  (global.fetch as jest.Mock).mockRejectedValue(new Error('Network Error'));
};

export const mockApiError = (status: number, message: string) => {
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: false,
    status,
    statusText: message,
    json: () => Promise.resolve({ message })
  });
};

// Performance testing utilities
export const measurePerformance = async (fn: () => Promise<any>): Promise<number> => {
  const start = performance.now();
  await fn();
  const end = performance.now();
  return end - start;
};

// Memory testing utilities
export const getMemoryUsage = (): number => {
  if (typeof (performance as any).memory !== 'undefined') {
    return (performance as any).memory.usedJSHeapSize;
  }
  return 0;
};

// Cleanup utilities
export const cleanupTestEnvironment = () => {
  // Clear all storage
  localStorage.clear();
  sessionStorage.clear();
  
  // Clear all timers
  jest.clearAllTimers();
  
  // Clear DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
  
  // Clear all mocks
  jest.clearAllMocks();
  
  // Reset fetch mock
  if (global.fetch) {
    (global.fetch as jest.Mock).mockClear();
  }
};

// Export test configuration
export const testConfig = {
  timeout: 30000,
  retries: 2,
  verbose: process.env.DEBUG_TESTS === 'true'
};