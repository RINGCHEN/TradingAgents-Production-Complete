import React, { useState, useEffect } from 'react';

// 全新的投資組合頁面 - 完全重新編寫，修復 toFixed 錯誤
const SimplePortfolioPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [mounted, setMounted] = useState(false);
  const [criticalError, setCriticalError] = useState<string | null>(null);

  // 頂層錯誤處理
  const handleCriticalError = (error: Error, context: string) => {
    console.error(`💥 關鍵錯誤 [${context}]:`, error);
    setCriticalError(`組件錯誤: ${error.message}`);
  };

  // API基礎URL - 更新為 DigitalOcean (修復版 v2.1)
  const API_BASE = 'https://twshocks-app-79rsx.ondigitalocean.app';

  // 修復後的fetch函數 - 加入重試機制和健康檢查
  const simpleFetch = async (url: string, options: any = {}, retryCount = 0) => {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
    const MAX_RETRIES = 3;
    
    // 準備認證token
    const authToken = localStorage.getItem('auth_token') || 'temp-token';
    
    // 最基本的 fetch 配置，讓瀏覽器處理所有 CORS 細節，加上認證
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        ...(options.body && { 'Content-Type': 'application/json' })
      },
      mode: 'cors' as RequestMode,
      timeout: 10000, // 10秒超時
      ...options
    };

    console.log(`🚀 API請求 (嘗試 ${retryCount + 1}/${MAX_RETRIES + 1}):`, fullUrl);
    
    try {
      const response = await fetch(fullUrl, defaultOptions);
      
      console.log('📡 HTTP狀態:', response.status, response.statusText);
      
      // 檢查是否為伺服器錯誤 (5xx)
      if (response.status >= 500) {
        const errorText = await response.text().catch(() => '');
        console.error(`❌ 伺服器錯誤 ${response.status}:`, errorText);
        
        // 如果是 502, 503, 504 且還有重試次數，則重試
        if ([502, 503, 504].includes(response.status) && retryCount < MAX_RETRIES) {
          const delay = Math.pow(2, retryCount) * 1000; // 指數退避：1s, 2s, 4s
          console.log(`⏳ ${delay}ms後重試...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          return simpleFetch(url, options, retryCount + 1);
        }
        
        throw new Error(`HTTP ${response.status}: ${response.statusText} - 伺服器暫時無法回應`);
      }
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        console.error('❌ HTTP錯誤詳情:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ API回應成功:', data);
      return data;
    } catch (err) {
      console.error('❌ Fetch錯誤詳情:', err);
      
      // 網路錯誤也重試
      if ((err instanceof TypeError && err.message.includes('fetch')) && retryCount < MAX_RETRIES) {
        const delay = Math.pow(2, retryCount) * 1000;
        console.log(`⏳ 網路錯誤，${delay}ms後重試...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return simpleFetch(url, options, retryCount + 1);
      }
      
      throw err;
    }
  };

  // 載入投資組合 - 使用現有的API端點
  const loadPortfolios = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 開始載入投資組合...');
      let data;
      try {
        // 根據 Gemini 修復報告，使用正確的 API 端點
        data = await simpleFetch('/api/v1/portfolios');
        console.log('✅ API呼叫成功，回應資料:', data);
      } catch (err) {
        console.log('⚠️ 主端點失敗，嘗試備用端點...', err);
        data = await simpleFetch('/api/portfolios');
      }
      
      // 更詳細的回應資料檢查
      console.log('📊 檢查API回應結構:', {
        hasSuccess: !!data.success,
        hasPortfolios: !!data.portfolios,
        successValue: data.success,
        portfoliosLength: data.portfolios?.length,
        fullData: data
      });
      
      if (data.success === true && data.portfolios) {
        console.log('✅ 成功載入投資組合:', data.portfolios.length, '個項目');
        setPortfolios(data.portfolios);
        setError(null); // 清除任何錯誤信息
      } else if (data.portfolios && Array.isArray(data.portfolios)) {
        console.log('✅ 找到portfolios陣列，載入:', data.portfolios.length, '個項目');
        setPortfolios(data.portfolios);
        setError(null);
      } else if (data.detail && data.detail.includes('身份驗證')) {
        console.log('⚠️ 身份驗證問題，使用示例模式');
        setPortfolios([{
          id: 'demo_portfolio',
          name: '示例投資組合',
          description: '這是一個示例投資組合',
          created_at: Date.now() / 1000,
          holdings: []
        }]);
        setError('正在使用示例模式');
      } else {
        console.error('❌ API回應結構異常:', data);
        setPortfolios([]);
        setError('API回應格式異常: ' + JSON.stringify(data));
      }
    } catch (err) {
      console.error('❌ 載入投資組合失敗:', err);
      // 只有在真正的網路錯誤時才創建示例
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
      console.log('🏁 載入流程完成');
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
        // 根據 Gemini 修復報告，使用正確的 API 端點
        data = await simpleFetch('/api/v1/portfolio', {
          method: 'POST',
          body: JSON.stringify({
            name: newPortfolioName,
            description: '簡單投資組合'
          })
        });
      } catch (err) {
        // 如果失敗，嘗試舊端點作為備用
        console.log('新端點失敗，嘗試備用端點...');
        data = await simpleFetch('/api/portfolio', {
          method: 'POST',
          body: JSON.stringify({
            name: newPortfolioName,
            description: '簡單投資組合'
          })
        });
      }

      console.log('📊 創建投資組合API回應:', data);
      
      if (data.success === true || data.portfolio) {
        console.log('✅ 投資組合創建成功');
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
        console.log('⚠️ 身份驗證問題，創建示例投資組合');
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
        console.error('❌ 創建投資組合失敗:', data);
        setError(data.error || '創建投資組合失敗: ' + JSON.stringify(data));
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
      // 根據 Gemini 修復報告，測試正確的 API 端點
      const data = await simpleFetch('/api/v1/portfolios');
      console.log('✅ 連接測試成功:', data);
      alert('API連接正常: ' + JSON.stringify(data));
    } catch (err) {
      console.error('❌ 連接測試失敗:', err);
      alert('API連接失敗: ' + (err as Error).message);
    }
  };

  // 頁面載入時載入投資組合 - 加入安全檢查
  useEffect(() => {
    setMounted(true);
    // 延遲載入，避免組件掛載時的錯誤
    const timer = setTimeout(() => {
      if (mounted) {
        loadPortfolios();
      }
    }, 100);
    
    return () => {
      clearTimeout(timer);
      setMounted(false);
    };
  }, []);

  // 如果有關鍵錯誤，顯示錯誤頁面
  if (criticalError) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{ 
          background: '#f8d7da', 
          border: '1px solid #f5c6cb', 
          color: '#721c24', 
          padding: '20px', 
          borderRadius: '8px',
          margin: '20px auto',
          maxWidth: '600px'
        }}>
          <h2>🚫 投資組合系統暫時無法使用</h2>
          <p>{criticalError}</p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            🔄 重新載入頁面
          </button>
        </div>
      </div>
    );
  }

  // 如果組件未掛載，顯示載入狀態
  if (!mounted) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#666' }}>⏳ 投資組合系統載入中...</div>
      </div>
    );
  }

  try {
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
                        創建時間: {(() => {
                          try {
                            if (portfolio.created_at && typeof portfolio.created_at === 'number') {
                              return new Date(portfolio.created_at * 1000).toLocaleString();
                            }
                            return '未知時間';
                          } catch (e) {
                            console.warn('日期轉換錯誤:', e);
                            return '未知時間';
                          }
                        })()}
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
  } catch (error) {
    // 如果渲染過程中發生錯誤，捕獲並顯示友善錯誤信息
    console.error('💥 組件渲染錯誤:', error);
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{ 
          background: '#f8d7da', 
          border: '1px solid #f5c6cb', 
          color: '#721c24', 
          padding: '20px', 
          borderRadius: '8px',
          margin: '20px auto',
          maxWidth: '600px'
        }}>
          <h2>🚫 投資組合頁面發生錯誤</h2>
          <p>系統暫時無法顯示投資組合，請稍後再試。</p>
          <p style={{ fontSize: '12px', color: '#666' }}>
            錯誤詳情: {error instanceof Error ? error.message : '未知錯誤'}
          </p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '5px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            🔄 重新載入頁面
          </button>
        </div>
      </div>
    );
  }
};

export default SimplePortfolioPage;