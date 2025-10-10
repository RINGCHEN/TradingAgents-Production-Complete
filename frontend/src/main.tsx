import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 撠?典? fetch 撠???- 靽桀儔 API 頝臬???
import './utils/globalFetch'

async function enableMocking() {
  if (import.meta.env.DEV) {
    try {
      const { worker } = await import('./mocks/browser')
      await worker.start({
        onUnhandledRequest: 'warn'
      })
      console.info('[MSW] Browser worker started (dev mode)')
    } catch (error) {
      console.warn('[MSW] Failed to start browser worker:', error)
    }
  }
}

async function startApp() {
  await enableMocking()

  // 蝣箔?DOM??摮
  const rootElement = document.getElementById('root')

  if (!rootElement) {
    throw new Error('Root element not found')
  }

  // ?梯?頛?
  const loadingElement = document.getElementById('loading')
  if (loadingElement) {
    loadingElement.style.display = 'none'
  }

  // 皜脫?React?
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )

  // ?頛摰?敺???
  console.log('?? TradingAgents React?撌脰???)
}

startApp()
