/**
 * 管理後台專用入口點
 * 用於 twstock-admin-466914.web.app 和 admin.03king.com
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import AdminOnly from './AdminOnly';

// 管理後台專用樣式
import './admin/styles/enterprise-theme.css';

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root container not found');
}

const root = createRoot(container);

// 渲染純管理後台應用
root.render(<AdminOnly />);

// 在控制台輸出管理後台啟動信息
console.log('🔧 TradingAgents 企業管理後台已載入');
console.log('📊 管理功能：用戶管理、系統監控、數據分析');
console.log('🎯 當前環境：', process.env.NODE_ENV);