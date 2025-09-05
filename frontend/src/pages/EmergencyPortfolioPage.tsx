import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const EmergencyPortfolioPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  // 初始化時創建示例數據
  useEffect(() => {
    const demoPortfolios = [
      {
        id: 'demo-1',
        name: '我的第一個投資組合',
        description: '示例投資組合，讓您了解功能',
        totalValue: 150000,
        totalCost: 140000,
        totalGain: 10000,
        totalGainPercent: 7.14,
        holdings: []
      }
    ];
    setPortfolios(demoPortfolios);
    setMessage('投資組合功能正常運行中');
  }, []);

  // 創建新投資組合
  const createPortfolio = () => {
    if (!newPortfolioName.trim()) {
      alert('請輸入投資組合名稱');
      return;
    }

    const newPortfolio = {
      id: `portfolio-${Date.now()}`,
      name: newPortfolioName,
      description: '用戶創建的投資組合',
      totalValue: 0,
      totalCost: 0,
      totalGain: 0,
      totalGainPercent: 0,
      holdings: []
    };

    setPortfolios(prev => [...prev, newPortfolio]);
    setNewPortfolioName('');
    setShowCreateForm(false);
    setMessage('投資組合創建成功！');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 標題 */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '30px',
        borderRadius: '10px',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: '0 0 10px 0' }}>📊 投資組合管理</h1>
        <p style={{ margin: '0', opacity: 0.9 }}>管理您的投資組合</p>
      </div>

      {/* 狀態信息 */}
      {message && (
        <div style={{
          background: '#d4edda',
          color: '#155724',
          padding: '10px',
          borderRadius: '5px',
          marginBottom: '20px',
          border: '1px solid #c3e6cb'
        }}>
          ✅ {message}
        </div>
      )}

      {/* 創建投資組合按鈕 */}
      <div style={{ marginBottom: '20px' }}>
        {!showCreateForm ? (
          <button
            onClick={() => setShowCreateForm(true)}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            ➕ 創建新投資組合
          </button>
        ) : (
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '8px',
            border: '2px solid #007bff'
          }}>
            <h3 style={{ marginTop: 0 }}>創建新投資組合</h3>
            <input
              type="text"
              placeholder="請輸入投資組合名稱"
              value={newPortfolioName}
              onChange={(e) => setNewPortfolioName(e.target.value)}
              style={{
                width: '300px',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                marginRight: '10px',
                fontSize: '16px'
              }}
            />
            <button
              onClick={createPortfolio}
              disabled={loading}
              style={{
                background: '#28a745',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: loading ? 'not-allowed' : 'pointer',
                marginRight: '10px'
              }}
            >
              {loading ? '創建中...' : '創建'}
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              取消
            </button>
          </div>
        )}
      </div>

      {/* 投資組合列表 */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <h2>我的投資組合 ({portfolios.length})</h2>
        
        {portfolios.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#666'
          }}>
            <p>還沒有投資組合，請創建一個</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '15px' }}>
            {portfolios.map((portfolio) => (
              <div
                key={portfolio.id}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  background: '#f8f9fa'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: '0 0 5px 0', color: '#495057' }}>
                      📈 {portfolio.name}
                    </h3>
                    <p style={{ margin: '0 0 10px 0', color: '#6c757d' }}>
                      {portfolio.description}
                    </p>
                    <div style={{ fontSize: '14px', color: '#6c757d' }}>
                      <span style={{ marginRight: '20px' }}>
                        總價值: ${portfolio.totalValue?.toLocaleString() || 0}
                      </span>
                      <span style={{ marginRight: '20px' }}>
                        總成本: ${portfolio.totalCost?.toLocaleString() || 0}
                      </span>
                      <span style={{ 
                        color: (portfolio.totalGain || 0) >= 0 ? '#28a745' : '#dc3545'
                      }}>
                        損益: ${portfolio.totalGain?.toLocaleString() || 0} 
                        ({portfolio.totalGainPercent?.toFixed(2) || 0}%)
                      </span>
                    </div>
                  </div>
                  <div>
                    <button
                      style={{
                        background: '#007bff',
                        color: 'white',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      查看詳情
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmergencyPortfolioPage;