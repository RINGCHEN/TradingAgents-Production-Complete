import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './MarketMonitorPage.css';

// 市場監控頁面 - 實時監控和通知
// Phase 2.5 - 實時監控和通知

interface WatchlistStock {
  id: string;
  symbol: string;
  companyName: string;
  market: string;
  currentPrice: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
  marketCap?: number;
  lastUpdated: string;
  alerts: PriceAlert[];
}

interface PriceAlert {
  id: string;
  symbol: string;
  type: 'price_above' | 'price_below' | 'change_percent' | 'volume_spike';
  condition: number;
  message: string;
  isActive: boolean;
  createdAt: string;
  triggeredAt?: string;
}

interface MarketEvent {
  id: string;
  type: 'earnings' | 'dividend' | 'split' | 'news' | 'economic';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  affectedSymbols: string[];
  eventTime: string;
  source: string;
}

interface MarketIndex {
  symbol: string;
  name: string;
  value: number;
  change: number;
  changePercent: number;
  lastUpdated: string;
}

const MarketMonitorPage: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [marketEvents, setMarketEvents] = useState<MarketEvent[]>([]);
  const [marketIndices, setMarketIndices] = useState<MarketIndex[]>([]);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [showAddStock, setShowAddStock] = useState(false);
  const [showCreateAlert, setShowCreateAlert] = useState(false);
  const [newStockSymbol, setNewStockSymbol] = useState('');
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [newAlert, setNewAlert] = useState({
    type: 'price_above' as const,
    condition: 0,
    message: ''
  });
  const [viewMode, setViewMode] = useState<'overview' | 'watchlist' | 'alerts' | 'events'>('overview');
  const wsRef = useRef<WebSocket | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadInitialData();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 載入初始數據
  const loadInitialData = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        navigate('/auth?mode=login');
        return;
      }

      // 並行載入所有數據
      const [watchlistRes, alertsRes, eventsRes, indicesRes] = await Promise.all([
        fetch('/api/market/watchlist', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('/api/market/alerts', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('/api/market/events'),
        fetch('/api/market/indices')
      ]);

      if (watchlistRes.ok) {
        const data = await watchlistRes.json();
        setWatchlist(data.watchlist || []);
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAlerts(data.alerts || []);
      }

      if (eventsRes.ok) {
        const data = await eventsRes.json();
        setMarketEvents(data.events || []);
      }

      if (indicesRes.ok) {
        const data = await indicesRes.json();
        setMarketIndices(data.indices || []);
      }
    } catch (error) {
      console.error('載入市場數據失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // WebSocket 連接
  const connectWebSocket = () => {
    try {
      const token = localStorage.getItem('auth_token');
      const wsUrl = `ws://localhost:8000/ws/market?token=${token}`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket 連接成功');
        setIsConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket 連接關閉');
        setIsConnected(false);
        
        // 5秒後重新連接
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.CLOSED) {
            connectWebSocket();
          }
        }, 5000);
      };
      
      wsRef.current.onerror = (error: any) => {
        console.error('WebSocket 錯誤:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('WebSocket 連接失敗:', error);
      setIsConnected(false);
    }
  };

  // 處理 WebSocket 消息
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'price_update':
        updateStockPrice(data.symbol, data.price_data);
        break;
      case 'alert_triggered':
        handleAlertTriggered(data.alert);
        break;
      case 'market_event':
        addMarketEvent(data.event);
        break;
      case 'index_update':
        updateMarketIndex(data.index_data);
        break;
    }
  };

  // 更新股票價格
  const updateStockPrice = (symbol: string, priceData: any) => {
    setWatchlist(prev => prev.map(stock => 
      stock.symbol === symbol 
        ? {
            ...stock,
            currentPrice: priceData.price,
            change: priceData.change,
            changePercent: priceData.changePercent,
            volume: priceData.volume,
            high: priceData.high,
            low: priceData.low,
            lastUpdated: new Date().toISOString()
          }
        : stock
    ));
  };

  // 處理預警觸發
  const handleAlertTriggered = (alert: PriceAlert) => {
    // 更新預警狀態
    setAlerts(prev => prev.map(a => 
      a.id === alert.id 
        ? { ...a, triggeredAt: new Date().toISOString() }
        : a
    ));

    // 顯示通知
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('TradingAgents 價格預警', {
        body: alert.message,
        icon: '/favicon.ico'
      });
    }

    // 播放提示音
    const audio = new Audio('/notification.mp3');
    audio.play().catch(() => {
      // 忽略播放失敗
    });
  };

  // 添加市場事件
  const addMarketEvent = (event: MarketEvent) => {
    setMarketEvents(prev => [event, ...prev.slice(0, 49)]); // 保持最新50個事件
  };

  // 更新市場指數
  const updateMarketIndex = (indexData: any) => {
    setMarketIndices(prev => prev.map(index => 
      index.symbol === indexData.symbol 
        ? { ...index, ...indexData, lastUpdated: new Date().toISOString() }
        : index
    ));
  };

  // 添加股票到關注列表
  const addToWatchlist = async () => {
    if (!newStockSymbol.trim()) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/market/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ symbol: newStockSymbol.toUpperCase() })
      });

      if (response.ok) {
        const data = await response.json();
        setWatchlist(prev => [...prev, data.stock]);
        setNewStockSymbol('');
        setShowAddStock(false);
      } else {
        const errorData = await response.json();
        alert(errorData.message || '添加失敗');
      }
    } catch (error) {
      console.error('添加股票失敗:', error);
      alert('添加失敗，請稍後再試');
    }
  };

  // 從關注列表移除股票
  const removeFromWatchlist = async (stockId: string) => {
    if (!confirm('確定要從關注列表中移除這支股票嗎？')) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/market/watchlist/${stockId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setWatchlist(prev => prev.filter(stock => stock.id !== stockId));
      }
    } catch (error) {
      console.error('移除股票失敗:', error);
      alert('移除失敗，請稍後再試');
    }
  };

  // 創建價格預警
  const createAlert = async () => {
    if (!selectedStock || !newAlert.condition || !newAlert.message.trim()) {
      alert('請填寫完整的預警資訊');
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/market/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          symbol: selectedStock,
          type: newAlert.type,
          condition: newAlert.condition,
          message: newAlert.message
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(prev => [...prev, data.alert]);
        setNewAlert({ type: 'price_above', condition: 0, message: '' });
        setSelectedStock('');
        setShowCreateAlert(false);
      } else {
        const errorData = await response.json();
        alert(errorData.message || '創建預警失敗');
      }
    } catch (error) {
      console.error('創建預警失敗:', error);
      alert('創建失敗，請稍後再試');
    }
  };

  // 切換預警狀態
  const toggleAlert = async (alertId: string, isActive: boolean) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/market/alerts/${alertId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ isActive })
      });

      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId ? { ...alert, isActive } : alert
        ));
      }
    } catch (error) {
      console.error('更新預警失敗:', error);
    }
  };

  // 刪除預警
  const deleteAlert = async (alertId: string) => {
    if (!confirm('確定要刪除這個預警嗎？')) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/market/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setAlerts(prev => prev.filter(alert => alert.id !== alertId));
      }
    } catch (error) {
      console.error('刪除預警失敗:', error);
      alert('刪除失敗，請稍後再試');
    }
  };

  // 請求通知權限
  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        alert('通知權限已開啟');
      }
    }
  };

  // 格式化數字
  const formatNumber = (num: number) => {
    if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (Math.abs(num) >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toFixed(2);
  };

  // 格式化百分比
  const formatPercent = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  // 獲取變化顏色
  const getChangeColor = (change: number) => {
    if (change > 0) return '#27ae60';
    if (change < 0) return '#e74c3c';
    return '#95a5a6';
  };

  // 獲取事件影響顏色
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#e74c3c';
      case 'medium': return '#f39c12';
      case 'low': return '#3498db';
      default: return '#95a5a6';
    }
  };

  // 格式化時間
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="market-monitor-loading">
        <div className="loading-spinner"></div>
        <p>載入市場數據中...</p>
      </div>
    );
  } 
 return (
    <div className="market-monitor-page">
      {/* 頁面標題 */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-main">
            <h1 className="page-title">市場監控</h1>
            <p className="page-subtitle">
              實時監控市場動態，獲得智能預警通知
            </p>
          </div>
          <div className="connection-status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              <span className="status-text">
                {isConnected ? '實時連接' : '連接中斷'}
              </span>
            </div>
            <button
              type="button"
              className="notification-btn"
              onClick={requestNotificationPermission}
            >
              🔔 開啟通知
            </button>
          </div>
        </div>
      </div>

      <div className="monitor-container">
        {/* 市場指數概覽 */}
        <div className="market-indices">
          <h3 className="section-title">市場指數</h3>
          <div className="indices-grid">
            {marketIndices.map((index) => (
              <div key={index.symbol} className="index-card">
                <div className="index-name">{index.name}</div>
                <div className="index-value">{formatNumber(index.value)}</div>
                <div 
                  className="index-change"
                  style={{ color: getChangeColor(index.change) }}
                >
                  {formatPercent(index.changePercent)} ({formatNumber(index.change)})
                </div>
                <div className="index-time">
                  {formatTime(index.lastUpdated)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 視圖切換 */}
        <div className="view-tabs">
          <button
            type="button"
            className={`view-tab ${viewMode === 'overview' ? 'active' : ''}`}
            onClick={() => setViewMode('overview')}
          >
            📊 概覽
          </button>
          <button
            type="button"
            className={`view-tab ${viewMode === 'watchlist' ? 'active' : ''}`}
            onClick={() => setViewMode('watchlist')}
          >
            👁️ 關注列表 ({watchlist.length})
          </button>
          <button
            type="button"
            className={`view-tab ${viewMode === 'alerts' ? 'active' : ''}`}
            onClick={() => setViewMode('alerts')}
          >
            🚨 預警 ({alerts.filter(a => a.isActive).length})
          </button>
          <button
            type="button"
            className={`view-tab ${viewMode === 'events' ? 'active' : ''}`}
            onClick={() => setViewMode('events')}
          >
            📰 市場事件
          </button>
        </div>

        {/* 內容區域 */}
        <div className="view-content">
          {viewMode === 'overview' && (
            <div className="overview-content">
              {/* 關注列表預覽 */}
              <div className="content-section">
                <div className="section-header">
                  <h4>關注列表</h4>
                  <button
                    type="button"
                    className="add-stock-btn"
                    onClick={() => setShowAddStock(true)}
                  >
                    + 添加股票
                  </button>
                </div>
                <div className="watchlist-preview">
                  {watchlist.slice(0, 5).map((stock) => (
                    <div key={stock.id} className="stock-preview-item">
                      <div className="stock-info">
                        <div className="stock-symbol">{stock.symbol}</div>
                        <div className="stock-name">{stock.companyName}</div>
                      </div>
                      <div className="stock-price">
                        <div className="current-price">${stock.currentPrice.toFixed(2)}</div>
                        <div 
                          className="price-change"
                          style={{ color: getChangeColor(stock.change) }}
                        >
                          {formatPercent(stock.changePercent)}
                        </div>
                      </div>
                    </div>
                  ))}
                  {watchlist.length === 0 && (
                    <div className="empty-watchlist">
                      <p>還沒有關注的股票</p>
                      <button
                        type="button"
                        className="add-first-stock-btn"
                        onClick={() => setShowAddStock(true)}
                      >
                        添加第一支股票
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* 活躍預警 */}
              <div className="content-section">
                <div className="section-header">
                  <h4>活躍預警</h4>
                  <button
                    type="button"
                    className="create-alert-btn"
                    onClick={() => setShowCreateAlert(true)}
                  >
                    + 創建預警
                  </button>
                </div>
                <div className="active-alerts">
                  {alerts.filter(alert => alert.isActive).slice(0, 3).map((alert) => (
                    <div key={alert.id} className="alert-preview-item">
                      <div className="alert-info">
                        <div className="alert-symbol">{alert.symbol}</div>
                        <div className="alert-message">{alert.message}</div>
                      </div>
                      <div className="alert-condition">
                        {alert.type === 'price_above' && `> $${alert.condition}`}
                        {alert.type === 'price_below' && `< $${alert.condition}`}
                        {alert.type === 'change_percent' && `${formatPercent(alert.condition)}`}
                        {alert.type === 'volume_spike' && `成交量 > ${formatNumber(alert.condition)}`}
                      </div>
                    </div>
                  ))}
                  {alerts.filter(alert => alert.isActive).length === 0 && (
                    <div className="empty-alerts">
                      <p>沒有活躍的預警</p>
                      <button
                        type="button"
                        className="create-first-alert-btn"
                        onClick={() => setShowCreateAlert(true)}
                      >
                        創建第一個預警
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* 最新市場事件 */}
              <div className="content-section">
                <h4>最新市場事件</h4>
                <div className="recent-events">
                  {marketEvents.slice(0, 5).map((event) => (
                    <div key={event.id} className="event-preview-item">
                      <div 
                        className="event-impact"
                        style={{ backgroundColor: getImpactColor(event.impact) }}
                      >
                        {event.impact.toUpperCase()}
                      </div>
                      <div className="event-content">
                        <div className="event-title">{event.title}</div>
                        <div className="event-time">{formatTime(event.eventTime)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {viewMode === 'watchlist' && (
            <div className="watchlist-content">
              <div className="content-header">
                <h4>關注列表 ({watchlist.length})</h4>
                <button
                  type="button"
                  className="add-stock-btn"
                  onClick={() => setShowAddStock(true)}
                >
                  + 添加股票
                </button>
              </div>
              
              <div className="watchlist-table">
                <div className="table-header">
                  <div className="col-stock">股票</div>
                  <div className="col-price">價格</div>
                  <div className="col-change">漲跌</div>
                  <div className="col-volume">成交量</div>
                  <div className="col-range">區間</div>
                  <div className="col-actions">操作</div>
                </div>
                
                {watchlist.map((stock) => (
                  <div key={stock.id} className="table-row">
                    <div className="col-stock">
                      <div className="stock-info">
                        <div className="stock-symbol">{stock.symbol}</div>
                        <div className="stock-name">{stock.companyName}</div>
                        <div className="stock-market">{stock.market}</div>
                      </div>
                    </div>
                    <div className="col-price">
                      <div className="current-price">${stock.currentPrice.toFixed(2)}</div>
                      <div className="previous-close">前收: ${stock.previousClose.toFixed(2)}</div>
                    </div>
                    <div className="col-change">
                      <div 
                        className="change-amount"
                        style={{ color: getChangeColor(stock.change) }}
                      >
                        {stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}
                      </div>
                      <div 
                        className="change-percent"
                        style={{ color: getChangeColor(stock.change) }}
                      >
                        {formatPercent(stock.changePercent)}
                      </div>
                    </div>
                    <div className="col-volume">
                      {formatNumber(stock.volume)}
                    </div>
                    <div className="col-range">
                      <div className="range-info">
                        <div>高: ${stock.high.toFixed(2)}</div>
                        <div>低: ${stock.low.toFixed(2)}</div>
                      </div>
                    </div>
                    <div className="col-actions">
                      <button
                        type="button"
                        className="action-btn analyze"
                        onClick={() => navigate(`/analysis?symbol=${stock.symbol}`)}
                        title="分析"
                      >
                        🔍
                      </button>
                      <button
                        type="button"
                        className="action-btn alert"
                        onClick={() => {
                          setSelectedStock(stock.symbol);
                          setShowCreateAlert(true);
                        }}
                        title="設置預警"
                      >
                        🚨
                      </button>
                      <button
                        type="button"
                        className="action-btn remove"
                        onClick={() => removeFromWatchlist(stock.id)}
                        title="移除"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
                
                {watchlist.length === 0 && (
                  <div className="empty-watchlist-table">
                    <div className="empty-icon">👁️</div>
                    <h3>關注列表為空</h3>
                    <p>添加股票到關注列表，實時監控價格變化</p>
                    <button
                      type="button"
                      className="add-first-stock-btn"
                      onClick={() => setShowAddStock(true)}
                    >
                      添加第一支股票
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}      
    {viewMode === 'alerts' && (
            <div className="alerts-content">
              <div className="content-header">
                <h4>價格預警 ({alerts.length})</h4>
                <button
                  type="button"
                  className="create-alert-btn"
                  onClick={() => setShowCreateAlert(true)}
                >
                  + 創建預警
                </button>
              </div>
              
              <div className="alerts-list">
                {alerts.map((alert) => (
                  <div key={alert.id} className="alert-item">
                    <div className="alert-main">
                      <div className="alert-header">
                        <div className="alert-symbol">{alert.symbol}</div>
                        <div className={`alert-status ${alert.isActive ? 'active' : 'inactive'}`}>
                          {alert.isActive ? '啟用' : '停用'}
                        </div>
                        {alert.triggeredAt && (
                          <div className="alert-triggered">已觸發</div>
                        )}
                      </div>
                      <div className="alert-message">{alert.message}</div>
                      <div className="alert-condition">
                        條件: {alert.type === 'price_above' && `價格高於 $${alert.condition}`}
                        {alert.type === 'price_below' && `價格低於 $${alert.condition}`}
                        {alert.type === 'change_percent' && `漲跌幅超過 ${formatPercent(alert.condition)}`}
                        {alert.type === 'volume_spike' && `成交量超過 ${formatNumber(alert.condition)}`}
                      </div>
                      <div className="alert-time">
                        創建於 {formatTime(alert.createdAt)}
                        {alert.triggeredAt && ` • 觸發於 ${formatTime(alert.triggeredAt)}`}
                      </div>
                    </div>
                    <div className="alert-actions">
                      <button
                        type="button"
                        className={`toggle-btn ${alert.isActive ? 'active' : 'inactive'}`}
                        onClick={() => toggleAlert(alert.id, !alert.isActive)}
                      >
                        {alert.isActive ? '停用' : '啟用'}
                      </button>
                      <button
                        type="button"
                        className="delete-btn"
                        onClick={() => deleteAlert(alert.id)}
                      >
                        刪除
                      </button>
                    </div>
                  </div>
                ))}
                
                {alerts.length === 0 && (
                  <div className="empty-alerts-list">
                    <div className="empty-icon">🚨</div>
                    <h3>還沒有設置預警</h3>
                    <p>創建價格預警，在重要價格變化時及時通知您</p>
                    <button
                      type="button"
                      className="create-first-alert-btn"
                      onClick={() => setShowCreateAlert(true)}
                    >
                      創建第一個預警
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {viewMode === 'events' && (
            <div className="events-content">
              <div className="content-header">
                <h4>市場事件</h4>
                <div className="event-filters">
                  <select className="filter-select">
                    <option value="all">全部事件</option>
                    <option value="earnings">財報</option>
                    <option value="dividend">股息</option>
                    <option value="news">新聞</option>
                    <option value="economic">經濟數據</option>
                  </select>
                </div>
              </div>
              
              <div className="events-list">
                {marketEvents.map((event) => (
                  <div key={event.id} className="event-item">
                    <div className="event-header">
                      <div 
                        className="event-impact-badge"
                        style={{ backgroundColor: getImpactColor(event.impact) }}
                      >
                        {event.impact.toUpperCase()}
                      </div>
                      <div className="event-type">{event.type}</div>
                      <div className="event-time">{formatTime(event.eventTime)}</div>
                    </div>
                    <div className="event-content">
                      <h5 className="event-title">{event.title}</h5>
                      <p className="event-description">{event.description}</p>
                      {event.affectedSymbols.length > 0 && (
                        <div className="affected-symbols">
                          <span className="symbols-label">相關股票:</span>
                          {event.affectedSymbols.map((symbol, index) => (
                            <span key={symbol} className="symbol-tag">
                              {symbol}
                              {index < event.affectedSymbols.length - 1 && ', '}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="event-source">來源: {event.source}</div>
                    </div>
                  </div>
                ))}
                
                {marketEvents.length === 0 && (
                  <div className="empty-events-list">
                    <div className="empty-icon">📰</div>
                    <h3>暫無市場事件</h3>
                    <p>市場事件將在這裡顯示</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 添加股票模態框 */}
      {showAddStock && (
        <div className="modal-overlay" onClick={() => setShowAddStock(false)}>
          <div className="add-stock-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加股票到關注列表</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowAddStock(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>股票代碼</label>
                <input
                  type="text"
                  value={newStockSymbol}
                  onChange={(e: any) => setNewStockSymbol(e.target.value.toUpperCase())}
                  placeholder="例如：2330, AAPL"
                  className="form-input"
                />
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn secondary"
                onClick={() => setShowAddStock(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="modal-btn primary"
                onClick={addToWatchlist}
                disabled={!newStockSymbol.trim()}
              >
                添加
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 創建預警模態框 */}
      {showCreateAlert && (
        <div className="modal-overlay" onClick={() => setShowCreateAlert(false)}>
          <div className="create-alert-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>創建價格預警</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowCreateAlert(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>股票代碼</label>
                <select
                  value={selectedStock}
                  onChange={(e: any) => setSelectedStock(e.target.value)}
                  className="form-select"
                >
                  <option value="">選擇股票</option>
                  {watchlist.map((stock) => (
                    <option key={stock.symbol} value={stock.symbol}>
                      {stock.symbol} - {stock.companyName}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>預警類型</label>
                <select
                  value={newAlert.type}
                  onChange={(e: any) => setNewAlert(prev => ({ 
                    ...prev, 
                    type: e.target.value as any 
                  }))}
                  className="form-select"
                >
                  <option value="price_above">價格高於</option>
                  <option value="price_below">價格低於</option>
                  <option value="change_percent">漲跌幅超過</option>
                  <option value="volume_spike">成交量超過</option>
                </select>
              </div>

              <div className="form-group">
                <label>
                  {newAlert.type === 'price_above' && '目標價格'}
                  {newAlert.type === 'price_below' && '目標價格'}
                  {newAlert.type === 'change_percent' && '漲跌幅 (%)'}
                  {newAlert.type === 'volume_spike' && '成交量'}
                </label>
                <input
                  type="number"
                  value={newAlert.condition || ''}
                  onChange={(e: any) => setNewAlert(prev => ({ 
                    ...prev, 
                    condition: Number(e.target.value) 
                  }))}
                  placeholder="輸入數值"
                  className="form-input"
                  step={newAlert.type.includes('price') ? '0.01' : '1'}
                />
              </div>

              <div className="form-group">
                <label>預警訊息</label>
                <input
                  type="text"
                  value={newAlert.message}
                  onChange={(e: any) => setNewAlert(prev => ({ 
                    ...prev, 
                    message: e.target.value 
                  }))}
                  placeholder="例如：台積電突破關鍵阻力位"
                  className="form-input"
                />
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn secondary"
                onClick={() => setShowCreateAlert(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="modal-btn primary"
                onClick={createAlert}
                disabled={!selectedStock || !newAlert.condition || !newAlert.message.trim()}
              >
                創建預警
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketMonitorPage;