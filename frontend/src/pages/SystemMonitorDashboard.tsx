#!/usr/bin/env tsx
/**
 * 系統監控儀表板組件 (System Monitor Dashboard)
 * 天工 (TianGong) - 實時系統監控可視化界面
 * 
 * 功能特色：
 * 1. 實時系統指標監控 (CPU、記憶體、磁碟)
 * 2. 應用性能監控 (請求響應時間、錯誤率)
 * 3. 告警系統集成和管理
 * 4. 互動式圖表和儀表板
 * 5. 自動刷新和歷史數據查看
 * 6. 專業級Taiwan市場系統監控
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { authService } from '../services/AuthService';
import './SystemMonitorDashboard.css';

// 數據介面定義
interface SystemMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_usage_percent: number;
  network_io: {
    bytes_sent: number;
    bytes_recv: number;
  };
  process_count: number;
  uptime_seconds: number;
}

interface ApplicationMetrics {
  timestamp: string;
  requests_per_second: number;
  average_response_time: number;
  error_rate: number;
  active_sessions: number;
  database_connections: number;
  cache_hit_rate: number;
}

interface AlertItem {
  id: string;
  level: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  timestamp: string;
  acknowledged: boolean;
  source: string;
}

interface MonitoringConfig {
  refresh_interval: number;
  alert_thresholds: {
    cpu_warning: number;
    cpu_critical: number;
    memory_warning: number;
    memory_critical: number;
    response_time_warning: number;
    response_time_critical: number;
  };
  auto_refresh: boolean;
}

const SystemMonitorDashboard: React.FC = () => {
  // 狀態管理
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [applicationMetrics, setApplicationMetrics] = useState<ApplicationMetrics | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [config, setConfig] = useState<MonitoringConfig>({
    refresh_interval: 5000, // 5秒
    alert_thresholds: {
      cpu_warning: 70,
      cpu_critical: 90,
      memory_warning: 80,
      memory_critical: 95,
      response_time_warning: 2000,
      response_time_critical: 5000
    },
    auto_refresh: true
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [historicalData, setHistoricalData] = useState<{
    cpu: number[];
    memory: number[];
    responseTime: number[];
    timestamps: string[];
  }>({
    cpu: [],
    memory: [],
    responseTime: [],
    timestamps: []
  });

  // Refs
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const chartRef = useRef<HTMLCanvasElement | null>(null);

  // 獲取系統指標
  const fetchSystemMetrics = useCallback(async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/system/metrics/system');
      if (response && response.ok) {
        const data = await response.json();
        setSystemMetrics(data);
        
        // 更新歷史數據
        setHistoricalData(prev => {
          const newData = {
            cpu: [...prev.cpu.slice(-19), data.cpu_percent],
            memory: [...prev.memory.slice(-19), data.memory_percent],
            responseTime: [...prev.responseTime.slice(-19), data.average_response_time || 0],
            timestamps: [...prev.timestamps.slice(-19), new Date().toLocaleTimeString()]
          };
          return newData;
        });
      }
    } catch (err) {
      console.error('獲取系統指標失敗:', err);
      setError('獲取系統指標失敗');
    }
  }, []);

  // 獲取應用指標
  const fetchApplicationMetrics = useCallback(async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/system/metrics/application');
      if (response && response.ok) {
        const data = await response.json();
        setApplicationMetrics(data);
      }
    } catch (err) {
      console.error('獲取應用指標失敗:', err);
    }
  }, []);

  // 獲取告警列表
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/system/alerts');
      if (response && response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (err) {
      console.error('獲取告警列表失敗:', err);
    }
  }, []);

  // 確認告警
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await authService.authenticatedRequest(`/admin/system/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
      
      if (response && response.ok) {
        setAlerts(prev => 
          prev.map(alert => 
            alert.id === alertId 
              ? { ...alert, acknowledged: true }
              : alert
          )
        );
      }
    } catch (err) {
      console.error('確認告警失敗:', err);
    }
  };

  // 獲取所有數據
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemMetrics(),
        fetchApplicationMetrics(),
        fetchAlerts()
      ]);
      setLastUpdate(new Date());
      setError('');
    } catch (err) {
      console.error('獲取監控數據失敗:', err);
      setError('獲取監控數據失敗');
    } finally {
      setLoading(false);
    }
  }, [fetchSystemMetrics, fetchApplicationMetrics, fetchAlerts]);

  // 判斷指標狀態
  const getMetricStatus = (value: number, warning: number, critical: number) => {
    if (value >= critical) return 'critical';
    if (value >= warning) return 'warning';
    return 'healthy';
  };

  // 格式化正常運行時間
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}天 ${hours}小時 ${minutes}分鐘`;
    } else if (hours > 0) {
      return `${hours}小時 ${minutes}分鐘`;
    } else {
      return `${minutes}分鐘`;
    }
  };

  // 格式化數據大小
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 組件初始化和定時器設置
  useEffect(() => {
    fetchAllData();

    if (config.auto_refresh) {
      intervalRef.current = setInterval(fetchAllData, config.refresh_interval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchAllData, config.auto_refresh, config.refresh_interval]);

  // 手動刷新
  const handleManualRefresh = () => {
    fetchAllData();
  };

  // 切換自動刷新
  const toggleAutoRefresh = () => {
    setConfig(prev => ({
      ...prev,
      auto_refresh: !prev.auto_refresh
    }));
  };

  if (loading && !systemMetrics) {
    return (
      <div className="system-monitor-dashboard loading">
        <div className="loading-container">
          <div className="loading-spinner large"></div>
          <p>載入系統監控數據...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="system-monitor-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>🖥️ 系統監控儀表板</h1>
          <p className="last-update">
            最後更新: {lastUpdate.toLocaleString()}
          </p>
        </div>
        <div className="header-right">
          <button 
            className="auto-refresh-toggle"
            onClick={toggleAutoRefresh}
            data-active={config.auto_refresh}
          >
            {config.auto_refresh ? '🔄 自動刷新' : '⏸️ 手動模式'}
          </button>
          <button 
            className="refresh-button"
            onClick={handleManualRefresh}
            disabled={loading}
          >
            {loading ? '🔄' : '↻'} 刷新
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* 主要指標卡片 */}
      <div className="metrics-overview">
        <div className="metric-cards-grid">
          {/* CPU 使用率 */}
          <div className={`metric-card ${systemMetrics ? getMetricStatus(
            systemMetrics.cpu_percent, 
            config.alert_thresholds.cpu_warning, 
            config.alert_thresholds.cpu_critical
          ) : ''}`}>
            <div className="metric-header">
              <span className="metric-icon">🔥</span>
              <h3>CPU 使用率</h3>
            </div>
            <div className="metric-value">
              {systemMetrics?.cpu_percent?.toFixed(1) || '--'}%
            </div>
            <div className="metric-bar">
              <div 
                className="metric-bar-fill"
                style={{ width: `${systemMetrics?.cpu_percent || 0}%` }}
              ></div>
            </div>
          </div>

          {/* 記憶體使用率 */}
          <div className={`metric-card ${systemMetrics ? getMetricStatus(
            systemMetrics.memory_percent, 
            config.alert_thresholds.memory_warning, 
            config.alert_thresholds.memory_critical
          ) : ''}`}>
            <div className="metric-header">
              <span className="metric-icon">💾</span>
              <h3>記憶體使用率</h3>
            </div>
            <div className="metric-value">
              {systemMetrics?.memory_percent?.toFixed(1) || '--'}%
            </div>
            <div className="metric-bar">
              <div 
                className="metric-bar-fill"
                style={{ width: `${systemMetrics?.memory_percent || 0}%` }}
              ></div>
            </div>
          </div>

          {/* 磁碟使用率 */}
          <div className={`metric-card ${systemMetrics ? getMetricStatus(
            systemMetrics.disk_usage_percent || 0, 
            80, 
            95
          ) : ''}`}>
            <div className="metric-header">
              <span className="metric-icon">💽</span>
              <h3>磁碟使用率</h3>
            </div>
            <div className="metric-value">
              {systemMetrics?.disk_usage_percent?.toFixed(1) || '--'}%
            </div>
            <div className="metric-bar">
              <div 
                className="metric-bar-fill"
                style={{ width: `${systemMetrics?.disk_usage_percent || 0}%` }}
              ></div>
            </div>
          </div>

          {/* 活躍會話 */}
          <div className="metric-card healthy">
            <div className="metric-header">
              <span className="metric-icon">👥</span>
              <h3>活躍會話</h3>
            </div>
            <div className="metric-value">
              {applicationMetrics?.active_sessions || 0}
            </div>
            <div className="metric-trend">
              <span>連接數</span>
            </div>
          </div>

          {/* 系統正常運行時間 */}
          <div className="metric-card healthy">
            <div className="metric-header">
              <span className="metric-icon">⏱️</span>
              <h3>正常運行時間</h3>
            </div>
            <div className="metric-value small">
              {systemMetrics?.uptime_seconds 
                ? formatUptime(systemMetrics.uptime_seconds) 
                : '--'
              }
            </div>
          </div>

          {/* 響應時間 */}
          <div className={`metric-card ${applicationMetrics ? getMetricStatus(
            applicationMetrics.average_response_time || 0,
            config.alert_thresholds.response_time_warning,
            config.alert_thresholds.response_time_critical
          ) : ''}`}>
            <div className="metric-header">
              <span className="metric-icon">⚡</span>
              <h3>平均響應時間</h3>
            </div>
            <div className="metric-value">
              {applicationMetrics?.average_response_time?.toFixed(0) || '--'}ms
            </div>
          </div>
        </div>
      </div>

      {/* 應用性能指標 */}
      <div className="performance-section">
        <h2>📊 應用性能指標</h2>
        <div className="performance-grid">
          <div className="performance-card">
            <h3>🚀 請求處理</h3>
            <div className="performance-stats">
              <div className="stat-item">
                <span className="stat-label">每秒請求數</span>
                <span className="stat-value">
                  {applicationMetrics?.requests_per_second?.toFixed(1) || '0.0'} RPS
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">錯誤率</span>
                <span className="stat-value error">
                  {applicationMetrics?.error_rate?.toFixed(2) || '0.00'}%
                </span>
              </div>
            </div>
          </div>

          <div className="performance-card">
            <h3>🗄️ 數據庫</h3>
            <div className="performance-stats">
              <div className="stat-item">
                <span className="stat-label">活躍連接</span>
                <span className="stat-value">
                  {applicationMetrics?.database_connections || 0}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">緩存命中率</span>
                <span className="stat-value success">
                  {applicationMetrics?.cache_hit_rate?.toFixed(1) || '--'}%
                </span>
              </div>
            </div>
          </div>

          <div className="performance-card">
            <h3>🌐 網路I/O</h3>
            <div className="performance-stats">
              <div className="stat-item">
                <span className="stat-label">發送流量</span>
                <span className="stat-value">
                  {systemMetrics?.network_io ? formatBytes(systemMetrics.network_io.bytes_sent) : '--'}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">接收流量</span>
                <span className="stat-value">
                  {systemMetrics?.network_io ? formatBytes(systemMetrics.network_io.bytes_recv) : '--'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 告警系統 */}
      <div className="alerts-section">
        <h2>🚨 系統告警</h2>
        <div className="alerts-container">
          {alerts.length === 0 ? (
            <div className="no-alerts">
              <span className="alert-icon">✅</span>
              <p>目前沒有活躍的告警</p>
            </div>
          ) : (
            <div className="alerts-list">
              {alerts.map(alert => (
                <div 
                  key={alert.id}
                  className={`alert-item ${alert.level} ${alert.acknowledged ? 'acknowledged' : ''}`}
                >
                  <div className="alert-header">
                    <span className={`alert-level-icon ${alert.level}`}>
                      {alert.level === 'critical' ? '🔴' : 
                       alert.level === 'warning' ? '🟡' : '🔵'}
                    </span>
                    <h4>{alert.title}</h4>
                    <span className="alert-source">{alert.source}</span>
                  </div>
                  <p className="alert-description">{alert.description}</p>
                  <div className="alert-footer">
                    <span className="alert-timestamp">
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                    {!alert.acknowledged && (
                      <button 
                        className="acknowledge-button"
                        onClick={() => acknowledgeAlert(alert.id)}
                      >
                        確認
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 歷史趨勢圖 */}
      <div className="trends-section">
        <h2>📈 歷史趨勢</h2>
        <div className="trends-container">
          <div className="trend-chart">
            <h3>CPU & 記憶體使用率趨勢</h3>
            <div className="simple-chart">
              {historicalData.cpu.map((value, index) => (
                <div key={index} className="chart-bar">
                  <div 
                    className="chart-bar-cpu"
                    style={{ height: `${value}%` }}
                    title={`CPU: ${value.toFixed(1)}%`}
                  ></div>
                  <div 
                    className="chart-bar-memory"
                    style={{ height: `${historicalData.memory[index]}%` }}
                    title={`記憶體: ${historicalData.memory[index]?.toFixed(1)}%`}
                  ></div>
                </div>
              ))}
            </div>
            <div className="chart-legend">
              <span className="legend-item">
                <span className="legend-color cpu"></span> CPU
              </span>
              <span className="legend-item">
                <span className="legend-color memory"></span> 記憶體
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMonitorDashboard;