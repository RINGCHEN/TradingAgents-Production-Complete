/**
 * Professional Enterprise User Management Component
 * Advanced user management with modern UI/UX patterns
 * 
 * Features:
 * - Advanced data table with sorting, filtering, pagination
 * - Inline editing with real-time validation
 * - Bulk operations with progress tracking
 * - Advanced search with filters
 * - Export functionality (CSV, Excel, PDF)
 * - Real-time updates via WebSocket
 * - Accessibility compliance (WCAG 2.1)
 * - Mobile-responsive design
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { 
  DataTable, 
  AdvancedSearch, 
  BulkActionBar,
  UserFormDrawer,
  QuickActionMenu,
  ExportModal,
  ConfirmModal,
  LoadingSpinner,
  EmptyState,
  ErrorBoundary,
  Toast
} from '../common';
import { 
  useUsers, 
  useNotifications, 
  useRealTimeUpdates,
  useKeyboardShortcuts,
  useLocalStorage
} from '../../hooks/useAdminHooks';
import { 
  User, 
  UserRole, 
  UserStatus, 
  TableColumn, 
  PaginationParams,
  BulkActionType,
  ExportFormat,
  SearchFilters
} from '../../types/AdminTypes';
import { adminApiService } from '../../services/AdminApiService_Fixed';
import { formatDate, formatNumber, debounce } from '../../utils/helpers';
import './UserManagement.scss';

interface UserManagementProps {
  user?: any;
  theme: 'light' | 'dark';
  onNotification: (type: string, title: string, message: string) => void;
}

export const UserManagement: React.FC<UserManagementProps> = ({ 
  user, 
  theme, 
  onNotification 
}) => {
  // State Management
  const [viewMode, setViewMode] = useState<'table' | 'grid' | 'cards'>('table');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [searchFilters, setSearchFilters] = useLocalStorage<SearchFilters>('userManagementFilters', {
    query: '',
    status: [],
    role: [],
    membershipTier: [],
    dateRange: null,
    customFilters: {}
  });
  
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    limit: 25,
    sortBy: 'createdAt',
    sortOrder: 'desc'
  });
  
  const [modalState, setModalState] = useState({
    createUser: false,
    editUser: null as User | null,
    bulkAction: false,
    export: false,
    confirmDelete: null as User | null
  });

  // Hooks
  const { 
    users, 
    loading, 
    error, 
    totalCount,
    refetch, 
    createUser, 
    updateUser, 
    deleteUser,
    bulkUpdate,
    statistics 
  } = useUsers(pagination, searchFilters);
  
  const { showSuccess, showError, showWarning, showInfo } = useNotifications();
  const realTimeUpdates = useRealTimeUpdates('users');
  
  // Keyboard shortcuts
  useKeyboardShortcuts({
    'ctrl+n': () => setModalState(prev => ({ ...prev, createUser: true })),
    'ctrl+f': () => focusSearch(),
    'ctrl+a': () => handleSelectAll(),
    'delete': () => handleBulkDelete(),
    'ctrl+e': () => setModalState(prev => ({ ...prev, export: true }))
  });

  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null);
  const tableRef = useRef<HTMLDivElement>(null);

  // Memoized values
  const filteredUserCount = useMemo(() => users?.length || 0, [users]);
  const selectedUserCount = useMemo(() => selectedUsers.length, [selectedUsers]);
  
  const statusOptions = useMemo(() => [
    { value: UserStatus.ACTIVE, label: '活躍', color: 'success', count: statistics?.activeUsers || 0 },
    { value: UserStatus.INACTIVE, label: '非活躍', color: 'secondary', count: statistics?.inactiveUsers || 0 },
    { value: UserStatus.SUSPENDED, label: '暫停', color: 'warning', count: statistics?.suspendedUsers || 0 },
    { value: UserStatus.DELETED, label: '已刪除', color: 'danger', count: statistics?.deletedUsers || 0 }
  ], [statistics]);

  /**
   * ⚠️ Phase 1 限制說明：
   * - role 欄位目前固定為 UserRole.USER（在 userDataMapper 中）
   * - 不可用於權限判斷或 RBAC 控制
   * - 僅用於 UI 標籤顯示（向後兼容）
   *
   * TODO Phase 2:
   * - 後端實現真正的 role 欄位或 is_admin/is_manager 標記
   * - 前端啟用基於 role 的權限控制
   * - 啟用批量修改角色功能
   */
  const roleOptions = useMemo(() => [
    { value: UserRole.ADMIN, label: '管理員', color: 'danger', icon: 'fas fa-crown' },
    { value: UserRole.MANAGER, label: '經理', color: 'warning', icon: 'fas fa-user-tie' },
    { value: UserRole.USER, label: '用戶', color: 'primary', icon: 'fas fa-user' }
  ], []);

  // Table columns configuration
  const columns: TableColumn<User>[] = useMemo(() => [
    {
      key: 'select',
      title: (
        <div className="select-header">
          <input
            type="checkbox"
            className="form-check-input"
            checked={selectedUsers.length === users?.length && users.length > 0}
            onChange={handleSelectAll}
            aria-label="全選用戶"
          />
        </div>
      ),
      width: '50px',
      render: (_, record: User) => (
        <input
          type="checkbox"
          className="form-check-input"
          checked={selectedUsers.includes(record.id)}
          onChange={(e) => handleUserSelect(record.id, e.target.checked)}
          aria-label={`選擇用戶 ${record.email}`}
        />
      )
    },
    {
      key: 'user',
      title: '用戶信息',
      sortable: true,
      searchable: true,
      width: '300px',
      render: (_, record: User) => (
        <div className="user-cell">
          <div className="user-avatar">
            {record.avatarUrl ? (
              <img 
                src={record.avatarUrl} 
                alt={record.displayName || record.email}
                className="avatar-image"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            ) : (
              <div className="avatar-placeholder">
                {(record.displayName || record.email).charAt(0).toUpperCase()}
              </div>
            )}
            {record.status === UserStatus.ACTIVE && (
              <div className="online-indicator" title="在線"></div>
            )}
          </div>
          <div className="user-info">
            <div className="user-name">
              {record.displayName || `${record.firstName || ''} ${record.lastName || ''}`.trim() || '未設置姓名'}
            </div>
            <div className="user-email">{record.email}</div>
            {record.username && (
              <div className="user-username">@{record.username}</div>
            )}
            <div className="user-meta">
              <span className="auth-provider">
                <i className={`fab fa-${record.authProvider}`} aria-hidden="true"></i>
                {record.authProvider}
              </span>
              {record.emailVerified && (
                <span className="verified-badge" title="已驗證郵箱">
                  <i className="fas fa-check-circle" aria-hidden="true"></i>
                </span>
              )}
            </div>
          </div>
        </div>
      )
    },
    {
      key: 'role',
      title: '角色權限',
      sortable: true,
      filterable: true,
      width: '150px',
      render: (value: UserRole, record: User) => {
        // ⚠️ Phase 1: role 固定為 USER，僅用於 UI 顯示（不可用於權限判斷）
        const roleConfig = roleOptions.find(r => r.value === value);
        return (
          <div className="role-cell">
            <span className={`badge badge-${roleConfig?.color || 'secondary'}`}>
              <i className={roleConfig?.icon || 'fas fa-user'} aria-hidden="true"></i>
              {roleConfig?.label || value}
            </span>
            {record.permissions && record.permissions.length > 0 && (
              <div className="permissions-preview">
                <small>+{record.permissions.length} 權限</small>
              </div>
            )}
          </div>
        );
      }
    },
    {
      key: 'status',
      title: '狀態',
      sortable: true,
      filterable: true,
      width: '120px',
      render: (value: UserStatus, record: User) => {
        const statusConfig = statusOptions.find(s => s.value === value);
        return (
          <div className="status-cell">
            <span 
              className={`status-badge status-${statusConfig?.color || 'secondary'}`}
              data-status={value}
            >
              <span className="status-indicator"></span>
              {statusConfig?.label || value}
            </span>
            {record.lastLoginAt && (
              <div className="last-seen">
                <small>最近活動: {formatDate(record.lastLoginAt, 'relative')}</small>
              </div>
            )}
          </div>
        );
      }
    },
    {
      key: 'membership',
      title: '會員等級',
      sortable: true,
      filterable: true,
      width: '150px',
      render: (_, record: User) => (
        <div className="membership-cell">
          <div className={`membership-badge tier-${record.membershipTier.toLowerCase()}`}>
            <i className="fas fa-crown" aria-hidden="true"></i>
            {record.membershipTier}
          </div>
          <div className="usage-stats">
            <div className="usage-bar">
              <div 
                className="usage-fill"
                style={{ 
                  width: `${(record.apiCallsToday / record.dailyApiQuota) * 100}%` 
                }}
              ></div>
            </div>
            <small>
              {formatNumber(record.apiCallsToday)} / {formatNumber(record.dailyApiQuota)}
            </small>
          </div>
        </div>
      )
    },
    {
      key: 'analytics',
      title: '使用統計',
      sortable: true,
      width: '180px',
      render: (_, record: User) => (
        <div className="analytics-cell">
          <div className="stat-row">
            <span className="stat-label">總分析:</span>
            <span className="stat-value">{formatNumber(record.totalAnalyses)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">本月API:</span>
            <span className="stat-value">{formatNumber(record.apiCallsMonth)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">登入次數:</span>
            <span className="stat-value">{formatNumber(record.loginCount)}</span>
          </div>
        </div>
      )
    },
    {
      key: 'dates',
      title: '重要日期',
      sortable: true,
      width: '200px',
      render: (_, record: User) => (
        <div className="dates-cell">
          <div className="date-row">
            <span className="date-label">註冊:</span>
            <span className="date-value" title={formatDate(record.createdAt)}>
              {formatDate(record.createdAt, 'relative')}
            </span>
          </div>
          {record.lastLoginAt && (
            <div className="date-row">
              <span className="date-label">最近登入:</span>
              <span className="date-value" title={formatDate(record.lastLoginAt)}>
                {formatDate(record.lastLoginAt, 'relative')}
              </span>
            </div>
          )}
          <div className="date-row">
            <span className="date-label">更新:</span>
            <span className="date-value" title={formatDate(record.updatedAt)}>
              {formatDate(record.updatedAt, 'relative')}
            </span>
          </div>
        </div>
      )
    },
    {
      key: 'actions',
      title: '操作',
      width: '120px',
      sticky: 'right',
      render: (_, record: User) => (
        <div className="actions-cell">
          <QuickActionMenu
            items={[
              {
                key: 'view',
                label: '查看詳情',
                icon: 'fas fa-eye',
                onClick: () => handleViewUser(record)
              },
              {
                key: 'edit',
                label: '編輯用戶',
                icon: 'fas fa-edit',
                onClick: () => handleEditUser(record)
              },
              {
                key: 'permissions',
                label: '權限設置',
                icon: 'fas fa-shield-alt',
                onClick: () => handleManagePermissions(record)
              },
              {
                key: 'quota',
                label: '配額管理',
                icon: 'fas fa-chart-pie',
                onClick: () => handleManageQuota(record)
              },
              {
                type: 'divider'
              },
              {
                key: 'suspend',
                label: record.status === UserStatus.SUSPENDED ? '取消暫停' : '暫停用戶',
                icon: record.status === UserStatus.SUSPENDED ? 'fas fa-play' : 'fas fa-pause',
                onClick: () => handleToggleUserStatus(record),
                className: 'text-warning'
              },
              {
                key: 'delete',
                label: '刪除用戶',
                icon: 'fas fa-trash',
                onClick: () => handleDeleteUser(record),
                className: 'text-danger'
              }
            ]}
          />
        </div>
      )
    }
  ], [users, selectedUsers, statusOptions, roleOptions]);

  // Event Handlers
  const handleUserSelect = useCallback((userId: string, selected: boolean) => {
    setSelectedUsers(prev => 
      selected 
        ? [...prev, userId]
        : prev.filter(id => id !== userId)
    );
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedUsers.length === users?.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users?.map(u => u.id) || []);
    }
  }, [selectedUsers, users]);

  const handleSearch = useCallback(
    debounce((query: string) => {
      setSearchFilters(prev => ({ ...prev, query }));
      setPagination(prev => ({ ...prev, page: 1 }));
    }, 300),
    []
  );

  const handleFilterChange = useCallback((filters: Partial<SearchFilters>) => {
    setSearchFilters(prev => ({ ...prev, ...filters }));
    setPagination(prev => ({ ...prev, page: 1 }));
  }, []);

  const handleCreateUser = useCallback(async (userData: Partial<User>) => {
    try {
      await createUser(userData);
      setModalState(prev => ({ ...prev, createUser: false }));
      onNotification('success', '創建成功', '用戶已成功創建');
      
      // Refresh data
      refetch();
    } catch (error) {
      onNotification('error', '創建失敗', '無法創建用戶，請檢查輸入信息');
    }
  }, [createUser, onNotification, refetch]);

  const handleEditUser = useCallback((user: User) => {
    setModalState(prev => ({ ...prev, editUser: user }));
  }, []);

  const handleUpdateUser = useCallback(async (userData: Partial<User>) => {
    if (!modalState.editUser) return;
    
    try {
      await updateUser(modalState.editUser.id, userData);
      setModalState(prev => ({ ...prev, editUser: null }));
      onNotification('success', '更新成功', '用戶信息已更新');
      
      // Refresh data
      refetch();
    } catch (error) {
      onNotification('error', '更新失敗', '無法更新用戶信息');
    }
  }, [modalState.editUser, updateUser, onNotification, refetch]);

  const handleDeleteUser = useCallback((user: User) => {
    setModalState(prev => ({ ...prev, confirmDelete: user }));
  }, []);

  const confirmDeleteUser = useCallback(async () => {
    if (!modalState.confirmDelete) return;
    
    try {
      await deleteUser(modalState.confirmDelete.id);
      setModalState(prev => ({ ...prev, confirmDelete: null }));
      onNotification('success', '刪除成功', '用戶已被刪除');
      
      // Remove from selection if selected
      setSelectedUsers(prev => prev.filter(id => id !== modalState.confirmDelete?.id));
      
      // Refresh data
      refetch();
    } catch (error) {
      onNotification('error', '刪除失敗', '無法刪除用戶');
    }
  }, [modalState.confirmDelete, deleteUser, onNotification, refetch]);

  const handleBulkAction = useCallback(async (action: BulkActionType, data?: any) => {
    if (selectedUsers.length === 0) {
      onNotification('warning', '請選擇用戶', '請至少選擇一個用戶進行批量操作');
      return;
    }

    try {
      await bulkUpdate(selectedUsers, action, data);
      onNotification('success', '批量操作成功', `已對 ${selectedUsers.length} 個用戶執行操作`);
      
      // Clear selection
      setSelectedUsers([]);
      
      // Refresh data
      refetch();
    } catch (error) {
      onNotification('error', '批量操作失敗', '無法完成批量操作');
    }
  }, [selectedUsers, bulkUpdate, onNotification, refetch]);

  const handleBulkDelete = useCallback(() => {
    if (selectedUsers.length === 0) return;
    
    // Show confirmation for bulk delete
    if (confirm(`確定要刪除 ${selectedUsers.length} 個用戶嗎？此操作無法撤銷。`)) {
      handleBulkAction('delete');
    }
  }, [selectedUsers, handleBulkAction]);

  const handleExport = useCallback(async (format: ExportFormat, options: any) => {
    try {
      const exportData = {
        format,
        filters: searchFilters,
        selectedUsers: selectedUsers.length > 0 ? selectedUsers : undefined,
        ...options
      };
      
      await adminApiService.exportUsers(exportData);
      setModalState(prev => ({ ...prev, export: false }));
      onNotification('info', '導出已開始', '文件準備完成後將自動下載');
    } catch (error) {
      onNotification('error', '導出失敗', '無法導出用戶數據');
    }
  }, [searchFilters, selectedUsers, onNotification]);

  const handleViewUser = useCallback((user: User) => {
    // Navigate to user detail page or show user detail modal
    console.log('View user:', user);
  }, []);

  const handleManagePermissions = useCallback((user: User) => {
    // Open permissions management for user
    console.log('Manage permissions for user:', user);
  }, []);

  const handleManageQuota = useCallback((user: User) => {
    // Open quota management for user
    console.log('Manage quota for user:', user);
  }, []);

  const handleToggleUserStatus = useCallback(async (user: User) => {
    const newStatus = user.status === UserStatus.SUSPENDED ? UserStatus.ACTIVE : UserStatus.SUSPENDED;
    
    try {
      await updateUser(user.id, { status: newStatus });
      onNotification('success', '狀態已更新', `用戶狀態已更改為${newStatus === UserStatus.ACTIVE ? '活躍' : '暫停'}`);
      refetch();
    } catch (error) {
      onNotification('error', '狀態更新失敗', '無法更新用戶狀態');
    }
  }, [updateUser, onNotification, refetch]);

  const focusSearch = useCallback(() => {
    searchInputRef.current?.focus();
  }, []);

  // Effects
  useEffect(() => {
    // Handle real-time updates
    if (realTimeUpdates) {
      refetch();
    }
  }, [realTimeUpdates, refetch]);

  // Error boundary fallback
  if (error) {
    return (
      <div className="user-management-error">
        <EmptyState
          icon="fas fa-exclamation-triangle"
          title="載入錯誤"
          description={error}
          actions={[
            {
              label: '重新載入',
              onClick: refetch,
              variant: 'primary'
            }
          ]}
        />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className={`user-management theme-${theme}`}>
        {/* Header Section */}
        <div className="page-header">
          <div className="header-content">
            <div className="header-title">
              <h1>用戶管理</h1>
              <p className="header-description">
                全面的用戶管理和權限控制系統
              </p>
            </div>
            
            <div className="header-actions">
              <button
                className="btn btn-outline-secondary"
                onClick={() => setModalState(prev => ({ ...prev, export: true }))}
                aria-label="導出用戶數據"
              >
                <i className="fas fa-download" aria-hidden="true"></i>
                <span>導出</span>
              </button>
              
              <button
                className="btn btn-primary"
                onClick={() => setModalState(prev => ({ ...prev, createUser: true }))}
                aria-label="創建新用戶"
              >
                <i className="fas fa-plus" aria-hidden="true"></i>
                <span>新增用戶</span>
              </button>
            </div>
          </div>

          {/* Statistics Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">
                <i className="fas fa-users" aria-hidden="true"></i>
              </div>
              <div className="stat-content">
                <div className="stat-number">{formatNumber(totalCount)}</div>
                <div className="stat-label">總用戶數</div>
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon active">
                <i className="fas fa-user-check" aria-hidden="true"></i>
              </div>
              <div className="stat-content">
                <div className="stat-number">{formatNumber(statistics?.activeUsers || 0)}</div>
                <div className="stat-label">活躍用戶</div>
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon premium">
                <i className="fas fa-crown" aria-hidden="true"></i>
              </div>
              <div className="stat-content">
                <div className="stat-number">{formatNumber(statistics?.premiumUsers || 0)}</div>
                <div className="stat-label">付費用戶</div>
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon new">
                <i className="fas fa-user-plus" aria-hidden="true"></i>
              </div>
              <div className="stat-content">
                <div className="stat-number">{formatNumber(statistics?.newUsersToday || 0)}</div>
                <div className="stat-label">今日新增</div>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="search-section">
          <AdvancedSearch
            ref={searchInputRef}
            placeholder="搜索用戶姓名、郵箱、用戶名..."
            value={searchFilters.query}
            onChange={handleSearch}
            filters={searchFilters}
            onFiltersChange={handleFilterChange}
            statusOptions={statusOptions}
            roleOptions={roleOptions}
            loading={loading}
          />
          
          <div className="view-controls">
            <div className="view-mode-selector">
              <button
                className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
                onClick={() => setViewMode('table')}
                aria-label="表格視圖"
              >
                <i className="fas fa-table" aria-hidden="true"></i>
              </button>
              <button
                className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                aria-label="網格視圖"
              >
                <i className="fas fa-th" aria-hidden="true"></i>
              </button>
              <button
                className={`view-btn ${viewMode === 'cards' ? 'active' : ''}`}
                onClick={() => setViewMode('cards')}
                aria-label="卡片視圖"
              >
                <i className="fas fa-id-card" aria-hidden="true"></i>
              </button>
            </div>
            
            <button
              className="btn btn-outline-secondary btn-sm"
              onClick={refetch}
              disabled={loading}
              aria-label="刷新數據"
            >
              <i className={`fas fa-sync-alt ${loading ? 'fa-spin' : ''}`} aria-hidden="true"></i>
              <span>刷新</span>
            </button>
          </div>
        </div>

        {/* Bulk Action Bar */}
        {selectedUserCount > 0 && (
          <BulkActionBar
            selectedCount={selectedUserCount}
            onAction={handleBulkAction}
            onClearSelection={() => setSelectedUsers([])}
            actions={[
              { key: 'activate', label: '批量激活', icon: 'fas fa-check' },
              { key: 'suspend', label: '批量暫停', icon: 'fas fa-pause' },
              // TODO Phase 2: 啟用批量修改角色功能（需要後端實現真正的 role 欄位）
              // { key: 'updateRole', label: '批量修改角色', icon: 'fas fa-user-tag' },
              { key: 'export', label: '導出選中', icon: 'fas fa-download' },
              { key: 'delete', label: '批量刪除', icon: 'fas fa-trash', variant: 'danger' }
            ]}
          />
        )}

        {/* Main Content */}
        <div className="content-section">
          {loading && users?.length === 0 ? (
            <div className="loading-container">
              <LoadingSpinner size="large" />
              <p>正在載入用戶數據...</p>
            </div>
          ) : users?.length === 0 ? (
            <EmptyState
              icon="fas fa-users"
              title="暫無用戶"
              description="尚未找到符合條件的用戶，請嘗試調整搜索條件或創建新用戶。"
              actions={[
                {
                  label: '創建用戶',
                  onClick: () => setModalState(prev => ({ ...prev, createUser: true })),
                  variant: 'primary'
                },
                {
                  label: '清除篩選',
                  onClick: () => setSearchFilters({
                    query: '',
                    status: [],
                    role: [],
                    membershipTier: [],
                    dateRange: null,
                    customFilters: {}
                  }),
                  variant: 'outline'
                }
              ]}
            />
          ) : (
            <div className="data-container">
              {viewMode === 'table' && (
                <DataTable
                  ref={tableRef}
                  columns={columns}
                  dataSource={users}
                  loading={loading}
                  pagination={{
                    ...pagination,
                    total: totalCount
                  }}
                  onPaginationChange={setPagination}
                  selection={{
                    selectedRowKeys: selectedUsers,
                    onChange: setSelectedUsers,
                    onSelectAll: handleSelectAll
                  }}
                  rowKey="id"
                  className="user-table"
                  sticky={true}
                  virtual={totalCount > 100}
                />
              )}
              
              {/* TODO: Implement grid and cards view modes */}
            </div>
          )}
        </div>

        {/* Modals and Drawers */}
        {modalState.createUser && (
          <UserFormDrawer
            title="創建新用戶"
            open={modalState.createUser}
            onClose={() => setModalState(prev => ({ ...prev, createUser: false }))}
            onSubmit={handleCreateUser}
            roleOptions={roleOptions}
            statusOptions={statusOptions}
          />
        )}

        {modalState.editUser && (
          <UserFormDrawer
            title="編輯用戶"
            open={!!modalState.editUser}
            onClose={() => setModalState(prev => ({ ...prev, editUser: null }))}
            onSubmit={handleUpdateUser}
            initialData={modalState.editUser}
            roleOptions={roleOptions}
            statusOptions={statusOptions}
          />
        )}

        {modalState.export && (
          <ExportModal
            open={modalState.export}
            onClose={() => setModalState(prev => ({ ...prev, export: false }))}
            onExport={handleExport}
            totalRecords={totalCount}
            selectedRecords={selectedUserCount}
          />
        )}

        {modalState.confirmDelete && (
          <ConfirmModal
            open={!!modalState.confirmDelete}
            onClose={() => setModalState(prev => ({ ...prev, confirmDelete: null }))}
            onConfirm={confirmDeleteUser}
            title="確認刪除用戶"
            message={
              <>
                <p>您即將刪除用戶:</p>
                <div className="user-info-preview">
                  <strong>{modalState.confirmDelete.displayName || modalState.confirmDelete.email}</strong>
                  <small>{modalState.confirmDelete.email}</small>
                </div>
                <p className="text-danger">
                  <i className="fas fa-exclamation-triangle" aria-hidden="true"></i>
                  此操作無法撤銷，用戶的所有數據將被永久刪除。
                </p>
              </>
            }
            confirmText="確認刪除"
            cancelText="取消"
            variant="danger"
          />
        )}
      </div>
    </ErrorBoundary>
  );
};

export default UserManagement;