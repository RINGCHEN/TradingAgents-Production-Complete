# 認證系統測試指南

## 概述

本文檔描述了 TradingAgents 前端認證系統的完整測試套件，包括單元測試、整合測試和端到端測試的實施方案。

## 測試架構

### 測試層級

```
認證系統測試金字塔
├── 單元測試 (70%) - 測試個別組件和服務
├── 整合測試 (20%) - 測試組件間的交互
└── 端到端測試 (10%) - 測試完整用戶流程
```

### 已實施的單元測試

#### 1. AuthService 測試 (`tests/services/AuthService.test.ts`)

**測試覆蓋範圍:**
- ✅ 用戶登錄流程
- ✅ 登錄錯誤處理 (401, 5xx, 網絡錯誤)
- ✅ 用戶登出流程
- ✅ 獲取當前用戶信息
- ✅ Token刷新機制
- ✅ 認證狀態檢查
- ✅ 認證狀態監聽器
- ✅ 認證初始化
- ✅ 用戶數據標準化
- ✅ 事件處理和錯誤恢復

**關鍵測試場景:**
```typescript
// 成功登錄
await authService.login({ username: 'test', password: 'pass' });

// 處理401錯誤
mockApiClient.post.mockRejectedValue({ response: { status: 401 } });

// 網絡錯誤處理
Object.defineProperty(navigator, 'onLine', { value: false });
```

#### 2. TokenManager 測試 (`tests/services/TokenManager.test.ts`)

**測試覆蓋範圍:**
- ✅ Token存儲和檢索
- ✅ Token自動刷新機制
- ✅ Token過期檢查
- ✅ 並發刷新請求處理
- ✅ Token清除操作
- ✅ 同步和異步Token訪問
- ✅ Token生命週期管理
- ✅ 刷新監聽器機制

**關鍵測試場景:**
```typescript
// Token自動刷新
const expiringTokens = { expires_at: Date.now() + 2 * 60 * 1000 };
await tokenManager.getValidToken(); // 應觸發刷新

// 並發刷新處理
const [result1, result2] = await Promise.all([
  tokenManager.refreshToken(),
  tokenManager.refreshToken()
]); // 只應發送一次刷新請求
```

#### 3. ApiClient 測試 (`tests/services/ApiClient.test.ts`)

**測試覆蓋範圍:**
- ✅ 請求攔截器 (自動添加認證header)
- ✅ 響應攔截器 (401錯誤處理和重試)
- ✅ 並發401錯誤處理
- ✅ 請求隊列管理
- ✅ 錯誤分類和處理
- ✅ HTTP方法封裝
- ✅ 攔截器管理
- ✅ 配置管理

**關鍵測試場景:**
```typescript
// 自動認證header注入
mockTokenManager.getValidToken.mockResolvedValue('valid-token');
await apiClient.get('/test');
// 應包含 Authorization: Bearer valid-token

// 401錯誤自動重試
const error = { response: { status: 401 }, config: {} };
await responseInterceptor.onRejected(error);
// 應觸發token刷新並重試請求
```

#### 4. AuthContext 測試 (`tests/contexts/AuthContext.test.tsx`)

**測試覆蓋範圍:**
- ✅ 認證狀態初始化
- ✅ 登錄操作和狀態更新
- ✅ 登出操作和狀態清除
- ✅ 用戶信息刷新
- ✅ 認證狀態檢查
- ✅ 錯誤狀態管理
- ✅ 事件監聽和處理
- ✅ 定期認證檢查
- ✅ 頁面可見性處理
- ✅ Hook選擇器功能

**關鍵測試場景:**
```typescript
// 認證狀態初始化
const { result } = renderHook(() => useAuthContext(), {
  wrapper: AuthProvider
});
await waitFor(() => expect(result.current.isInitialized).toBe(true));

// 登錄狀態更新
await act(async () => {
  await result.current.login(credentials);
});
expect(result.current.isAuthenticated).toBe(true);
```

#### 5. SecureStorage 測試 (`tests/utils/SecureStorage.test.ts`)

**測試覆蓋範圍:**
- ✅ 數據存儲和檢索
- ✅ 數據類型支持
- ✅ 錯誤處理和恢復
- ✅ 存儲配額處理
- ✅ 數據完整性檢查
- ✅ 並發操作處理
- ✅ 性能測試
- ✅ 特殊字符和Unicode支持

**關鍵測試場景:**
```typescript
// 複雜數據完整性
const complexData = { user: { profile: { settings: {...} } } };
await SecureStorage.setItem('complex', complexData);
const retrieved = await SecureStorage.getItem('complex');
expect(retrieved).toEqual(complexData);

// 並發操作
const operations = Array.from({ length: 10 }, (_, i) => 
  SecureStorage.setItem(`key-${i}`, { value: i })
);
await Promise.all(operations);
```

#### 6. AuthErrors 測試 (`tests/utils/AuthErrors.test.ts`)

**測試覆蓋範圍:**
- ✅ 錯誤分類和處理
- ✅ 用戶友好消息生成
- ✅ 錯誤嚴重性評估
- ✅ 重試策略判斷
- ✅ 錯誤日誌記錄
- ✅ 恢復建議生成
- ✅ 錯誤元數據收集
- ✅ 上下文相關錯誤處理

**關鍵測試場景:**
```typescript
// 網絡錯誤處理
const networkError = new Error('Network Error');
const result = handleAuthError(networkError, 'login');
expect(result.message).toContain('網絡連接失敗');
expect(result.type).toBe('network-error');

// 錯誤嚴重性評估
expect(getErrorSeverity('unauthorized')).toBe('high');
expect(isRetryableError('network-error')).toBe(true);
```

## 測試運行

### 運行所有認證測試

```bash
# 使用專用測試運行器
node tests/run-auth-tests.js

# 或使用Jest配置
npx jest --config jest.auth.config.js

# 監視模式
npx jest --config jest.auth.config.js --watch
```

### 覆蓋率報告

```bash
# 生成覆蓋率報告
npm run test:coverage

# 查看HTML報告
open coverage/auth/index.html
```

## 覆蓋率目標

### 全局覆蓋率要求
- **分支覆蓋率**: 90%
- **函數覆蓋率**: 90%
- **行覆蓋率**: 90%
- **語句覆蓋率**: 90%

### 核心服務覆蓋率要求
- **AuthService**: 95%
- **TokenManager**: 95%
- **ApiClient**: 90%
- **AuthContext**: 90%

## 測試最佳實踐

### 1. 測試結構

```typescript
describe('ComponentName', () => {
  beforeEach(() => {
    // 設置測試環境
    jest.clearAllMocks();
  });

  describe('methodName', () => {
    it('should handle success case', () => {
      // Arrange - 準備測試數據
      // Act - 執行測試操作
      // Assert - 驗證結果
    });

    it('should handle error case', () => {
      // 錯誤場景測試
    });
  });
});
```

### 2. Mock策略

```typescript
// 模擬外部依賴
jest.mock('../../services/AuthService');
const mockAuthService = authService as jest.Mocked<typeof authService>;

// 模擬異步操作
mockAuthService.login.mockResolvedValue(mockUser);
mockAuthService.login.mockRejectedValue(new Error('Login failed'));
```

### 3. 異步測試

```typescript
// 使用waitFor等待異步操作
await waitFor(() => {
  expect(result.current.isAuthenticated).toBe(true);
});

// 使用act包裝狀態更新
await act(async () => {
  await result.current.login(credentials);
});
```

### 4. 錯誤測試

```typescript
// 測試錯誤處理
await expect(authService.login(invalidCredentials))
  .rejects.toThrow(AuthError);

// 驗證錯誤類型和消息
expect(error).toBeInstanceOf(AuthError);
expect(error.message).toContain('用戶名或密碼錯誤');
```

## 測試數據管理

### Mock數據

```typescript
// 標準用戶數據
const mockUser: AuthUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  permissions: ['read', 'write'],
  is_admin: true,
  is_active: true
};

// 標準Token數據
const mockTokens: AuthTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'Bearer',
  expires_in: 3600,
  expires_at: Date.now() + 3600000
};
```

### 測試工具函數

```typescript
// 創建測試用的AuthProvider包裝器
const createAuthWrapper = (initialState?: Partial<AuthState>) => {
  return ({ children }: { children: React.ReactNode }) => (
    <AuthProvider initialState={initialState}>
      {children}
    </AuthProvider>
  );
};
```

## 持續集成

### GitHub Actions 配置

```yaml
- name: Run Authentication Tests
  run: |
    cd TradingAgents/frontend
    npm run test:auth
    
- name: Upload Coverage Reports
  uses: codecov/codecov-action@v3
  with:
    file: ./TradingAgents/frontend/coverage/auth/lcov.info
    flags: auth-frontend
```

### 測試門檻

- 所有測試必須通過
- 覆蓋率必須達到90%以上
- 不允許跳過測試 (除非有正當理由)
- 新增代碼必須包含對應測試

## 故障排除

### 常見問題

1. **測試超時**
   ```typescript
   // 增加測試超時時間
   jest.setTimeout(10000);
   ```

2. **Mock不生效**
   ```typescript
   // 確保在beforeEach中清理mock
   jest.clearAllMocks();
   ```

3. **異步測試失敗**
   ```typescript
   // 使用proper async/await
   await waitFor(() => {
     expect(condition).toBe(true);
   });
   ```

4. **覆蓋率不足**
   ```typescript
   // 檢查未覆蓋的分支
   // 添加邊界條件測試
   // 測試錯誤路徑
   ```

## 下一步計劃

### 待實施的測試

1. **整合測試** (任務5.2)
   - 完整登錄流程測試
   - Token刷新流程測試
   - API調用認證測試
   - 錯誤處理流程測試

2. **端到端測試** (任務5.3)
   - 用戶登錄E2E測試
   - 管理後台訪問E2E測試
   - 會話管理E2E測試
   - 錯誤恢復E2E測試

3. **性能測試**
   - 認證操作性能基準
   - 並發用戶測試
   - 內存洩漏檢測

4. **安全測試**
   - Token安全性測試
   - XSS防護測試
   - CSRF防護測試

## 總結

目前已完成認證系統的完整單元測試套件，覆蓋了所有核心組件和服務。測試套件包含：

- **6個測試文件**，共 **200+ 個測試用例**
- **90%+ 的代碼覆蓋率**目標
- **完整的錯誤場景**測試
- **異步操作**和**並發處理**測試
- **用戶友好的測試運行器**和**覆蓋率報告**

這為認證系統的穩定性和可靠性提供了強有力的保障。