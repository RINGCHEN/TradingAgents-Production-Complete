/**
 * 管理後台專用React Hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { realAdminApiService } from '../services/RealAdminApiService';
import { notificationService } from '../services/NotificationService';
import { ApiResponse } from '../../services/ApiClient';

// 通用API調用Hook
export function useApiCall<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiCall();
      if (response.success) {
        setData(response.data);
      } else {
        setError(response.message || '請求失敗');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知錯誤');
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
}

// 系統狀態Hook
export function useSystemStatus() {
  return useApiCall(() => realAdminApiService.getSystemStatus() as any, []);
}

// 用戶管理Hook
export function useUsers(pagination?: any, searchFilters?: any) {
  const [users, setUsers] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statistics, setStatistics] = useState<any>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Build API params from pagination and searchFilters
      const params = {
        page: pagination?.page || 1,
        limit: pagination?.limit || 25,
        search: searchFilters?.query || undefined,
        role: searchFilters?.role?.length > 0 ? searchFilters.role[0] : undefined,
        status: searchFilters?.status?.length > 0 ? searchFilters.status[0] : undefined,
      };

      const response = await realAdminApiService.getUsers(params);

      // RealAdminApiService.getUsers returns { users, total, page, limit }
      setUsers(response.users || []);
      setTotalCount(response.total || 0);

      // Calculate statistics from users data
      const stats = {
        activeUsers: response.users?.filter((u: any) => u.status === 'active').length || 0,
        inactiveUsers: response.users?.filter((u: any) => u.status === 'inactive').length || 0,
        suspendedUsers: response.users?.filter((u: any) => u.status === 'suspended').length || 0,
        deletedUsers: 0,
        premiumUsers: response.users?.filter((u: any) => u.isPremium).length || 0,
        newUsersToday: 0,
      };
      setStatistics(stats);
    } catch (err) {
      const message = err instanceof Error ? err.message : '獲取用戶列表失敗';
      setError(message);
      notificationService.error('錯誤', message);
    } finally {
      setLoading(false);
    }
  }, [pagination, searchFilters]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const createUser = useCallback(async (userData: any) => {
    try {
      const response = await realAdminApiService.createUser(userData);
      if (response.success) {
        notificationService.success('成功', response.message || '用戶創建成功');
        await fetchUsers(); // 重新獲取列表
        return response.data;
      } else {
        const errorMsg = response.message || '創建用戶失敗';
        notificationService.error('錯誤', errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '創建用戶失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  const updateUser = useCallback(async (userId: string, userData: any) => {
    try {
      const response = await realAdminApiService.updateUser(userId, userData);
      if (response.success) {
        notificationService.success('成功', response.message || '用戶更新成功');
        await fetchUsers(); // 重新獲取列表
        return response.data;
      } else {
        const errorMsg = response.message || '更新用戶失敗';
        notificationService.error('錯誤', errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '更新用戶失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  const deleteUser = useCallback(async (userId: string) => {
    try {
      const response = await realAdminApiService.deleteUser(userId);
      if (response.success) {
        notificationService.success('成功', response.message || '用戶刪除成功');
        await fetchUsers(); // 重新獲取列表
      } else {
        const errorMsg = response.message || '刪除用戶失敗';
        notificationService.error('錯誤', errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '刪除用戶失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  const bulkUpdate = useCallback(async (userIds: string[], action: string, data?: any) => {
    try {
      // TODO: Implement bulk operations when backend API is ready
      notificationService.info('提示', '批量操作功能開發中');
      await fetchUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : '批量操作失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  return {
    users,
    loading,
    error,
    totalCount,
    statistics,
    refetch: fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    bulkUpdate
  };
}

// 通知Hook
export function useNotifications() {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const unsubscribe = notificationService.subscribe(setNotifications);
    return unsubscribe;
  }, []);

  return {
    notifications,
    showSuccess: notificationService.success.bind(notificationService),
    showError: notificationService.error.bind(notificationService),
    showWarning: notificationService.warning.bind(notificationService),
    showInfo: notificationService.info.bind(notificationService),
    remove: notificationService.remove.bind(notificationService),
    clear: notificationService.clear.bind(notificationService)
  };
}

// 載入狀態管理Hook
export function useLoadingState() {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});

  const setLoading = useCallback((key: string, loading: boolean) => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: loading
    }));
  }, []);

  const isLoading = useCallback((key?: string) => {
    if (key) {
      return loadingStates[key] || false;
    }
    return Object.values(loadingStates).some(loading => loading);
  }, [loadingStates]);

  return { setLoading, isLoading, loadingStates };
}

// Real-time Updates Hook
export function useRealTimeUpdates(resource: string) {
  const [updateReceived, setUpdateReceived] = useState(false);

  useEffect(() => {
    // TODO: Implement WebSocket connection for real-time updates
    // For now, return false (no updates)
    setUpdateReceived(false);
  }, [resource]);

  return updateReceived;
}

// Keyboard Shortcuts Hook
export function useKeyboardShortcuts(shortcuts: Record<string, () => void>) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const key = [
        event.ctrlKey && 'ctrl',
        event.shiftKey && 'shift',
        event.altKey && 'alt',
        event.key.toLowerCase()
      ].filter(Boolean).join('+');

      if (shortcuts[key]) {
        event.preventDefault();
        shortcuts[key]();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

// Local Storage Hook
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error loading ${key} from localStorage:`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.warn(`Error saving ${key} to localStorage:`, error);
    }
  }, [key]);

  return [storedValue, setValue];
}