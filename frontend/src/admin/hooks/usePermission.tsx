/**
 * usePermission Hook
 * Phase 1 Day 2新增 - React Hook for UI權限控制
 *
 * 使用方式:
 * ```tsx
 * const { can, canRead, canWrite, role } = usePermission();
 *
 * // 條件渲染按鈕
 * {canWrite('system') && <button>重啟服務</button>}
 *
 * // 條件渲染整個區塊
 * {canRead('analysts') ? <AnalystsList /> : <NoPermission />}
 * ```
 */

import { useMemo } from 'react';
import {
  PermissionChecker,
  UserRole,
  ModuleName,
  ActionType,
  PermissionConfig
} from '../utils/PermissionChecker';

interface UsePermissionReturn {
  /**
   * 檢查是否有權限執行操作
   */
  can: (config: PermissionConfig) => boolean;

  /**
   * 檢查是否可以讀取模組
   */
  canRead: (module: ModuleName) => boolean;

  /**
   * 檢查是否可以寫入模組
   */
  canWrite: (module: ModuleName) => boolean;

  /**
   * 檢查是否可以刪除模組內容
   */
  canDelete: (module: ModuleName) => boolean;

  /**
   * 取得模組的允許操作列表
   */
  getAllowedActions: (module: ModuleName) => ActionType[];

  /**
   * 當前用戶角色
   */
  role: UserRole;

  /**
   * 是否為管理員
   */
  isAdmin: boolean;

  /**
   * 是否為唯讀用戶
   */
  isReadonly: boolean;

  /**
   * 是否為財務用戶
   */
  isFinance: boolean;

  /**
   * 權限檢查器實例（高級用法）
   */
  checker: PermissionChecker;
}

/**
 * usePermission Hook
 * 從localStorage取得用戶角色並創建權限檢查器
 */
export function usePermission(): UsePermissionReturn {
  // 從localStorage取得用戶角色
  const userRole = useMemo(() => {
    const roleStr = localStorage.getItem('admin_user_role');

    if (roleStr === 'admin' || roleStr === 'readonly' || roleStr === 'finance') {
      return roleStr as UserRole;
    }

    // 如果沒有角色信息，默認為readonly（最安全）
    console.warn('⚠️ usePermission: 未找到角色信息，默認為readonly');
    return 'readonly' as UserRole;
  }, []);

  // 創建權限檢查器實例（使用useMemo避免重複創建）
  const checker = useMemo(() => {
    return new PermissionChecker(userRole);
  }, [userRole]);

  // 返回便利方法和狀態
  return useMemo(
    () => ({
      can: (config: PermissionConfig) => checker.can(config),
      canRead: (module: ModuleName) => checker.canRead(module),
      canWrite: (module: ModuleName) => checker.canWrite(module),
      canDelete: (module: ModuleName) => checker.canDelete(module),
      getAllowedActions: (module: ModuleName) => checker.getAllowedActions(module),
      role: userRole,
      isAdmin: checker.isAdmin(),
      isReadonly: checker.isReadonly(),
      isFinance: checker.isFinance(),
      checker
    }),
    [checker, userRole]
  );
}

/**
 * usePermissionGuard Hook
 * 用於整個組件的權限守衛，無權限時返回null或自定義fallback
 *
 * 使用方式:
 * ```tsx
 * function SystemMonitor() {
 *   const hasPermission = usePermissionGuard('system', 'read');
 *
 *   if (!hasPermission) return null; // 或者返回 <NoPermission />
 *
 *   return <div>系統監控內容</div>;
 * }
 * ```
 */
export function usePermissionGuard(
  module: ModuleName,
  action: ActionType
): boolean {
  const { can } = usePermission();
  return can({ module, action });
}

/**
 * 權限守衛HOC（Higher-Order Component）
 * 用於包裝整個組件，無權限時顯示fallback
 *
 * 使用方式:
 * ```tsx
 * const ProtectedSystemMonitor = withPermission(
 *   SystemMonitor,
 *   'system',
 *   'read',
 *   <NoPermission message="您沒有權限訪問系統監控" />
 * );
 * ```
 */
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  module: ModuleName,
  action: ActionType,
  fallback: React.ReactNode = null
): React.FC<P> {
  return function PermissionGuardedComponent(props: P) {
    const { can } = usePermission();

    if (!can({ module, action })) {
      return <>{fallback}</>;
    }

    return <Component {...props} />;
  };
}