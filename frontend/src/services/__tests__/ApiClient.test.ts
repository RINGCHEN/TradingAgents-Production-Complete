/**
 * ApiClient 測試套件
 * 測試API響應格式驗證、錯誤處理和重試機制
 */

import { ApiClient } from '../ApiClient';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('ApiClient', () => {
  let apiClient: ApiClient;

  beforeEach(() => {
    apiClient = new ApiClient('https://api.example.com');
    mockFetch.mockClear();
  });

  describe('JSON響應格式驗證', () => {
    it('應該正確處理有效的JSON響應', async () => {
      const mockData = { message: 'success', data: [1, 2, 3] };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockData))
      });

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(true);
      expect(response.data).toEqual(mockData);
      expect(response.status).toBe(200);
    });

    it('應該檢測並報告HTML響應錯誤', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/html' }),
        text: () => Promise.resolve('<html><body>Error Page</body></html>')
      });

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('format');
      expect(response.error?.message).toContain('HTML而非JSON');
      expect(response.isHtml).toBe(true);
    });

    it('應該處理JSON解析錯誤', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve('invalid json {')
      });

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('format');
      expect(response.error?.message).toContain('JSON解析失敗');
    });

    it('應該處理空響應', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve('')
      });

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(true);
      expect(response.data).toBe(null);
    });
  });

  describe('HTTP狀態碼處理', () => {
    it('應該正確處理404錯誤', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
        text: () => Promise.resolve('Not Found')
      });

      const response = await apiClient.get('/api/nonexistent');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('not_found');
      expect(response.error?.status).toBe(404);
      expect(response.error?.message).toContain('API端點不存在');
    });

    it('應該正確處理服務器錯誤（5xx）', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Headers(),
        text: () => Promise.resolve('Server Error')
      });

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('server');
      expect(response.error?.status).toBe(500);
      expect(response.error?.isRetryable).toBe(true);
    });

    it('應該正確處理客戶端錯誤（4xx）', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: new Headers(),
        text: () => Promise.resolve('Bad Request')
      });

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('client');
      expect(response.error?.status).toBe(400);
      expect(response.error?.isRetryable).toBe(false);
    });
  });

  describe('網路錯誤處理', () => {
    it('應該處理網路錯誤', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Failed to fetch'));

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('network');
      expect(response.error?.message).toContain('網路錯誤');
      expect(response.error?.isRetryable).toBe(true);
    });

    it('應該處理超時錯誤', async () => {
      mockFetch.mockImplementationOnce(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout after 1000ms')), 100)
        )
      );

      const response = await apiClient.get('/api/test', { timeout: 1000 });

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('timeout');
      expect(response.error?.message).toContain('請求超時');
    });

    it('應該檢測CORS錯誤', async () => {
      mockFetch.mockRejectedValueOnce(new Error('blocked by CORS policy'));

      const response = await apiClient.get('/api/test');

      expect(response.success).toBe(false);
      expect(response.error?.type).toBe('cors');
      expect(response.error?.message).toContain('CORS錯誤');
      expect(response.isCorsError).toBe(true);
    });
  });

  describe('重試機制', () => {
    it('應該在網路錯誤時重試', async () => {
      // 前兩次失敗，第三次成功
      mockFetch
        .mockRejectedValueOnce(new Error('Failed to fetch'))
        .mockRejectedValueOnce(new Error('Failed to fetch'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          text: () => Promise.resolve('{"success": true}')
        });

      const response = await apiClient.get('/api/test', { retryAttempts: 3 });

      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(response.success).toBe(true);
    });

    it('不應該在CORS錯誤時重試', async () => {
      mockFetch.mockRejectedValue(new Error('blocked by CORS policy'));

      const response = await apiClient.get('/api/test', { retryAttempts: 3 });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(response.error?.type).toBe('cors');
    });

    it('不應該在格式錯誤時重試', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/html' }),
        text: () => Promise.resolve('<html>Error</html>')
      });

      const response = await apiClient.get('/api/test', { retryAttempts: 3 });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(response.error?.type).toBe('format');
    });
  });

  describe('HTTP方法', () => {
    it('應該正確發送POST請求', async () => {
      const postData = { name: 'test', value: 123 };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve('{"created": true}')
      });

      await apiClient.post('/api/create', postData);

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/create',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('應該正確發送PUT請求', async () => {
      const putData = { id: 1, name: 'updated' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve('{"updated": true}')
      });

      await apiClient.put('/api/update/1', putData);

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/update/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData)
        })
      );
    });

    it('應該正確發送DELETE請求', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers(),
        text: () => Promise.resolve('')
      });

      await apiClient.delete('/api/delete/1');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/delete/1',
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  describe('CORS配置檢查', () => {
    it('應該檢查CORS配置', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({
          'access-control-allow-origin': '*',
          'access-control-allow-methods': 'GET, POST, PUT, DELETE'
        }),
        text: () => Promise.resolve('OK')
      });

      const result = await apiClient.checkCorsConfiguration();

      expect(result.success).toBe(true);
      expect(result.details).toBeDefined();
    });

    it('應該檢測CORS配置問題', async () => {
      mockFetch.mockRejectedValueOnce(new Error('CORS policy blocked'));

      const result = await apiClient.checkCorsConfiguration();

      expect(result.success).toBe(false);
      expect(result.details?.error).toBeDefined();
    });
  });

  describe('健康檢查', () => {
    it('應該執行健康檢查', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('OK')
      });

      const isHealthy = await apiClient.healthCheck();

      expect(isHealthy).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/health',
        expect.objectContaining({
          method: 'GET'
        })
      );
    });

    it('健康檢查失敗時應該返回false', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Health check failed'));

      const isHealthy = await apiClient.healthCheck();

      expect(isHealthy).toBe(false);
    });
  });

  describe('URL構建', () => {
    it('應該正確構建相對URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('{}')
      });

      await apiClient.get('/api/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/test',
        expect.any(Object)
      );
    });

    it('應該正確處理絕對URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('{}')
      });

      await apiClient.get('https://other-api.com/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://other-api.com/test',
        expect.any(Object)
      );
    });

    it('應該處理沒有前導斜線的端點', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('{}')
      });

      await apiClient.get('api/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/test',
        expect.any(Object)
      );
    });
  });

  describe('請求頭處理', () => {
    it('應該設置默認請求頭', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('{}')
      });

      await apiClient.get('/api/test');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          })
        })
      );
    });

    it('應該允許覆蓋請求頭', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve('{}')
      });

      await apiClient.get('/api/test', {
        headers: {
          'Authorization': 'Bearer token123',
          'Content-Type': 'application/xml'
        }
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer token123',
            'Content-Type': 'application/xml',
            'Accept': 'application/json'
          })
        })
      );
    });
  });
});