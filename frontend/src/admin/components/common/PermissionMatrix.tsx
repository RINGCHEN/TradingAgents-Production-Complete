/**
 * PermissionMatrix - 權限矩陣編輯器組件
 * 提供視覺化的權限管理界面，支援角色權限批量編輯
 * 支援權限組、繼承、條件權限等高級功能
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';

export interface Permission {
  id: string;
  name: string;
  description: string;
  category: string;
  module: string;
  actions: string[];
  dependencies?: string[];
  isSystemPermission?: boolean;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  level: number;
  permissions: string[];
  inheritsFrom?: string[];
  isSystemRole?: boolean;
  color?: string;
}

export interface PermissionGroup {
  id: string;
  name: string;
  permissions: string[];
  description?: string;
}

export interface PermissionMatrixProps {
  roles?: Role[];
  permissions?: Permission[];
  permissionGroups?: PermissionGroup[];
  enableRoleInheritance?: boolean;
  enablePermissionGroups?: boolean;
  enableBulkEdit?: boolean;
  readOnly?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onPermissionChange?: (roleId: string, permissionId: string, granted: boolean) => void;
  onRoleChange?: (role: Role) => void;
  onBulkPermissionChange?: (changes: Array<{roleId: string, permissionId: string, granted: boolean}>) => void;
  onSave?: (roles: Role[]) => void;
}

/**
 * PermissionMatrix - 權限矩陣編輯器
 * 提供完整的權限管理和編輯功能
 */
export const PermissionMatrix: React.FC<PermissionMatrixProps> = ({
  roles: initialRoles = [],
  permissions: initialPermissions = [],
  permissionGroups: initialGroups = [],
  enableRoleInheritance = true,
  enablePermissionGroups = true,
  enableBulkEdit = true,
  readOnly = false,
  className = '',
  style = {},
  onPermissionChange,
  onRoleChange,
  onBulkPermissionChange,
  onSave
}) => {
  const [roles, setRoles] = useState<Role[]>(initialRoles);
  const [permissions, setPermissions] = useState<Permission[]>(initialPermissions);
  const [permissionGroups, setPermissionGroups] = useState<PermissionGroup[]>(initialGroups);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showInheritedPermissions, setShowInheritedPermissions] = useState(true);
  const [bulkEditMode, setBulkEditMode] = useState(false);
  const [selectedCells, setSelectedCells] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // 生成模擬數據
  const generateMockData = useCallback(() => {
    const mockPermissions: Permission[] = [
      {
        id: 'user_read',
        name: '查看用戶',
        description: '查看用戶列表和詳細信息',
        category: '用戶管理',
        module: 'users',
        actions: ['read']
      },
      {
        id: 'user_write',
        name: '編輯用戶',
        description: '創建、編輯和刪除用戶',
        category: '用戶管理',
        module: 'users',
        actions: ['create', 'update', 'delete'],
        dependencies: ['user_read']
      },
      {
        id: 'analytics_read',
        name: '查看分析',
        description: '查看系統分析數據',
        category: '數據分析',
        module: 'analytics',
        actions: ['read']
      },
      {
        id: 'analytics_export',
        name: '導出數據',
        description: '導出分析數據報告',
        category: '數據分析',
        module: 'analytics',
        actions: ['export'],
        dependencies: ['analytics_read']
      },
      {
        id: 'system_config',
        name: '系統配置',
        description: '修改系統配置和設置',
        category: '系統管理',
        module: 'system',
        actions: ['read', 'write'],
        isSystemPermission: true
      },
      {
        id: 'financial_read',
        name: '查看財務',
        description: '查看財務數據和報告',
        category: '財務管理',
        module: 'financial',
        actions: ['read']
      },
      {
        id: 'financial_write',
        name: '管理財務',
        description: '管理財務數據和交易',
        category: '財務管理',
        module: 'financial',
        actions: ['create', 'update', 'delete'],
        dependencies: ['financial_read']
      },
      {
        id: 'content_read',
        name: '查看內容',
        description: '查看內容管理系統',
        category: '內容管理',
        module: 'content',
        actions: ['read']
      },
      {
        id: 'content_write',
        name: '編輯內容',
        description: '創建和編輯內容',
        category: '內容管理',
        module: 'content',
        actions: ['create', 'update', 'delete'],
        dependencies: ['content_read']
      },
      {
        id: 'subscription_read',
        name: '查看訂閱',
        description: '查看用戶訂閱信息',
        category: '訂閱管理',
        module: 'subscription',
        actions: ['read']
      },
      {
        id: 'subscription_write',
        name: '管理訂閱',
        description: '管理用戶訂閱和計劃',
        category: '訂閱管理',
        module: 'subscription',
        actions: ['create', 'update', 'delete'],
        dependencies: ['subscription_read']
      }
    ];

    const mockRoles: Role[] = [
      {
        id: 'super_admin',
        name: '超級管理員',
        description: '系統最高權限用戶',
        level: 100,
        permissions: mockPermissions.map(p => p.id),
        isSystemRole: true,
        color: '#ff6b6b'
      },
      {
        id: 'admin',
        name: '管理員',
        description: '系統管理員',
        level: 80,
        permissions: mockPermissions.filter(p => !p.isSystemPermission).map(p => p.id),
        color: '#4ecdc4'
      },
      {
        id: 'manager',
        name: '經理',
        description: '部門經理',
        level: 60,
        permissions: ['user_read', 'analytics_read', 'analytics_export', 'financial_read', 'content_read', 'subscription_read'],
        inheritsFrom: [],
        color: '#45b7d1'
      },
      {
        id: 'analyst',
        name: '分析師',
        description: '數據分析師',
        level: 40,
        permissions: ['analytics_read', 'analytics_export', 'financial_read'],
        color: '#96ceb4'
      },
      {
        id: 'editor',
        name: '編輯',
        description: '內容編輯員',
        level: 30,
        permissions: ['content_read', 'content_write'],
        color: '#feca57'
      },
      {
        id: 'user',
        name: '普通用戶',
        description: '基本用戶權限',
        level: 10,
        permissions: ['user_read'],
        color: '#a8e6cf'
      }
    ];

    const mockGroups: PermissionGroup[] = [
      {
        id: 'basic_access',
        name: '基礎權限',
        permissions: ['user_read', 'analytics_read'],
        description: '基本系統訪問權限'
      },
      {
        id: 'content_management',
        name: '內容管理',
        permissions: ['content_read', 'content_write'],
        description: '內容管理相關權限'
      },
      {
        id: 'financial_access',
        name: '財務權限',
        permissions: ['financial_read', 'financial_write'],
        description: '財務管理相關權限'
      }
    ];

    return { mockPermissions, mockRoles, mockGroups };
  }, []);

  // 初始化數據
  useEffect(() => {
    if (roles.length === 0 || permissions.length === 0) {
      const { mockPermissions, mockRoles, mockGroups } = generateMockData();
      setPermissions(mockPermissions);
      setRoles(mockRoles);
      setPermissionGroups(mockGroups);
    }
  }, [generateMockData, roles.length, permissions.length]);

  // 計算有效權限（包含繼承）
  const getEffectivePermissions = useCallback((role: Role): string[] => {
    if (!enableRoleInheritance || !role.inheritsFrom) {
      return role.permissions;
    }

    const inheritedPermissions = new Set(role.permissions);
    
    const processInheritance = (roleId: string, visited: Set<string> = new Set()) => {
      if (visited.has(roleId)) return; // 防止循環繼承
      visited.add(roleId);
      
      const parentRole = roles.find(r => r.id === roleId);
      if (parentRole) {
        parentRole.permissions.forEach(p => inheritedPermissions.add(p));
        if (parentRole.inheritsFrom) {
          parentRole.inheritsFrom.forEach(parentId => processInheritance(parentId, visited));
        }
      }
    };

    role.inheritsFrom.forEach(parentId => processInheritance(parentId));
    
    return Array.from(inheritedPermissions);
  }, [roles, enableRoleInheritance]);

  // 檢查權限是否被授予
  const hasPermission = useCallback((roleId: string, permissionId: string): boolean => {
    const role = roles.find(r => r.id === roleId);
    if (!role) return false;

    const effectivePermissions = getEffectivePermissions(role);
    return effectivePermissions.includes(permissionId);
  }, [roles, getEffectivePermissions]);

  // 檢查權限是否繼承而來
  const isInheritedPermission = useCallback((roleId: string, permissionId: string): boolean => {
    const role = roles.find(r => r.id === roleId);
    if (!role) return false;

    return !role.permissions.includes(permissionId) && hasPermission(roleId, permissionId);
  }, [roles, hasPermission]);

  // 篩選權限
  const filteredPermissions = useMemo(() => {
    return permissions.filter(permission => {
      if (selectedCategory !== 'all' && permission.category !== selectedCategory) {
        return false;
      }
      
      if (selectedModule !== 'all' && permission.module !== selectedModule) {
        return false;
      }
      
      if (searchTerm && !permission.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !permission.description.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      return true;
    });
  }, [permissions, selectedCategory, selectedModule, searchTerm]);

  // 獲取所有分類
  const categories = useMemo(() => {
    return Array.from(new Set(permissions.map(p => p.category)));
  }, [permissions]);

  // 獲取所有模組
  const modules = useMemo(() => {
    return Array.from(new Set(permissions.map(p => p.module)));
  }, [permissions]);

  // 切換權限
  const togglePermission = useCallback((roleId: string, permissionId: string) => {
    if (readOnly) return;

    const role = roles.find(r => r.id === roleId);
    if (!role) return;

    const currentlyHas = role.permissions.includes(permissionId);
    const newPermissions = currentlyHas
      ? role.permissions.filter(p => p !== permissionId)
      : [...role.permissions, permissionId];

    const updatedRole = { ...role, permissions: newPermissions };
    
    setRoles(prev => prev.map(r => r.id === roleId ? updatedRole : r));
    setHasChanges(true);

    if (onPermissionChange) {
      onPermissionChange(roleId, permissionId, !currentlyHas);
    }

    if (onRoleChange) {
      onRoleChange(updatedRole);
    }
  }, [roles, readOnly, onPermissionChange, onRoleChange]);

  // 處理批量編輯
  const handleCellClick = useCallback((roleId: string, permissionId: string, event: React.MouseEvent) => {
    if (!bulkEditMode) {
      togglePermission(roleId, permissionId);
      return;
    }

    const cellKey = `${roleId}_${permissionId}`;
    const newSelection = new Set(selectedCells);
    
    if (event.ctrlKey || event.metaKey) {
      // Ctrl/Cmd + 點擊：切換選擇
      if (newSelection.has(cellKey)) {
        newSelection.delete(cellKey);
      } else {
        newSelection.add(cellKey);
      }
    } else if (event.shiftKey && selectedCells.size > 0) {
      // Shift + 點擊：範圍選擇
      // 簡化實現：選擇到最後一個點擊的單元格
      newSelection.add(cellKey);
    } else {
      // 普通點擊：單選
      newSelection.clear();
      newSelection.add(cellKey);
    }

    setSelectedCells(newSelection);
  }, [bulkEditMode, selectedCells, togglePermission]);

  // 批量授予/撤銷權限
  const applyBulkPermission = useCallback((grant: boolean) => {
    if (selectedCells.size === 0) return;

    const changes: Array<{roleId: string, permissionId: string, granted: boolean}> = [];
    
    selectedCells.forEach(cellKey => {
      const [roleId, permissionId] = cellKey.split('_');
      changes.push({ roleId, permissionId, granted: grant });
    });

    // 應用變更
    setRoles(prev => {
      const newRoles = [...prev];
      changes.forEach(({ roleId, permissionId, granted }) => {
        const roleIndex = newRoles.findIndex(r => r.id === roleId);
        if (roleIndex !== -1) {
          const role = newRoles[roleIndex];
          const hasPermission = role.permissions.includes(permissionId);
          
          if (granted && !hasPermission) {
            newRoles[roleIndex] = {
              ...role,
              permissions: [...role.permissions, permissionId]
            };
          } else if (!granted && hasPermission) {
            newRoles[roleIndex] = {
              ...role,
              permissions: role.permissions.filter(p => p !== permissionId)
            };
          }
        }
      });
      return newRoles;
    });

    setHasChanges(true);
    setSelectedCells(new Set());

    if (onBulkPermissionChange) {
      onBulkPermissionChange(changes);
    }
  }, [selectedCells, onBulkPermissionChange]);

  // 保存更改
  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    setIsLoading(true);
    try {
      // 模擬保存API調用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setHasChanges(false);
      
      if (onSave) {
        onSave(roles);
      }
      
      alert('權限設置已保存');
    } catch (error) {
      alert('保存失敗，請重試');
    } finally {
      setIsLoading(false);
    }
  }, [hasChanges, roles, onSave]);

  // 重置更改
  const handleReset = useCallback(() => {
    if (initialRoles.length > 0) {
      setRoles(initialRoles);
    } else {
      const { mockRoles } = generateMockData();
      setRoles(mockRoles);
    }
    setHasChanges(false);
    setSelectedCells(new Set());
  }, [initialRoles, generateMockData]);

  return (
    <div 
      className={`permission-matrix ${className}`}
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* 控制欄 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>
            🔐 權限矩陣編輯器
          </h3>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: '4px 8px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              color: 'inherit',
              fontSize: '12px'
            }}
          >
            <option value="all">所有分類</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            style={{
              padding: '4px 8px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              color: 'inherit',
              fontSize: '12px'
            }}
          >
            <option value="all">所有模組</option>
            {modules.map(module => (
              <option key={module} value={module}>{module}</option>
            ))}
          </select>

          <input
            type="text"
            placeholder="搜尋權限..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              padding: '4px 8px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              color: 'inherit',
              fontSize: '12px',
              width: '150px'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {enableBulkEdit && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
              <input
                type="checkbox"
                checked={bulkEditMode}
                onChange={(e) => setBulkEditMode(e.target.checked)}
              />
              批量編輯
            </label>
          )}

          {enableRoleInheritance && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
              <input
                type="checkbox"
                checked={showInheritedPermissions}
                onChange={(e) => setShowInheritedPermissions(e.target.checked)}
              />
              顯示繼承權限
            </label>
          )}

          {hasChanges && (
            <>
              <button
                onClick={handleReset}
                style={{
                  padding: '6px 12px',
                  backgroundColor: 'rgba(255, 193, 7, 0.8)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                重置
              </button>
              
              <button
                onClick={handleSave}
                disabled={isLoading}
                style={{
                  padding: '6px 12px',
                  backgroundColor: 'rgba(76, 175, 80, 0.8)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  opacity: isLoading ? 0.5 : 1
                }}
              >
                {isLoading ? '保存中...' : '保存更改'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* 批量操作工具欄 */}
      {bulkEditMode && selectedCells.size > 0 && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(74, 144, 226, 0.1)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '14px' }}>
            已選擇 {selectedCells.size} 個權限單元格
          </span>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => applyBulkPermission(true)}
              style={{
                padding: '4px 8px',
                backgroundColor: 'rgba(76, 175, 80, 0.8)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              批量授予
            </button>
            
            <button
              onClick={() => applyBulkPermission(false)}
              style={{
                padding: '4px 8px',
                backgroundColor: 'rgba(244, 67, 54, 0.8)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              批量撤銷
            </button>
            
            <button
              onClick={() => setSelectedCells(new Set())}
              style={{
                padding: '4px 8px',
                backgroundColor: 'rgba(158, 158, 158, 0.8)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              清除選擇
            </button>
          </div>
        </div>
      )}

      {/* 權限矩陣表格 */}
      <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '600px' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '12px'
        }}>
          <thead style={{ 
            backgroundColor: 'rgba(0, 0, 0, 0.1)',
            position: 'sticky',
            top: 0,
            zIndex: 10
          }}>
            <tr>
              <th style={{
                padding: '12px 8px',
                textAlign: 'left',
                borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                minWidth: '200px',
                backgroundColor: 'rgba(0, 0, 0, 0.2)'
              }}>
                權限名稱
              </th>
              
              {roles.map(role => (
                <th
                  key={role.id}
                  style={{
                    padding: '12px 8px',
                    textAlign: 'center',
                    borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    minWidth: '100px',
                    backgroundColor: role.color ? `${role.color}20` : 'rgba(0, 0, 0, 0.1)',
                    writingMode: 'vertical-rl',
                    textOrientation: 'mixed'
                  } as React.CSSProperties}
                  title={role.description}
                >
                  <div style={{
                    transform: 'rotate(-45deg)',
                    whiteSpace: 'nowrap',
                    fontSize: '11px',
                    fontWeight: 'bold'
                  }}>
                    {role.name}
                  </div>
                  {role.isSystemRole && (
                    <div style={{ fontSize: '10px', color: 'orange' }}>🔒</div>
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {filteredPermissions.map((permission, permIndex) => (
              <tr
                key={permission.id}
                style={{
                  backgroundColor: permIndex % 2 === 0 
                    ? 'rgba(255, 255, 255, 0.02)' 
                    : 'rgba(255, 255, 255, 0.05)'
                }}
              >
                <td style={{
                  padding: '8px',
                  borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  backgroundColor: 'rgba(0, 0, 0, 0.05)'
                }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
                    {permission.name}
                    {permission.isSystemPermission && (
                      <span style={{ color: 'orange', marginLeft: '4px' }}>🔒</span>
                    )}
                  </div>
                  
                  <div style={{
                    fontSize: '10px',
                    color: 'rgba(255, 255, 255, 0.6)',
                    marginBottom: '2px'
                  }}>
                    {permission.description}
                  </div>
                  
                  <div style={{ fontSize: '10px', color: 'rgba(255, 255, 255, 0.5)' }}>
                    {permission.category} • {permission.module}
                  </div>

                  {permission.dependencies && permission.dependencies.length > 0 && (
                    <div style={{
                      fontSize: '10px',
                      color: 'rgba(255, 193, 7, 0.8)',
                      marginTop: '2px'
                    }}>
                      依賴: {permission.dependencies.join(', ')}
                    </div>
                  )}
                </td>

                {roles.map(role => {
                  const cellKey = `${role.id}_${permission.id}`;
                  const hasDirectPermission = role.permissions.includes(permission.id);
                  const hasEffectivePermission = hasPermission(role.id, permission.id);
                  const isInherited = isInheritedPermission(role.id, permission.id);
                  const isSelected = selectedCells.has(cellKey);
                  const isReadOnlyCell = readOnly || (role.isSystemRole && role.id === 'super_admin');

                  return (
                    <td
                      key={cellKey}
                      style={{
                        padding: '8px',
                        textAlign: 'center',
                        borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        cursor: isReadOnlyCell ? 'not-allowed' : 'pointer',
                        backgroundColor: isSelected 
                          ? 'rgba(74, 144, 226, 0.3)'
                          : hasDirectPermission
                            ? 'rgba(76, 175, 80, 0.6)'
                            : isInherited && showInheritedPermissions
                              ? 'rgba(255, 193, 7, 0.4)'
                              : 'transparent',
                        opacity: isReadOnlyCell ? 0.5 : 1,
                        position: 'relative'
                      }}
                      onClick={(e) => !isReadOnlyCell && handleCellClick(role.id, permission.id, e)}
                      title={
                        hasDirectPermission
                          ? '直接權限'
                          : isInherited
                            ? '繼承權限'
                            : '無權限'
                      }
                    >
                      {hasDirectPermission ? (
                        <span style={{ fontSize: '16px', color: '#4CAF50' }}>✅</span>
                      ) : isInherited && showInheritedPermissions ? (
                        <span style={{ fontSize: '16px', color: '#FFC107' }}>🔗</span>
                      ) : (
                        <span style={{ fontSize: '16px', color: 'rgba(255, 255, 255, 0.3)' }}>❌</span>
                      )}

                      {isReadOnlyCell && (
                        <div style={{
                          position: 'absolute',
                          top: '2px',
                          right: '2px',
                          fontSize: '8px',
                          color: 'orange'
                        }}>
                          🔒
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 圖例 */}
      <div style={{
        padding: '12px 16px',
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        fontSize: '12px'
      }}>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '14px' }}>✅</span>
            <span>直接權限</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '14px' }}>🔗</span>
            <span>繼承權限</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '14px' }}>❌</span>
            <span>無權限</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '14px' }}>🔒</span>
            <span>系統保護</span>
          </div>
        </div>

        {hasChanges && (
          <div style={{
            marginTop: '8px',
            padding: '8px',
            backgroundColor: 'rgba(255, 193, 7, 0.2)',
            borderRadius: '4px',
            border: '1px solid rgba(255, 193, 7, 0.5)',
            fontSize: '12px'
          }}>
            ⚠️ 您有未保存的更改，請記得點擊「保存更改」按鈕
          </div>
        )}
      </div>
    </div>
  );
};

export default PermissionMatrix;