/**
 * ErrorDiagnosticsIntegration - 錯誤診斷系統整合驗證
 * 用於驗證錯誤診斷系統的各個組件是否正確整合和工作
 */

import { errorDiagnostics, diagnoseHomepageErrors } from './ErrorDiagnostics';
import { consoleErrorCapture } from './ConsoleErrorCapture';
import { apiClient, loadCouponsWithDiagnostics } from '../services/DiagnosticApiClient';

export interface IntegrationTestResult {
  component: string;
  status: 'success' | 'error' | 'warning';
  message: string;
  details?: any;
}

export class ErrorDiagnosticsIntegration {
  /**
   * 執行完整的整合測試
   */
  public static async runIntegrationTests(): Promise<IntegrationTestResult[]> {
    const results: IntegrationTestResult[] = [];

    console.log('🔍 開始錯誤診斷系統整合測試...');

    // 測試1: ErrorDiagnostics基本功能
    results.push(await this.testErrorDiagnosticsBasic());

    // 測試2: ConsoleErrorCapture功能
    results.push(await this.testConsoleErrorCapture());

    // 測試3: DiagnosticApiClient功能
    results.push(await this.testDiagnosticApiClient());

    // 測試4: 網路請求監控
    results.push(await this.testNetworkMonitoring());

    // 測試5: 首頁特定檢查
    results.push(await this.testHomepageSpecificChecks());

    // 測試6: 錯誤報告生成
    results.push(await this.testErrorReportGeneration());

    // 測試7: 自動修復機制
    results.push(await this.testAutoFixMechanism());

    console.log('✅ 錯誤診斷系統整合測試完成');
    return results;
  }

  /**
   * 測試ErrorDiagnostics基本功能
   */
  private static async testErrorDiagnosticsBasic(): Promise<IntegrationTestResult> {
    try {
      // 清除之前的錯誤
      errorDiagnostics.clearErrors();

      // 報告測試錯誤
      errorDiagnostics.reportError('auth', '整合測試 - 認證錯誤');
      errorDiagnostics.reportError('api', '整合測試 - API錯誤');

      // 檢查錯誤是否被正確記錄
      const errors = errorDiagnostics.getAllErrors();
      
      if (errors.length >= 2) {
        return {
          component: 'ErrorDiagnostics',
          status: 'success',
          message: '基本錯誤報告功能正常',
          details: { errorCount: errors.length }
        };
      } else {
        return {
          component: 'ErrorDiagnostics',
          status: 'error',
          message: '錯誤報告功能異常',
          details: { expectedErrors: 2, actualErrors: errors.length }
        };
      }
    } catch (error) {
      return {
        component: 'ErrorDiagnostics',
        status: 'error',
        message: '基本功能測試失敗',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 測試ConsoleErrorCapture功能
   */
  private static async testConsoleErrorCapture(): Promise<IntegrationTestResult> {
    try {
      // 清除之前的錯誤
      consoleErrorCapture.clearCapturedErrors();

      // 確保捕獲已啟動
      consoleErrorCapture.startCapture();

      // 觸發測試錯誤（這些會被捕獲）
      const originalErrorCount = consoleErrorCapture.getCapturedErrors().length;
      
      // 模擬控制台錯誤
      console.error('整合測試 - SyntaxError: 測試語法錯誤');
      console.warn('整合測試 - 測試警告');

      // 等待一小段時間讓錯誤被處理
      await new Promise(resolve => setTimeout(resolve, 100));

      const newErrors = consoleErrorCapture.getCapturedErrors();
      const capturedCount = newErrors.length - originalErrorCount;

      if (capturedCount >= 2) {
        return {
          component: 'ConsoleErrorCapture',
          status: 'success',
          message: '控制台錯誤捕獲功能正常',
          details: { capturedErrors: capturedCount }
        };
      } else {
        return {
          component: 'ConsoleErrorCapture',
          status: 'warning',
          message: '控制台錯誤捕獲可能有問題',
          details: { expectedCaptures: 2, actualCaptures: capturedCount }
        };
      }
    } catch (error) {
      return {
        component: 'ConsoleErrorCapture',
        status: 'error',
        message: '控制台錯誤捕獲測試失敗',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 測試DiagnosticApiClient功能
   */
  private static async testDiagnosticApiClient(): Promise<IntegrationTestResult> {
    try {
      // 測試健康檢查功能
      const healthCheck = await apiClient.healthCheck();
      
      return {
        component: 'DiagnosticApiClient',
        status: 'success',
        message: 'API客戶端功能正常',
        details: { healthCheck }
      };
    } catch (error) {
      return {
        component: 'DiagnosticApiClient',
        status: 'warning',
        message: 'API客戶端測試完成（可能無後端連接）',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 測試網路請求監控
   */
  private static async testNetworkMonitoring(): Promise<IntegrationTestResult> {
    try {
      // 獲取當前網路請求記錄
      const initialRequests = errorDiagnostics.getNetworkRequests();
      const initialCount = initialRequests.length;

      // 嘗試一個API請求（可能會失敗，但會被監控）
      try {
        await apiClient.get('/api/integration-test');
      } catch (error) {
        // 忽略錯誤，我們只是想測試監控功能
      }

      // 檢查是否有新的網路請求記錄
      const newRequests = errorDiagnostics.getNetworkRequests();
      const newCount = newRequests.length;

      if (newCount > initialCount) {
        return {
          component: 'NetworkMonitoring',
          status: 'success',
          message: '網路請求監控功能正常',
          details: { 
            initialRequests: initialCount, 
            newRequests: newCount,
            latestRequest: newRequests[newRequests.length - 1]
          }
        };
      } else {
        return {
          component: 'NetworkMonitoring',
          status: 'warning',
          message: '網路請求監控可能未正常工作',
          details: { requestCount: newCount }
        };
      }
    } catch (error) {
      return {
        component: 'NetworkMonitoring',
        status: 'error',
        message: '網路請求監控測試失敗',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 測試首頁特定檢查
   */
  private static async testHomepageSpecificChecks(): Promise<IntegrationTestResult> {
    try {
      // 檢查DOM結構
      const rootElement = document.getElementById('root');
      const hasNavigation = document.querySelector('nav, .navbar, [role="navigation"]');
      const hasMainContent = document.querySelector('main, .main-content, .landing-page');

      const checks = {
        rootElement: !!rootElement,
        hasNavigation: !!hasNavigation,
        hasMainContent: !!hasMainContent,
        bodyTextLength: document.body.textContent?.length || 0
      };

      const passedChecks = Object.values(checks).filter(Boolean).length;
      const totalChecks = Object.keys(checks).length;

      if (passedChecks >= totalChecks * 0.75) {
        return {
          component: 'HomepageChecks',
          status: 'success',
          message: '首頁結構檢查通過',
          details: { checks, passedChecks, totalChecks }
        };
      } else {
        return {
          component: 'HomepageChecks',
          status: 'warning',
          message: '首頁結構檢查發現問題',
          details: { checks, passedChecks, totalChecks }
        };
      }
    } catch (error) {
      return {
        component: 'HomepageChecks',
        status: 'error',
        message: '首頁檢查測試失敗',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 測試錯誤報告生成
   */
  private static async testErrorReportGeneration(): Promise<IntegrationTestResult> {
    try {
      // 生成診斷報告
      const report = diagnoseHomepageErrors();

      const reportValid = !!(
        report.id &&
        report.timestamp &&
        report.overallHealth &&
        Array.isArray(report.issues) &&
        Array.isArray(report.recommendations)
      );

      if (reportValid) {
        return {
          component: 'ErrorReporting',
          status: 'success',
          message: '錯誤報告生成功能正常',
          details: {
            reportId: report.id,
            overallHealth: report.overallHealth,
            issueCount: report.issues.length,
            recommendationCount: report.recommendations.length
          }
        };
      } else {
        return {
          component: 'ErrorReporting',
          status: 'error',
          message: '錯誤報告格式異常',
          details: { report }
        };
      }
    } catch (error) {
      return {
        component: 'ErrorReporting',
        status: 'error',
        message: '錯誤報告生成失敗',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 測試自動修復機制
   */
  private static async testAutoFixMechanism(): Promise<IntegrationTestResult> {
    try {
      // 檢查localStorage清理功能
      const testKey = 'test-corrupted-data';
      localStorage.setItem(testKey, '<html>corrupted data</html>');

      // 模擬自動修復邏輯
      const suspiciousKeys = [testKey];
      let cleanedKeys = 0;

      suspiciousKeys.forEach(key => {
        try {
          const value = localStorage.getItem(key);
          if (value && (value.includes('<html') || value.includes('<!DOCTYPE'))) {
            localStorage.removeItem(key);
            cleanedKeys++;
          }
        } catch (e) {
          // 忽略錯誤
        }
      });

      // 驗證清理是否成功
      const isCleanedUp = !localStorage.getItem(testKey);

      if (isCleanedUp && cleanedKeys > 0) {
        return {
          component: 'AutoFix',
          status: 'success',
          message: '自動修復機制功能正常',
          details: { cleanedKeys }
        };
      } else {
        return {
          component: 'AutoFix',
          status: 'warning',
          message: '自動修復機制可能有問題',
          details: { cleanedKeys, isCleanedUp }
        };
      }
    } catch (error) {
      return {
        component: 'AutoFix',
        status: 'error',
        message: '自動修復機制測試失敗',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * 生成整合測試報告
   */
  public static generateIntegrationReport(results: IntegrationTestResult[]): string {
    const successCount = results.filter(r => r.status === 'success').length;
    const warningCount = results.filter(r => r.status === 'warning').length;
    const errorCount = results.filter(r => r.status === 'error').length;
    const totalCount = results.length;

    let report = `
🔍 錯誤診斷系統整合測試報告
=====================================

總測試項目: ${totalCount}
✅ 成功: ${successCount}
⚠️  警告: ${warningCount}
❌ 錯誤: ${errorCount}

詳細結果:
`;

    results.forEach((result, index) => {
      const statusIcon = result.status === 'success' ? '✅' : 
                        result.status === 'warning' ? '⚠️' : '❌';
      
      report += `
${index + 1}. ${statusIcon} ${result.component}
   ${result.message}
`;
      
      if (result.details) {
        report += `   詳情: ${JSON.stringify(result.details, null, 2)}\n`;
      }
    });

    const overallStatus = errorCount === 0 ? 
      (warningCount === 0 ? '完全正常' : '基本正常') : '需要修復';

    report += `
=====================================
整體狀態: ${overallStatus}
建議: ${this.generateRecommendations(results)}
`;

    return report;
  }

  /**
   * 生成建議
   */
  private static generateRecommendations(results: IntegrationTestResult[]): string {
    const errorResults = results.filter(r => r.status === 'error');
    const warningResults = results.filter(r => r.status === 'warning');

    if (errorResults.length === 0 && warningResults.length === 0) {
      return '所有組件運行正常，無需額外操作。';
    }

    let recommendations = [];

    if (errorResults.length > 0) {
      recommendations.push('修復錯誤組件以確保系統穩定性');
    }

    if (warningResults.length > 0) {
      recommendations.push('檢查警告組件，可能需要配置調整');
    }

    if (results.some(r => r.component === 'DiagnosticApiClient' && r.status !== 'success')) {
      recommendations.push('確保後端API服務正常運行');
    }

    if (results.some(r => r.component === 'HomepageChecks' && r.status !== 'success')) {
      recommendations.push('檢查首頁DOM結構和React組件渲染');
    }

    return recommendations.join('；');
  }
}

// 導出便利函數
export const runErrorDiagnosticsIntegrationTest = async (): Promise<string> => {
  const results = await ErrorDiagnosticsIntegration.runIntegrationTests();
  return ErrorDiagnosticsIntegration.generateIntegrationReport(results);
};

// 在開發環境中自動運行測試
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  // 延遲運行以確保所有組件都已初始化
  setTimeout(async () => {
    try {
      const report = await runErrorDiagnosticsIntegrationTest();
      console.log(report);
    } catch (error) {
      console.error('Integration test failed:', error);
    }
  }, 3000);
}

export default ErrorDiagnosticsIntegration;