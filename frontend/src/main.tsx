import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 導入全域 fetch 封裝器 - 修復 API 路徑問題
import './utils/globalFetch'

// 確保DOM元素存在
const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found')
}

// 隱藏載入動畫
const loadingElement = document.getElementById('loading')
if (loadingElement) {
  loadingElement.style.display = 'none'
}

// 渲染React應用
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// 應用載入完成後的處理
console.log('🚀 TradingAgents React應用已載入')
