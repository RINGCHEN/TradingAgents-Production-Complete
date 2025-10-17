import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Global fetch wrapper for API monitoring
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

  // Find root DOM element
  const rootElement = document.getElementById('root')

  if (!rootElement) {
    throw new Error('Root element not found')
  }

  // Hide loading screen
  const loadingElement = document.getElementById('loading')
  if (loadingElement) {
    loadingElement.style.display = 'none'
  }

  // Mount React app
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )

  // Log successful startup
  console.log('[TradingAgents] React application started successfully')
}

startApp()
