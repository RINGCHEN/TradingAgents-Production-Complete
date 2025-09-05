/**
 * ApiClient 單元測試
 * 測試API客戶端的認證處理和錯誤重試機制
 */

import axios, { AxiosError, AxiosResponse } from 'axios';
import { ApiClient } from '../../services/ApiClient';
import { TokenManager } from '../../services/TokenManager';

// Mock dependencies
jest.mock('axios');
jest.mock('../../services/TokenManager');

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ApiClient', () => {
  let apiClient: ApiClient;
  let mockTokenManager: jest.Mocked<TokenManager>;
  let mockAxiosInstance: jest.Mocked<any>;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    // Mock axios.create
    mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      patch: jest.fn(),
      interceptors: {
        request: {
          use: jest.fn(),
          eject: jest.fn()
        },
        response: {
          use: jest.fn(),
          eject: jest.fn()
        }
      },
      defaults: {
        timeout: 10000,
        baseURL: '/api'
      }
    };

    mockedAxios.create.mockReturnValue(mockAxiosInstance);

    // Mock TokenManager
    mockTokenManager = new TokenManager() as jest.Mocked<TokenManager>;
    (TokenManager as jest.Mock).mockImplementation(() => mockTokenManager);

    // Create ApiClient instance
    apiClient = new ApiClient();
  });

  describe('constructor', () => {
    it('should create axios instance with correct config', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: '/api',
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
    });

    it('should setup request and response interceptors', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('request interceptor', () => {
    let requestInterceptor: (config: any) => Promise<any>;

    beforeEach(() => {
      // Get the request interceptor function
      const interceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0];
      requestInterceptor = interceptorCall[0];
    });

    it('should add authorization header when token exists', async () => {
      // Arrange
      mockTokenManager.getValidToken.mockResolvedValue('valid-token');
      const config = { headers: {} };

      // Act
      const result = await requestInterceptor(config);

      // Assert
      expect(result.headers.Authorization).toBe('Bearer valid-token');
    });

    it('should not add authorization header when no token exists', async () => {
      // Arrange
      mockTokenManager.getValidToken.mockResolvedValue(null);
      const config = { headers: {} };

      // Act
      const result = await requestInterceptor(config);

      // Assert
      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('response interceptor', () => {
    let responseInterceptor: {
      onFulfilled: (response: any) => any;
      onRejected: (error: any) => Promise<any>;
    };

    beforeEach(() => {
      // Get the response interceptor functions
      const interceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0];
      responseInterceptor = {
        onFulfilled: interceptorCall[0],
        onRejected: interceptorCall[1]
      };
    });

    it('should pass through successful responses', () => {
      // Arrange
      const response = { data: { success: true } };

      // Act
      const result = responseInterceptor.onFulfilled(response);

      // Assert
      expect(result).toBe(response);
    });

    it('should retry request after successful token refresh on 401', async () => {
      // Arrange
      const originalRequest = {
        headers: {},
        _retry: undefined
      };

      const error = {
        response: { status: 401 },
        config: originalRequest
      } as AxiosError;

      mockTokenManager.refreshToken.mockResolvedValue(true);
      mockTokenManager.getValidToken.mockResolvedValue('new-token');
      mockAxiosInstance.mockResolvedValue({ data: 'success' });

      // Act
      const result = await responseInterceptor.onRejected(error);

      // Assert
      expect(mockTokenManager.refreshToken).toHaveBeenCalled();
      expect(originalRequest.headers.Authorization).toBe('Bearer new-token');
      expect(originalRequest._retry).toBe(true);
      expect(mockAxiosInstance).toHaveBeenCalledWith(originalRequest);
    });

    it('should not retry request if already retried', async () => {
      // Arrange
      const originalRequest = {
        headers: {},
        _retry: true // Already retried
      };

      const error = {
        response: { status: 401 },
        config: originalRequest
      } as AxiosError;

      // Act & Assert
      await expect(responseInterceptor.onRejected(error)).rejects.toMatchObject({
        isAuthError: true
      });

      expect(mockTokenManager.refreshToken).not.toHaveBeenCalled();
    });

    it('should handle auth failure when token refresh fails', async () => {
      // Arrange
      const originalRequest = {
        headers: {},
        _retry: undefined
      };

      const error = {
        response: { status: 401 },
        config: originalRequest
      } as AxiosError;

      mockTokenManager.refreshToken.mockResolvedValue(false);

      const eventListener = jest.fn();
      window.addEventListener('auth-error', eventListener);

      // Act & Assert
      await expect(responseInterceptor.onRejected(error)).rejects.toMatchObject({
        isAuthError: true
      });

      expect(eventListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: { type: 'token-refresh-failed' }
        })
      );

      // Cleanup
      window.removeEventListener('auth-error', eventListener);
    });

    it('should handle concurrent 401 errors with token refresh', async () => {
      // Arrange
      const request1 = { headers: {}, _retry: undefined };
      const request2 = { headers: {}, _retry: undefined };

      const error1 = { response: { status: 401 }, config: request1 } as AxiosError;
      const error2 = { response: { status: 401 }, config: request2 } as AxiosError;

      mockTokenManager.refreshToken.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(true), 100))
      );
      mockTokenManager.getValidToken.mockResolvedValue('new-token');
      mockAxiosInstance.mockResolvedValue({ data: 'success' });

      // Act
      const promise1 = responseInterceptor.onRejected(error1);
      const promise2 = responseInterceptor.onRejected(error2);

      await Promise.all([promise1, promise2]);

      // Assert - refresh should only be called once
      expect(mockTokenManager.refreshToken).toHaveBeenCalledTimes(1);
    });

    it('should pass through non-401 errors', async () => {
      // Arrange
      const error = {
        response: { status: 500 },
        config: {}
      } as AxiosError;

      // Act & Assert
      await expect(responseInterceptor.onRejected(error)).rejects.toMatchObject({
        status: 500,
        isNetworkError: false,
        isAuthError: false
      });
    });

    it('should handle network errors', async () => {
      // Arrange
      const error = {
        message: 'Network Error',
        config: {}
      } as AxiosError;

      // Act & Assert
      await expect(responseInterceptor.onRejected(error)).rejects.toMatchObject({
        isNetworkError: true,
        isAuthError: false
      });
    });
  });

  describe('HTTP methods', () => {
    beforeEach(() => {
      // Mock successful response for all methods
      mockAxiosInstance.get.mockResolvedValue({ data: 'get-response' });
      mockAxiosInstance.post.mockResolvedValue({ data: 'post-response' });
      mockAxiosInstance.put.mockResolvedValue({ data: 'put-response' });
      mockAxiosInstance.delete.mockResolvedValue({ data: 'delete-response' });
      mockAxiosInstance.patch.mockResolvedValue({ data: 'patch-response' });
    });

    it('should call axios get method', async () => {
      // Act
      const result = await apiClient.get('/test');

      // Assert
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', undefined);
      expect(result.data).toBe('get-response');
    });

    it('should call axios post method', async () => {
      // Arrange
      const data = { test: 'data' };

      // Act
      const result = await apiClient.post('/test', data);

      // Assert
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', data, undefined);
      expect(result.data).toBe('post-response');
    });

    it('should call axios put method', async () => {
      // Arrange
      const data = { test: 'data' };

      // Act
      const result = await apiClient.put('/test', data);

      // Assert
      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test', data, undefined);
      expect(result.data).toBe('put-response');
    });

    it('should call axios delete method', async () => {
      // Act
      const result = await apiClient.delete('/test');

      // Assert
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test', undefined);
      expect(result.data).toBe('delete-response');
    });

    it('should call axios patch method', async () => {
      // Arrange
      const data = { test: 'data' };

      // Act
      const result = await apiClient.patch('/test', data);

      // Assert
      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/test', data, undefined);
      expect(result.data).toBe('patch-response');
    });
  });

  describe('configuration methods', () => {
    it('should set timeout', () => {
      // Act
      apiClient.setTimeout(5000);

      // Assert
      expect(mockAxiosInstance.defaults.timeout).toBe(5000);
    });

    it('should set base URL', () => {
      // Act
      apiClient.setBaseURL('https://api.example.com');

      // Assert
      expect(mockAxiosInstance.defaults.baseURL).toBe('https://api.example.com');
    });
  });

  describe('interceptor management', () => {
    it('should add request interceptor', () => {
      // Arrange
      const onFulfilled = jest.fn();
      const onRejected = jest.fn();
      mockAxiosInstance.interceptors.request.use.mockReturnValue(123);

      // Act
      const interceptorId = apiClient.addRequestInterceptor(onFulfilled, onRejected);

      // Assert
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledWith(onFulfilled, onRejected);
      expect(interceptorId).toBe(123);
    });

    it('should add response interceptor', () => {
      // Arrange
      const onFulfilled = jest.fn();
      const onRejected = jest.fn();
      mockAxiosInstance.interceptors.response.use.mockReturnValue(456);

      // Act
      const interceptorId = apiClient.addResponseInterceptor(onFulfilled, onRejected);

      // Assert
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalledWith(onFulfilled, onRejected);
      expect(interceptorId).toBe(456);
    });

    it('should remove request interceptor', () => {
      // Act
      apiClient.removeInterceptor('request', 123);

      // Assert
      expect(mockAxiosInstance.interceptors.request.eject).toHaveBeenCalledWith(123);
    });

    it('should remove response interceptor', () => {
      // Act
      apiClient.removeInterceptor('response', 456);

      // Assert
      expect(mockAxiosInstance.interceptors.response.eject).toHaveBeenCalledWith(456);
    });
  });

  describe('error handling', () => {
    it('should create API error with correct properties', async () => {
      // Arrange
      const axiosError = {
        message: 'Request failed',
        response: {
          status: 400,
          data: { error: 'Bad request' }
        }
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(axiosError);

      // Act & Assert
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        message: 'Request failed',
        status: 400,
        response: { error: 'Bad request' },
        isNetworkError: false,
        isAuthError: false
      });
    });

    it('should identify network errors', async () => {
      // Arrange
      const networkError = {
        message: 'Network Error'
        // No response property indicates network error
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(networkError);

      // Act & Assert
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        isNetworkError: true,
        isAuthError: false
      });
    });

    it('should identify auth errors', async () => {
      // Arrange
      const authError = {
        message: 'Unauthorized',
        response: { status: 401 }
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(authError);

      // Act & Assert
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        isNetworkError: false,
        isAuthError: true
      });
    });
  });

  describe('request queue handling', () => {
    let responseInterceptor: {
      onFulfilled: (response: any) => any;
      onRejected: (error: any) => Promise<any>;
    };

    beforeEach(() => {
      const interceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0];
      responseInterceptor = {
        onFulfilled: interceptorCall[0],
        onRejected: interceptorCall[1]
      };
    });

    it('should queue requests during token refresh', async () => {
      // Arrange
      const request1 = { headers: {}, _retry: undefined };
      const request2 = { headers: {}, _retry: undefined };

      const error1 = { response: { status: 401 }, config: request1 } as AxiosError;
      const error2 = { response: { status: 401 }, config: request2 } as AxiosError;

      let refreshResolve: (value: boolean) => void;
      const refreshPromise = new Promise<boolean>(resolve => {
        refreshResolve = resolve;
      });

      mockTokenManager.refreshToken.mockReturnValue(refreshPromise);
      mockTokenManager.getValidToken.mockResolvedValue('new-token');
      mockAxiosInstance.mockResolvedValue({ data: 'success' });

      // Act - start both requests
      const promise1 = responseInterceptor.onRejected(error1);
      const promise2 = responseInterceptor.onRejected(error2);

      // Resolve the refresh after a delay
      setTimeout(() => refreshResolve!(true), 50);

      const results = await Promise.all([promise1, promise2]);

      // Assert
      expect(results).toEqual([{ data: 'success' }, { data: 'success' }]);
      expect(mockAxiosInstance).toHaveBeenCalledTimes(2);
    });

    it('should clear queue on auth failure', async () => {
      // Arrange
      const request1 = { headers: {}, _retry: undefined };
      const error1 = { response: { status: 401 }, config: request1 } as AxiosError;

      mockTokenManager.refreshToken.mockResolvedValue(false);

      // Act & Assert
      await expect(responseInterceptor.onRejected(error1)).rejects.toMatchObject({
        isAuthError: true
      });

      // The queue should be cleared (tested implicitly through the auth-error event)
    });
  });
});