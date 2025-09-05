/**
 * 管理後台配置
 */

export const ADMIN_CONFIG = {
  // API配置
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || '/api',
  API_TIMEOUT: 30000,
  
  // 分頁配置
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  
  // 表格配置
  TABLE_SCROLL_Y: 400,
  
  // 通知配置
  NOTIFICATION_DURATION: 5000,
  
  // 主題配置
  THEME: {
    PRIMARY_COLOR: '#667eea',
    SECONDARY_COLOR: '#764ba2',
    SUCCESS_COLOR: '#28a745',
    WARNING_COLOR: '#ffc107',
    ERROR_COLOR: '#dc3545',
    INFO_COLOR: '#17a2b8'
  },
  
  // 功能開關
  FEATURES: {
    USER_MANAGEMENT: true,
    ANALYTICS: true,
    CONTENT_MANAGEMENT: true,
    FINANCIAL_MANAGEMENT: true,
    SYSTEM_MONITORING: true
  }
};