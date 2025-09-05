#!/usr/bin/env node

/**
 * 認證系統測試運行器
 * 專門運行認證相關的單元測試並生成覆蓋率報告
 */

const { execSync } = require('child_process');
const path = require('path');

const testFiles = [
  'tests/services/AuthService.test.ts',
  'tests/services/TokenManager.test.ts', 
  'tests/services/ApiClient.test.ts',
  'tests/contexts/AuthContext.test.tsx',
  'tests/utils/SecureStorage.test.ts',
  'tests/utils/AuthErrors.test.ts'
];

const testPattern = testFiles.join('|');

console.log('🚀 開始運行認證系統單元測試...\n');

try {
  // 運行測試並生成覆蓋率報告
  const command = `npx jest --testPathPattern="(${testPattern})" --coverage --coverageDirectory=coverage/auth --coverageReporters=text,html,lcov --verbose`;
  
  console.log('執行命令:', command);
  console.log('─'.repeat(80));
  
  execSync(command, { 
    stdio: 'inherit',
    cwd: path.resolve(__dirname, '..')
  });
  
  console.log('\n✅ 認證系統測試完成！');
  console.log('📊 覆蓋率報告已生成到 coverage/auth 目錄');
  
} catch (error) {
  console.error('\n❌ 測試運行失敗:', error.message);
  process.exit(1);
}