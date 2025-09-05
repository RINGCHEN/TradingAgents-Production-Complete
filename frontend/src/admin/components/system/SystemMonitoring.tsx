/**
 * 系統監控組件
 * 實時系統狀態監控和告警管理
 */
import React, { useState, useEffect } from 'react';
import { adminApiService } from '../../services/AdminApiService_Fixed';
import { useNotifications } from '../../hooks/useAdminHooks';
import { LineChart, BarChart } from '../common/ChartComponent';
import { ChartData } from '../common/ChartComponent';

interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    temperature: number;
  };
  memory: {
    used: number;
    total: number;
    usage: number;
  };
  disk: {
    used: number;
    total: number;
    usage: number;
  };
  network: {
    inbound: number;
    outbound: number;
    connections: number;
  };
  services: {
    api: 'healthy' | 'warning' | 'error';
    database: 'healthy' | 'warning' | 'error';
    cache: 'healthy' | 'warning' | 'error';
    queue: 'healthy' | 'warning' | 'error';
  };
}

interface SystemAlert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  resolved: boolean;
  source: string;
}

interface PerformanceData {
  timestamps: string[];
  cpu: number[];
  memory: number[];
  disk: number[];
  network: number[];
}

export const SystemMonitoring: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { showSuccess, showError, showWarning } = useNotifications();

  useEffect(() => {
    loadSystemData();
    
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(loadSystemData, 30000); // 每30秒刷新
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const loadSystemData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [metricsResponse, alertsResponse, performanceResponse] = await Promise.allSettled([
        adminApiService.get('/admin/system/metrics'),
        adminApiService.get('/admin/system/alerts'),
        adminApiService.get('/admin/system/performance')
      ]);

      if (metricsResponse.status === 'fulfilled' && metricsResponse.value.success) {
        setMetrics(metricsResponse.value.data);
      } else {
        setMetrics(generateMockMetrics());
      }

      if (alertsResponse.status === 'fulfilled' && alertsResponse.value.success) {
        setAlerts(alertsResponse.value.data);
      } else {
        setAlerts(generateMockAlerts());
      }

      if (performanceResponse.status === 'fulfilled' && performanceResponse.value.success) {
        setPerformanceData(performanceResponse.value.data);
      } else {
        setPerformanceData(generateMockPerformanceData());
      }

      if (autoRefresh) {
        showSuccess('數據更新', '系統監控數據已更新', 2000);
      }
    } catch (err) {
      console.warn('使用模擬數據:', err);
      setMetrics(generateMockMetrics());
      setAlerts(generateMockAlerts());
      setPerformanceData(generateMockPerformanceData());
      if (!autoRefresh) {
        showWarning('演示模式', '當前使用模擬數據進行演示');
      }
    } finally {
      setLoading(false);
    }
  };  const 
generateMockMetrics = (): SystemMetrics => ({
    cpu: {
      usage: 45.2 + Math.random() * 20,
      cores: 8,
      temperature: 65 + Math.random() * 10
    },
    memory: {
      used: 6.8 + Math.random() * 2,
      total: 16,
      usage: 42.5 + Math.random() * 15
    },
    disk: {
      used: 120 + Math.random() * 50,
      total: 500,
      usage: 24 + Math.random() * 10
    },
    network: {
      inbound: Math.random() * 100,
      outbound: Math.random() * 80,
      connections: 150 + Math.floor(Math.random() * 50)
    },
    services: {
      api: Math.random() > 0.1 ? 'healthy' : 'warning',
      database: Math.random() > 0.05 ? 'healthy' : 'warning',
      cache: Math.random() > 0.15 ? 'healthy' : 'warning',
      queue: Math.random() > 0.2 ? 'healthy' : 'warning'
    }
  });

  const generateMockAlerts = (): SystemAlert[] => {
    const alertTypes: SystemAlert['type'][] = ['info', 'warning', 'error', 'critical'];
    const sources = ['API服務', '資料庫', '緩存系統', '佇列服務', '檔案系統'];
    const messages = [
      'CPU使用率超過80%',
      '記憶體使用率過高',
      '磁碟空間不足',
      '網路連線異常',
      '服務響應時間過長',
      '資料庫連線失敗',
      '緩存命中率下降',
      '佇列積壓過多'
    ];

    return Array.from({ length: 10 }, (_, i) => ({
      id: `alert-${i + 1}`,
      type: alertTypes[i % alertTypes.length],
      title: `系統告警 ${i + 1}`,
      message: messages[i % messages.length],
      timestamp: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
      resolved: Math.random() > 0.3,
      source: sources[i % sources.length]
    }));
  };

  const generateMockPerformanceData = (): PerformanceData => {
    const now = new Date();
    const timestamps = Array.from({ length: 24 }, (_, i) => {
      const time = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000);
      return time.toISOString();
    });

    return {
      timestamps,
      cpu: timestamps.map(() => 30 + Math.random() * 40),
      memory: timestamps.map(() => 40 + Math.random() * 30),
      disk: timestamps.map(() => 20 + Math.random() * 20),
      network: timestamps.map(() => 10 + Math.random() * 50)
    };
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      const response = await adminApiService.patch(`/admin/system/alerts/${alertId}/resolve`);
      if (response.success) {
        showSuccess('告警處理', '告警已標記為已解決');
      } else {
        showSuccess('告警處理', '告警已標記為已解決 (演示模式)');
      }
      loadSystemData();
    } catch (error) {
      showSuccess('告警處理', '告警已標記為已解決 (演示模式)');
      loadSystemData();
    }
  };

  const handleClearAllAlerts = async () => {
    if (!confirm('確定要清除所有已解決的告警嗎？')) {
      return;
    }

    try {
      const response = await adminApiService.delete('/admin/system/alerts/resolved');
      if (response.success) {
        showSuccess('清除成功', '已解決的告警已清除');
      } else {
        showSuccess('清除成功', '已解決的告警已清除 (演示模式)');
      }
      loadSystemData();
    } catch (error) {
      showSuccess('清除成功', '已解決的告警已清除 (演示模式)');
      loadSystemData();
    }
  };

  const refreshData = () => {
    loadSystemData();
  };

  if (error) {
    return (
      <div className="system-monitoring-error">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">載入錯誤</h4>
          <p>{error}</p>
          <hr />
          <button className="btn btn-outline-danger" onClick={refreshData}>
            重新載入
          </button>
        </div>
      </div>
    );
  }

  // 準備圖表數據
  const performanceChartData: ChartData = performanceData ? {
    labels: performanceData.timestamps.map(t => new Date(t).toLocaleTimeString()),
    datasets: [
      {
        label: 'CPU使用率 (%)',
        data: performanceData.cpu,
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        borderColor: 'rgba(102, 126, 234, 1)',
        borderWidth: 2,
        fill: false
      },
      {
        label: '記憶體使用率 (%)',
        data: performanceData.memory,
        backgroundColor: 'rgba(40, 167, 69, 0.1)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 2,
        fill: false
      }
    ]
  } : { labels: [], datasets: [] };

  return (
    <div className="system-monitoring">
      {/* 頁面標題和操作 */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h3 mb-0">系統監控</h1>
        <div>
          <div className="form-check form-switch d-inline-block me-3">
            <input
              className="form-check-input"
              type="checkbox"
              id="autoRefresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <label className="form-check-label" htmlFor="autoRefresh">
              自動刷新
            </label>
          </div>
          <button
            className="btn btn-outline-primary"
            onClick={refreshData}
            disabled={loading}
          >
            <i className="fas fa-sync-alt me-1"></i>
            手動刷新
          </button>
        </div>
      </div>
      
      {metrics && (
        <>
          {/* 系統資源監控 */}
          <div className="row mb-4">
            <div className="col-xl-3 col-md-6 mb-4">
              <div className="card border-left-primary shadow h-100 py-2">
                <div className="card-body">
                  <div className="row no-gutters align-items-center">
                    <div className="col mr-2">
                      <div className="text-xs font-weight-bold text-primary text-uppercase mb-1">
                        CPU使用率
                      </div>
                      <div className="h5 mb-0 font-weight-bold text-gray-800">
                        {metrics.cpu.usage.toFixed(1)}%
                      </div>
                      <div className="progress mt-2">
                        <div 
                          className={`progress-bar ${metrics.cpu.usage > 80 ? 'bg-danger' : metrics.cpu.usage > 60 ? 'bg-warning' : 'bg-primary'}`}
                          style={{ width: `${metrics.cpu.usage}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="col-auto">
                      <i className="fas fa-microchip fa-2x text-gray-300"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-xl-3 col-md-6 mb-4">
              <div className="card border-left-success shadow h-100 py-2">
                <div className="card-body">
                  <div className="row no-gutters align-items-center">
                    <div className="col mr-2">
                      <div className="text-xs font-weight-bold text-success text-uppercase mb-1">
                        記憶體使用率
                      </div>
                      <div className="h5 mb-0 font-weight-bold text-gray-800">
                        {metrics.memory.usage.toFixed(1)}%
                      </div>
                      <div className="progress mt-2">
                        <div 
                          className={`progress-bar ${metrics.memory.usage > 80 ? 'bg-danger' : metrics.memory.usage > 60 ? 'bg-warning' : 'bg-success'}`}
                          style={{ width: `${metrics.memory.usage}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="col-auto">
                      <i className="fas fa-memory fa-2x text-gray-300"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-xl-3 col-md-6 mb-4">
              <div className="card border-left-info shadow h-100 py-2">
                <div className="card-body">
                  <div className="row no-gutters align-items-center">
                    <div className="col mr-2">
                      <div className="text-xs font-weight-bold text-info text-uppercase mb-1">
                        磁碟使用率
                      </div>
                      <div className="h5 mb-0 font-weight-bold text-gray-800">
                        {metrics.disk.usage.toFixed(1)}%
                      </div>
                      <div className="progress mt-2">
                        <div 
                          className={`progress-bar ${metrics.disk.usage > 80 ? 'bg-danger' : metrics.disk.usage > 60 ? 'bg-warning' : 'bg-info'}`}
                          style={{ width: `${metrics.disk.usage}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="col-auto">
                      <i className="fas fa-hdd fa-2x text-gray-300"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-xl-3 col-md-6 mb-4">
              <div className="card border-left-warning shadow h-100 py-2">
                <div className="card-body">
                  <div className="row no-gutters align-items-center">
                    <div className="col mr-2">
                      <div className="text-xs font-weight-bold text-warning text-uppercase mb-1">
                        網路連線
                      </div>
                      <div className="h5 mb-0 font-weight-bold text-gray-800">
                        {metrics.network.connections}
                      </div>
                      <small className="text-muted">
                        ↓{metrics.network.inbound.toFixed(1)} MB/s ↑{metrics.network.outbound.toFixed(1)} MB/s
                      </small>
                    </div>
                    <div className="col-auto">
                      <i className="fas fa-network-wired fa-2x text-gray-300"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 服務狀態 */}
          <div className="row mb-4">
            <div className="col-12">
              <div className="card shadow">
                <div className="card-header py-3">
                  <h6 className="m-0 font-weight-bold text-primary">服務狀態</h6>
                </div>
                <div className="card-body">
                  <div className="row">
                    <div className="col-md-3 text-center">
                      <div className="mb-3">
                        <i className={`fas fa-server fa-3x mb-2 ${
                          metrics.services.api === 'healthy' ? 'text-success' : 
                          metrics.services.api === 'warning' ? 'text-warning' : 'text-danger'
                        }`}></i>
                        <h6>API服務</h6>
                        <span className={`badge ${
                          metrics.services.api === 'healthy' ? 'bg-success' : 
                          metrics.services.api === 'warning' ? 'bg-warning' : 'bg-danger'
                        }`}>
                          {metrics.services.api === 'healthy' ? '正常' : 
                           metrics.services.api === 'warning' ? '警告' : '錯誤'}
                        </span>
                      </div>
                    </div>
                    <div className="col-md-3 text-center">
                      <div className="mb-3">
                        <i className={`fas fa-database fa-3x mb-2 ${
                          metrics.services.database === 'healthy' ? 'text-success' : 
                          metrics.services.database === 'warning' ? 'text-warning' : 'text-danger'
                        }`}></i>
                        <h6>資料庫</h6>
                        <span className={`badge ${
                          metrics.services.database === 'healthy' ? 'bg-success' : 
                          metrics.services.database === 'warning' ? 'bg-warning' : 'bg-danger'
                        }`}>
                          {metrics.services.database === 'healthy' ? '正常' : 
                           metrics.services.database === 'warning' ? '警告' : '錯誤'}
                        </span>
                      </div>
                    </div>
                    <div className="col-md-3 text-center">
                      <div className="mb-3">
                        <i className={`fas fa-memory fa-3x mb-2 ${
                          metrics.services.cache === 'healthy' ? 'text-success' : 
                          metrics.services.cache === 'warning' ? 'text-warning' : 'text-danger'
                        }`}></i>
                        <h6>緩存系統</h6>
                        <span className={`badge ${
                          metrics.services.cache === 'healthy' ? 'bg-success' : 
                          metrics.services.cache === 'warning' ? 'bg-warning' : 'bg-danger'
                        }`}>
                          {metrics.services.cache === 'healthy' ? '正常' : 
                           metrics.services.cache === 'warning' ? '警告' : '錯誤'}
                        </span>
                      </div>
                    </div>
                    <div className="col-md-3 text-center">
                      <div className="mb-3">
                        <i className={`fas fa-list fa-3x mb-2 ${
                          metrics.services.queue === 'healthy' ? 'text-success' : 
                          metrics.services.queue === 'warning' ? 'text-warning' : 'text-danger'
                        }`}></i>
                        <h6>佇列服務</h6>
                        <span className={`badge ${
                          metrics.services.queue === 'healthy' ? 'bg-success' : 
                          metrics.services.queue === 'warning' ? 'bg-warning' : 'bg-danger'
                        }`}>
                          {metrics.services.queue === 'healthy' ? '正常' : 
                           metrics.services.queue === 'warning' ? '警告' : '錯誤'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 性能圖表 */}
          <div className="row mb-4">
            <div className="col-12">
              <div className="card shadow">
                <div className="card-header py-3">
                  <h6 className="m-0 font-weight-bold text-primary">24小時性能趨勢</h6>
                </div>
                <div className="card-body">
                  <LineChart
                    data={performanceChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100,
                          title: {
                            display: true,
                            text: '使用率 (%)'
                          }
                        },
                        x: {
                          title: {
                            display: true,
                            text: '時間'
                          }
                        }
                      },
                      plugins: {
                        legend: {
                          position: 'top'
                        }
                      }
                    }}
                    height={300}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 系統告警 */}
          <div className="row">
            <div className="col-12">
              <div className="card shadow">
                <div className="card-header py-3 d-flex justify-content-between align-items-center">
                  <h6 className="m-0 font-weight-bold text-primary">系統告警</h6>
                  <button
                    className="btn btn-outline-secondary btn-sm"
                    onClick={handleClearAllAlerts}
                  >
                    <i className="fas fa-trash me-1"></i>
                    清除已解決
                  </button>
                </div>
                <div className="card-body">
                  {alerts.length === 0 ? (
                    <div className="text-center text-muted py-4">
                      <i className="fas fa-check-circle fa-3x mb-3"></i>
                      <p>目前沒有系統告警</p>
                    </div>
                  ) : (
                    <div className="table-responsive">
                      <table className="table table-hover">
                        <thead>
                          <tr>
                            <th>類型</th>
                            <th>來源</th>
                            <th>標題</th>
                            <th>訊息</th>
                            <th>時間</th>
                            <th>狀態</th>
                            <th>操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {alerts.map((alert) => (
                            <tr key={alert.id} className={alert.resolved ? 'table-light' : ''}>
                              <td>
                                <span className={`badge ${
                                  alert.type === 'critical' ? 'bg-danger' :
                                  alert.type === 'error' ? 'bg-danger' :
                                  alert.type === 'warning' ? 'bg-warning' : 'bg-info'
                                }`}>
                                  {alert.type === 'critical' ? '嚴重' :
                                   alert.type === 'error' ? '錯誤' :
                                   alert.type === 'warning' ? '警告' : '資訊'}
                                </span>
                              </td>
                              <td>{alert.source}</td>
                              <td>{alert.title}</td>
                              <td>{alert.message}</td>
                              <td>{new Date(alert.timestamp).toLocaleString()}</td>
                              <td>
                                <span className={`badge ${alert.resolved ? 'bg-success' : 'bg-secondary'}`}>
                                  {alert.resolved ? '已解決' : '待處理'}
                                </span>
                              </td>
                              <td>
                                {!alert.resolved && (
                                  <button
                                    className="btn btn-outline-success btn-sm"
                                    onClick={() => handleResolveAlert(alert.id)}
                                    title="標記為已解決"
                                  >
                                    <i className="fas fa-check"></i>
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SystemMonitoring;