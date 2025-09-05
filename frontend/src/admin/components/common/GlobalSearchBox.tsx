/**
 * 全局搜尋框組件
 * 基於 functional_admin.html 的優秀搜尋功能實現
 * 提供即時搜尋、搜尋建議、結果高亮等功能
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { globalSearchService } from '../../services/GlobalSearchService';

interface SearchResult {
  id: string;
  title: string;
  type: 'user' | 'content' | 'analytics' | 'financial' | 'system' | 'subscription';
  content: string;
  url?: string;
  score: number;
}

interface GlobalSearchBoxProps {
  placeholder?: string;
  onResultSelect?: (result: SearchResult) => void;
  className?: string;
}

export const GlobalSearchBox: React.FC<GlobalSearchBoxProps> = ({
  placeholder = "全局搜尋...",
  onResultSelect,
  className = ""
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 防抖搜尋
  const debouncedSearch = useCallback(async (searchQuery: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(async () => {
      if (!searchQuery.trim()) {
        setResults([]);
        setSuggestions([]);
        setShowDropdown(false);
        return;
      }

      setIsLoading(true);
      try {
        const [searchResults, searchSuggestions] = await Promise.all([
          globalSearchService.performGlobalSearch(searchQuery),
          Promise.resolve(globalSearchService.getSearchSuggestions(searchQuery))
        ]);

        setResults(searchResults.slice(0, 8)); // 限制顯示結果數量
        setSuggestions(searchSuggestions);
        setShowDropdown(true);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, []);

  // 處理輸入變化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setSelectedIndex(-1);
    debouncedSearch(value);
  };

  // 處理鍵盤事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const totalItems = suggestions.length + results.length;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < totalItems - 1 ? prev + 1 : -1
        );
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > -1 ? prev - 1 : totalItems - 1
        );
        break;
      
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          if (selectedIndex < suggestions.length) {
            // 選擇建議
            const suggestion = suggestions[selectedIndex];
            setQuery(suggestion);
            debouncedSearch(suggestion);
          } else {
            // 選擇結果
            const result = results[selectedIndex - suggestions.length];
            handleResultSelect(result);
          }
        } else if (query.trim()) {
          // 直接搜尋
          debouncedSearch(query);
        }
        break;
      
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  // 處理結果選擇
  const handleResultSelect = (result: SearchResult) => {
    setQuery(result.title);
    setShowDropdown(false);
    onResultSelect?.(result);
  };

  // 處理建議選擇
  const handleSuggestionSelect = (suggestion: string) => {
    setQuery(suggestion);
    debouncedSearch(suggestion);
  };

  // 點擊外部關閉下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 獲取類型圖標
  const getTypeIcon = (type: string) => {
    const icons = {
      user: 'fas fa-user',
      content: 'fas fa-file-alt',
      analytics: 'fas fa-chart-bar',
      financial: 'fas fa-dollar-sign',
      system: 'fas fa-server',
      subscription: 'fas fa-credit-card'
    };
    return icons[type as keyof typeof icons] || 'fas fa-search';
  };

  // 獲取類型標籤
  const getTypeLabel = (type: string) => {
    const labels = {
      user: '用戶',
      content: '內容',
      analytics: '分析',
      financial: '財務',
      system: '系統',
      subscription: '訂閱'
    };
    return labels[type as keyof typeof labels] || type;
  };

  return (
    <div className={`global-search-container ${className}`}>
      <div className="search-input-wrapper">
        <div className="input-group">
          <span className="input-group-text">
            <i className="fas fa-search text-muted"></i>
          </span>
          <input
            ref={inputRef}
            type="text"
            className="form-control"
            placeholder={placeholder}
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => query && setShowDropdown(true)}
            autoComplete="off"
          />
          {isLoading && (
            <span className="input-group-text">
              <div className="spinner-border spinner-border-sm text-primary" role="status">
                <span className="visually-hidden">搜尋中...</span>
              </div>
            </span>
          )}
          {query && (
            <button
              className="btn btn-outline-secondary"
              type="button"
              onClick={() => {
                setQuery('');
                setResults([]);
                setSuggestions([]);
                setShowDropdown(false);
                globalSearchService.removeHighlights(document.body);
                inputRef.current?.focus();
              }}
            >
              <i className="fas fa-times"></i>
            </button>
          )}
        </div>
      </div>

      {/* 搜尋結果下拉框 */}
      {showDropdown && (suggestions.length > 0 || results.length > 0) && (
        <div ref={dropdownRef} className="search-dropdown">
          <div className="dropdown-content">
            {/* 搜尋建議 */}
            {suggestions.length > 0 && (
              <div className="suggestions-section">
                <div className="section-header">
                  <i className="fas fa-history text-muted me-2"></i>
                  <span className="text-muted">搜尋建議</span>
                </div>
                {suggestions.map((suggestion, index) => (
                  <div
                    key={`suggestion-${index}`}
                    className={`suggestion-item ${
                      index === selectedIndex ? 'selected' : ''
                    }`}
                    onClick={() => handleSuggestionSelect(suggestion)}
                  >
                    <i className="fas fa-clock text-muted me-2"></i>
                    <span>{suggestion}</span>
                  </div>
                ))}
              </div>
            )}

            {/* 搜尋結果 */}
            {results.length > 0 && (
              <div className="results-section">
                <div className="section-header">
                  <i className="fas fa-search-plus text-muted me-2"></i>
                  <span className="text-muted">搜尋結果</span>
                </div>
                {results.map((result, index) => (
                  <div
                    key={result.id}
                    className={`result-item ${
                      index + suggestions.length === selectedIndex ? 'selected' : ''
                    }`}
                    onClick={() => handleResultSelect(result)}
                  >
                    <div className="result-content">
                      <div className="result-header">
                        <i className={`${getTypeIcon(result.type)} text-primary me-2`}></i>
                        <span className="result-title">{result.title}</span>
                        <span className="badge bg-secondary ms-auto">
                          {getTypeLabel(result.type)}
                        </span>
                      </div>
                      <div className="result-description">
                        {result.content.length > 100
                          ? `${result.content.substring(0, 100)}...`
                          : result.content
                        }
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 無結果提示 */}
            {query && !isLoading && suggestions.length === 0 && results.length === 0 && (
              <div className="no-results">
                <i className="fas fa-search text-muted me-2"></i>
                <span className="text-muted">找不到相關結果</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};