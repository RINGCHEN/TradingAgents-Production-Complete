/**
 * Authentication Test Runner
 * 運行所有認證相關測試的腳本
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

interface TestResult {
  suite: string;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  coverage?: {
    statements: number;
    branches: number;
    functions: number;
    lines: number;
  };
}

interface TestSuite {
  name: string;
  pattern: string;
  description: string;
  timeout?: number;
}

class AuthenticationTestRunner {
  private testSuites: TestSuite[] = [
    {
      name: 'Unit Tests - AuthContext',
      pattern: 'tests/contexts/AuthContext.test.tsx',
      description: '測試認證上下文的狀態管理和操作'
    },
    {
      name: 'Unit Tests - TokenManager',
      pattern: 'tests/services/TokenManager.test.ts',
      description: '測試token管理器的核心功能'
    },
    {
      name: 'Unit Tests - ApiClient',
      pattern: 'tests/services/ApiClient.test.ts',
      description: '測試API客戶端的認證處理'
    },
    {
      name: 'Unit Tests - AuthService',
      pattern: 'tests/services/AuthService.test.ts',
      description: '測試認證服務的業務邏輯'
    },
    {
      name: 'Unit Tests - SecureStorage',
      pattern: 'tests/utils/SecureStorage.test.ts',
      description: '測試安全存儲工具'
    },
    {
      name: 'Unit Tests - AuthErrors',
      pattern: 'tests/utils/AuthErrors.test.ts',
      description: '測試認證錯誤處理'
    },
    {
      name: 'Integration Tests - Login Flow',
      pattern: 'tests/integration/LoginFlow.integration.test.tsx',
      description: '測試完整登錄流程整合',
      timeout: 30000
    },
    {
      name: 'Integration Tests - Token Refresh',
      pattern: 'tests/integration/TokenRefresh.integration.test.ts',
      description: '測試token刷新流程整合',
      timeout: 30000
    },
    {
      name: 'Integration Tests - API Authentication',
      pattern: 'tests/integration/ApiAuthentication.integration.test.ts',
      description: '測試API認證整合',
      timeout: 30000
    },
    {
      name: 'Integration Tests - Error Handling',
      pattern: 'tests/integration/ErrorHandling.integration.test.tsx',
      description: '測試錯誤處理整合',
      timeout: 30000
    },
    {
      name: 'Integration Tests - Admin Authentication',
      pattern: 'tests/integration/AdminAuthentication.integration.test.tsx',
      description: '測試管理員認證完整流程',
      timeout: 45000
    },
    {
      name: 'Security Tests',
      pattern: 'tests/security/AuthenticationSecurity.test.ts',
      description: '測試認證系統安全性',
      timeout: 60000
    },
    {
      name: 'Performance Tests',
      pattern: 'tests/performance/AuthenticationPerformance.test.ts',
      description: '測試認證系統性能',
      timeout: 120000
    }
  ];

  private results: TestResult[] = [];

  async runAllTests(): Promise<void> {
    console.log('🚀 開始運行認證系統測試套件...\n');
    
    const startTime = Date.now();
    let totalPassed = 0;
    let totalFailed = 0;
    let totalSkipped = 0;

    for (const suite of this.testSuites) {
      console.log(`📋 運行測試套件: ${suite.name}`);
      console.log(`   描述: ${suite.description}`);
      
      try {
        const result = await this.runTestSuite(suite);
        this.results.push(result);
        
        totalPassed += result.passed;
        totalFailed += result.failed;
        totalSkipped += result.skipped;
        
        this.printTestResult(result);
      } catch (error) {
        console.error(`❌ 測試套件運行失敗: ${suite.name}`);
        console.error(`   錯誤: ${error.message}`);
        
        this.results.push({
          suite: suite.name,
          passed: 0,
          failed: 1,
          skipped: 0,
          duration: 0
        });
        totalFailed += 1;
      }
      
      console.log(''); // Empty line for readability
    }

    const totalTime = Date.now() - startTime;
    
    console.log('📊 測試總結');
    console.log('=' .repeat(50));
    console.log(`總測試時間: ${(totalTime / 1000).toFixed(2)}秒`);
    console.log(`通過測試: ${totalPassed}`);
    console.log(`失敗測試: ${totalFailed}`);
    console.log(`跳過測試: ${totalSkipped}`);
    console.log(`總測試數: ${totalPassed + totalFailed + totalSkipped}`);
    console.log(`成功率: ${((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(2)}%`);
    
    // Generate detailed report
    await this.generateReport();
    
    if (totalFailed > 0) {
      console.log('\n❌ 部分測試失敗，請檢查詳細報告');
      process.exit(1);
    } else {
      console.log('\n✅ 所有測試通過！');
    }
  }

  private async runTestSuite(suite: TestSuite): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      // Build Jest command
      const jestCommand = [
        'npx jest',
        `--testPathPattern="${suite.pattern}"`,
        '--verbose',
        '--coverage',
        '--coverageReporters=json-summary',
        '--coverageReporters=text',
        suite.timeout ? `--testTimeout=${suite.timeout}` : '',
        '--detectOpenHandles',
        '--forceExit'
      ].filter(Boolean).join(' ');

      // Run the test
      const output = execSync(jestCommand, {
        cwd: path.resolve(__dirname, '..'),
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const duration = Date.now() - startTime;
      
      // Parse Jest output
      const result = this.parseJestOutput(output, suite.name, duration);
      
      // Try to read coverage data
      try {
        const coveragePath = path.resolve(__dirname, '../coverage/coverage-summary.json');
        if (fs.existsSync(coveragePath)) {
          const coverageData = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
          result.coverage = {
            statements: coverageData.total.statements.pct,
            branches: coverageData.total.branches.pct,
            functions: coverageData.total.functions.pct,
            lines: coverageData.total.lines.pct
          };
        }
      } catch (coverageError) {
        console.warn(`⚠️  無法讀取覆蓋率數據: ${coverageError.message}`);
      }

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      
      // Parse error output
      const errorOutput = error.stdout || error.stderr || error.message;
      return this.parseJestOutput(errorOutput, suite.name, duration);
    }
  }

  private parseJestOutput(output: string, suiteName: string, duration: number): TestResult {
    // Default result
    const result: TestResult = {
      suite: suiteName,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration
    };

    try {
      // Parse Jest summary line
      const summaryMatch = output.match(/Tests:\s+(\d+)\s+failed,\s+(\d+)\s+passed,\s+(\d+)\s+total/);
      if (summaryMatch) {
        result.failed = parseInt(summaryMatch[1]);
        result.passed = parseInt(summaryMatch[2]);
        // Total includes skipped, so calculate skipped
        const total = parseInt(summaryMatch[3]);
        result.skipped = total - result.passed - result.failed;
      } else {
        // Try alternative format
        const passMatch = output.match(/(\d+)\s+passing/);
        const failMatch = output.match(/(\d+)\s+failing/);
        const skipMatch = output.match(/(\d+)\s+pending/);
        
        if (passMatch) result.passed = parseInt(passMatch[1]);
        if (failMatch) result.failed = parseInt(failMatch[1]);
        if (skipMatch) result.skipped = parseInt(skipMatch[1]);
      }

      // If no tests were found, check for "No tests found" message
      if (output.includes('No tests found')) {
        result.skipped = 1;
      }
    } catch (parseError) {
      console.warn(`⚠️  無法解析測試輸出: ${parseError.message}`);
      // Assume failure if we can't parse
      result.failed = 1;
    }

    return result;
  }

  private printTestResult(result: TestResult): void {
    const status = result.failed > 0 ? '❌' : '✅';
    const duration = (result.duration / 1000).toFixed(2);
    
    console.log(`   ${status} 結果: ${result.passed} 通過, ${result.failed} 失敗, ${result.skipped} 跳過`);
    console.log(`   ⏱️  耗時: ${duration}秒`);
    
    if (result.coverage) {
      console.log(`   📈 覆蓋率: ${result.coverage.lines.toFixed(1)}% 行, ${result.coverage.functions.toFixed(1)}% 函數`);
    }
  }

  private async generateReport(): Promise<void> {
    const reportPath = path.resolve(__dirname, '../test-reports/authentication-test-report.json');
    const htmlReportPath = path.resolve(__dirname, '../test-reports/authentication-test-report.html');
    
    // Ensure reports directory exists
    const reportsDir = path.dirname(reportPath);
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    // Generate JSON report
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalSuites: this.results.length,
        totalPassed: this.results.reduce((sum, r) => sum + r.passed, 0),
        totalFailed: this.results.reduce((sum, r) => sum + r.failed, 0),
        totalSkipped: this.results.reduce((sum, r) => sum + r.skipped, 0),
        totalDuration: this.results.reduce((sum, r) => sum + r.duration, 0),
        averageCoverage: this.calculateAverageCoverage()
      },
      results: this.results
    };

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    // Generate HTML report
    const htmlReport = this.generateHtmlReport(report);
    fs.writeFileSync(htmlReportPath, htmlReport);

    console.log(`📄 詳細報告已生成:`);
    console.log(`   JSON: ${reportPath}`);
    console.log(`   HTML: ${htmlReportPath}`);
  }

  private calculateAverageCoverage(): any {
    const coverageResults = this.results.filter(r => r.coverage);
    
    if (coverageResults.length === 0) {
      return null;
    }

    return {
      statements: coverageResults.reduce((sum, r) => sum + r.coverage!.statements, 0) / coverageResults.length,
      branches: coverageResults.reduce((sum, r) => sum + r.coverage!.branches, 0) / coverageResults.length,
      functions: coverageResults.reduce((sum, r) => sum + r.coverage!.functions, 0) / coverageResults.length,
      lines: coverageResults.reduce((sum, r) => sum + r.coverage!.lines, 0) / coverageResults.length
    };
  }

  private generateHtmlReport(report: any): string {
    return `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .metric { background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 24px; font-weight: bold; color: #2196F3; }
        .metric-label { color: #666; font-size: 14px; }
        .test-suite { background: white; margin-bottom: 15px; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .suite-name { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .suite-results { display: flex; gap: 20px; }
        .result-item { padding: 5px 10px; border-radius: 3px; font-size: 14px; }
        .passed { background: #4CAF50; color: white; }
        .failed { background: #F44336; color: white; }
        .skipped { background: #FF9800; color: white; }
        .coverage { margin-top: 10px; font-size: 14px; color: #666; }
        .success { color: #4CAF50; }
        .error { color: #F44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔐 Authentication System Test Report</h1>
        <p>Generated on: ${new Date(report.timestamp).toLocaleString('zh-TW')}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <div class="metric-value">${report.summary.totalSuites}</div>
            <div class="metric-label">Test Suites</div>
        </div>
        <div class="metric">
            <div class="metric-value ${report.summary.totalPassed > 0 ? 'success' : ''}">${report.summary.totalPassed}</div>
            <div class="metric-label">Passed Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value ${report.summary.totalFailed > 0 ? 'error' : ''}">${report.summary.totalFailed}</div>
            <div class="metric-label">Failed Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value">${report.summary.totalSkipped}</div>
            <div class="metric-label">Skipped Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value">${(report.summary.totalDuration / 1000).toFixed(2)}s</div>
            <div class="metric-label">Total Duration</div>
        </div>
        ${report.summary.averageCoverage ? `
        <div class="metric">
            <div class="metric-value">${report.summary.averageCoverage.lines.toFixed(1)}%</div>
            <div class="metric-label">Average Coverage</div>
        </div>
        ` : ''}
    </div>

    <h2>Test Suite Results</h2>
    ${report.results.map((result: TestResult) => `
        <div class="test-suite">
            <div class="suite-name">${result.suite}</div>
            <div class="suite-results">
                <span class="result-item passed">${result.passed} Passed</span>
                <span class="result-item failed">${result.failed} Failed</span>
                <span class="result-item skipped">${result.skipped} Skipped</span>
                <span>Duration: ${(result.duration / 1000).toFixed(2)}s</span>
            </div>
            ${result.coverage ? `
                <div class="coverage">
                    Coverage: ${result.coverage.lines.toFixed(1)}% lines, 
                    ${result.coverage.functions.toFixed(1)}% functions, 
                    ${result.coverage.branches.toFixed(1)}% branches
                </div>
            ` : ''}
        </div>
    `).join('')}

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px;">
        <p>Generated by TradingAgents Authentication Test Runner</p>
    </footer>
</body>
</html>
    `.trim();
  }

  async runSpecificSuite(suiteName: string): Promise<void> {
    const suite = this.testSuites.find(s => s.name.toLowerCase().includes(suiteName.toLowerCase()));
    
    if (!suite) {
      console.error(`❌ 找不到測試套件: ${suiteName}`);
      console.log('可用的測試套件:');
      this.testSuites.forEach(s => console.log(`  - ${s.name}`));
      return;
    }

    console.log(`🚀 運行特定測試套件: ${suite.name}\n`);
    
    try {
      const result = await this.runTestSuite(suite);
      this.results.push(result);
      this.printTestResult(result);
      
      if (result.failed > 0) {
        console.log('\n❌ 測試失敗');
        process.exit(1);
      } else {
        console.log('\n✅ 測試通過！');
      }
    } catch (error) {
      console.error(`❌ 測試套件運行失敗: ${error.message}`);
      process.exit(1);
    }
  }
}

// CLI interface
async function main() {
  const runner = new AuthenticationTestRunner();
  const args = process.argv.slice(2);
  
  if (args.length > 0) {
    const command = args[0];
    
    if (command === '--suite' && args[1]) {
      await runner.runSpecificSuite(args[1]);
    } else if (command === '--help') {
      console.log('Authentication Test Runner');
      console.log('');
      console.log('Usage:');
      console.log('  npm run test:auth              # Run all authentication tests');
      console.log('  npm run test:auth --suite unit # Run specific test suite');
      console.log('  npm run test:auth --help       # Show this help');
      console.log('');
      console.log('Available test suites:');
      console.log('  unit, integration, security, performance, e2e');
    } else {
      console.error('❌ 未知命令，使用 --help 查看幫助');
      process.exit(1);
    }
  } else {
    await runner.runAllTests();
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ 測試運行器發生錯誤:', error);
    process.exit(1);
  });
}

export { AuthenticationTestRunner };