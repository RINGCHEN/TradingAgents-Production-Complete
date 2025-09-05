/**
 * CORS調試工具
 * 用於診斷和修復CORS相關問題
 */

export interface CorsTestResult {
  success: boolean;
  error?: string;
  details: {
    method: string;
    url: string;
    status?: number;
    headers?: Record<string, string>;
    corsHeaders?: Record<string, string>;
    timestamp: string;
  };
}

export class CorsDebugger {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  /**
   * 測試CORS配置
   */
  async testCorsConfiguration(): Promise<CorsTestResult> {
    const testUrl = `${this.baseUrl}/cors-test`;
    const timestamp = new Date().toISOString();

    try {
      const response = await fetch(testUrl, {
        method: 'GET',
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CORS-Test': 'true'
        }
      });

      const responseHeaders = this.extractHeaders(response.headers);
      const corsHeaders = this.extractCorsHeaders(response.headers);

      const result: CorsTestResult = {
        success: response.ok,
        details: {
          method: 'GET',
          url: testUrl,
          status: response.status,
          headers: responseHeaders,
          corsHeaders,
          timestamp
        }
      };

      if (!response.ok) {
        result.error = `HTTP ${response.status}: ${response.statusText}`;
      }

      return result;

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        details: {
          method: 'GET',
          url: testUrl,
          timestamp
        }
      };
    }
  }

  /**
   * 測試OPTIONS預檢請求
   */
  async testPreflightRequest(): Promise<CorsTestResult> {
    const testUrl = `${this.baseUrl}/cors-test`;
    const timestamp = new Date().toISOString();

    try {
      const response = await fetch(testUrl, {
        method: 'OPTIONS',
        mode: 'cors',
        headers: {
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
      });

      const responseHeaders = this.extractHeaders(response.headers);
      const corsHeaders = this.extractCorsHeaders(response.headers);

      return {
        success: response.ok,
        details: {
          method: 'OPTIONS',
          url: testUrl,
          status: response.status,
          headers: responseHeaders,
          corsHeaders,
          timestamp
        }
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        details: {
          method: 'OPTIONS',
          url: testUrl,
          timestamp
        }
      };
    }
  }

  /**
   * 測試API端點可達性
   */
  async testApiEndpoint(endpoint: string): Promise<CorsTestResult> {
    const testUrl = `${this.baseUrl}/api${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    const timestamp = new Date().toISOString();

    try {
      const response = await fetch(testUrl, {
        method: 'GET',
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      const responseHeaders = this.extractHeaders(response.headers);
      const corsHeaders = this.extractCorsHeaders(response.headers);

      return {
        success: response.ok,
        details: {
          method: 'GET',
          url: testUrl,
          status: response.status,
          headers: responseHeaders,
          corsHeaders,
          timestamp
        }
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        details: {
          method: 'GET',
          url: testUrl,
          timestamp
        }
      };
    }
  }

  /**
   * 運行完整的CORS診斷
   */
  async runFullDiagnostic(): Promise<{
    overall: boolean;
    tests: {
      corsTest: CorsTestResult;
      preflightTest: CorsTestResult;
      healthCheck: CorsTestResult;
    };
    recommendations: string[];
  }> {
    const corsTest = await this.testCorsConfiguration();
    const preflightTest = await this.testPreflightRequest();
    const healthCheck = await this.testApiEndpoint('/health');

    const overall = corsTest.success && preflightTest.success && healthCheck.success;
    const recommendations: string[] = [];

    // 生成建議
    if (!corsTest.success) {
      recommendations.push('CORS基本配置失敗，檢查服務器CORS設置');
    }

    if (!preflightTest.success) {
      recommendations.push('OPTIONS預檢請求失敗，檢查服務器OPTIONS處理');
    }

    if (!healthCheck.success) {
      recommendations.push('API健康檢查失敗，檢查API服務器狀態');
    }

    if (corsTest.details.corsHeaders && !corsTest.details.corsHeaders['access-control-allow-origin']) {
      recommendations.push('缺少Access-Control-Allow-Origin頭');
    }

    if (corsTest.details.corsHeaders && !corsTest.details.corsHeaders['access-control-allow-credentials']) {
      recommendations.push('缺少Access-Control-Allow-Credentials頭');
    }

    return {
      overall,
      tests: {
        corsTest,
        preflightTest,
        healthCheck
      },
      recommendations
    };
  }

  /**
   * 提取響應頭
   */
  private extractHeaders(headers: Headers): Record<string, string> {
    const result: Record<string, string> = {};
    headers.forEach((value, key) => {
      result[key.toLowerCase()] = value;
    });
    return result;
  }

  /**
   * 提取CORS相關頭
   */
  private extractCorsHeaders(headers: Headers): Record<string, string> {
    const corsHeaders: Record<string, string> = {};
    const corsHeaderNames = [
      'access-control-allow-origin',
      'access-control-allow-credentials',
      'access-control-allow-methods',
      'access-control-allow-headers',
      'access-control-expose-headers',
      'access-control-max-age'
    ];

    headers.forEach((value, key) => {
      if (corsHeaderNames.includes(key.toLowerCase())) {
        corsHeaders[key.toLowerCase()] = value;
      }
    });

    return corsHeaders;
  }

  /**
   * 生成CORS診斷報告
   */
  generateDiagnosticReport(diagnostic: Awaited<ReturnType<typeof this.runFullDiagnostic>>): string {
    const { overall, tests, recommendations } = diagnostic;

    let report = `CORS診斷報告 - ${new Date().toLocaleString()}\n`;
    report += `整體狀態: ${overall ? '✅ 正常' : '❌ 異常'}\n\n`;

    report += `測試結果:\n`;
    report += `1. CORS基本測試: ${tests.corsTest.success ? '✅' : '❌'}\n`;
    if (!tests.corsTest.success && tests.corsTest.error) {
      report += `   錯誤: ${tests.corsTest.error}\n`;
    }

    report += `2. OPTIONS預檢測試: ${tests.preflightTest.success ? '✅' : '❌'}\n`;
    if (!tests.preflightTest.success && tests.preflightTest.error) {
      report += `   錯誤: ${tests.preflightTest.error}\n`;
    }

    report += `3. API健康檢查: ${tests.healthCheck.success ? '✅' : '❌'}\n`;
    if (!tests.healthCheck.success && tests.healthCheck.error) {
      report += `   錯誤: ${tests.healthCheck.error}\n`;
    }

    if (recommendations.length > 0) {
      report += `\n修復建議:\n`;
      recommendations.forEach((rec, index) => {
        report += `${index + 1}. ${rec}\n`;
      });
    }

    return report;
  }
}

// 創建默認實例
export const corsDebugger = new CorsDebugger();

export default CorsDebugger;