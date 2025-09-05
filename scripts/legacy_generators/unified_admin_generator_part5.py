#!/usr/bin/env python3
"""
統一管理後台架構生成器 - 第五部分
通用組件
"""

class ComponentsGenerator:
    """組件生成器"""
    
    def __init__(self, base_path: str):
        self.components_path = f"{base_path}/admin/components"
    
    def generate_admin_layout(self) -> str:
        """生成管理後台佈局組件"""
        return '''/**
 * 管理後台主佈局組件
 * 基於admin_enhanced.html的設計
 */

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { NotificationContainer } from './NotificationContainer';
import { useNotifications } from '../hooks/useAdminHooks';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { notifications } = useNotifications();

  return (
    <div className="admin-container">
      <Sidebar 
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <Header 
          onSidebarToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        <main className="content-area">
          {children}
        </main>
      </div>
      <NotificationContainer notifications={notifications} />
    </div>
  );
};'''
    
    def generate_data_table(self) -> str:
        """生成數據表格組件"""
        return '''/**
 * 通用數據表格組件
 * 支援排序、篩選、分頁等功能
 */

import React, { useState, useMemo } from 'react';
import { TableProps, TableColumn, PaginationParams } from '../types/AdminTypes';

export function DataTable<T = any>({
  columns,
  dataSource,
  pagination,
  onPaginationChange,
  rowKey = 'id',
  selection,
  loading = false,
  className = ''
}: TableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  const sortedData = useMemo(() => {
    if (!sortConfig) return dataSource;

    return [...dataSource].sort((a, b) => {
      const aValue = a[sortConfig.key as keyof T];
      const bValue = b[sortConfig.key as keyof T];

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [dataSource, sortConfig]);

  const handleSort = (key: string) => {
    setSortConfig(current => {
      if (current?.key === key) {
        return current.direction === 'asc' 
          ? { key, direction: 'desc' }
          : null;
      }
      return { key, direction: 'asc' };
    });
  };

  const getRowKey = (record: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return String(record[rowKey as keyof T]) || String(index);
  };

  if (loading) {
    return (
      <div className="table-loading">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">載入中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`data-table-container ${className}`}>
      <div className="table-responsive">
        <table className="table table-hover">
          <thead className="table-dark">
            <tr>
              {selection && (
                <th>
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      const allKeys = sortedData.map((record, index) => getRowKey(record, index));
                      selection.onChange(e.target.checked ? allKeys : []);
                    }}
                    checked={selection.selectedRowKeys.length === sortedData.length}
                  />
                </th>
              )}
              {columns.map((column, index) => (
                <th 
                  key={String(column.key) || index}
                  style={{ width: column.width }}
                  className={column.sortable ? 'sortable' : ''}
                  onClick={() => column.sortable && handleSort(String(column.key))}
                >
                  {column.title}
                  {column.sortable && (
                    <span className="sort-indicator">
                      {sortConfig?.key === column.key ? (
                        sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                      ) : ' ↕'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.map((record, index) => {
              const key = getRowKey(record, index);
              return (
                <tr key={key}>
                  {selection && (
                    <td>
                      <input
                        type="checkbox"
                        checked={selection.selectedRowKeys.includes(key)}
                        onChange={(e) => {
                          const newSelection = e.target.checked
                            ? [...selection.selectedRowKeys, key]
                            : selection.selectedRowKeys.filter(k => k !== key);
                          selection.onChange(newSelection);
                        }}
                      />
                    </td>
                  )}
                  {columns.map((column, colIndex) => (
                    <td key={String(column.key) || colIndex}>
                      {column.render 
                        ? column.render(
                            column.dataIndex ? record[column.dataIndex] : record,
                            record,
                            index
                          )
                        : column.dataIndex 
                          ? String(record[column.dataIndex] || '')
                          : ''
                      }
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {pagination && onPaginationChange && (
        <div className="table-pagination">
          <nav>
            <ul className="pagination justify-content-center">
              <li className={`page-item ${pagination.page <= 1 ? 'disabled' : ''}`}>
                <button 
                  className="page-link"
                  onClick={() => onPaginationChange({ ...pagination, page: pagination.page - 1 })}
                  disabled={pagination.page <= 1}
                >
                  上一頁
                </button>
              </li>
              <li className="page-item active">
                <span className="page-link">
                  第 {pagination.page} 頁
                </span>
              </li>
              <li className="page-item">
                <button 
                  className="page-link"
                  onClick={() => onPaginationChange({ ...pagination, page: pagination.page + 1 })}
                >
                  下一頁
                </button>
              </li>
            </ul>
          </nav>
        </div>
      )}
    </div>
  );
}'''