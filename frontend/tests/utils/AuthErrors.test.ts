/**
 * AuthErrors 單元測試
 * 測試認證錯誤處理工具的錯誤分類和用戶友好消息生成
 */

import { 
  handleAuthError, 
  AuthErrorType, 
  getErrorMessage, 
  isRetryableError,
  getErrorSeverity,
  logAuthError
} from '../../utils/AuthErrors';
import { AuthError } from '../../services/AuthService';

// Mock console methods
jest.spyOn(console, 'error').mockImplementation(() => {});
jest.spyOn(console, 'warn').mockImplementation(() => {});
jest.spyOn(console, 'log').mockImplementation(() => {});

describe('AuthErrors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('handleAuthError', () => {
    it('should handle network errors', () => {
      // Arrange
      const networkError = new Error('Network Error');
      (networkError as any).code = 'NETWORK_ERROR';

      // Act
      const result = handleAuthError(networkError, 'login');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('網絡連接失敗');
      expect((result as any).type).toBe('network-error');
      expect((result as any).context).toBe('login');
    });

    it('should handle 401 unauthorized errors', () => {
      // Arrange
      const unauthorizedError = {
        response: { status: 401, data: { message: 'Unauthorized' } }
      };

      // Act
      const result = handleAuthError(unauthorizedError, 'api-call');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('認證已過期');
      expect((result as any).type).toBe('unauthorized');
    });

    it('should handle 403 forbidden errors', () => {
      // Arrange
      const forbiddenError = {
        response: { status: 403, data: { message: 'Forbidden' } }
      };

      // Act
      const result = handleAuthError(forbiddenError, 'admin-action');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('權限不足');
      expect((result as any).type).toBe('forbidden');
    });

    it('should handle 429 rate limit errors', () => {
      // Arrange
      const rateLimitError = {
        response: { 
          status: 429, 
          headers: { 'retry-after': '60' },
          data: { message: 'Too Many Requests' } 
        }
      };

      // Act
      const result = handleAuthError(rateLimitError, 'login');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('請求過於頻繁');
      expect((result as any).type).toBe('rate-limit');
      expect((result as any).retryAfter).toBe(60);
    });

    it('should handle 500 server errors', () => {
      // Arrange
      const serverError = {
        response: { status: 500, data: { message: 'Internal Server Error' } }
      };

      // Act
      const result = handleAuthError(serverError, 'refresh-token');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('服務器錯誤');
      expect((result as any).type).toBe('server-error');
    });

    it('should handle timeout errors', () => {
      // Arrange
      const timeoutError = new Error('timeout of 10000ms exceeded');
      (timeoutError as any).code = 'ECONNABORTED';

      // Act
      const result = handleAuthError(timeoutError, 'login');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('請求超時');
      expect((result as any).type).toBe('timeout');
    });

    it('should handle validation errors', () => {
      // Arrange
      const validationError = {
        response: { 
          status: 400, 
          data: { 
            message: 'Validation failed',
            errors: {
              username: ['用戶名不能為空'],
              password: ['密碼長度至少8位']
            }
          } 
        }
      };

      // Act
      const result = handleAuthError(validationError, 'login');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('輸入驗證失敗');
      expect((result as any).type).toBe('validation-error');
      expect((result as any).validationErrors).toEqual({
        username: ['用戶名不能為空'],
        password: ['密碼長度至少8位']
      });
    });

    it('should handle already existing AuthError instances', () => {
      // Arrange
      const existingAuthError = new AuthError('Existing error');
      (existingAuthError as any).type = 'custom-error';

      // Act
      const result = handleAuthError(existingAuthError, 'test');

      // Assert
      expect(result).toBe(existingAuthError);
      expect((result as any).context).toBe('test');
    });

    it('should handle unknown errors with generic message', () => {
      // Arrange
      const unknownError = { weird: 'error object' };

      // Act
      const result = handleAuthError(unknownError, 'unknown-operation');

      // Assert
      expect(result).toBeInstanceOf(AuthError);
      expect(result.message).toContain('未知錯誤');
      expect((result as any).type).toBe('unknown');
    });

    it('should preserve original error information', () => {
      // Arrange
      const originalError = new Error('Original message');
      (originalError as any).stack = 'Error stack trace';

      // Act
      const result = handleAuthError(originalError, 'test');

      // Assert
      expect(result.originalError).toBe(originalError);
      expect((result as any).originalStack).toBe('Error stack trace');
    });
  });

  describe('getErrorMessage', () => {
    it('should return correct messages for different error types', () => {
      const testCases: Array<[AuthErrorType, string]> = [
        ['network-error', '網絡連接失敗'],
        ['unauthorized', '認證已過期'],
        ['forbidden', '權限不足'],
        ['rate-limit', '請求過於頻繁'],
        ['server-error', '服務器錯誤'],
        ['timeout', '請求超時'],
        ['validation-error', '輸入驗證失敗'],
        ['token-expired', 'Token已過期'],
        ['token-invalid', 'Token無效'],
        ['login-failed', '登錄失敗'],
        ['logout-failed', '登出失敗'],
        ['refresh-failed', 'Token刷新失敗'],
        ['unknown', '未知錯誤']
      ];

      testCases.forEach(([type, expectedMessage]) => {
        const message = getErrorMessage(type);
        expect(message).toContain(expectedMessage);
      });
    });

    it('should return generic message for invalid error type', () => {
      // Act
      const message = getErrorMessage('invalid-type' as AuthErrorType);

      // Assert
      expect(message).toContain('未知錯誤');
    });
  });

  describe('isRetryableError', () => {
    it('should identify retryable errors correctly', () => {
      const retryableTypes: AuthErrorType[] = [
        'network-error',
        'timeout',
        'server-error',
        'rate-limit'
      ];

      const nonRetryableTypes: AuthErrorType[] = [
        'unauthorized',
        'forbidden',
        'validation-error',
        'token-invalid',
        'login-failed'
      ];

      retryableTypes.forEach(type => {
        expect(isRetryableError(type)).toBe(true);
      });

      nonRetryableTypes.forEach(type => {
        expect(isRetryableError(type)).toBe(false);
      });
    });
  });

  describe('getErrorSeverity', () => {
    it('should return correct severity levels', () => {
      const testCases: Array<[AuthErrorType, 'low' | 'medium' | 'high' | 'critical']> = [
        ['network-error', 'medium'],
        ['unauthorized', 'high'],
        ['forbidden', 'high'],
        ['rate-limit', 'medium'],
        ['server-error', 'high'],
        ['timeout', 'medium'],
        ['validation-error', 'low'],
        ['token-expired', 'medium'],
        ['token-invalid', 'high'],
        ['login-failed', 'medium'],
        ['logout-failed', 'low'],
        ['refresh-failed', 'high'],
        ['unknown', 'medium']
      ];

      testCases.forEach(([type, expectedSeverity]) => {
        const severity = getErrorSeverity(type);
        expect(severity).toBe(expectedSeverity);
      });
    });
  });

  describe('logAuthError', () => {
    it('should log errors with appropriate level based on severity', () => {
      // Arrange
      const error = new AuthError('Test error');
      (error as any).type = 'unauthorized';
      (error as any).context = 'login';

      // Act
      logAuthError(error);

      // Assert
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Auth Error [unauthorized]'),
        expect.objectContaining({
          message: 'Test error',
          type: 'unauthorized',
          context: 'login'
        })
      );
    });

    it('should log medium severity errors as warnings', () => {
      // Arrange
      const error = new AuthError('Network error');
      (error as any).type = 'network-error';
      (error as any).context = 'api-call';

      // Act
      logAuthError(error);

      // Assert
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('Auth Error [network-error]'),
        expect.any(Object)
      );
    });

    it('should log low severity errors as info', () => {
      // Arrange
      const error = new AuthError('Validation error');
      (error as any).type = 'validation-error';
      (error as any).context = 'form-submit';

      // Act
      logAuthError(error);

      // Assert
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Auth Error [validation-error]'),
        expect.any(Object)
      );
    });

    it('should include additional error details in log', () => {
      // Arrange
      const error = new AuthError('Rate limit error');
      (error as any).type = 'rate-limit';
      (error as any).context = 'login';
      (error as any).retryAfter = 60;
      (error as any).validationErrors = { field: ['error'] };

      // Act
      logAuthError(error);

      // Assert
      expect(console.warn).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          retryAfter: 60,
          validationErrors: { field: ['error'] }
        })
      );
    });
  });

  describe('error context handling', () => {
    it('should provide context-specific error messages', () => {
      // Arrange
      const contexts = ['login', 'logout', 'refresh-token', 'api-call', 'initialization'];

      contexts.forEach(context => {
        const error = {
          response: { status: 401 }
        };

        // Act
        const result = handleAuthError(error, context);

        // Assert
        expect((result as any).context).toBe(context);
        expect(result.message).toBeDefined();
      });
    });

    it('should handle missing context gracefully', () => {
      // Arrange
      const error = new Error('Test error');

      // Act
      const result = handleAuthError(error);

      // Assert
      expect((result as any).context).toBe('unknown');
    });
  });

  describe('error recovery suggestions', () => {
    it('should provide recovery suggestions for different error types', () => {
      // Arrange
      const testCases: Array<[any, string[]]> = [
        [
          { response: { status: 401 } },
          ['請重新登錄', '檢查認證狀態']
        ],
        [
          { response: { status: 403 } },
          ['聯繫管理員獲取權限', '檢查用戶角色']
        ],
        [
          { code: 'NETWORK_ERROR' },
          ['檢查網絡連接', '稍後重試']
        ],
        [
          { response: { status: 429 } },
          ['稍後重試', '減少請求頻率']
        ]
      ];

      testCases.forEach(([errorInput, expectedSuggestions]) => {
        // Act
        const result = handleAuthError(errorInput, 'test');

        // Assert
        expect((result as any).recoverySuggestions).toEqual(
          expect.arrayContaining(expectedSuggestions)
        );
      });
    });
  });

  describe('error metadata', () => {
    it('should include timestamp in error metadata', () => {
      // Arrange
      const error = new Error('Test error');
      const beforeTime = Date.now();

      // Act
      const result = handleAuthError(error, 'test');

      // Assert
      const afterTime = Date.now();
      expect((result as any).timestamp).toBeGreaterThanOrEqual(beforeTime);
      expect((result as any).timestamp).toBeLessThanOrEqual(afterTime);
    });

    it('should include user agent information', () => {
      // Arrange
      const originalUserAgent = navigator.userAgent;
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Test User Agent',
        configurable: true
      });

      const error = new Error('Test error');

      // Act
      const result = handleAuthError(error, 'test');

      // Assert
      expect((result as any).userAgent).toBe('Test User Agent');

      // Cleanup
      Object.defineProperty(navigator, 'userAgent', {
        value: originalUserAgent,
        configurable: true
      });
    });

    it('should include request ID if available', () => {
      // Arrange
      const error = {
        response: {
          status: 500,
          headers: {
            'x-request-id': 'req-123456'
          }
        }
      };

      // Act
      const result = handleAuthError(error, 'api-call');

      // Assert
      expect((result as any).requestId).toBe('req-123456');
    });
  });
});