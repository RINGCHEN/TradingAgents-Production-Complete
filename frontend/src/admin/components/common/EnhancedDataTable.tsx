/**
 * 增強型數據表格組件
 * 基於 functional_admin.html 的 DataTables 優秀功能
 * 提供排序、篩選、分頁、搜尋、導出等完整功能
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useToast } from './ToastNotification';

export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  filterType?: 'text' | 'select' | 'date' | 'number';
  filterOptions?: Array<{ label: string; value: any }>;
  align?: 'left' | 'center' | 'right';
  fixed?: 'left' | 'right';
}

export interface TablePaginationConfig {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: string[];
}

export interface EnhancedDataTableProps<T = any> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: TablePaginationConfig | false;
  rowSelection?: {
    type: 'checkbox' | 'radio';
    selectedRowKeys?: React.Key[];
    onChange?: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
    getCheckboxProps?: (record: T) => object;
  };
  expandable?: {
    expandedRowRender: (record: T, index: number) => React.ReactNode;
    rowExpandable?: (record: T) => boolean;
  };
  scroll?: { x?: number | string; y?: number | string };
  size?: 'large' | 'middle' | 'small';
  showHeader?: boolean;
  title?: string;
  bordered?: boolean;
  striped?: boolean;
  hover?: boolean;
  responsive?: boolean;
  exportable?: boolean;
  searchable?: boolean;
  className?: string;
  rowKey?: string | ((record: T) => string);
  onRow?: (record: T, index: number) => object;
  locale?: {
    emptyText?: string;
    filterTitle?: string;
    filterConfirm?: string;
    filterReset?: string;
    selectAll?: string;
    selectInvert?: string;
    sortTitle?: string;
  };
}

export const EnhancedDataTable = <T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  pagination = {
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: true,
    pageSizeOptions: ['10', '20', '50', '100']
  },
  rowSelection,
  expandable,
  scroll,
  size = 'middle',
  showHeader = true,
  title,
  bordered = true,
  striped = true,
  hover = true,
  responsive = true,
  exportable = true,
  searchable = true,
  className = '',
  rowKey = 'id',
  onRow,
  locale = {
    emptyText: '暫無數據',
    filterTitle: '篩選',
    filterConfirm: '確定',
    filterReset: '重置',
    selectAll: '全選',
    selectInvert: '反選',
    sortTitle: '排序'
  }
}: EnhancedDataTableProps<T>) => {
  const [currentPage, setCurrentPage] = useState(pagination ? pagination.current : 1);
  const [pageSize, setPageSize] = useState(pagination ? pagination.pageSize : 10);
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [searchText, setSearchText] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>(
    rowSelection?.selectedRowKeys || []
  );
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([]);

  const tableRef = useRef<HTMLTableElement>(null);
  const toast = useToast();

  // 獲取行鍵值
  const getRowKey = useCallback((record: T, index: number): React.Key => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] ?? index;
  }, [rowKey]);

  // 數據處理：搜尋、篩選、排序
  const processedData = useMemo(() => {
    let result = [...data];

    // 全局搜尋
    if (searchText) {
      result = result.filter(record =>
        Object.values(record).some(value =>
          String(value).toLowerCase().includes(searchText.toLowerCase())
        )
      );
    }

    // 列篩選
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        result = result.filter(record => {
          const recordValue = record[key];
          if (Array.isArray(value)) {
            return value.includes(recordValue);
          }
          return String(recordValue).toLowerCase().includes(String(value).toLowerCase());
        });
      }
    });

    // 排序
    if (sortConfig) {
      result.sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        if (aValue === bValue) return 0;
        
        const comparison = aValue > bValue ? 1 : -1;
        return sortConfig.direction === 'desc' ? -comparison : comparison;
      });
    }

    return result;
  }, [data, searchText, filters, sortConfig]);

  // 分頁數據
  const paginatedData = useMemo(() => {
    if (!pagination) return processedData;
    
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return processedData.slice(start, end);
  }, [processedData, currentPage, pageSize, pagination]);

  // 排序處理
  const handleSort = (columnKey: string) => {
    setSortConfig(prev => {
      if (!prev || prev.key !== columnKey) {
        return { key: columnKey, direction: 'asc' };
      }
      if (prev.direction === 'asc') {
        return { key: columnKey, direction: 'desc' };
      }
      return null; // 取消排序
    });
  };

  // 篩選處理
  const handleFilter = (columnKey: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [columnKey]: value
    }));
    setCurrentPage(1); // 重置到第一頁
  };

  // 分頁處理
  const handlePageChange = (page: number, size?: number) => {
    setCurrentPage(page);
    if (size) setPageSize(size);
  };

  // 行選擇處理
  const handleRowSelection = (key: React.Key, selected: boolean) => {
    let newSelectedRowKeys: React.Key[];
    
    if (selected) {
      newSelectedRowKeys = [...selectedRowKeys, key];
    } else {
      newSelectedRowKeys = selectedRowKeys.filter(k => k !== key);
    }
    
    setSelectedRowKeys(newSelectedRowKeys);
    
    if (rowSelection?.onChange) {
      const selectedRows = processedData.filter(record =>
        newSelectedRowKeys.includes(getRowKey(record, 0))
      );
      rowSelection.onChange(newSelectedRowKeys, selectedRows);
    }
  };

  // 全選/取消全選
  const handleSelectAll = (selected: boolean) => {
    let newSelectedRowKeys: React.Key[];
    
    if (selected) {
      newSelectedRowKeys = paginatedData.map((record, index) => getRowKey(record, index));
    } else {
      newSelectedRowKeys = [];
    }
    
    setSelectedRowKeys(newSelectedRowKeys);
    
    if (rowSelection?.onChange) {
      const selectedRows = selected ? paginatedData : [];
      rowSelection.onChange(newSelectedRowKeys, selectedRows);
    }
  };

  // 展開行處理
  const handleRowExpand = (key: React.Key, expanded: boolean) => {
    if (expanded) {
      setExpandedRowKeys([...expandedRowKeys, key]);
    } else {
      setExpandedRowKeys(expandedRowKeys.filter(k => k !== key));
    }
  };

  // 導出數據
  const handleExport = (format: 'csv' | 'excel' | 'json') => {
    try {
      let exportData: any[];
      
      // 準備導出數據
      exportData = processedData.map(record => {
        const row: any = {};
        columns.forEach(column => {
          const value = record[column.dataIndex || column.key];
          row[column.title] = value;
        });
        return row;
      });

      if (format === 'csv') {
        downloadCSV(exportData, `table-data-${new Date().toISOString().split('T')[0]}.csv`);
      } else if (format === 'json') {
        downloadJSON(exportData, `table-data-${new Date().toISOString().split('T')[0]}.json`);
      } else {
        toast.info('Excel 導出功能開發中', '提示');
      }
    } catch (error) {
      toast.error('導出失敗，請稍後重試', '導出錯誤');
    }
  };

  // CSV下載
  const downloadCSV = (data: any[], filename: string) => {
    if (data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    downloadFile(blob, filename);
  };

  // JSON下載
  const downloadJSON = (data: any[], filename: string) => {
    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    downloadFile(blob, filename);
  };

  // 文件下載
  const downloadFile = (blob: Blob, filename: string) => {
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  // 渲染排序圖標
  const renderSortIcon = (columnKey: string) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <i className="fas fa-sort text-muted ms-1"></i>;
    }
    
    return sortConfig.direction === 'asc' 
      ? <i className="fas fa-sort-up text-primary ms-1"></i>
      : <i className="fas fa-sort-down text-primary ms-1"></i>;
  };

  // 渲染篩選器
  const renderFilter = (column: TableColumn<T>) => {
    if (!column.filterable) return null;

    const currentValue = filters[column.key] || '';

    if (column.filterType === 'select' && column.filterOptions) {
      return (
        <select
          className="form-select form-select-sm"
          value={currentValue}
          onChange={(e) => handleFilter(column.key, e.target.value)}
        >
          <option value="">全部</option>
          {column.filterOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        type={column.filterType || 'text'}
        className="form-control form-control-sm"
        placeholder={`篩選 ${column.title}`}
        value={currentValue}
        onChange={(e) => handleFilter(column.key, e.target.value)}
      />
    );
  };

  return (
    <div className={`enhanced-data-table ${className}`}>
      {/* 工具欄 */}
      <div className="table-toolbar">
        <div className="row align-items-center mb-3">
          <div className="col-md-6">
            {title && <h5 className="table-title mb-0">{title}</h5>}
          </div>
          <div className="col-md-6">
            <div className="d-flex gap-2 justify-content-end">
              {/* 搜尋框 */}
              {searchable && (
                <div className="table-search">
                  <input
                    type="search"
                    className="form-control form-control-sm"
                    placeholder="搜尋表格數據..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    style={{ width: '200px' }}
                  />
                </div>
              )}
              
              {/* 導出按鈕 */}
              {exportable && (
                <div className="dropdown">
                  <button
                    className="btn btn-outline-secondary btn-sm dropdown-toggle"
                    type="button"
                    data-bs-toggle="dropdown"
                    aria-expanded="false"
                  >
                    <i className="fas fa-download me-1"></i>
                    導出
                  </button>
                  <ul className="dropdown-menu">
                    <li>
                      <button 
                        className="dropdown-item" 
                        onClick={() => handleExport('csv')}
                      >
                        <i className="fas fa-file-csv me-2"></i>CSV
                      </button>
                    </li>
                    <li>
                      <button 
                        className="dropdown-item" 
                        onClick={() => handleExport('json')}
                      >
                        <i className="fas fa-file-code me-2"></i>JSON
                      </button>
                    </li>
                    <li>
                      <button 
                        className="dropdown-item" 
                        onClick={() => handleExport('excel')}
                      >
                        <i className="fas fa-file-excel me-2"></i>Excel
                      </button>
                    </li>
                  </ul>
                </div>
              )}
              
              {/* 刷新按鈕 */}
              <button
                className="btn btn-outline-primary btn-sm"
                onClick={() => window.location.reload()}
                title="刷新數據"
              >
                <i className="fas fa-sync-alt"></i>
              </button>
            </div>
          </div>
        </div>
        
        {/* 選擇行信息 */}
        {rowSelection && selectedRowKeys.length > 0 && (
          <div className="alert alert-info py-2 mb-3">
            <i className="fas fa-info-circle me-2"></i>
            已選擇 {selectedRowKeys.length} 項
            <button
              className="btn btn-link btn-sm p-0 ms-2"
              onClick={() => setSelectedRowKeys([])}
            >
              清空選擇
            </button>
          </div>
        )}
      </div>

      {/* 表格容器 */}
      <div className="table-container">
        <div className={`table-responsive ${responsive ? 'table-responsive-lg' : ''}`}>
          <table
            ref={tableRef}
            className={`table ${bordered ? 'table-bordered' : ''} ${striped ? 'table-striped' : ''} ${hover ? 'table-hover' : ''} table-${size}`}
          >
            {/* 表頭 */}
            {showHeader && (
              <thead className="table-dark">
                <tr>
                  {/* 選擇列 */}
                  {rowSelection && (
                    <th style={{ width: 50 }}>
                      {rowSelection.type === 'checkbox' && (
                        <div className="form-check">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            checked={paginatedData.length > 0 && paginatedData.every((record, index) => 
                              selectedRowKeys.includes(getRowKey(record, index))
                            )}
                            onChange={(e) => handleSelectAll(e.target.checked)}
                          />
                        </div>
                      )}
                    </th>
                  )}
                  
                  {/* 展開列 */}
                  {expandable && <th style={{ width: 50 }}></th>}
                  
                  {/* 數據列 */}
                  {columns.map(column => (
                    <th
                      key={column.key}
                      style={{ 
                        width: column.width,
                        textAlign: column.align || 'left'
                      }}
                    >
                      <div className="table-header-cell">
                        <span
                          className={column.sortable ? 'sortable-header' : ''}
                          onClick={() => column.sortable && handleSort(column.key)}
                        >
                          {column.title}
                          {column.sortable && renderSortIcon(column.key)}
                        </span>
                        {column.filterable && (
                          <div className="filter-container mt-1">
                            {renderFilter(column)}
                          </div>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            
            {/* 表體 */}
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length + (rowSelection ? 1 : 0) + (expandable ? 1 : 0)} className="text-center py-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">載入中...</span>
                    </div>
                    <div className="mt-2">數據載入中...</div>
                  </td>
                </tr>
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length + (rowSelection ? 1 : 0) + (expandable ? 1 : 0)} className="text-center text-muted py-4">
                    <i className="fas fa-inbox fa-2x mb-2"></i>
                    <div>{locale.emptyText}</div>
                  </td>
                </tr>
              ) : (
                paginatedData.map((record, index) => {
                  const recordKey = getRowKey(record, index);
                  const isSelected = selectedRowKeys.includes(recordKey);
                  const isExpanded = expandedRowKeys.includes(recordKey);
                  
                  return (
                    <React.Fragment key={recordKey}>
                      <tr
                        className={isSelected ? 'table-active' : ''}
                        {...onRow?.(record, index)}
                      >
                        {/* 選擇列 */}
                        {rowSelection && (
                          <td>
                            <div className="form-check">
                              <input
                                className="form-check-input"
                                type={rowSelection.type}
                                checked={isSelected}
                                onChange={(e) => handleRowSelection(recordKey, e.target.checked)}
                                {...rowSelection.getCheckboxProps?.(record)}
                              />
                            </div>
                          </td>
                        )}
                        
                        {/* 展開列 */}
                        {expandable && (
                          <td>
                            {(!expandable.rowExpandable || expandable.rowExpandable(record)) && (
                              <button
                                className="btn btn-link btn-sm p-0"
                                onClick={() => handleRowExpand(recordKey, !isExpanded)}
                              >
                                <i className={`fas fa-chevron-${isExpanded ? 'down' : 'right'}`}></i>
                              </button>
                            )}
                          </td>
                        )}
                        
                        {/* 數據列 */}
                        {columns.map(column => {
                          const value = record[column.dataIndex || column.key];
                          const cellContent = column.render 
                            ? column.render(value, record, index)
                            : value;
                            
                          return (
                            <td
                              key={column.key}
                              style={{ textAlign: column.align || 'left' }}
                            >
                              {cellContent}
                            </td>
                          );
                        })}
                      </tr>
                      
                      {/* 展開行 */}
                      {expandable && isExpanded && (
                        <tr>
                          <td colSpan={columns.length + (rowSelection ? 1 : 0) + 1}>
                            <div className="expanded-row-content">
                              {expandable.expandedRowRender(record, index)}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 分頁 */}
      {pagination && (
        <div className="table-pagination">
          <div className="row align-items-center">
            <div className="col-md-6">
              {pagination.showTotal && (
                <div className="pagination-info text-muted">
                  共 {processedData.length} 條記錄
                  {pagination.showSizeChanger && (
                    <>
                      ，每頁顯示
                      <select
                        className="form-select form-select-sm d-inline-block mx-2"
                        style={{ width: 'auto' }}
                        value={pageSize}
                        onChange={(e) => handlePageChange(1, Number(e.target.value))}
                      >
                        {pagination.pageSizeOptions?.map(size => (
                          <option key={size} value={size}>{size}</option>
                        ))}
                      </select>
                      條
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="col-md-6">
              <nav aria-label="表格分頁">
                <ul className="pagination pagination-sm justify-content-end mb-0">
                  <li className={`page-item ${currentPage <= 1 ? 'disabled' : ''}`}>
                    <button
                      className="page-link"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage <= 1}
                    >
                      上一頁
                    </button>
                  </li>
                  
                  {/* 頁碼 */}
                  {Array.from({ length: Math.ceil(processedData.length / pageSize) }, (_, i) => i + 1)
                    .slice(Math.max(0, currentPage - 3), currentPage + 2)
                    .map(page => (
                      <li key={page} className={`page-item ${page === currentPage ? 'active' : ''}`}>
                        <button
                          className="page-link"
                          onClick={() => handlePageChange(page)}
                        >
                          {page}
                        </button>
                      </li>
                    ))}
                  
                  <li className={`page-item ${currentPage >= Math.ceil(processedData.length / pageSize) ? 'disabled' : ''}`}>
                    <button
                      className="page-link"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage >= Math.ceil(processedData.length / pageSize)}
                    >
                      下一頁
                    </button>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};