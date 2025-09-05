#!/usr/bin/env python3
"""
統一管理後台架構生成器 - 第四部分
React Hooks和狀態管理
"""

class HooksGenerator:
    """React Hooks生成器"""
    
    def __init__(self, base_path: str):
        self.hooks_path = f"{base_path}/admin/hooks"
    
    def generate_admin_hooks(self) -> str:
        """生成管理後台專用Hooks"""
        return '''/**
 * 管理後台專用React Hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { adminApiService } from '../services/AdminApiService';
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
  return useApiCall(() => adminApiService.getSystemStatus(), []);
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
      const response = await adminApiService.getUsers(pagination);
      if (response.success) {
        setUsers(response.data.data);
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
      const response = await adminApiService.createUser(userData);
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
      const response = await adminApiService.updateUser(userId, userData);
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
      const response = await adminApiService.deleteUser(userId);
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
}'''