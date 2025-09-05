/**
 * ApiClientDemo - API客戶端演示組件
 * 展示API響應格式驗證和錯誤處理功能
 */

import React, { useState, useCallback } from 'react';
import { ApiClient, ApiResponse, ApiError } from '../services/ApiClient';
import { apiErrorHandler } from '../utils/ApiErrorHandler';

interface TestResult {
  timestamp: string;
  endpoint: string;
  success: boolean;
  message: string;
  details?: any;
}

const ApiClientDemo: React.FC = () => {
  const [apiClient] = useState(() => new ApiClient('', 5000));
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addTestResult = useCallback((result: TestResult) => {
    setTestResults(prev => [result, ...prev.slice(0, 9)]); // 保留最近10條
  }, []);

  const testJsonResponse = useCallback(async () => {
    setIsLoading(true);
    try {
      // 模擬正常的JSON API響應
      const mockResponse = {
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve('{"message": "success", "data": [1, 2, 3]}')
      };
      
      // 暫時替換fetch來模擬響應
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue(mockResponse);
      
      const response = await apiClient.get('/api/test-json');
      
      // 恢復原始fetch
      global.fetch = originalFetch;
      
      addTestResult({
        timestamp: new Date().toLocaleTimeString(),
        endpoint: '/api/test-json',
        success: response.success,
        message: response.success ? '✅ JSON響應正常' : '❌ JSON響應失敗',
        details: response.data
      });
    } catch (error) {
      addTestResult({
        timestamp: new Date().toLocaleTimeString(),
        endpoint: '/api/test-json',
        success: false,
        message: '❌ 測試執行失敗',
        details: error
      });
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, addTestResult]);

  const testHtmlResponse = useCallback(async () => {
    setIsLoading(true);
    try {
      // 模擬返回HTML而非JSON的錯誤響應
      const mockResponse = {
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/html' }),
        text: () => Promise.resolve('<html><body>Error Page</body></html>')
      };
      
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue(mockResponse);
      
      const response = await apiClient.get('/api/test-html');
      
      global.fetch = originalFetch;
      
      if (!response.success && response.error?.type === 'format') {
        const strategy = apiErrorHandler.handleError(response.error);
        addTestResult({
          timestamp: new Date().toLocaleTimeString(),
          endpoint: '/api/test-html',
          success: false,
          message: '✅ HTML格式錯誤檢測正常',
          details: {
            errorType: response.error.type,
            userMessage: strategy.userMessage,
            fallbackAction: strategy.fallbackAction
          }
        });
      } else {
        addTestResult({
          timestamp: new Date().toLocaleTimeString(),
          endpoint: '/api/test-html',
          success: false,
          message: '❌ HTML格式錯誤檢測失敗',
          details: response
        });
      }
    } catch (error) {
      addTestResult({
        timestamp: new Date().toLocaleTimeString(),
        endpoint: '/api/test-html',
        success: false,
        message: '❌ 測試執行失敗',
        details: error
      });
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, addTestResult]);

  const testNetworkError = useCallback(async () => {
    setIsLoading(true);
    try {
      // 模擬網路錯誤
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockRejectedValue(new Error('Failed to fetch'));
      
      const response = await apiClient.get('/api/test-network');
      
      global.fetch = originalFetch;
      
      if (!response.success && response.error?.type === 'network') {
        const strategy = apiErrorHandler.handleError(response.error);
        addTestResult({
          timestamp: new Date().toLocaleTimeString(),
          endpoint: '/api/test-network',
          success: false,
          message: '✅ 網路錯誤處理正常',
          details: {
            errorType: response.error.type,
            shouldRetry: strategy.shouldRetry,
            retryDelay: strategy.retryDelay
          }
        });
      } else {
        addTestResult({
          timestamp: new Date().toLocaleTimeString(),
          endpoint: '/api/test-network',
          success: false,
          message: '❌ 網路錯誤處理失敗',
          details: response
        });
      }
    } catch (error) {
      addTestResult({
        timestamp: new Date().toLocaleTimeString(),
        endpoint: '/api/test-network',
        success: false,
        message: '❌ 測試執行失敗',
        details: error
      });
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, addTestResult]);

  const test404Error = useCallback(async () => {
    setIsLoading(true);
    try {
      // 模擬404錯誤
      const mockResponse = {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
        text: () => Promise.resolve('Not Found')
      };
      
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue(mockResponse);
      
      const response = await apiClient.get('/api/test-404');
      
      global.fetch = originalFetch;
      
      if (!response.success && response.error?.type === 'not_found') {
        const strategy = apiErrorHandler.handleError(response.error);
        addTestResult({
          timestamp: new Date().toLocaleTimeString(),
          endpoint: '/api/test-404',
          success: false,
          message: '✅ 404錯誤處理正常',
          details: {
            errorType: response.error.type,
            status: response.error.status,
            userMessage: strategy.userMessage
          }
        });
      } else {
        addTestResult({
          timestamp: new Date().toLocaleTimeString(),
          endpoint: '/api/test-404',
          success: false,
          message: '❌ 404錯誤處理失敗',
          details: response
        });
      }
    } catch (error) {
      addTestResult({
        timestamp: new Date().toLocaleTimeString(),
        endpoint: '/api/test-404',
        success: false,
        message: '❌ 測試執行失敗',
        details: error
      });
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, addTestResult]);

  const clearResults = useCallback(() => {
    setTestResults([]);
    apiErrorHandler.clearErrorLog();
  }, []);

  const getErrorStatistics = useCallback(() => {
    const stats = apiErrorHandler.getErrorStatistics();
    addTestResult({
      timestamp: new Date().toLocaleTimeString(),
      endpoint: 'system',
      success: true,
      message: '📊 錯誤統計',
      details: stats
    });
  }, [addTestResult]);

  return (
    <div className="api-client-demo p-6 bg-white rounded-lg shadow-lg max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">
        API客戶端演示 - 響應格式驗證與錯誤處理
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold mb-3 text-gray-700">測試功能</h3>
          <div className="space-y-2">
            <button
              onClick={testJsonResponse}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 transition-colors"
            >
              測試正常JSON響應
            </button>
            <button
              onClick={testHtmlResponse}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:bg-gray-400 transition-colors"
            >
              測試HTML格式錯誤
            </button>
            <button
              onClick={testNetworkError}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400 transition-colors"
            >
              測試網路錯誤
            </button>
            <button
              onClick={test404Error}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
            >
              測試404錯誤
            </button>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold mb-3 text-gray-700">系統功能</h3>
          <div className="space-y-2">
            <button
              onClick={getErrorStatistics}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              獲取錯誤統計
            </button>
            <button
              onClick={clearResults}
              disabled={isLoading}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:bg-gray-400 transition-colors"
            >
              清除測試結果
            </button>
          </div>
          
          {isLoading && (
            <div className="mt-3 text-center text-blue-600">
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="ml-2">測試中...</span>
            </div>
          )}
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold mb-3 text-gray-700">測試結果 (最近10條)</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {testResults.length === 0 ? (
            <div className="text-gray-500 text-sm">暫無測試結果</div>
          ) : (
            testResults.map((result, index) => (
              <div
                key={index}
                className={`p-3 rounded border-l-4 ${
                  result.success 
                    ? 'bg-green-50 border-green-400' 
                    : result.message.includes('✅')
                    ? 'bg-blue-50 border-blue-400'
                    : 'bg-red-50 border-red-400'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="font-medium text-sm">{result.message}</span>
                  <span className="text-xs text-gray-500">{result.timestamp}</span>
                </div>
                <div className="text-xs text-gray-600 mb-1">
                  端點: {result.endpoint}
                </div>
                {result.details && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                      詳細信息
                    </summary>
                    <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                      {JSON.stringify(result.details, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="mt-6 text-sm text-gray-600">
        <h4 className="font-semibold mb-2">功能說明:</h4>
        <ul className="space-y-1 list-disc list-inside">
          <li>自動檢測API響應格式，確保返回JSON而非HTML</li>
          <li>智能錯誤分類和處理策略</li>
          <li>網路錯誤自動重試機制</li>
          <li>CORS配置問題檢測</li>
          <li>完整的錯誤統計和分析</li>
        </ul>
      </div>
    </div>
  );
};

export default ApiClientDemo;