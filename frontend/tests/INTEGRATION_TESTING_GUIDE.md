# 認證系統整合測試指南

## 概述

本文檔描述了 TradingAgents 前端認證系統的整合測試實施，驗證各組件間的協作和完整的用戶流程。

## 整合測試架構

### 測試層級定位

```
測試金字塔中的整合測試層
├── 單元測試 (70%) ✅ 已完成
├── 整合測試 (20%) ✅ 當前層級
└── 端到端測試 (10%) ⏳ 待實施
```

### 整合測試範圍

整合測試專注於驗證：
- **組件間協作** - 服務、上下文、組件的交互
- **完整業務流程** - 從用戶操作到系統響應的完整鏈路
- **錯誤處理流程** - 跨組件的錯誤傳播和恢復
- **狀態同步** - 認證狀態在不同組件間的一致性

## 已實施的整合測試

### 1. 登錄流程整合測試 (`LoginFlow.integration.test.tsx`)

**測試覆蓋範圍:**
- ✅ 完整登錄流程 (表單 → API → 狀態更新)
- ✅ 認證狀態持久化和恢復
- ✅ 登錄錯誤處理 (401, 500, 網絡錯誤)
- ✅ 載入狀態管理
- ✅ 表單驗證整合
- ✅ 跨組件狀態同步
- ✅ 內存洩漏防護
- ✅ 並發登錄處理

**關鍵測試場景:**
```typescript
// 完整登錄流程
await user.type(usernameInput, 'admin');
await user.type(passwordInput, 'password123');
await user.click(loginButton);

// 驗證API調用
expect(fetch).toHaveBeenCalledWith('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ username: 'admin', password: 'password123' })
});

// 驗證狀態更新
await waitFor(() => {
  expect(screen.getByText('歡迎, admin')).toBeInTheDocument();
});
```

**測試統計:**
- **測試用例數**: 25+
- **覆蓋的組件**: AdminLogin, AuthContext, AuthService, TokenManager
- **測試場景**: 成功登錄、錯誤處理、狀態管理、性能測試

### 2. Token刷新整合測試 (`TokenRefresh.integration.test.ts`)

**測試覆蓋範圍:**
- ✅ 自動Token刷新機制
- ✅ 並發刷新請求處理
- ✅ Token過期檢測和處理
- ✅ 刷新失敗恢復機制
- ✅ 監聽器通知系統
- ✅ 與AuthService的整合
- ✅ 錯誤恢復策略
- ✅ 性能和內存管理

**關鍵測試場景:**
```typescript
// 自動Token刷新
const expiringTokens = { expires_at: Date.now() + 2 * 60 * 1000 };
mockStorage.getItem.mockResolvedValue(expiringTokens);

const token = await tokenManager.getValidToken();

// 驗證刷新被觸發
expect(fetch).toHaveBeenCalledWith('/auth/refresh', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer refresh-token' }
});

// 驗證新Token被返回
expect(token).toBe('new-access-token');
```

**測試統計:**
- **測試用例數**: 20+
- **覆蓋的組件**: TokenManager, ApiClient, AuthService
- **測試場景**: 自動刷新、並發處理、錯誤恢復、監聽器機制

### 3. API認證整合測試 (`ApiAuthentication.integration.test.ts`)

**測試覆蓋範圍:**
- ✅ 自動認證Header注入
- ✅ 401錯誤自動重試機制
- ✅ 請求隊列管理
- ✅ 所有HTTP方法支持
- ✅ 認證失敗處理
- ✅ 與AuthService整合
- ✅ 網絡錯誤處理
- ✅ 高頻請求性能

**關鍵測試場景:**
```typescript
// 自動認證Header
mockStorage.getItem.mockResolvedValue(validTokens);
await apiClient.get('/api/protected');

expect(fetch).toHaveBeenCalledWith('/api/protected', {
  headers: { 'Authorization': 'Bearer valid-token' }
});

// 401錯誤自動重試
fetch.mockImplementationOnce(() => ({ ok: false, status: 401 }))
     .mockImplementationOnce(() => ({ ok: true, json: () => newTokens }))
     .mockImplementationOnce(() => ({ ok: true, data: 'success' }));

const response = await apiClient.get('/api/protected');
expect(response.data).toBe('success');
```

**測試統計:**
- **測試用例數**: 30+
- **覆蓋的組件**: ApiClient, TokenManager, AuthService
- **測試場景**: 認證注入、錯誤重試、隊列管理、性能測試

### 4. 錯誤處理整合測試 (`ErrorHandling.integration.test.tsx`)

**測試覆蓋範圍:**
- ✅ 網絡錯誤處理和恢復
- ✅ 認證錯誤處理 (401, 403)
- ✅ 服務器錯誤處理 (500, 429)
- ✅ 驗證錯誤處理
- ✅ 重試機制和指數退避
- ✅ 錯誤狀態管理
- ✅ 全局錯誤處理
- ✅ 離線/在線狀態處理

**關鍵測試場景:**
```typescript
// 網絡錯誤處理
fetch.mockRejectedValue(new Error('Network Error'));
handleAuthError.mockReturnValue({
  message: '網絡連接失敗，請檢查網絡設置',
  type: 'network-error',
  isRetryable: true
});

await user.click(loginButton);

// 驗證錯誤顯示和重試選項
expect(screen.getByText('網絡連接失敗')).toBeInTheDocument();
expect(screen.getByRole('button', { name: /重試/ })).toBeInTheDocument();
```

**測試統計:**
- **測試用例數**: 35+
- **覆蓋的組件**: 所有認證相關組件
- **測試場景**: 各類錯誤處理、恢復機制、狀態管理

## 整合測試配置

### Jest配置 (`jest.integration.config.js`)

```javascript
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/tests/integration/**/*.integration.test.(ts|tsx)'],
  testTimeout: 30000, // 整合測試需要更長超時
  runInBand: true,    // 順序執行避免並發問題
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

### 測試環境設置 (`setup.js`)

```javascript
// 擴展的localStorage模擬
global.localStorage = createLocalStorageMock();

// 增強的fetch模擬
global.fetch = createFetchMock();

// 測試工具函數
global.testUtils = {
  waitForAsync: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  createMockUser: (overrides) => ({ id: 1, username: 'test', ...overrides }),
  createMockTokens: (overrides) => ({ access_token: 'token', ...overrides })
};
```

## 運行整合測試

### 命令行運行

```bash
# 運行所有整合測試
node tests/integration/run-integration-tests.js

# 使用Jest配置運行
npx jest --config jest.integration.config.js

# 監視模式
npx jest --config jest.integration.config.js --watch

# 生成覆蓋率報告
npx jest --config jest.integration.config.js --coverage
```

### 測試運行器特性

```javascript
// 自動化測試運行器
const integrationTestFiles = [
  'LoginFlow.integration.test.tsx',
  'TokenRefresh.integration.test.ts', 
  'ApiAuthentication.integration.test.ts',
  'ErrorHandling.integration.test.tsx'
];

// 順序執行，詳細報告
execSync(`npx jest --testPathPattern="(${testPattern})" --runInBand --verbose`);
```

## 測試數據管理

### Mock數據工廠

```typescript
// 標準用戶數據
const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  permissions: ['read', 'write'],
  is_admin: true,
  is_active: true,
  ...overrides
});

// 標準Token數據
const createMockTokens = (overrides = {}) => ({
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'Bearer',
  expires_in: 3600,
  expires_at: Date.now() + 3600000,
  ...overrides
});
```

### API響應模擬

```typescript
// 成功響應
const createMockResponse = (data, options = {}) => ({
  ok: true,
  status: 200,
  json: () => Promise.resolve(data),
  ...options
});

// 錯誤響應
const createMockErrorResponse = (status, message) => ({
  ok: false,
  status,
  json: () => Promise.resolve({ message })
});
```

## 測試最佳實踐

### 1. 測試隔離

```typescript
beforeEach(() => {
  // 重置所有模擬
  jest.clearAllMocks();
  
  // 清理存儲
  localStorage.clear();
  
  // 重置fetch模擬
  fetch.mockReset();
});
```

### 2. 異步操作處理

```typescript
// 使用waitFor等待異步操作
await waitFor(() => {
  expect(screen.getByText('登錄成功')).toBeInTheDocument();
});

// 使用act包裝狀態更新
await act(async () => {
  await authService.login(credentials);
});
```

### 3. 錯誤場景測試

```typescript
// 模擬網絡錯誤
fetch.mockRejectedValue(new Error('Network Error'));

// 模擬API錯誤
fetch.mockResolvedValue({
  ok: false,
  status: 401,
  json: () => Promise.resolve({ message: 'Unauthorized' })
});
```

### 4. 並發場景測試

```typescript
// 測試並發請求
const promises = [
  apiClient.get('/endpoint1'),
  apiClient.get('/endpoint2'),
  apiClient.get('/endpoint3')
];

const results = await Promise.all(promises);

// 驗證只有一次token刷新
expect(fetch).toHaveBeenCalledTimes(4); // 3 requests + 1 refresh
```

## 覆蓋率和質量指標

### 覆蓋率目標

- **整體覆蓋率**: 80%+
- **關鍵流程覆蓋率**: 90%+
- **錯誤處理覆蓋率**: 85%+

### 質量指標

- **測試執行時間**: < 2分鐘
- **測試穩定性**: 99%+ 通過率
- **並發安全性**: 無競態條件
- **內存使用**: 無內存洩漏

## 持續集成整合

### GitHub Actions配置

```yaml
- name: Run Integration Tests
  run: |
    cd TradingAgents/frontend
    npm run test:integration
    
- name: Upload Integration Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage/integration/lcov.info
    flags: integration-frontend
```

### 測試門檻

- 所有整合測試必須通過
- 覆蓋率不得低於80%
- 測試執行時間不得超過3分鐘
- 不允許跳過測試

## 故障排除

### 常見問題

1. **測試超時**
   ```javascript
   // 增加超時時間
   jest.setTimeout(30000);
   ```

2. **異步操作失敗**
   ```javascript
   // 正確等待異步操作
   await waitFor(() => {
     expect(condition).toBe(true);
   }, { timeout: 5000 });
   ```

3. **Mock不生效**
   ```javascript
   // 確保在beforeEach中重置
   beforeEach(() => {
     jest.clearAllMocks();
     fetch.mockReset();
   });
   ```

4. **狀態不同步**
   ```javascript
   // 使用act包裝狀態更新
   await act(async () => {
     await stateUpdateFunction();
   });
   ```

## 測試報告

### HTML報告

整合測試會生成詳細的HTML報告：
- **測試結果概覽**
- **覆蓋率詳情**
- **失敗測試詳情**
- **性能指標**

### JUnit報告

生成標準的JUnit XML報告用於CI/CD整合：
```xml
<testsuite name="Authentication Integration Tests">
  <testcase name="should complete full login flow" />
  <testcase name="should handle token refresh" />
  <!-- ... -->
</testsuite>
```

## 下一步計劃

### 待優化項目

1. **測試數據管理**
   - 實施測試數據工廠模式
   - 添加更多邊界條件測試

2. **性能測試**
   - 添加負載測試場景
   - 內存使用監控

3. **可視化測試**
   - 添加視覺回歸測試
   - UI組件交互測試

4. **端到端測試準備**
   - 為E2E測試準備測試數據
   - 建立測試環境

## 總結

整合測試套件成功驗證了認證系統的：

- **✅ 完整業務流程** - 從登錄到API調用的完整鏈路
- **✅ 組件間協作** - 服務、上下文、組件的無縫整合
- **✅ 錯誤處理機制** - 各種錯誤場景的正確處理和恢復
- **✅ 狀態同步** - 認證狀態在整個應用中的一致性
- **✅ 性能表現** - 高頻操作和並發場景的穩定性

這為認證系統的可靠性和穩定性提供了強有力的保障，確保各組件能夠正確協作，為用戶提供流暢的認證體驗。