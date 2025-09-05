/**
 * 高性能虛擬化列表組件
 * 支援大數據集的高效渲染，提升用戶體驗
 * 天工 - 第三優先級性能優化任務
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number; // 預渲染的項目數量
  onScroll?: (scrollTop: number) => void;
  className?: string;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  itemKey?: (item: T, index: number) => string | number;
}

export function VirtualizedList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  onScroll,
  className = '',
  loading = false,
  loadingComponent,
  emptyComponent,
  itemKey
}: VirtualizedListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // 計算可見範圍
  const visibleRange = useMemo(() => {
    const containerTop = scrollTop;
    const containerBottom = containerTop + containerHeight;
    
    const startIndex = Math.max(0, Math.floor(containerTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil(containerBottom / itemHeight) + overscan
    );

    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemHeight, items.length, overscan]);

  // 計算總高度
  const totalHeight = items.length * itemHeight;

  // 滾動處理
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    onScroll?.(newScrollTop);
  }, [onScroll]);

  // 渲染可見項目
  const visibleItems = useMemo(() => {
    const { startIndex, endIndex } = visibleRange;
    const result = [];

    for (let i = startIndex; i <= endIndex; i++) {
      if (i >= items.length) break;
      
      const item = items[i];
      const key = itemKey ? itemKey(item, i) : i;
      const style = {
        position: 'absolute' as const,
        top: i * itemHeight,
        left: 0,
        right: 0,
        height: itemHeight
      };

      result.push(
        <div key={key} style={style} className="virtualized-item">
          {renderItem(item, i)}
        </div>
      );
    }

    return result;
  }, [visibleRange, items, itemHeight, renderItem, itemKey]);

  // 滾動到指定項目
  const scrollToItem = useCallback((index: number, align: 'start' | 'center' | 'end' = 'start') => {
    if (!scrollElementRef.current) return;

    let scrollTo = index * itemHeight;

    if (align === 'center') {
      scrollTo -= containerHeight / 2 - itemHeight / 2;
    } else if (align === 'end') {
      scrollTo -= containerHeight - itemHeight;
    }

    scrollTo = Math.max(0, Math.min(scrollTo, totalHeight - containerHeight));

    scrollElementRef.current.scrollTop = scrollTo;
    setScrollTop(scrollTo);
  }, [itemHeight, containerHeight, totalHeight]);

  // 滾動到頂部
  const scrollToTop = useCallback(() => {
    scrollToItem(0, 'start');
  }, [scrollToItem]);

  // 滾動到底部
  const scrollToBottom = useCallback(() => {
    scrollToItem(items.length - 1, 'end');
  }, [scrollToItem, items.length]);

  // 載入狀態
  if (loading) {
    return (
      <div className={`virtualized-list-container ${className}`} style={{ height: containerHeight }}>
        {loadingComponent || (
          <div className="d-flex justify-content-center align-items-center h-100">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">載入中...</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  // 空狀態
  if (items.length === 0) {
    return (
      <div className={`virtualized-list-container ${className}`} style={{ height: containerHeight }}>
        {emptyComponent || (
          <div className="d-flex justify-content-center align-items-center h-100 text-muted">
            <div className="text-center">
              <i className="fas fa-inbox fa-3x mb-3"></i>
              <p>暫無數據</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`virtualized-list-container ${className}`}
      style={{ height: containerHeight, position: 'relative' }}
    >
      <div
        ref={scrollElementRef}
        className="virtualized-list-scroll"
        style={{
          height: '100%',
          overflowY: 'auto',
          overflowX: 'hidden'
        }}
        onScroll={handleScroll}
      >
        <div
          className="virtualized-list-content"
          style={{
            height: totalHeight,
            position: 'relative'
          }}
        >
          {visibleItems}
        </div>
      </div>
      
      {/* 滾動控制按鈕 */}
      <div className="virtualized-list-controls">
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={scrollToTop}
          style={{ position: 'absolute', top: 10, right: 10, zIndex: 10 }}
          title="滾動到頂部"
        >
          <i className="fas fa-chevron-up"></i>
        </button>
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={scrollToBottom}
          style={{ position: 'absolute', bottom: 10, right: 10, zIndex: 10 }}
          title="滾動到底部"
        >
          <i className="fas fa-chevron-down"></i>
        </button>
      </div>
    </div>
  );
}

// 帶搜索和過濾的虛擬化列表
interface SearchableVirtualizedListProps<T> extends VirtualizedListProps<T> {
  searchable?: boolean;
  searchPlaceholder?: string;
  filterFn?: (item: T, searchTerm: string) => boolean;
  onSearchChange?: (searchTerm: string, filteredItems: T[]) => void;
}

export function SearchableVirtualizedList<T>({
  items,
  searchable = true,
  searchPlaceholder = "搜索...",
  filterFn,
  onSearchChange,
  ...listProps
}: SearchableVirtualizedListProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');

  // 過濾項目
  const filteredItems = useMemo(() => {
    if (!searchTerm || !filterFn) return items;
    
    const filtered = items.filter(item => filterFn(item, searchTerm));
    onSearchChange?.(searchTerm, filtered);
    
    return filtered;
  }, [items, searchTerm, filterFn, onSearchChange]);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  return (
    <div className="searchable-virtualized-list">
      {searchable && (
        <div className="search-container mb-3">
          <div className="input-group">
            <span className="input-group-text">
              <i className="fas fa-search"></i>
            </span>
            <input
              type="text"
              className="form-control"
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={handleSearchChange}
            />
            {searchTerm && (
              <button
                className="btn btn-outline-secondary"
                type="button"
                onClick={() => setSearchTerm('')}
                title="清除搜索"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
          {searchTerm && (
            <small className="text-muted">
              找到 {filteredItems.length} 個結果
            </small>
          )}
        </div>
      )}
      
      <VirtualizedList
        {...listProps}
        items={filteredItems}
      />
    </div>
  );
}

// 帶分頁的虛擬化列表
interface PaginatedVirtualizedListProps<T> extends VirtualizedListProps<T> {
  pageSize?: number;
  totalCount?: number;
  currentPage?: number;
  onPageChange?: (page: number) => void;
  showPagination?: boolean;
}

export function PaginatedVirtualizedList<T>({
  items,
  pageSize = 50,
  totalCount,
  currentPage = 1,
  onPageChange,
  showPagination = true,
  ...listProps
}: PaginatedVirtualizedListProps<T>) {
  const totalPages = Math.ceil((totalCount || items.length) / pageSize);

  const handlePageChange = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages) {
      onPageChange?.(page);
    }
  }, [totalPages, onPageChange]);

  return (
    <div className="paginated-virtualized-list">
      <VirtualizedList {...listProps} items={items} />
      
      {showPagination && totalPages > 1 && (
        <div className="pagination-container mt-3">
          <nav>
            <ul className="pagination justify-content-center">
              <li className={`page-item ${currentPage <= 1 ? 'disabled' : ''}`}>
                <button
                  className="page-link"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                >
                  上一頁
                </button>
              </li>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = i + 1;
                return (
                  <li key={page} className={`page-item ${currentPage === page ? 'active' : ''}`}>
                    <button
                      className="page-link"
                      onClick={() => handlePageChange(page)}
                    >
                      {page}
                    </button>
                  </li>
                );
              })}
              
              <li className={`page-item ${currentPage >= totalPages ? 'disabled' : ''}`}>
                <button
                  className="page-link"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                >
                  下一頁
                </button>
              </li>
            </ul>
          </nav>
          
          <div className="text-center text-muted small">
            第 {currentPage} 頁，共 {totalPages} 頁 | 總共 {totalCount || items.length} 個項目
          </div>
        </div>
      )}
    </div>
  );
}

export default VirtualizedList;