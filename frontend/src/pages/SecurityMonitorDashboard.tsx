import React, { useState, useEffect } from 'react';
import './SecurityMonitorDashboard.css';
import { authService } from '../services/AuthService';

// 告警級別定義
interface SecurityAlert {
  id: string;
  level: 'info' | 'warning' | 'critical' | 'emergency';
  threat_type: string;
  title: string;
  description: string;
  source_ip: string;
  user_id?: string;
  timestamp: string;
  acknowledged: boolean;
  metadata?: Record<string, any>;
}

// 安全統計數據
interface SecurityStats {
  active_alerts_count: number;
  recent_alerts_count: number;
  blocked_ips_count: number;
  failed_login_ips: number;
  suspicious_activity_types: number;
  alerts_by_level: Record<string, number>;
  alerts_by_type: Record<string, number>;
  top_threat_ips: Array<{
    ip: string;
    threat_count: number;
    blocked: boolean;
  }>;
  security_score: number;
  system_status: 'normal' | 'elevated' | 'critical';
}

const SecurityMonitorDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [blockedIps, setBlockedIps] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);

  // 獲取安全告警
  const fetchAlerts = async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/security/alerts?limit=100');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts);
      } else {
        throw new Error('載入告警失敗');
      }
    } catch (error) {
      console.error('獲取告警失敗:', error);
      setError('載入安全告警失敗');
    }
  };

  // 獲取安全統計
  const fetchStats = async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/security/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        throw new Error('載入統計失敗');
      }
    } catch (error) {
      console.error('獲取統計失敗:', error);
      setError('載入安全統計失敗');
    }
  };

  // 獲取封鎖IP列表
  const fetchBlockedIps = async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/security/blocked-ips');
      if (response.ok) {
        const data = await response.json();
        setBlockedIps(data.blocked_ips);
      } else {
        throw new Error('載入封鎖IP失敗');
      }
    } catch (error) {
      console.error('獲取封鎖IP失敗:', error);
      setError('載入封鎖IP列表失敗');
    }
  };

  // 確認告警
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await authService.authenticatedRequest(
        `/admin/security/alerts/${alertId}/acknowledge`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        // 更新本地狀態
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, acknowledged: true }
            : alert
        ));
        setSelectedAlert(null);
      } else {
        throw new Error('確認告警失敗');
      }
    } catch (error) {
      console.error('確認告警失敗:', error);
      alert('確認告警失敗');
    }
  };

  // 解除IP封鎖
  const unblockIp = async (ip: string) => {
    try {
      const response = await authService.authenticatedRequest(
        `/admin/security/blocked-ips/${ip}/unblock`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        setBlockedIps(prev => prev.filter(blockedIp => blockedIp !== ip));
        alert(`IP ${ip} 已解除封鎖`);
      } else {
        throw new Error('解除封鎖失敗');
      }
    } catch (error) {
      console.error('解除封鎖失敗:', error);
      alert('解除IP封鎖失敗');
    }
  };

  // 創建測試告警
  const createTestAlert = async () => {
    try {
      const response = await authService.authenticatedRequest(
        '/admin/security/test-alert',
        { method: 'POST' }
      );
      
      if (response.ok) {
        alert('測試告警已創建');
        fetchAlerts(); // 重新載入告警
      } else {
        throw new Error('創建測試告警失敗');
      }
    } catch (error) {
      console.error('創建測試告警失敗:', error);
      alert('創建測試告警失敗');
    }
  };

  // 初始化和自動刷新
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([fetchAlerts(), fetchStats(), fetchBlockedIps()]);
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // 自動刷新
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAlerts();
        fetchStats();
        fetchBlockedIps();
      }, 30000); // 30秒刷新一次

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // 獲取告警級別的樣式類
  const getAlertLevelClass = (level: string) => {
    const classes = {
      info: 'alert-info',
      warning: 'alert-warning',
      critical: 'alert-critical',
      emergency: 'alert-emergency'
    };
    return classes[level as keyof typeof classes] || 'alert-info';
  };

  // 獲取系統狀態顯示
  const getSystemStatusDisplay = (status: string) => {
    const displays = {
      normal: { text: '正常', class: 'status-normal', icon: '✅' },
      elevated: { text: '警戒', class: 'status-elevated', icon: '⚠️' },
      critical: { text: '危險', class: 'status-critical', icon: '🚨' }
    };
    return displays[status as keyof typeof displays] || displays.normal;
  };

  // 格式化時間
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-TW');
  };

  if (loading) {
    return (
      <div className="security-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>載入安全監控數據...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="security-dashboard">
        <div className="error-container">
          <h3>❌ 載入失敗</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>重新載入</button>
        </div>
      </div>
    );
  }

  const statusDisplay = stats ? getSystemStatusDisplay(stats.system_status) : null;

  return (
    <div className="security-dashboard">
      <div className="dashboard-header">
        <h2>🔒 安全監控儀表板</h2>
        <div className="header-controls">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e: any) => setAutoRefresh(e.target.checked)}
            />
            自動刷新 (30秒)
          </label>
          <button 
            className="test-alert-btn"
            onClick={createTestAlert}
            title="創建測試告警"
          >
            🧪 測試告警
          </button>
        </div>
      </div>

      {/* 系統狀態概覽 */}
      {stats && (
        <div className="status-overview">
          <div className="status-card system-status">
            <h3>系統狀態</h3>
            <div className={`status-indicator ${statusDisplay?.class}`}>
              <span className="status-icon">{statusDisplay?.icon}</span>
              <span className="status-text">{statusDisplay?.text}</span>
            </div>
            <div className="security-score">
              安全評分: <span className="score">{stats.security_score}/100</span>
            </div>
          </div>

          <div className="status-card">
            <h3>📊 告警統計</h3>
            <div className="stat-grid">
              <div className="stat-item">
                <span className="stat-label">活躍告警:</span>
                <span className="stat-value">{stats.active_alerts_count}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">近期告警:</span>
                <span className="stat-value">{stats.recent_alerts_count}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">封鎖IP:</span>
                <span className="stat-value">{stats.blocked_ips_count}</span>
              </div>
            </div>
          </div>

          <div className="status-card">
            <h3>⚠️ 告警級別分佈</h3>
            <div className="alert-level-chart">
              {Object.entries(stats.alerts_by_level).map(([level, count]) => (
                <div key={level} className={`level-bar ${getAlertLevelClass(level)}`}>
                  <span className="level-name">{level}</span>
                  <span className="level-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-content">
        {/* 安全告警列表 */}
        <div className="section alerts-section">
          <div className="section-header">
            <h3>🚨 安全告警 ({alerts.length})</h3>
            <div className="section-filters">
              <select onChange={(e: any) => {
                // 實施告警級別篩選邏輯
              }}>
                <option value="">所有級別</option>
                <option value="critical">嚴重</option>
                <option value="warning">警告</option>
                <option value="info">資訊</option>
              </select>
            </div>
          </div>

          <div className="alerts-container">
            {alerts.length === 0 ? (
              <div className="no-alerts">
                <p>✅ 目前沒有安全告警</p>
              </div>
            ) : (
              <div className="alerts-list">
                {alerts.map((alert) => (
                  <div 
                    key={alert.id} 
                    className={`alert-card ${getAlertLevelClass(alert.level)} ${alert.acknowledged ? 'acknowledged' : ''}`}
                    onClick={() => setSelectedAlert(alert)}
                  >
                    <div className="alert-header">
                      <span className="alert-level">{alert.level.toUpperCase()}</span>
                      <span className="alert-time">{formatTime(alert.timestamp)}</span>
                      {alert.acknowledged && <span className="acknowledged-badge">已確認</span>}
                    </div>
                    <div className="alert-title">{alert.title}</div>
                    <div className="alert-description">{alert.description}</div>
                    <div className="alert-meta">
                      <span>來源IP: {alert.source_ip}</span>
                      {alert.user_id && <span>用戶ID: {alert.user_id}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 封鎖IP管理 */}
        <div className="section blocked-ips-section">
          <h3>🔒 封鎖IP管理 ({blockedIps.length})</h3>
          
          {blockedIps.length === 0 ? (
            <div className="no-blocked-ips">
              <p>✅ 目前沒有被封鎖的IP</p>
            </div>
          ) : (
            <div className="blocked-ips-list">
              {blockedIps.map((ip) => (
                <div key={ip} className="blocked-ip-card">
                  <div className="ip-info">
                    <span className="ip-address">{ip}</span>
                    <span className="ip-status">🔒 已封鎖</span>
                  </div>
                  <button
                    className="unblock-btn"
                    onClick={() => unblockIp(ip)}
                    title={`解除 ${ip} 的封鎖`}
                  >
                    🔓 解除封鎖
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 威脅IP排行 */}
        {stats && stats.top_threat_ips.length > 0 && (
          <div className="section threat-ips-section">
            <h3>🎯 威脅IP排行</h3>
            <div className="threat-ips-list">
              {stats.top_threat_ips.map((threatIp, index) => (
                <div key={threatIp.ip} className="threat-ip-card">
                  <div className="rank">#{index + 1}</div>
                  <div className="ip-info">
                    <div className="ip-address">{threatIp.ip}</div>
                    <div className="threat-count">威脅次數: {threatIp.threat_count}</div>
                  </div>
                  <div className="ip-status">
                    {threatIp.blocked ? (
                      <span className="blocked">🔒 已封鎖</span>
                    ) : (
                      <span className="active">⚠️ 活躍</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 告警詳情模態框 */}
      {selectedAlert && (
        <div className="modal-overlay" onClick={() => setSelectedAlert(null)}>
          <div className="alert-modal" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>告警詳情</h3>
              <button className="close-btn" onClick={() => setSelectedAlert(null)}>×</button>
            </div>
            <div className="modal-content">
              <div className="alert-detail">
                <div className="detail-row">
                  <label>告警ID:</label>
                  <span>{selectedAlert.id}</span>
                </div>
                <div className="detail-row">
                  <label>級別:</label>
                  <span className={getAlertLevelClass(selectedAlert.level)}>
                    {selectedAlert.level.toUpperCase()}
                  </span>
                </div>
                <div className="detail-row">
                  <label>威脅類型:</label>
                  <span>{selectedAlert.threat_type}</span>
                </div>
                <div className="detail-row">
                  <label>標題:</label>
                  <span>{selectedAlert.title}</span>
                </div>
                <div className="detail-row">
                  <label>描述:</label>
                  <span>{selectedAlert.description}</span>
                </div>
                <div className="detail-row">
                  <label>來源IP:</label>
                  <span>{selectedAlert.source_ip}</span>
                </div>
                {selectedAlert.user_id && (
                  <div className="detail-row">
                    <label>用戶ID:</label>
                    <span>{selectedAlert.user_id}</span>
                  </div>
                )}
                <div className="detail-row">
                  <label>時間:</label>
                  <span>{formatTime(selectedAlert.timestamp)}</span>
                </div>
                {selectedAlert.metadata && Object.keys(selectedAlert.metadata).length > 0 && (
                  <div className="detail-row">
                    <label>詳細資訊:</label>
                    <pre className="metadata">
                      {JSON.stringify(selectedAlert.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-actions">
              {!selectedAlert.acknowledged && (
                <button 
                  className="acknowledge-btn"
                  onClick={() => acknowledgeAlert(selectedAlert.id)}
                >
                  ✅ 確認告警
                </button>
              )}
              <button 
                className="close-modal-btn"
                onClick={() => setSelectedAlert(null)}
              >
                關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityMonitorDashboard;