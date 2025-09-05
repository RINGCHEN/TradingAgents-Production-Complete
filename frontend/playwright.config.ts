/**
 * Playwright 端到端測試配置
 * 專門用於認證系統的E2E測試
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // 測試目錄
  testDir: './tests/e2e',
  
  // 全局設置
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // 報告器配置
  reporter: [
    ['html', { outputFolder: 'test-results/e2e-report' }],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['junit', { outputFile: 'test-results/e2e-results.xml' }]
  ],
  
  // 全局測試配置
  use: {
    // 基礎URL
    baseURL: 'http://localhost:3000',
    
    // 瀏覽器設置
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    
    // 截圖和視頻
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // 超時設置
    actionTimeout: 10000,
    navigationTimeout: 30000,
    
    // 其他設置
    locale: 'zh-TW',
    timezoneId: 'Asia/Taipei'
  },

  // 項目配置 - 不同瀏覽器
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    // 移動端測試
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // 測試服務器配置
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
  
  // 輸出目錄
  outputDir: 'test-results/e2e-artifacts',
  
  // 全局設置和清理
  globalSetup: require.resolve('./tests/e2e/global-setup.ts'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.ts'),
  
  // 測試超時
  timeout: 60000,
  expect: {
    timeout: 10000
  }
});