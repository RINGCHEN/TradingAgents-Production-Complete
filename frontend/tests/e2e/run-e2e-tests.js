#!/usr/bin/env node

/**
 * 認證系統端到端測試運行器
 * 運行所有E2E測試並生成詳細報告
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const e2eTestFiles = [
  'tests/e2e/auth/user-login.e2e.test.ts',
  'tests/e2e/auth/admin-dashboard.e2e.test.ts',
  'tests/e2e/auth/session-management.e2e.test.ts',
  'tests/e2e/auth/error-recovery.e2e.test.ts'
];

console.log('🎭 開始運行認證系統端到端測試...\n');

// 檢查Playwright是否已安裝
try {
  execSync('npx playwright --version', { stdio: 'pipe' });
} catch (error) {
  console.log('📦 安裝Playwright瀏覽器...');
  execSync('npx playwright install', { stdio: 'inherit' });
}

// 確保測試結果目錄存在
const testResultsDir = path.resolve(__dirname, '../../test-results');
if (!fs.existsSync(testResultsDir)) {
  fs.mkdirSync(testResultsDir, { recursive: true });
}

try {
  // 運行E2E測試
  const command = `npx playwright test --config=playwright.config.ts`;
  
  console.log('執行命令:', command);
  console.log('─'.repeat(80));
  
  execSync(command, { 
    stdio: 'inherit',
    cwd: path.resolve(__dirname, '../..')
  });
  
  console.log('\n✅ 認證系統端到端測試完成！');
  console.log('📊 測試報告已生成：');
  console.log('   • HTML報告: test-results/e2e-report/index.html');
  console.log('   • JSON結果: test-results/e2e-results.json');
  console.log('   • JUnit報告: test-results/e2e-results.xml');
  console.log('🎯 E2E測試驗證了以下場景：');
  console.log('   • 用戶登錄完整流程');
  console.log('   • 管理後台訪問控制');
  console.log('   • 會話生命週期管理');
  console.log('   • 錯誤處理和恢復機制');
  
} catch (error) {
  console.error('\n❌ E2E測試運行失敗:', error.message);
  
  // 提供故障排除建議
  console.log('\n🔧 故障排除建議：');
  console.log('1. 確保應用服務器正在運行 (npm run dev)');
  console.log('2. 檢查端口3000是否可用');
  console.log('3. 確保所有依賴已安裝 (npm install)');
  console.log('4. 檢查Playwright瀏覽器是否已安裝 (npx playwright install)');
  
  process.exit(1);
}