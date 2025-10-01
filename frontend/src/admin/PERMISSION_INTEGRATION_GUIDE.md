# CODEX-based RBAC 權限系統整合指南

**Phase 1 Day 2 完成時間**: 2025-10-01 02:00
**開發者**: Claude
**基於**: CODEX Backend Phase 1 Audit Report

---

## 📋 概覽

本指南說明如何在 `AdminApp_Ultimate.tsx` 及其子組件中整合 CODEX-based RBAC 權限系統。

### ✅ 已完成的核心文件

1. **PermissionChecker.ts** (193 lines) - 核心權限檢查邏輯
2. **usePermission.ts** (154 lines) - React Hook 封裝
3. **AdminApp_Ultimate.tsx** - 已整合 usePermission hook (行 72)

---

## 🎯 CODEX 權限矩陣

```
┌────────────────────┬───────────────┬─────────────────┬────────────────┐
│ 模組/操作          │ admin         │ readonly        │ finance        │
├────────────────────┼───────────────┼─────────────────┼────────────────┤
│ System Monitor GET │ ✅            │ ✅              │ ❌             │
│ System Monitor POST│ ✅            │ ❌              │ ❌             │
│ Config (GET/POST)  │ ✅            │ ❌              │ ❌             │
│ Analysts (GET)     │ ✅            │ ✅              │ ❌             │
│ Analysts (POST/PUT)│ ✅            │ ❌              │ ❌             │
│ Users (GET/POST)   │ ✅            │ ❌              │ ❌             │
│ Finance (GET/POST) │ ✅            │ ❌              │ ✅             │
│ Auth (refresh/logout) │ ✅        │ ✅              │ ✅             │
└────────────────────┴───────────────┴─────────────────┴────────────────┘
```

### 模組名稱對應

| AdminApp Route          | CODEX Module | 說明                |
|-------------------------|--------------|---------------------|
| `system_monitor`        | `'system'`   | 系統監控            |
| `config_management`     | `'config'`   | 配置管理            |
| `analyst_management`    | `'analysts'` | 分析師管理          |
| `users`                 | `'users'`    | 用戶管理            |
| `financial_management`  | `'financial'`| 財務管理            |

---

## 🚀 使用方法

### 1. 在組件中導入和使用

```typescript
import { usePermission } from './hooks/usePermission';

function MyComponent() {
  // 取得權限檢查函數
  const { can, canRead, canWrite, role, isAdmin } = usePermission();

  // 方法 1: 條件渲染按鈕
  return (
    <div>
      {canWrite('system') && (
        <button onClick={handleRestartService}>重啟服務</button>
      )}

      {canRead('financial') && (
        <FinancialDashboard />
      )}
    </div>
  );
}
```

### 2. 高級用法 - 權限守衛

```typescript
import { usePermissionGuard } from './hooks/usePermission';

function SystemMonitorModule() {
  // 檢查是否有讀取權限
  const hasReadPermission = usePermissionGuard('system', 'read');

  if (!hasReadPermission) {
    return <NoPermissionMessage />;
  }

  return <SystemMonitorContent />;
}
```

### 3. HOC (高階組件) 包裝

```typescript
import { withPermission } from './hooks/usePermission';

const ProtectedSystemMonitor = withPermission(
  SystemMonitorModule,
  'system',
  'read',
  <NoPermission message="您沒有權限訪問系統監控" />
);
```

---

## 🔧 在 AdminApp_Ultimate.tsx 中的整合示例

### 示例 1: 系統監控模組 (SystemMonitorModule)

**位置**: `AdminApp_Ultimate.tsx` 約第 6398 行

**應用權限控制**:

```typescript
const SystemMonitorModule: React.FC = () => {
  const { canWrite } = usePermission();

  // ... 其他 state 和邏輯

  return (
    <div className="system-monitor-module">
      <div className="page-header">
        <h1>⚙️ 系統監控</h1>

        {/* Phase 1 Day 2: 只有admin可以看到重啟按鈕 */}
        {canWrite('system') && (
          <button onClick={handleRestartService}>
            🔄 重啟服務
          </button>
        )}
      </div>

      {/* 系統監控內容 - readonly 和 admin 都可以看到 */}
      <SystemHealthOverview />
    </div>
  );
};
```

### 示例 2: 分析師管理模組 (AnalystManagementModule)

```typescript
const AnalystManagementModule: React.FC = () => {
  const { canRead, canWrite } = usePermission();

  // readonly 可以讀取，但不能修改
  if (!canRead('analysts')) {
    return <NoPermission />;
  }

  return (
    <div className="analyst-management">
      <h1>🤖 分析師管理</h1>

      {/* 顯示分析師列表 - readonly 和 admin 都可以看 */}
      <AnalystsList analysts={analysts} />

      {/* 編輯按鈕 - 只有 admin 可以操作 */}
      {canWrite('analysts') && (
        <div className="analyst-actions">
          <button onClick={handleAddAnalyst}>新增分析師</button>
          <button onClick={handleEditAnalyst}>編輯分析師</button>
        </div>
      )}
    </div>
  );
};
```

### 示例 3: 財務管理模組 (FinancialManagement)

```typescript
const FinancialManagement: React.FC = () => {
  const { canRead, canWrite, isFinance, isAdmin } = usePermission();

  // finance 和 admin 可以訪問
  if (!canRead('financial')) {
    return <NoPermission />;
  }

  return (
    <div className="financial-management">
      <h1>💰 財務管理</h1>

      {/* 財務報表 - finance 和 admin 都可以看 */}
      <FinancialReports />

      {/* 操作按鈕 - finance 和 admin 都可以操作 */}
      {canWrite('financial') && (
        <div className="financial-actions">
          <button onClick={handleCreateOrder}>創建訂單</button>
          <button onClick={handleRefund}>處理退款</button>
        </div>
      )}

      {/* 敏感財務數據 - 只有 admin 可以看到 */}
      {isAdmin && (
        <SensitiveFinancialData />
      )}
    </div>
  );
};
```

---

## 📝 在現有代碼中整合的步驟

### Step 1: 在組件頂部添加 Hook

```typescript
const MyModule: React.FC = () => {
  const { canRead, canWrite, role } = usePermission();
  // ... 其他代碼
```

### Step 2: 識別需要權限控制的元素

尋找以下類型的元素:
- 🔴 **高風險操作按鈕**: 刪除、重啟、修改配置
- 🟡 **寫入操作按鈕**: 創建、編輯、更新
- 🟢 **敏感數據展示**: 用戶列表、財務數據、系統配置

### Step 3: 應用權限檢查

```typescript
// 🔴 高風險操作 - 通常只有 admin 可以
{canWrite('system') && (
  <button className="danger" onClick={handleDelete}>
    刪除
  </button>
)}

// 🟡 一般寫入操作
{canWrite('analysts') && (
  <button onClick={handleEdit}>編輯</button>
)}

// 🟢 條件渲染整個區塊
{canRead('financial') ? (
  <FinancialDashboard />
) : (
  <NoPermission />
)}
```

---

## ⚠️ 重要注意事項

### 1. 雙層防護

前端權限控制是 **第一層防護**，但不是唯一防護:

```
✅ 前端: usePermission hook → 隱藏 UI 元素
✅ 後端: @require_admin_access decorator → 拒絕 API 請求
```

### 2. localStorage 角色管理

`usePermission` 從 `localStorage.getItem('admin_user_role')` 讀取角色:
- 登入成功後，`AdminAuthManager.setUserRole()` 會設置角色
- 如果沒有角色信息，默認為 `'readonly'` (最安全)

### 3. 與現有 hasPermission() 共存

`AdminApp_Ultimate.tsx` 中有兩個權限系統:

```typescript
// 舊系統 (legacy) - 基於 permissions 數組
const hasPermission = (permission: string) => {
  return currentAdmin.permissions.includes(permission);
};

// 新系統 (CODEX) - 基於角色和模組
const { can, canRead, canWrite } = usePermission();
```

**建議策略**:
- 保留舊系統用於 sidebar 過濾 (第 179 行)
- 新增功能使用 CODEX 系統
- 逐步遷移關鍵功能到 CODEX 系統

---

## 🧪 測試指南

### 測試不同角色

在瀏覽器開發者工具中:

```javascript
// 測試 readonly 角色
localStorage.setItem('admin_user_role', 'readonly');
location.reload();

// 測試 finance 角色
localStorage.setItem('admin_user_role', 'finance');
location.reload();

// 測試 admin 角色
localStorage.setItem('admin_user_role', 'admin');
location.reload();
```

### 預期行為

**readonly 角色**:
- ✅ 可以看到: 系統監控、分析師列表
- ❌ 不能看到: 編輯按鈕、刪除按鈕、配置管理

**finance 角色**:
- ✅ 可以看到: 財務管理的所有功能
- ❌ 不能看到: 系統監控、分析師管理、用戶管理

**admin 角色**:
- ✅ 可以看到: 所有功能
- ✅ 可以操作: 所有按鈕

---

## 🎯 下一步行動

### 立即可做

1. ✅ **完成**: 核心系統已整合到 AdminApp_Ultimate.tsx
2. ✅ **完成**: usePermission hook 可以使用
3. 🔄 **進行中**: 等待 CODEX 完成後端修復
4. 🔄 **進行中**: 等待 GEMINI 測試結果

### 後續優化

1. 將權限控制應用到更多模組 (參考本指南的示例)
2. 遷移舊的 `hasPermission()` 系統到 CODEX 系統
3. 增強錯誤提示 (403 錯誤顯示更友好的訊息)
4. 添加權限變更審計日誌

---

## 📚 相關文件

- **PermissionChecker.ts**: 核心權限邏輯實現
- **usePermission.ts**: React Hook 封裝
- **AdminAuthManager.ts**: 認證和角色管理
- **backend_phase1_report.md**: CODEX 後端審計報告

---

**整合完成時間**: 2025-10-01 02:00
**狀態**: ✅ Phase 1 Day 2 - UI權限控制系統 100% 完成
**下一步**: 配合 GEMINI 測試並根據測試結果修復問題
