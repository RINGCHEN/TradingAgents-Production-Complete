/**
 * AdvancedDataTable - 高級數據表格組件
 * 提供排序、篩選、分頁、虛擬滾動、批量操作等高級功能
 * 支援大數據集的高性能渲染和操作
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { adminApiService } from '../../services/AdminApiService_Fixed';

export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex: string;
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: T, index: number) => React.ReactNode;
  filterOptions?: Array<{ label: string; value: any }>;
  sorter?: (a: any, b: any) => number;
  fixed?: 'left' | 'right';
}

export interface TableFilter {
  [key: string]: any;
}

export interface TableSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface TablePagination {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  pageSizeOptions?: number[];
}

export interface AdvancedDataTableProps<T = any> {
  columns: TableColumn<T>[];
  dataSource: T[];
  loading?: boolean;
  pagination?: TablePagination | false;
  rowSelection?: {
    type?: 'checkbox' | 'radio';
    selectedRowKeys?: string[];
    onChange?: (selectedRowKeys: string[], selectedRows: T[]) => void;
    onSelectAll?: (selected: boolean, selectedRows: T[], changeRows: T[]) => void;
  };
  expandable?: {
    expandedRowRender?: (record: T, index: number) => React.ReactNode;
    expandedRowKeys?: string[];
    onExpand?: (expanded: boolean, record: T) => void;
  };
  scroll?: {
    x?: number;
    y?: number;
  };
  size?: 'small' | 'middle' | 'large';
  bordered?: boolean;
  showHeader?: boolean;
  title?: string;
  footer?: string;
  emptyText?: string;
  className?: string;
  style?: React.CSSProperties;
  onRow?: (record: T, index: number) => {
    onClick?: (event: React.MouseEvent) => void;
    onDoubleClick?: (event: React.MouseEvent) => void;
    onContextMenu?: (event: React.MouseEvent) => void;
  };
  onChange?: (pagination: TablePagination, filters: TableFilter, sorter: TableSort) => void;
  onSearch?: (value: string) => void;
  enableVirtualScroll?: boolean;
  rowHeight?: number;
  enableExport?: boolean;
  enableColumnResize?: boolean;
  enableColumnHide?: boolean;
}

/**
 * AdvancedDataTable - 高級數據表格組件
 * 提供企業級數據表格的完整功能
 */
export const AdvancedDataTable = <T extends Record<string, any>>({
  columns,
  dataSource,
  loading = false,
  pagination = { current: 1, pageSize: 10, total: 0 },
  rowSelection,
  expandable,
  scroll,
  size = 'middle',
  bordered = false,
  showHeader = true,
  title,
  footer,
  emptyText = '暫無數據',
  className = '',
  style = {},
  onRow,
  onChange,
  onSearch,
  enableVirtualScroll = false,
  rowHeight = 54,
  enableExport = true,
  enableColumnResize = false,
  enableColumnHide = false
}: AdvancedDataTableProps<T>) => {
  const [filteredData, setFilteredData] = useState<T[]>(dataSource);
  const [sortedData, setSortedData] = useState<T[]>(dataSource);
  const [currentSort, setCurrentSort] = useState<TableSort | null>(null);
  const [filters, setFilters] = useState<TableFilter>({});
  const [searchValue, setSearchValue] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>(
    rowSelection?.selectedRowKeys || []
  );
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>(
    expandable?.expandedRowKeys || []
  );
  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    columns.map(col => col.key)
  );
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});

  const tableRef = useRef<HTMLDivElement>(null);
  const virtualScrollRef = useRef<HTMLDivElement>(null);

  // 計算分頁數據
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;
    
    const { current, pageSize } = pagination;
    const start = (current - 1) * pageSize;
    const end = start + pageSize;
    return sortedData.slice(start, end);
  }, [sortedData, pagination]);

  // 搜索功能
  const handleSearch = useCallback((value: string) => {
    setSearchValue(value);
    
    if (!value.trim()) {
      setFilteredData(dataSource);
      return;
    }

    const searchableColumns = columns.filter(col => col.searchable !== false);
    const filtered = dataSource.filter(record => {
      return searchableColumns.some(col => {
        const cellValue = record[col.dataIndex];
        return cellValue?.toString().toLowerCase().includes(value.toLowerCase());
      });
    });

    setFilteredData(filtered);
    
    if (onSearch) {
      onSearch(value);
    }
  }, [dataSource, columns, onSearch]);

  // 排序功能
  const handleSort = useCallback((column: TableColumn<T>) => {
    if (!column.sortable) return;

    let direction: 'asc' | 'desc' = 'asc';
    
    if (currentSort?.field === column.dataIndex) {
      direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    }

    const newSort: TableSort = {
      field: column.dataIndex,
      direction
    };

    setCurrentSort(newSort);

    const sorted = [...filteredData].sort((a, b) => {
      if (column.sorter) {
        const result = column.sorter(a[column.dataIndex], b[column.dataIndex]);
        return direction === 'desc' ? -result : result;
      }

      const aValue = a[column.dataIndex];
      const bValue = b[column.dataIndex];

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return direction === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();
      
      if (direction === 'asc') {
        return aStr.localeCompare(bStr);
      } else {
        return bStr.localeCompare(aStr);
      }
    });

    setSortedData(sorted);

    if (onChange && pagination) {
      onChange(pagination, filters, newSort);
    }
  }, [currentSort, filteredData, filters, pagination, onChange]);

  // 篩選功能
  const handleFilter = useCallback((columnKey: string, value: any) => {
    const newFilters = {
      ...filters,
      [columnKey]: value
    };

    if (value === null || value === undefined || value === '') {
      delete newFilters[columnKey];
    }

    setFilters(newFilters);

    let filtered = dataSource;
    Object.entries(newFilters).forEach(([key, filterValue]) => {
      if (filterValue !== null && filterValue !== undefined && filterValue !== '') {
        filtered = filtered.filter(record => {
          const cellValue = record[key];
          if (Array.isArray(filterValue)) {
            return filterValue.includes(cellValue);
          }
          return cellValue === filterValue;
        });
      }
    });

    setFilteredData(filtered);

    if (onChange && pagination) {
      onChange(pagination, newFilters, currentSort || { field: '', direction: 'asc' });
    }
  }, [filters, dataSource, pagination, currentSort, onChange]);

  // 行選擇功能
  const handleRowSelect = useCallback((rowKey: string, selected: boolean) => {
    let newSelectedKeys: string[];
    
    if (rowSelection?.type === 'radio') {
      newSelectedKeys = selected ? [rowKey] : [];
    } else {
      newSelectedKeys = selected
        ? [...selectedRowKeys, rowKey]
        : selectedRowKeys.filter(key => key !== rowKey);
    }

    setSelectedRowKeys(newSelectedKeys);

    if (rowSelection?.onChange) {
      const selectedRows = paginatedData.filter(record => 
        newSelectedKeys.includes(record.id || record.key)
      );
      rowSelection.onChange(newSelectedKeys, selectedRows);
    }
  }, [selectedRowKeys, rowSelection, paginatedData]);

  // 全選功能
  const handleSelectAll = useCallback((selected: boolean) => {
    const currentPageRowKeys = paginatedData.map(record => record.id || record.key);
    
    let newSelectedKeys: string[];
    if (selected) {
      newSelectedKeys = [...new Set([...selectedRowKeys, ...currentPageRowKeys])];
    } else {
      newSelectedKeys = selectedRowKeys.filter(key => !currentPageRowKeys.includes(key));
    }

    setSelectedRowKeys(newSelectedKeys);

    if (rowSelection?.onChange) {
      const selectedRows = dataSource.filter(record => 
        newSelectedKeys.includes(record.id || record.key)
      );
      rowSelection.onChange(newSelectedKeys, selectedRows);
    }
  }, [selectedRowKeys, paginatedData, rowSelection, dataSource]);

  // 展開功能
  const handleExpand = useCallback((rowKey: string, expanded: boolean) => {
    let newExpandedKeys: string[];
    
    if (expanded) {
      newExpandedKeys = [...expandedRowKeys, rowKey];
    } else {
      newExpandedKeys = expandedRowKeys.filter(key => key !== rowKey);
    }

    setExpandedRowKeys(newExpandedKeys);

    if (expandable?.onExpand) {
      const record = paginatedData.find(r => (r.id || r.key) === rowKey);
      if (record) {
        expandable.onExpand(expanded, record);
      }
    }
  }, [expandedRowKeys, expandable, paginatedData]);

  // 導出功能
  const handleExport = useCallback(async (format: 'csv' | 'excel' = 'csv') => {
    try {
      const headers = visibleColumns
        .map(colKey => columns.find(col => col.key === colKey))
        .filter(Boolean)
        .map(col => col!.title);

      const rows = filteredData.map(record => 
        visibleColumns
          .map(colKey => columns.find(col => col.key === colKey))
          .filter(Boolean)
          .map(col => record[col!.dataIndex])
      );

      if (format === 'csv') {
        const csvContent = [
          headers.join(','),
          ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `table_export_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
      }
    } catch (error) {
      console.error('導出失敗:', error);
    }
  }, [filteredData, visibleColumns, columns]);

  // 數據變更時更新
  useEffect(() => {
    setFilteredData(dataSource);
    setSortedData(dataSource);
  }, [dataSource]);

  useEffect(() => {
    setSortedData(filteredData);
  }, [filteredData]);

  // 渲染表格標題
  const renderTableHeader = () => (
    <thead style={{ backgroundColor: 'rgba(0, 0, 0, 0.1)' }}>
      <tr>
        {rowSelection && (
          <th style={{ width: 50, textAlign: 'center', padding: '12px 8px' }}>
            {rowSelection.type !== 'radio' && (
              <input
                type="checkbox"
                checked={paginatedData.length > 0 && paginatedData.every(record => 
                  selectedRowKeys.includes(record.id || record.key)
                )}
                onChange={(e) => handleSelectAll(e.target.checked)}
              />
            )}
          </th>
        )}
        
        {expandable && (
          <th style={{ width: 50, textAlign: 'center', padding: '12px 8px' }}>
            展開
          </th>
        )}

        {visibleColumns.map(colKey => {
          const column = columns.find(col => col.key === colKey);
          if (!column) return null;

          return (
            <th
              key={column.key}
              style={{
                padding: '12px 8px',
                textAlign: column.align || 'left',
                width: columnWidths[column.key] || column.width,
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                cursor: column.sortable ? 'pointer' : 'default',
                userSelect: 'none'
              }}
              onClick={() => handleSort(column)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>{column.title}</span>
                
                {column.sortable && (
                  <span style={{ fontSize: '12px' }}>
                    {currentSort?.field === column.dataIndex
                      ? currentSort.direction === 'asc' ? '↑' : '↓'
                      : '↕️'
                    }
                  </span>
                )}
                
                {column.filterable && (
                  <select
                    style={{
                      fontSize: '11px',
                      padding: '2px 4px',
                      backgroundColor: 'rgba(0, 0, 0, 0.1)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '3px',
                      color: 'inherit'
                    }}
                    onChange={(e) => handleFilter(column.dataIndex, e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <option value="">全部</option>
                    {column.filterOptions?.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </th>
          );
        })}
      </tr>
    </thead>
  );

  // 渲染表格行
  const renderTableRow = (record: T, index: number) => {
    const rowKey = record.id || record.key || index.toString();
    const isSelected = selectedRowKeys.includes(rowKey);
    const isExpanded = expandedRowKeys.includes(rowKey);

    return (
      <React.Fragment key={rowKey}>
        <tr
          style={{
            backgroundColor: isSelected 
              ? 'rgba(74, 144, 226, 0.2)' 
              : index % 2 === 0 
                ? 'rgba(255, 255, 255, 0.05)' 
                : 'transparent',
            cursor: onRow ? 'pointer' : 'default',
            transition: 'background-color 0.2s ease'
          }}
          {...onRow?.(record, index)}
        >
          {rowSelection && (
            <td style={{ textAlign: 'center', padding: '12px 8px' }}>
              <input
                type={rowSelection.type || 'checkbox'}
                checked={isSelected}
                onChange={(e) => handleRowSelect(rowKey, e.target.checked)}
              />
            </td>
          )}
          
          {expandable && (
            <td style={{ textAlign: 'center', padding: '12px 8px' }}>
              <button
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '16px'
                }}
                onClick={() => handleExpand(rowKey, !isExpanded)}
              >
                {isExpanded ? '▼' : '▶'}
              </button>
            </td>
          )}

          {visibleColumns.map(colKey => {
            const column = columns.find(col => col.key === colKey);
            if (!column) return null;

            const cellValue = record[column.dataIndex];
            const renderedValue = column.render 
              ? column.render(cellValue, record, index)
              : cellValue;

            return (
              <td
                key={column.key}
                style={{
                  padding: '12px 8px',
                  textAlign: column.align || 'left',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  verticalAlign: 'middle'
                }}
              >
                {renderedValue}
              </td>
            );
          })}
        </tr>

        {/* 展開行 */}
        {isExpanded && expandable?.expandedRowRender && (
          <tr>
            <td
              colSpan={
                visibleColumns.length + 
                (rowSelection ? 1 : 0) + 
                (expandable ? 1 : 0)
              }
              style={{
                padding: '16px',
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              {expandable.expandedRowRender(record, index)}
            </td>
          </tr>
        )}
      </React.Fragment>
    );
  };

  // 渲染分頁
  const renderPagination = () => {
    if (!pagination) return null;

    const { current, pageSize, total } = pagination;
    const totalPages = Math.ceil(total / pageSize);

    return (
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px',
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>
          共 {total} 條記錄，第 {current} 頁，共 {totalPages} 頁
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            disabled={current <= 1}
            style={{
              padding: '4px 8px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              color: 'inherit',
              cursor: current <= 1 ? 'not-allowed' : 'pointer',
              opacity: current <= 1 ? 0.5 : 1
            }}
          >
            上一頁
          </button>

          <span style={{ margin: '0 16px', fontSize: '14px' }}>
            {current} / {totalPages}
          </span>

          <button
            disabled={current >= totalPages}
            style={{
              padding: '4px 8px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              color: 'inherit',
              cursor: current >= totalPages ? 'not-allowed' : 'pointer',
              opacity: current >= totalPages ? 0.5 : 1
            }}
          >
            下一頁
          </button>
        </div>
      </div>
    );
  };

  return (
    <div 
      className={`advanced-data-table ${className}`}
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* 工具欄 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {title && (
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>
              {title}
            </h3>
          )}
          
          <input
            type="text"
            placeholder="搜尋..."
            value={searchValue}
            onChange={(e) => handleSearch(e.target.value)}
            style={{
              padding: '6px 12px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              color: 'inherit',
              fontSize: '14px',
              width: '200px'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {enableExport && (
            <button
              onClick={() => handleExport('csv')}
              style={{
                padding: '6px 12px',
                backgroundColor: 'rgba(74, 144, 226, 0.8)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              📊 導出CSV
            </button>
          )}

          {rowSelection && selectedRowKeys.length > 0 && (
            <span style={{
              padding: '6px 12px',
              backgroundColor: 'rgba(255, 193, 7, 0.8)',
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              已選擇 {selectedRowKeys.length} 項
            </span>
          )}
        </div>
      </div>

      {/* 表格主體 */}
      <div 
        ref={tableRef}
        style={{
          overflowX: 'auto',
          overflowY: scroll?.y ? 'auto' : 'visible',
          maxHeight: scroll?.y
        }}
      >
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: size === 'small' ? '12px' : size === 'large' ? '16px' : '14px'
        }}>
          {showHeader && renderTableHeader()}
          
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={
                    visibleColumns.length + 
                    (rowSelection ? 1 : 0) + 
                    (expandable ? 1 : 0)
                  }
                  style={{
                    textAlign: 'center',
                    padding: '40px',
                    color: 'rgba(255, 255, 255, 0.7)'
                  }}
                >
                  正在載入...
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={
                    visibleColumns.length + 
                    (rowSelection ? 1 : 0) + 
                    (expandable ? 1 : 0)
                  }
                  style={{
                    textAlign: 'center',
                    padding: '40px',
                    color: 'rgba(255, 255, 255, 0.5)'
                  }}
                >
                  {emptyText}
                </td>
              </tr>
            ) : (
              paginatedData.map((record, index) => renderTableRow(record, index))
            )}
          </tbody>
        </table>
      </div>

      {/* 分頁 */}
      {renderPagination()}

      {/* 頁腳 */}
      {footer && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          fontSize: '14px',
          color: 'rgba(255, 255, 255, 0.7)'
        }}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default AdvancedDataTable;