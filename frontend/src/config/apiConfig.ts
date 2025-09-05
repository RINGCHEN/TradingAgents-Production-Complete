/**
 * 統一的 API 配置
 * 確保所有組件都使用正確的生產環境 API 地址
 */

// 生產環境 API 基礎URL
export const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8001' 
  : 'https://tradingagents-main-351731559902.asia-east1.run.app';

// WebSocket URL
export const WS_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'ws://localhost:8001' 
  : 'wss://tradingagents-main-351731559902.asia-east1.run.app';

// API 端點構造器
export const createApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${cleanEndpoint}`;
};

// WebSocket URL 構造器
export const createWsUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${WS_BASE_URL}${cleanEndpoint}`;
};

console.log(`🌐 API Config loaded: ${process.env.NODE_ENV} mode using ${API_BASE_URL}`);

export default {
  API_BASE_URL,
  WS_BASE_URL,
  createApiUrl,
  createWsUrl
};