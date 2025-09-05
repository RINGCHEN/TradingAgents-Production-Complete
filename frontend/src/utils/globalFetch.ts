/**
 * 全域 fetch 封裝器
 * 自動將相對 API 路徑轉換為完整的後端 URL
 * 解決生產環境中 /api/ 路徑指向前端而不是後端的問題
 */

import { API_BASE_URL } from '../config/apiConfig';

// 創建增強的 fetch 函數
const enhancedFetch = (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  let url: string;
  
  if (typeof input === 'string') {
    url = input;
  } else if (input instanceof URL) {
    url = input.toString();
  } else {
    url = input.url;
  }
  
  // 如果是相對的 API 路徑，轉換為完整的後端 URL
  if (url.startsWith('/api/')) {
    const originalUrl = url;
    url = `${API_BASE_URL}${url}`;
    console.log(`🔧 GLOBALFETCH ACTIVE: ${originalUrl} → ${url}`);
    console.log(`🎯 API_BASE_URL: ${API_BASE_URL}`);
    console.log(`🚀 This message confirms globalFetch is working!`);
  }
  
  // 調用原始的 fetch
  return window.originalFetch(url, init);
};

// 保存原始的 fetch 函數
if (typeof window !== 'undefined' && !window.originalFetch) {
  window.originalFetch = window.fetch;
  
  // 替換全域的 fetch 函數
  window.fetch = enhancedFetch;
  
  console.log('🚀 GLOBALFETCH INITIALIZED - VERSION 2.0');
  console.log('🔧 All /api/ paths will be redirected to backend URL');
  console.log('🎯 Backend URL:', API_BASE_URL);
}

// 手動轉換 URL 的工具函數
export const convertApiUrl = (url: string): string => {
  if (url.startsWith('/api/')) {
    return `${API_BASE_URL}${url}`;
  }
  return url;
};

// TypeScript 聲明
declare global {
  interface Window {
    originalFetch: typeof fetch;
  }
}

export default enhancedFetch;