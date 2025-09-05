/**
 * ApiErrorHandler 測試套件
 * 測試API錯誤分類、處理策略和錯誤統計
 */

import { ApiErrorHandler, apiErrorHandler } from '../ApiErrorHandler';
import { ApiError } from '../../services/ApiClient';

describe('ApiErrorHandler', () => {
  let errorHandler: ApiErrorHandler;

  beforeEach(() => {
    errorHandler = new ApiErrorHandler();
  });

  describe('錯誤分類和處理策略', () => {
    it('應該正確處理格式錯誤（HTML響應）', () => {
      const error: ApiError = {
        type: 'format',
        status: 200,
        message: 'API返回HTML而非JSON',
        endpoint: '/api/test',
        timestamp: new Date(),
        details: {
          contentType: 'text/html',
          expectedType: 'application/json'
        }
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(false);
      expect(strategy.fallbackAction).toBe('cache');
      expect(strategy.userMessage).toContain('服務暫時不可用');
      expect(strategy.severity).toBe('high');
    });

    it('應該正確處理網路錯誤', () => {
      const error: ApiError = {
        type: 'network',
        message: '網路連接失敗',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(true);
      expect(strategy.retryDelay).toBe(2000);
      expect(strategy.maxRetries).toBe(3);
      expect(strategy.fallbackAction).toBe('offline');
      expect(strategy.userMessage).toContain('網路連接問題');
      expect(strategy.severity).toBe('medium');
    });

    it('應該正確處理超時錯誤', () => {
      const error: ApiError = {
        type: 'timeout',
        message: '請求超時',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(true);
      expect(strategy.retryDelay).toBe(3000);
      expect(strategy.maxRetries).toBe(2);
      expect(strategy.fallbackAction).toBe('cache');
      expect(strategy.userMessage).toContain('請求超時');
    });

    it('應該正確處理CORS錯誤', () => {
      const error: ApiError = {
        type: 'cors',
        message: 'CORS policy blocked',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(false);
      expect(strategy.fallbackAction).toBe('minimal');
      expect(strategy.userMessage).toContain('服務配置問題');
      expect(strategy.severity).toBe('critical');
    });

    it('應該正確處理404錯誤', () => {
      const error: ApiError = {
        type: 'not_found',
        status: 404,
        message: 'API端點不存在',
        endpoint: '/api/nonexistent',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(false);
      expect(strategy.fallbackAction).toBe('minimal');
      expect(strategy.userMessage).toContain('請求的資源不存在');
      expect(strategy.severity).toBe('medium');
    });

    it('應該正確處理服務器錯誤', () => {
      const error: ApiError = {
        type: 'server',
        status: 500,
        message: '內部服務器錯誤',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(true);
      expect(strategy.maxRetries).toBe(3);
      expect(strategy.fallbackAction).toBe('cache');
      expect(strategy.userMessage).toContain('服務器暫時不可用');
      expect(strategy.severity).toBe('high');
    });

    it('應該正確處理401認證錯誤', () => {
      const error: ApiError = {
        type: 'client',
        status: 401,
        message: '未授權',
        endpoint: '/api/protected',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(false);
      expect(strategy.fallbackAction).toBe('none');
      expect(strategy.userMessage).toContain('請重新登錄');
      expect(strategy.severity).toBe('medium');
    });

    it('應該正確處理403權限錯誤', () => {
      const error: ApiError = {
        type: 'client',
        status: 403,
        message: '禁止訪問',
        endpoint: '/api/admin',
        timestamp: new Date()
      };

      const strategy = errorHandler.handleError(error);

      expect(strategy.shouldRetry).toBe(false);
      expect(strategy.fallbackAction).toBe('minimal');
      expect(strategy.userMessage).toContain('沒有權限訪問');
      expect(strategy.severity).toBe('medium');
    });
  });

  describe('錯誤日誌和統計', () => {
    it('應該記錄錯誤到日誌', () => {
      const error: ApiError = {
        type: 'network',
        message: '網路錯誤',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      errorHandler.handleError(error);

      const recentErrors = errorHandler.getRecentErrors(1);
      expect(recentErrors).toHaveLength(1);
      expect(recentErrors[0].type).toBe('network');
    });

    it('應該生成錯誤統計', () => {
      const errors: ApiError[] = [
        {
          type: 'network',
          message: '網路錯誤1',
          endpoint: '/api/test1',
          timestamp: new Date()
        },
        {
          type: 'network',
          message: '網路錯誤2',
          endpoint: '/api/test2',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤',
          endpoint: '/api/test1',
          timestamp: new Date()
        }
      ];

      errors.forEach(error => errorHandler.handleError(error));

      const stats = errorHandler.getErrorStatistics();
      expect(stats.totalErrors).toBe(3);
      expect(stats.errorsByType.network).toBe(2);
      expect(stats.errorsByType.format).toBe(1);
      expect(stats.errorsByEndpoint['/api/test1']).toBe(2);
      expect(stats.errorsByEndpoint['/api/test2']).toBe(1);
    });

    it('應該限制日誌大小', () => {
      // 創建一個小的日誌大小限制的處理器
      const smallHandler = new (class extends ApiErrorHandler {
        constructor() {
          super();
          (this as any).maxLogSize = 2;
        }
      })();

      const errors: ApiError[] = [
        {
          type: 'network',
          message: '錯誤1',
          endpoint: '/api/test1',
          timestamp: new Date()
        },
        {
          type: 'network',
          message: '錯誤2',
          endpoint: '/api/test2',
          timestamp: new Date()
        },
        {
          type: 'network',
          message: '錯誤3',
          endpoint: '/api/test3',
          timestamp: new Date()
        }
      ];

      errors.forEach(error => smallHandler.handleError(error));

      const recentErrors = smallHandler.getRecentErrors(10);
      expect(recentErrors).toHaveLength(2);
      expect(recentErrors[0].message).toBe('錯誤3'); // 最新的錯誤
      expect(recentErrors[1].message).toBe('錯誤2');
    });

    it('應該檢測嚴重錯誤', () => {
      const corsError: ApiError = {
        type: 'cors',
        message: 'CORS錯誤',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      errorHandler.handleError(corsError);

      expect(errorHandler.hasCriticalErrors()).toBe(true);
    });

    it('應該清除錯誤日誌', () => {
      const error: ApiError = {
        type: 'network',
        message: '網路錯誤',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      errorHandler.handleError(error);
      expect(errorHandler.getErrorStatistics().totalErrors).toBe(1);

      errorHandler.clearErrorLog();
      expect(errorHandler.getErrorStatistics().totalErrors).toBe(0);
    });
  });

  describe('錯誤報告生成', () => {
    it('應該生成完整的錯誤報告', () => {
      const errors: ApiError[] = [
        {
          type: 'cors',
          message: 'CORS錯誤',
          endpoint: '/api/test1',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤1',
          endpoint: '/api/test2',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤2',
          endpoint: '/api/test3',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤3',
          endpoint: '/api/test4',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤4',
          endpoint: '/api/test5',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤5',
          endpoint: '/api/test6',
          timestamp: new Date()
        },
        {
          type: 'format',
          message: '格式錯誤6',
          endpoint: '/api/test7',
          timestamp: new Date()
        }
      ];

      errors.forEach(error => errorHandler.handleError(error));

      const report = errorHandler.generateErrorReport();

      expect(report.summary).toContain('總錯誤數: 7');
      expect(report.criticalIssues).toContain('檢測到CORS配置問題');
      expect(report.criticalIssues).toContain('頻繁的格式錯誤');
      expect(report.recommendations).toContain('檢查服務器CORS配置');
      expect(report.recommendations).toContain('檢查API路由配置，確保返回JSON格式');
    });

    it('應該根據錯誤模式生成建議', () => {
      // 添加多個網路錯誤
      for (let i = 0; i < 15; i++) {
        const error: ApiError = {
          type: 'network',
          message: `網路錯誤${i}`,
          endpoint: `/api/test${i}`,
          timestamp: new Date()
        };
        errorHandler.handleError(error);
      }

      const report = errorHandler.generateErrorReport();
      expect(report.recommendations).toContain('檢查網路連接穩定性');
    });

    it('應該檢測服務器錯誤模式', () => {
      // 添加多個服務器錯誤
      for (let i = 0; i < 8; i++) {
        const error: ApiError = {
          type: 'server',
          status: 500,
          message: `服務器錯誤${i}`,
          endpoint: `/api/test${i}`,
          timestamp: new Date()
        };
        errorHandler.handleError(error);
      }

      const report = errorHandler.generateErrorReport();
      expect(report.criticalIssues).toContain('服務器錯誤頻繁');
      expect(report.recommendations).toContain('檢查後端服務狀態');
    });
  });

  describe('重試策略', () => {
    it('應該為服務器錯誤實施指數退避', () => {
      const endpoint = '/api/test';
      
      // 第一次錯誤
      const error1: ApiError = {
        type: 'server',
        status: 500,
        message: '服務器錯誤',
        endpoint,
        timestamp: new Date()
      };
      const strategy1 = errorHandler.handleError(error1);
      expect(strategy1.retryDelay).toBe(1000);

      // 第二次錯誤（同一端點）
      const error2: ApiError = {
        type: 'server',
        status: 500,
        message: '服務器錯誤',
        endpoint,
        timestamp: new Date()
      };
      const strategy2 = errorHandler.handleError(error2);
      expect(strategy2.retryDelay).toBe(2000);

      // 第三次錯誤（同一端點）
      const error3: ApiError = {
        type: 'server',
        status: 500,
        message: '服務器錯誤',
        endpoint,
        timestamp: new Date()
      };
      const strategy3 = errorHandler.handleError(error3);
      expect(strategy3.retryDelay).toBe(4000);
    });

    it('應該在達到最大重試次數後停止重試', () => {
      const endpoint = '/api/test';
      
      // 添加多個服務器錯誤
      for (let i = 0; i < 5; i++) {
        const error: ApiError = {
          type: 'server',
          status: 500,
          message: '服務器錯誤',
          endpoint,
          timestamp: new Date()
        };
        errorHandler.handleError(error);
      }

      // 第6次錯誤應該不再重試
      const error: ApiError = {
        type: 'server',
        status: 500,
        message: '服務器錯誤',
        endpoint,
        timestamp: new Date()
      };
      const strategy = errorHandler.handleError(error);
      expect(strategy.shouldRetry).toBe(false);
    });
  });

  describe('全局錯誤處理器', () => {
    it('應該提供全局實例', () => {
      expect(apiErrorHandler).toBeInstanceOf(ApiErrorHandler);
    });

    it('全局實例應該正常工作', () => {
      const error: ApiError = {
        type: 'network',
        message: '測試錯誤',
        endpoint: '/api/test',
        timestamp: new Date()
      };

      const strategy = apiErrorHandler.handleError(error);
      expect(strategy).toBeDefined();
      expect(strategy.userMessage).toBeDefined();
    });
  });
});