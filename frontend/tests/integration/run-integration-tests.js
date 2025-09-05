#!/usr/bin/env node

/**
 * 認證系統整合測試運行器
 * 運行所有整合測試並生成詳細報告
 */

const { execSync } = require('child_process');
const path = require('path');

const integrationTestFiles = [
  'tests/integration/LoginFlow.integration.test.tsx',
  'tests/integration/TokenRefresh.integration.test.ts',
  'tests/integration/ApiAuthentication.integration.test.ts',
  'tests/integration/ErrorHandling.integration.test.tsx'
];

const testPattern = integrationTestFiles.join('|');

console.log('🔄 開始運行認證系統整合測試...\n');

try {
  // 運行整合測試
  const command = `npx jest --testPathPattern="(${testPattern})" --coverage --coverageDirectory=coverage/integration --coverageReporters=text,html,lcov --verbose --runInBand`;
  
  console.log('執行命令:', command);
  console.log('─'.repeat(80));
  
  execSync(command, { 
    stdio: 'inherit',
    cwd: path.resolve(__dirname, '../..')
  });
  
  console.log('\n✅ 認證系統整合測試完成！');
  console.log('📊 覆蓋率報告已生成到 coverage/integration 目錄');
  console.log('🔗 整合測試驗證了以下流程：');
  console.log('   • 完整登錄流程');
  console.log('   • Token自動刷新機制');
  console.log('   • API調用認證處理');
  console.log('   • 錯誤處理和恢復');
  
} catch (error) {
  console.error('\n❌ 整合測試運行失敗:', error.message);
  process.exit(1);
}