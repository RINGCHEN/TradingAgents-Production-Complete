import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      // API代理配置 - 修復CORS和路由問題
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
      // 健康檢查代理
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // CORS測試代理
      '/cors-test': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'build',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom']
        }
      }
    }
  },
  base: '/',
  define: {
    // 環境變量定義
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_BASE_URL || ''),
    __ENVIRONMENT__: JSON.stringify(process.env.NODE_ENV || 'development')
  }
})
