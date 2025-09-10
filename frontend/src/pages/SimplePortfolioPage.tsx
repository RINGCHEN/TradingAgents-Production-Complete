import React, { useState, useEffect } from 'react';

// 全新的投資組合頁面 - 完全重新編寫
const SimplePortfolioPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newPortfolioName, setNewPortfolioName] = useState('');

  // API基礎URL - 更新為 DigitalOcean
  const API_BASE = 'https://twshocks-app-79rsx.ondigitalocean.app';

  // 簡單的fetch函數，強制使用CORS
  const simpleFetch = async (url: string, options: any = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
    
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': window.location.origin,
      },
      mode: 'cors' as RequestMode,
      credentials: 'include' as RequestCredentials,
      ...options
    };

    console.log('🚀 Simple Fetch:', fullUrl, defaultOptions);
    
    try {
      const response = await fetch(fullUrl, defaultOptions);
      const data = await response.json();
      console.log('📦 Response:', data);
      return data;
    } catch (err) {
      console.error('❌ Fetch Error:', err);
      throw err;
    }
  };

  // 載入投資組合 - 使用現有的API端點
  const loadPortfolios = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 首先嘗試新的API端點
      let data;
      try {
        data = await simpleFetch('/api/simple-portfolios');
      } catch (err) {
        // 如果新端點失敗，使用舊的端點
        console.log('新端點失敗，嘗試舊端點...');
        data = await simpleFetch('/api/portfolios');
      }
      
      if (data.success || data.portfolios) {
        setPortfolios(data.portfolios || []);
      } else if (data.detail && data.detail.includes('身份驗證')) {
        // 身份驗證失敗，創建一個示例投資組合
        setPortfolios([{
          id: 'demo_portfolio',
          name: '示例投資組合',
          description: '這是一個示例投資組合',
          created_at: Date.now() / 1000,
          holdings: []
        }]);
        setError('正在使用示例模式');
      } else {
        setError(data.error || '載入投資組合失敗');
      }
    } catch (err) {
      // 創建示例投資組合作為後備
      setPortfolios([{
        id: 'demo_portfolio',
        name: '示例投資組合',
        description: '這是一個示例投資組合',
        created_at: Date.now() / 1000,
        holdings: []
      }]);
      setError('網路連接問題，使用示例模式: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // 創建新投資組合 - 兼容模式
  const createPortfolio = async () => {
    if (!newPortfolioName.trim()) {
      setError('請輸入投資組合名稱');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let data;
      try {
        // 首先嘗試新的API端點
        data = await simpleFetch('/api/simple-portfolios', {
          method: 'POST',
          body: JSON.stringify({
            name: newPortfolioName,
            description: '簡單投資組合'
          })
        });
      } catch (err) {
        // 如果新端點失敗，嘗試舊端點
        console.log('新端點失敗，嘗試舊端點...');
        data = await simpleFetch('/api/portfolio', {
          method: 'POST',
          body: JSON.stringify({
            name: newPortfolioName,
            description: '簡單投資組合'
          })
        });
      }

      if (data.success || data.portfolio) {
        setNewPortfolioName('');
        // 直接添加新投資組合到列表，避免重新載入
        const newPortfolio = data.portfolio || {
          id: `manual_${Date.now()}`,
          name: newPortfolioName,
          description: '簡單投資組合',
          created_at: Date.now() / 1000,
          holdings: []
        };
        setPortfolios(prev => [...prev, newPortfolio]);
        setError(null);
      } else if (data.detail && data.detail.includes('身份驗證')) {
        // 身份驗證失敗，手動創建投資組合
        const newPortfolio = {
          id: `demo_${Date.now()}`,
          name: newPortfolioName,
          description: '示例投資組合',
          created_at: Date.now() / 1000,
          holdings: []
        };
        setPortfolios(prev => [...prev, newPortfolio]);
        setNewPortfolioName('');
        setError('已在示例模式下創建投資組合');
      } else {
        setError(data.error || '創建投資組合失敗');
      }
    } catch (err) {
      // 作為後備，手動創建投資組合
      const newPortfolio = {
        id: `offline_${Date.now()}`,
        name: newPortfolioName,
        description: '離線投資組合',
        created_at: Date.now() / 1000,
        holdings: []
      };
      setPortfolios(prev => [...prev, newPortfolio]);
      setNewPortfolioName('');
      setError('網路問題，已離線創建投資組合');
    } finally {
      setLoading(false);
    }
  };

  // 測試API連接
  const testConnection = async () => {
    try {
      const data = await simpleFetch('/api/simple-portfolios/health');
      console.log('✅ 連接測試成功:', data);
      alert('API連接正常: ' + JSON.stringify(data));
    } catch (err) {
      console.error('❌ 連接測試失敗:', err);
      alert('API連接失敗: ' + (err as Error).message);
    }
  };

  // 頁面載入時載入投資組合
  useEffect(() => {
    loadPortfolios();
  }, []);

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '30px',
        borderRadius: '10px',
        marginBottom: '30px'
      }}>
        <h1 style={{ margin: '0 0 10px 0', fontSize: '2.5em' }}>
          🚀 全新投資組合系統
        </h1>
        <p style={{ margin: '0', fontSize: '1.2em', opacity: 0.9 }}>
          重新打造，簡單可靠的投資組合管理
        </p>
      </div>

      {/* 測試連接按鈕 */}
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={testConnection}
          style={{
            background: '#28a745',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '5px',
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          🔍 測試API連接
        </button>
        <button 
          onClick={loadPortfolios}
          disabled={loading}
          style={{
            background: '#17a2b8',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? '⏳ 載入中...' : '🔄 重新載入'}
        </button>
      </div>

      {/* 創建新投資組合 */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <h3>📝 創建新投資組合</h3>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="輸入投資組合名稱"
            value={newPortfolioName}
            onChange={(e) => setNewPortfolioName(e.target.value)}
            style={{
              flex: 1,
              padding: '10px',
              border: '2px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
          <button
            onClick={createPortfolio}
            disabled={loading}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? '⏳' : '➕'} 創建
          </button>
        </div>
      </div>

      {/* 錯誤信息 */}
      {error && (
        <div style={{
          background: '#f8d7da',
          border: '1px solid #f5c6cb',
          color: '#721c24',
          padding: '15px',
          borderRadius: '5px',
          marginBottom: '20px'
        }}>
          ❌ {error}
        </div>
      )}

      {/* 投資組合列表 */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <h3>📊 我的投資組合 ({portfolios.length})</h3>
        
        {portfolios.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#666',
            fontSize: '18px'
          }}>
            {loading ? '⏳ 載入中...' : '📁 還沒有投資組合，請創建一個'}
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '15px' }}>
            {portfolios.map((portfolio) => {
              // 安全檢查，防止 undefined 錯誤
              if (!portfolio || typeof portfolio !== 'object') {
                return null;
              }
              
              return (
                <div
                  key={portfolio.id || `portfolio-${Math.random()}`}
                  style={{
                    border: '2px solid #e9ecef',
                    borderRadius: '8px',
                    padding: '15px',
                    background: '#f8f9fa'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ margin: '0 0 5px 0', color: '#495057' }}>
                        📈 {portfolio.name || '未命名投資組合'}
                      </h4>
                      <p style={{ margin: '0', color: '#6c757d', fontSize: '14px' }}>
                        {portfolio.description || '無描述'}
                      </p>
                      <small style={{ color: '#adb5bd' }}>
                        創建時間: {portfolio.created_at ? new Date(portfolio.created_at * 1000).toLocaleString() : '未知時間'}
                      </small>
                    </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      style={{
                        background: '#28a745',
                        color: 'white',
                        border: 'none',
                        padding: '5px 15px',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      📋 查看持股
                    </button>
                    <button
                      style={{
                        background: '#ffc107',
                        color: '#212529',
                        border: 'none',
                        padding: '5px 15px',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      ➕ 添加持股
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 調試信息 */}
      <div style={{
        marginTop: '20px',
        padding: '10px',
        background: '#f8f9fa',
        borderRadius: '5px',
        fontSize: '12px',
        fontFamily: 'monospace'
      }}>
        <strong>🔧 調試信息:</strong><br/>
        當前域名: {window.location.origin}<br/>
        API基礎URL: {API_BASE}<br/>
        投資組合數量: {portfolios.length}<br/>
        載入狀態: {loading ? '載入中' : '完成'}<br/>
        錯誤狀態: {error || '無'}
      </div>
    </div>
  );
};

export default SimplePortfolioPage;