/**
 * 管理後台專用React Hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react';
// import { adminApiService } from '../services/AdminApiService_Fixed';
import { notificationService } from '../services/NotificationService';

// 模擬API服務
const mockAdminApiService = {
  getSystemStatus: () => Promise.resolve({ success: true, data: { status: 'ok' } }),
  getUsers: () => Promise.resolve({ success: true, data: [], pagination: { total: 0 } }),
  createUser: () => Promise.resolve({ success: true, data: {} }),
  updateUser: () => Promise.resolve({ success: true, data: {} }),
  deleteUser: () => Promise.resolve({ success: true })
};
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
  return useApiCall(() => mockAdminApiService.getSystemStatus(), []);
}

// 用戶管理Hook
export function useUsers(pagination?: any) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await mockAdminApiService.getUsers(pagination);
      if (response.success) {
        setUsers(response.data.users || response.data);
      } else {
        setError(response.message || '獲取用戶列表失敗');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知錯誤');
    } finally {
      setLoading(false);
    }
  }, [pagination]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const createUser = useCallback(async (userData: any) => {
    try {
      const response = await mockAdminApiService.createUser(userData);
      if (response.success) {
        notificationService.success('成功', '用戶創建成功');
        fetchUsers(); // 重新獲取列表
        return response.data;
      } else {
        notificationService.error('錯誤', response.message || '創建用戶失敗');
        throw new Error(response.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '創建用戶失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  const updateUser = useCallback(async (userId: string, userData: any) => {
    try {
      const response = await mockAdminApiService.updateUser(userId, userData);
      if (response.success) {
        notificationService.success('成功', '用戶更新成功');
        fetchUsers(); // 重新獲取列表
        return response.data;
      } else {
        notificationService.error('錯誤', response.message || '更新用戶失敗');
        throw new Error(response.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '更新用戶失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  const deleteUser = useCallback(async (userId: string) => {
    try {
      const response = await mockAdminApiService.deleteUser(userId);
      if (response.success) {
        notificationService.success('成功', '用戶刪除成功');
        fetchUsers(); // 重新獲取列表
      } else {
        notificationService.error('錯誤', response.message || '刪除用戶失敗');
        throw new Error(response.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '刪除用戶失敗';
      notificationService.error('錯誤', message);
      throw err;
    }
  }, [fetchUsers]);

  return {
    users,
    loading,
    error,
    refetch: fetchUsers,
    createUser,
    updateUser,
    deleteUser
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