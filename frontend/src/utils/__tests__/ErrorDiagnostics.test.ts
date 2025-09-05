/**
 * ErrorDiagnostics 簡化測試套件
 * 驗證錯誤診斷系統的基本功能
 */

import { ErrorDiagnostics } from '../ErrorDiagnostics';

// Mock fetch for testing
global.fetch = jest.fn();

describe('ErrorDiagnostics - 基本功能', () => {
  let errorDiagnostics: ErrorDiagnostics;

  beforeEach(() => {
    errorDiagnostics = ErrorDiagnostics.getInstance();
    errorDiagnostics.clearErrors();
    jest.clearAllMocks();
  });

  afterEach(() => {
    errorDiagnostics.clearErrors();
  });

  test('應該能夠手動報告錯誤', () => {
    errorDiagnostics.reportError('auth', '認證失敗測試', { testData: true });
    
    const errors = errorDiagnostics.getAllErrors();
    expect(errors).toHaveLength(1);
    expect(errors[0].category).toBe('auth');
    expect(errors[0].message).toBe('認證失敗測試');
  });

  test('應該能夠生成診斷報告', () => {
    errorDiagnostics.reportError('api', 'API錯誤測試');
    errorDiagnostics.reportError('render', '渲染錯誤測試');
    
    const report = errorDiagnostics.generateReport();
    
    expect(report.issues.length).toBeGreaterThan(0);
    expect(report.overallHealth).toBeDefined();
    expect(report.recommendations).toBeDefined();
    expect(report.timestamp).toBeInstanceOf(Date);
  });

  test('應該能夠清除錯誤', () => {
    errorDiagnostics.reportError('test', '測試錯誤');
    expect(errorDiagnostics.getAllErrors()).toHaveLength(1);
    
    errorDiagnostics.clearErrors();
    expect(errorDiagnostics.getAllErrors()).toHaveLength(0);
  });

});