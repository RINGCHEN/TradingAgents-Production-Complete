import React from 'react';
import { Link } from 'react-router-dom';

const ApiPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">API 文檔</h1>
        
        <div className="prose max-w-none">
          <p className="text-gray-600 mb-8">
            TradingAgents API 為開發者提供程式化存取我們AI投資分析服務的能力。
          </p>
          
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-8">
            <p className="font-medium text-blue-800">開發者預覽版</p>
            <p className="text-blue-700">
              API服務目前處於開發者預覽階段。完整的API文檔即將推出。
            </p>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">主要功能</h2>
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">股票分析 API</h3>
              <p className="text-gray-600 text-sm">
                獲取AI分析師對特定股票的專業分析和建議
              </p>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">市場數據 API</h3>
              <p className="text-gray-600 text-sm">
                存取即時和歷史市場數據，包括價格、成交量等
              </p>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">投資組合 API</h3>
              <p className="text-gray-600 text-sm">
                管理和分析投資組合，獲取績效報告和建議
              </p>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">風險評估 API</h3>
              <p className="text-gray-600 text-sm">
                計算投資風險指標，提供風險管理建議
              </p>
            </div>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">認證方式</h2>
          <p className="mb-4">API 使用 Bearer Token 認證方式：</p>
          <div className="bg-gray-100 p-4 rounded-lg mb-6">
            <code className="text-sm">
              Authorization: Bearer YOUR_API_TOKEN
            </code>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">使用限制</h2>
          <ul className="list-disc pl-6 mb-6">
            <li>免費用戶：每日100次請求</li>
            <li>黃金會員：每日1,000次請求</li>
            <li>鑽石會員：每日10,000次請求</li>
            <li>請求頻率限制：每秒最多10次請求</li>
          </ul>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">基本範例</h2>
          <div className="bg-gray-100 p-4 rounded-lg mb-6">
            <pre className="text-sm"><code>{`// 獲取股票分析
fetch('https://api.tradingagents.com/v1/analysis/2330', {
  headers: {
    'Authorization': 'Bearer YOUR_API_TOKEN',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));`}</code></pre>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">回應格式</h2>
          <p className="mb-4">所有API回應使用JSON格式：</p>
          <div className="bg-gray-100 p-4 rounded-lg mb-6">
            <pre className="text-sm"><code>{`{
  "success": true,
  "data": {
    "symbol": "2330",
    "analysis": {
      "recommendation": "買進",
      "target_price": 650,
      "confidence": 0.85
    }
  },
  "timestamp": "2025-01-17T12:00:00Z"
}`}</code></pre>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">獲取 API 金鑰</h2>
          <p className="mb-4">
            要使用我們的API，您需要先註冊帳戶並升級至付費方案：
          </p>
          <div className="space-x-4">
            <Link 
              to="/auth?mode=register" 
              className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              註冊帳戶
            </Link>
            <Link 
              to="/subscription" 
              className="inline-block border border-blue-600 text-blue-600 px-6 py-2 rounded-lg hover:bg-blue-50 transition-colors"
            >
              查看方案
            </Link>
          </div>
          
          <div className="mt-12 p-4 bg-yellow-50 rounded-lg">
            <h3 className="font-semibold text-yellow-800 mb-2">即將推出</h3>
            <ul className="text-yellow-700 text-sm space-y-1">
              <li>• 完整的API文檔和互動式測試工具</li>
              <li>• SDK支援（Python、JavaScript、Go）</li>
              <li>• Webhook支援即時通知</li>
              <li>• GraphQL API端點</li>
            </ul>
          </div>
        </div>
        
        <div className="mt-8">
          <Link 
            to="/" 
            className="text-blue-600 hover:text-blue-800 transition-colors"
          >
            ← 返回首頁
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ApiPage;