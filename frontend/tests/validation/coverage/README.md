# 覆蓋率監控系統

TradingAgents 前端覆蓋率監控系統提供全面的代碼覆蓋率收集、分析和報告功能。

## 功能特性

### 🎯 核心功能
- **多源覆蓋率收集**: 支援 Vitest、Cypress、Jest、Istanbul 等工具
- **實時監控**: 持續監控覆蓋率變化和趨勢
- **智能分析**: 提供趨勢分析、熱點識別和改進建議
- **多格式報告**: 支援 HTML、JSON、LCOV、控制台等格式
- **閾值檢查**: 可配置的覆蓋率閾值和告警機制
- **CI/CD 整合**: 與 GitHub Actions 等 CI/CD 系統深度整合

### 📊 監控指標
- **行覆蓋率** (Line Coverage)
- **函數覆蓋率** (Function Coverage)  
- **分支覆蓋率** (Branch Coverage)
- **語句覆蓋率** (Statement Coverage)

### 🔔 通知系統
- Slack 通知
- 郵件通知
- Webhook 通知
- GitHub 狀態檢查

## 快速開始

### 1. 初始化配置

```bash
npm run coverage:init
```

這會創建一個 `coverage.config.json` 配置文件。

### 2. 收集覆蓋率

```bash
# 基本收集
npm run coverage

# 帶閾值檢查
npm run coverage:threshold

# 監控模式
npm run coverage:watch
```

### 3. 生成報告

```bash
# 生成所有格式報告
npm run coverage:report

# 生成特定格式
npm run coverage:report -- --format html
```

### 4. 分析趨勢

```bash
# 分析最近 30 天趨勢
npm run coverage:analyze

# 分析特定天數
npm run coverage:analyze -- --days 7
```

## 配置說明

### 基本配置

```json
{
  "monitor": {
    "thresholds": {
      "lines": 85,
      "functions": 85,
      "branches": 80,
      "statements": 85
    },
    "outputDir": "./coverage-reports",
    "alertEnabled": true
  }
}
```

### 整合配置

```json
{
  "integrations": {
    "vitest": true,
    "cypress": true,
    "jest": false,
    "istanbul": true
  }
}
```

### 報告配置

```json
{
  "reporters": {
    "html": true,
    "json": true,
    "lcov": true,
    "console": true,
    "slack": {
      "webhook": "https://hooks.slack.com/...",
      "channel": "#coverage"
    }
  }
}
```

## CLI 命令

### 收集命令

```bash
# 基本收集
npx tsx tests/validation/coverage/cli.ts collect

# 帶選項
npx tsx tests/validation/coverage/cli.ts collect \
  --config ./custom-config.json \
  --threshold 90 \
  --fail-on-threshold \
  --format html
```

### 監控命令

```bash
# 啟動監控
npx tsx tests/validation/coverage/cli.ts monitor \
  --interval 300 \
  --alert-threshold 80 \
  --webhook https://hooks.slack.com/...
```

### 分析命令

```bash
# 趨勢分析
npx tsx tests/validation/coverage/cli.ts analyze \
  --days 30 \
  --format console
```

### 比較命令

```bash
# 比較兩個覆蓋率報告
npx tsx tests/validation/coverage/cli.ts compare \
  --baseline ./baseline-coverage.json \
  --current ./current-coverage.json
```

## 整合指南

### GitHub Actions 整合

在 `.github/workflows/coverage.yml` 中配置：

```yaml
- name: Run coverage analysis
  run: npm run coverage:threshold

- name: Upload coverage reports
  uses: actions/upload-artifact@v4
  with:
    name: coverage-reports
    path: coverage-reports/
```

### Vitest 整合

在 `vitest.config.ts` 中配置：

```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 80,
        statements: 85
      }
    }
  }
})
```

### Cypress 整合

在 `cypress.config.ts` 中配置：

```typescript
export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      require('@cypress/code-coverage/task')(on, config)
      return config
    }
  }
})
```

## 最佳實踐

### 1. 設定合理的閾值

```json
{
  "thresholds": {
    "lines": 85,      // 行覆蓋率 85%
    "functions": 85,  // 函數覆蓋率 85%
    "branches": 80,   // 分支覆蓋率 80% (通常較低)
    "statements": 85  // 語句覆蓋率 85%
  }
}
```

### 2. 排除不必要的文件

```json
{
  "excludePatterns": [
    "**/*.test.{ts,tsx}",
    "**/*.spec.{ts,tsx}",
    "**/*.stories.{ts,tsx}",
    "**/*.d.ts",
    "**/node_modules/**",
    "**/dist/**",
    "**/__mocks__/**"
  ]
}
```

### 3. 設定告警機制

```json
{
  "alertThresholds": {
    "warning": 80,   // 警告閾值
    "critical": 70   // 嚴重閾值
  }
}
```

### 4. 定期清理

```bash
# 清理 30 天前的報告
npm run coverage:clean -- --older-than 30
```

## 故障排除

### 常見問題

#### 1. 覆蓋率數據收集失敗

**問題**: 找不到覆蓋率文件

**解決方案**:
```bash
# 檢查測試是否生成覆蓋率
npm run test:coverage

# 檢查文件路徑
ls -la coverage/
```

#### 2. 閾值檢查失敗

**問題**: 覆蓋率低於設定閾值

**解決方案**:
```bash
# 查看詳細報告
npm run coverage:report -- --format html

# 分析未覆蓋的代碼
npm run coverage:analyze
```

#### 3. CI/CD 整合問題

**問題**: GitHub Actions 中覆蓋率檢查失敗

**解決方案**:
```yaml
# 確保正確的工作目錄
working-directory: frontend

# 檢查依賴安裝
- run: npm ci
```

### 調試模式

啟用詳細日誌：

```bash
DEBUG=coverage:* npm run coverage
```

### 驗證設置

```bash
# 驗證配置
npm run coverage:validate

# 檢查整合工具
npm run coverage:collect -- --dry-run
```

## API 參考

### CoverageMonitor

```typescript
const monitor = new CoverageMonitor({
  thresholds: { lines: 85, functions: 85, branches: 80, statements: 85 },
  outputDir: './coverage-reports'
})

await monitor.initialize()
const coverage = await monitor.collectCoverage(['coverage/coverage-final.json'])
const report = await monitor.generateReport(coverage)
```

### CoverageIntegrator

```typescript
const integrator = new CoverageIntegrator({
  integrations: { vitest: true, cypress: true },
  reporters: { html: true, json: true }
})

await integrator.initialize()
const metrics = await integrator.runCoverageAnalysis()
```

## 進階功能

### 1. 自定義報告器

```typescript
class CustomReporter implements CoverageReporter {
  name = 'custom'
  
  async generate(metrics: CoverageMetrics): Promise<string> {
    // 自定義報告邏輯
    return outputPath
  }
  
  getOutputPath(): string {
    return './custom-report.txt'
  }
}
```

### 2. 自定義通知器

```typescript
class CustomNotifier implements CoverageNotifier {
  async notify(alert: CoverageAlert): Promise<void> {
    // 自定義通知邏輯
  }
}
```

### 3. 覆蓋率目標追蹤

```json
{
  "goals": [
    {
      "name": "達到 90% 覆蓋率",
      "target": { "lines": 90 },
      "deadline": "2025-03-01",
      "priority": "high"
    }
  ]
}
```

## 貢獻指南

### 開發設置

```bash
# 克隆專案
git clone https://github.com/tradingagents/frontend.git

# 安裝依賴
cd frontend && npm install

# 運行測試
npm run test

# 運行覆蓋率
npm run coverage
```

### 提交規範

- 功能: `feat: 添加新的覆蓋率報告器`
- 修復: `fix: 修復覆蓋率計算錯誤`
- 文檔: `docs: 更新覆蓋率配置說明`

## 許可證

MIT License - 詳見 [LICENSE](../../../LICENSE) 文件。

## 支援

- 📧 Email: support@tradingagents.com
- 💬 Slack: #frontend-coverage
- 🐛 Issues: [GitHub Issues](https://github.com/tradingagents/frontend/issues)
- 📖 Wiki: [項目 Wiki](https://github.com/tradingagents/frontend/wiki)