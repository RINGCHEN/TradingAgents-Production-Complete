import React, { useState, useEffect } from 'react';
import './UserDetailsManagement.css';
import { authService } from '../services/AuthService';

// 用戶數據接口定義
interface User {
  user_id: string;
  username: string;
  email: string;
  membership_tier: 'FREE' | 'GOLD' | 'DIAMOND';
  registration_date: string;
  last_login: string;
  status: 'active' | 'suspended' | 'inactive';
  login_count: number;
  total_api_calls: number;
  subscription_expiry?: string;
  preferences: {
    notifications: boolean;
    dark_mode: boolean;
    auto_analysis: boolean;
  };
  usage_stats: {
    this_month_api_calls: number;
    this_month_analysis: number;
    total_analysis: number;
  };
}

// 用戶篩選條件
interface UserFilters {
  status: string;
  membership_tier: string;
  search: string;
  date_range: string;
}

const UserDetailsManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<UserFilters>({
    status: 'all',
    membership_tier: 'all',
    search: '',
    date_range: 'all'
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState<string>('registration_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showUserModal, setShowUserModal] = useState(false);

  // 獲取用戶列表
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20',
        sort_by: sortBy,
        sort_order: sortOrder,
        ...filters
      });

      const response = await authService.authenticatedRequest(
        `/admin/users?${queryParams}`
      );

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
        setTotalPages(data.total_pages || 1);
      } else {
        throw new Error('載入用戶列表失敗');
      }
    } catch (error) {
      console.error('獲取用戶列表失敗:', error);
      setError('載入用戶資料失敗');
    } finally {
      setLoading(false);
    }
  };

  // 獲取用戶詳細信息
  const fetchUserDetails = async (userId: string) => {
    try {
      const response = await authService.authenticatedRequest(
        `/admin/users/${userId}/details`
      );

      if (response.ok) {
        const userData = await response.json();
        setSelectedUser(userData);
        setShowUserModal(true);
      } else {
        throw new Error('載入用戶詳情失敗');
      }
    } catch (error) {
      console.error('獲取用戶詳情失敗:', error);
      alert('載入用戶詳細資料失敗');
    }
  };

  // 更新用戶狀態
  const updateUserStatus = async (userId: string, newStatus: string) => {
    try {
      const response = await authService.authenticatedRequest(
        `/admin/users/${userId}/status`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        }
      );

      if (response.ok) {
        // 更新本地狀態
        setUsers(prev => prev.map(user => 
          user.user_id === userId 
            ? { ...user, status: newStatus as any }
            : user
        ));

        if (selectedUser && selectedUser.user_id === userId) {
          setSelectedUser(prev => prev ? { ...prev, status: newStatus as any } : null);
        }

        alert(`用戶狀態已更新為: ${newStatus}`);
      } else {
        throw new Error('更新用戶狀態失敗');
      }
    } catch (error) {
      console.error('更新用戶狀態失敗:', error);
      alert('更新用戶狀態失敗');
    }
  };

  // 更新會員等級
  const updateMembershipTier = async (userId: string, newTier: string) => {
    try {
      const response = await authService.authenticatedRequest(
        `/admin/users/${userId}/membership`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ membership_tier: newTier })
        }
      );

      if (response.ok) {
        // 更新本地狀態
        setUsers(prev => prev.map(user => 
          user.user_id === userId 
            ? { ...user, membership_tier: newTier as any }
            : user
        ));

        if (selectedUser && selectedUser.user_id === userId) {
          setSelectedUser(prev => prev ? { ...prev, membership_tier: newTier as any } : null);
        }

        alert(`會員等級已更新為: ${newTier}`);
      } else {
        throw new Error('更新會員等級失敗');
      }
    } catch (error) {
      console.error('更新會員等級失敗:', error);
      alert('更新會員等級失敗');
    }
  };

  // 重置用戶密碼
  const resetUserPassword = async (userId: string) => {
    const confirmReset = window.confirm('確定要重置此用戶的密碼嗎？');
    if (!confirmReset) return;

    try {
      const response = await authService.authenticatedRequest(
        `/admin/users/${userId}/reset-password`,
        { method: 'POST' }
      );

      if (response.ok) {
        const data = await response.json();
        alert(`密碼已重置。新密碼: ${data.new_password}`);
      } else {
        throw new Error('重置密碼失敗');
      }
    } catch (error) {
      console.error('重置密碼失敗:', error);
      alert('重置用戶密碼失敗');
    }
  };

  // 導出用戶數據
  const exportUserData = async (format: 'csv' | 'json' = 'csv') => {
    try {
      const response = await authService.authenticatedRequest(
        `/admin/users/export?format=${format}&${new URLSearchParams(filters)}`
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `users_export_${new Date().toISOString().split('T')[0]}.${format}`;
        link.click();
        window.URL.revokeObjectURL(url);
      } else {
        throw new Error('導出用戶數據失敗');
      }
    } catch (error) {
      console.error('導出用戶數據失敗:', error);
      alert('導出用戶數據失敗');
    }
  };

  // 初始化和依賴更新
  useEffect(() => {
    fetchUsers();
  }, [currentPage, sortBy, sortOrder, filters]);

  // 篩選變更處理
  const handleFilterChange = (key: keyof UserFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // 重置到第一頁
  };

  // 排序變更處理
  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  // 獲取會員等級顯示樣式
  const getMembershipBadgeClass = (tier: string) => {
    const classes = {
      FREE: 'membership-free',
      GOLD: 'membership-gold',
      DIAMOND: 'membership-diamond'
    };
    return classes[tier as keyof typeof classes] || 'membership-free';
  };

  // 獲取狀態顯示樣式
  const getStatusBadgeClass = (status: string) => {
    const classes = {
      active: 'status-active',
      suspended: 'status-suspended',
      inactive: 'status-inactive'
    };
    return classes[status as keyof typeof classes] || 'status-inactive';
  };

  // 格式化時間
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW');
  };

  // 格式化時間（相對時間）
  const formatRelativeTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '昨天';
    if (diffDays < 7) return `${diffDays}天前`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}週前`;
    return `${Math.floor(diffDays / 30)}個月前`;
  };

  if (loading) {
    return (
      <div className="user-management">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>載入用戶資料...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-management">
        <div className="error-container">
          <h3>❌ 載入失敗</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>重新載入</button>
        </div>
      </div>
    );
  }

  return (
    <div className="user-management">
      <div className="management-header">
        <div className="header-title">
          <h2>👥 用戶詳情管理</h2>
          <p>管理系統用戶帳戶、會員等級和使用權限</p>
        </div>
        <div className="header-actions">
          <button 
            className="export-btn"
            onClick={() => exportUserData('csv')}
            title="導出為CSV"
          >
            📊 導出CSV
          </button>
          <button 
            className="export-btn"
            onClick={() => exportUserData('json')}
            title="導出為JSON"
          >
            📄 導出JSON
          </button>
        </div>
      </div>

      {/* 篩選和搜索區域 */}
      <div className="filters-section">
        <div className="filters-row">
          <div className="filter-group">
            <label>搜索用戶:</label>
            <input
              type="text"
              placeholder="用戶名或email..."
              value={filters.search}
              onChange={(e: any) => handleFilterChange('search', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <label>狀態:</label>
            <select
              value={filters.status}
              onChange={(e: any) => handleFilterChange('status', e.target.value)}
            >
              <option value="all">所有狀態</option>
              <option value="active">活躍</option>
              <option value="suspended">暫停</option>
              <option value="inactive">非活躍</option>
            </select>
          </div>

          <div className="filter-group">
            <label>會員等級:</label>
            <select
              value={filters.membership_tier}
              onChange={(e: any) => handleFilterChange('membership_tier', e.target.value)}
            >
              <option value="all">所有等級</option>
              <option value="FREE">免費用戶</option>
              <option value="GOLD">黃金會員</option>
              <option value="DIAMOND">鑽石會員</option>
            </select>
          </div>

          <div className="filter-group">
            <label>註冊時間:</label>
            <select
              value={filters.date_range}
              onChange={(e: any) => handleFilterChange('date_range', e.target.value)}
            >
              <option value="all">所有時間</option>
              <option value="today">今天</option>
              <option value="week">本週</option>
              <option value="month">本月</option>
              <option value="quarter">本季</option>
            </select>
          </div>
        </div>

        <div className="results-info">
          <span>共找到 {users.length} 位用戶</span>
        </div>
      </div>

      {/* 用戶列表 */}
      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('username')} className="sortable">
                用戶名 {sortBy === 'username' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('email')} className="sortable">
                Email {sortBy === 'email' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('membership_tier')} className="sortable">
                會員等級 {sortBy === 'membership_tier' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('status')} className="sortable">
                狀態 {sortBy === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('last_login')} className="sortable">
                最後登錄 {sortBy === 'last_login' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('total_api_calls')} className="sortable">
                API調用 {sortBy === 'total_api_calls' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.user_id} className="user-row">
                <td className="username-cell">
                  <div className="user-info">
                    <span className="username">{user.username}</span>
                    <span className="user-id">ID: {user.user_id}</span>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>
                  <span className={`membership-badge ${getMembershipBadgeClass(user.membership_tier)}`}>
                    {user.membership_tier}
                  </span>
                </td>
                <td>
                  <span className={`status-badge ${getStatusBadgeClass(user.status)}`}>
                    {user.status}
                  </span>
                </td>
                <td className="last-login-cell">
                  <span className="relative-time">{formatRelativeTime(user.last_login)}</span>
                  <span className="absolute-time">{formatDate(user.last_login)}</span>
                </td>
                <td className="api-calls">{user.total_api_calls.toLocaleString()}</td>
                <td className="actions-cell">
                  <div className="action-buttons">
                    <button
                      className="view-btn"
                      onClick={() => fetchUserDetails(user.user_id)}
                      title="查看詳情"
                    >
                      👁️
                    </button>
                    <button
                      className="edit-btn"
                      onClick={() => {/* TODO: 實施編輯功能 */}}
                      title="編輯用戶"
                    >
                      ✏️
                    </button>
                    <button
                      className="reset-btn"
                      onClick={() => resetUserPassword(user.user_id)}
                      title="重置密碼"
                    >
                      🔑
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分頁控制 */}
      <div className="pagination">
        <button 
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
        >
          ← 上一頁
        </button>
        
        <div className="page-info">
          第 {currentPage} 頁，共 {totalPages} 頁
        </div>
        
        <button 
          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
        >
          下一頁 →
        </button>
      </div>

      {/* 用戶詳情模態框 */}
      {showUserModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowUserModal(false)}>
          <div className="user-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>用戶詳細資料</h3>
              <button className="close-btn" onClick={() => setShowUserModal(false)}>×</button>
            </div>
            
            <div className="modal-content">
              <div className="user-details-grid">
                {/* 基本信息 */}
                <div className="detail-section">
                  <h4>📋 基本信息</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>用戶ID:</label>
                      <span>{selectedUser.user_id}</span>
                    </div>
                    <div className="detail-item">
                      <label>用戶名:</label>
                      <span>{selectedUser.username}</span>
                    </div>
                    <div className="detail-item">
                      <label>Email:</label>
                      <span>{selectedUser.email}</span>
                    </div>
                    <div className="detail-item">
                      <label>註冊時間:</label>
                      <span>{formatDate(selectedUser.registration_date)}</span>
                    </div>
                  </div>
                </div>

                {/* 會員信息 */}
                <div className="detail-section">
                  <h4>💎 會員信息</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>會員等級:</label>
                      <div className="membership-controls">
                        <span className={`membership-badge ${getMembershipBadgeClass(selectedUser.membership_tier)}`}>
                          {selectedUser.membership_tier}
                        </span>
                        <select
                          value={selectedUser.membership_tier}
                          onChange={(e: any) => updateMembershipTier(selectedUser.user_id, e.target.value)}
                        >
                          <option value="FREE">免費用戶</option>
                          <option value="GOLD">黃金會員</option>
                          <option value="DIAMOND">鑽石會員</option>
                        </select>
                      </div>
                    </div>
                    <div className="detail-item">
                      <label>狀態:</label>
                      <div className="status-controls">
                        <span className={`status-badge ${getStatusBadgeClass(selectedUser.status)}`}>
                          {selectedUser.status}
                        </span>
                        <select
                          value={selectedUser.status}
                          onChange={(e: any) => updateUserStatus(selectedUser.user_id, e.target.value)}
                        >
                          <option value="active">活躍</option>
                          <option value="suspended">暫停</option>
                          <option value="inactive">非活躍</option>
                        </select>
                      </div>
                    </div>
                    {selectedUser.subscription_expiry && (
                      <div className="detail-item">
                        <label>訂閱到期:</label>
                        <span>{formatDate(selectedUser.subscription_expiry)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 使用統計 */}
                <div className="detail-section">
                  <h4>📊 使用統計</h4>
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="stat-value">{selectedUser.login_count}</div>
                      <div className="stat-label">總登錄次數</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{selectedUser.total_api_calls.toLocaleString()}</div>
                      <div className="stat-label">總API調用</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{selectedUser.usage_stats.this_month_api_calls}</div>
                      <div className="stat-label">本月API調用</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{selectedUser.usage_stats.total_analysis}</div>
                      <div className="stat-label">總分析次數</div>
                    </div>
                  </div>
                </div>

                {/* 用戶偏好 */}
                <div className="detail-section">
                  <h4>⚙️ 用戶偏好</h4>
                  <div className="preferences-grid">
                    <div className="preference-item">
                      <label>通知:</label>
                      <span className={selectedUser.preferences.notifications ? 'enabled' : 'disabled'}>
                        {selectedUser.preferences.notifications ? '✅ 開啟' : '❌ 關閉'}
                      </span>
                    </div>
                    <div className="preference-item">
                      <label>深色模式:</label>
                      <span className={selectedUser.preferences.dark_mode ? 'enabled' : 'disabled'}>
                        {selectedUser.preferences.dark_mode ? '✅ 開啟' : '❌ 關閉'}
                      </span>
                    </div>
                    <div className="preference-item">
                      <label>自動分析:</label>
                      <span className={selectedUser.preferences.auto_analysis ? 'enabled' : 'disabled'}>
                        {selectedUser.preferences.auto_analysis ? '✅ 開啟' : '❌ 關閉'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button 
                className="reset-password-btn"
                onClick={() => resetUserPassword(selectedUser.user_id)}
              >
                🔑 重置密碼
              </button>
              <button 
                className="close-modal-btn"
                onClick={() => setShowUserModal(false)}
              >
                關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserDetailsManagement;