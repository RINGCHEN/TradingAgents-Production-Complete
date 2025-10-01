/**
 * 權限檢查器
 * Phase 1 Day 2新增 - 基於CODEX權限矩陣的前端UI權限控制
 *
 * 權限矩陣（來自backend_phase1_report.md）:
 * ┌────────────────────┬───────────────┬─────────────────┬────────────────┐
 * │ 模組/操作          │ gemini_admin  │ gemini_readonly │ gemini_finance │
 * ├────────────────────┼───────────────┼─────────────────┼────────────────┤
 * │ System Monitor GET │ ✅            │ ✅              │ ❌             │
 * │ System Monitor POST│ ✅            │ ❌              │ ❌             │
 * │ Config (GET/POST)  │ ✅            │ ❌              │ ❌             │
 * │ Analysts (GET)     │ ✅            │ ✅              │ ❌             │
 * │ Analysts (POST/PUT)│ ✅            │ ❌              │ ❌             │
 * │ Users (GET/POST)   │ ✅            │ ❌              │ ❌             │
 * │ Finance (GET/POST) │ ✅            │ ❌              │ ✅             │
 * │ Auth (refresh/logout) │ ✅        │ ✅              │ ✅             │
 * └────────────────────┴───────────────┴─────────────────┴────────────────┘
 */

// 用戶角色類型
export type UserRole = 'admin' | 'readonly' | 'finance';

// 模組名稱類型
export type ModuleName =
  | 'system'      // System Monitor
  | 'config'      // Config Management
  | 'analysts'    // Analyst Management
  | 'users'       // User Management
  | 'financial';  // Financial Management

// 操作類型
export type ActionType = 'read' | 'write' | 'delete';

// 權限配置接口
export interface PermissionConfig {
  module: ModuleName;
  action: ActionType;
}

/**
 * 權限檢查器類
 * 根據用戶角色檢查是否有權限執行特定操作
 */
export class PermissionChecker {
  private role: UserRole;

  constructor(role: UserRole) {
    this.role = role;
    console.log(`🔐 PermissionChecker 初始化: 角色=${role}`);
  }

  /**
   * 檢查用戶是否有權限執行操作
   * @param config 權限配置（模組+操作）
   * @returns true表示有權限，false表示無權限
   */
  can(config: PermissionConfig): boolean {
    const { module, action } = config;
    const hasPermission = this.checkPermission(module, action);

    console.log(
      `🔍 權限檢查: 角色=${this.role}, 模組=${module}, 操作=${action}, 結果=${hasPermission ? '✅允許' : '❌拒絕'}`
    );

    return hasPermission;
  }

  /**
   * 內部權限檢查邏輯
   * 根據CODEX權限矩陣實作
   */
  private checkPermission(module: ModuleName, action: ActionType): boolean {
    // Admin有所有權限
    if (this.role === 'admin') {
      return true;
    }

    // Readonly角色權限
    if (this.role === 'readonly') {
      // 只能讀取system和analysts模組
      if (action === 'read') {
        return ['system', 'analysts'].includes(module);
      }
      // 不允許任何寫入操作
      return false;
    }

    // Finance角色權限
    if (this.role === 'finance') {
      // 只能操作financial模組
      if (module === 'financial') {
        return ['read', 'write'].includes(action);
      }
      // 不允許訪問其他模組
      return false;
    }

    // 默認拒絕
    return false;
  }

  /**
   * 檢查是否可以讀取模組
   * 便利方法
   */
  canRead(module: ModuleName): boolean {
    return this.can({ module, action: 'read' });
  }

  /**
   * 檢查是否可以寫入模組
   * 便利方法
   */
  canWrite(module: ModuleName): boolean {
    return this.can({ module, action: 'write' });
  }

  /**
   * 檢查是否可以刪除模組內容
   * 便利方法
   */
  canDelete(module: ModuleName): boolean {
    return this.can({ module, action: 'delete' });
  }

  /**
   * 取得當前角色
   */
  getRole(): UserRole {
    return this.role;
  }

  /**
   * 檢查是否為管理員
   */
  isAdmin(): boolean {
    return this.role === 'admin';
  }

  /**
   * 檢查是否為唯讀用戶
   */
  isReadonly(): boolean {
    return this.role === 'readonly';
  }

  /**
   * 檢查是否為財務用戶
   */
  isFinance(): boolean {
    return this.role === 'finance';
  }

  /**
   * 取得模組的允許操作列表
   * 用於UI顯示（例如顯示哪些按鈕）
   */
  getAllowedActions(module: ModuleName): ActionType[] {
    const actions: ActionType[] = [];

    if (this.canRead(module)) actions.push('read');
    if (this.canWrite(module)) actions.push('write');
    if (this.canDelete(module)) actions.push('delete');

    return actions;
  }

  /**
   * 批量檢查多個權限
   * 返回權限映射
   */
  checkMultiple(configs: PermissionConfig[]): Map<string, boolean> {
    const results = new Map<string, boolean>();

    configs.forEach(config => {
      const key = `${config.module}:${config.action}`;
      results.set(key, this.can(config));
    });

    return results;
  }
}