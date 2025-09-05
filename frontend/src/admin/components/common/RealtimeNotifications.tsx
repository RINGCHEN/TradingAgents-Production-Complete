/**
 * 實時通知組件
 * 整合WebSocket管理器，提供即時通知和系統狀態更新
 * 天工 - 第三優先級WebSocket整合任務
 */

import React, { useState, useEffect, useCallback } from 'react';
import { globalWebSocketManager } from '../../services/WebSocketManager';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: number;
  persistent?: boolean;
  autoClose?: number; // 自動關閉時間（毫秒）
}

interface RealtimeNotificationsProps {
  maxNotifications?: number;
  autoCloseDelay?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  showConnectionStatus?: boolean;
}

export const RealtimeNotifications: React.FC<RealtimeNotificationsProps> = ({
  maxNotifications = 5,
  autoCloseDelay = 5000,
  position = 'top-right',
  showConnectionStatus = true
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // 添加通知
  const addNotification = useCallback((notification: Notification) => {
    setNotifications(prev => {
      const newNotifications = [notification, ...prev];
      
      // 限制通知數量
      if (newNotifications.length > maxNotifications) {
        newNotifications.splice(maxNotifications);
      }
      
      return newNotifications;
    });

    // 自動關閉
    if (!notification.persistent) {
      const delay = notification.autoClose || autoCloseDelay;
      setTimeout(() => {
        removeNotification(notification.id);
      }, delay);
    }
  }, [maxNotifications, autoCloseDelay]);

  // 移除通知
  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  // 清除所有通知
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // 設置WebSocket事件監聽器
  useEffect(() => {
    // 監聽通知消息
    const handleNotification = (notification: any) => {
      addNotification({
        id: notification.id || `${Date.now()}-${Math.random()}`,
        title: notification.title,
        message: notification.message,
        type: notification.type || 'info',
        timestamp: notification.timestamp || Date.now(),
        persistent: notification.persistent,
        autoClose: notification.autoClose
      });
    };

    // 監聽系統更新
    const handleSystemUpdate = (update: any) => {
      const statusMap = {
        online: { type: 'success' as const, title: '系統上線' },
        offline: { type: 'error' as const, title: '系統離線' },
        degraded: { type: 'warning' as const, title: '系統性能降級' }
      };

      const config = statusMap[update.status] || { type: 'info' as const, title: '系統狀態變更' };

      addNotification({
        id: `system-${update.component}-${update.timestamp}`,
        title: config.title,
        message: `${update.component} 狀態更新: ${update.status}`,
        type: config.type,
        timestamp: update.timestamp,
        persistent: update.status === 'offline'
      });
    };

    // 監聽數據更新
    const handleDataUpdate = (update: any) => {
      const actionMap = {
        create: '新增',
        update: '更新',
        delete: '刪除'
      };

      addNotification({
        id: `data-${update.resource}-${update.timestamp}`,
        title: '數據更新',
        message: `${update.resource} 已${actionMap[update.action] || '變更'}`,
        type: 'info',
        timestamp: update.timestamp,
        autoClose: 3000 // 數據更新通知3秒後自動關閉
      });
    };

    // 註冊事件處理器
    globalWebSocketManager.onNotification(handleNotification);
    globalWebSocketManager.onSystemUpdate(handleSystemUpdate);
    globalWebSocketManager.onDataUpdate(handleDataUpdate);

    // 監聽連接狀態變化
    const checkConnectionStatus = () => {
      setConnectionStatus(globalWebSocketManager.getConnectionStatus());
    };

    checkConnectionStatus();
    const statusTimer = setInterval(checkConnectionStatus, 1000);

    return () => {
      clearInterval(statusTimer);
    };
  }, [addNotification]);

  // 獲取通知圖標
  const getNotificationIcon = (type: string) => {
    const iconMap = {
      info: 'fas fa-info-circle',
      success: 'fas fa-check-circle',
      warning: 'fas fa-exclamation-triangle',
      error: 'fas fa-times-circle'
    };
    return iconMap[type] || iconMap.info;
  };

  // 獲取通知顏色
  const getNotificationColor = (type: string) => {
    const colorMap = {
      info: 'info',
      success: 'success',
      warning: 'warning',
      error: 'danger'
    };
    return colorMap[type] || colorMap.info;
  };

  // 獲取連接狀態樣式
  const getConnectionStatusStyle = () => {
    const statusMap = {
      connected: { color: 'success', icon: 'fas fa-wifi', text: '已連接' },
      connecting: { color: 'warning', icon: 'fas fa-spinner fa-spin', text: '連接中' },
      disconnected: { color: 'secondary', icon: 'fas fa-wifi-slash', text: '已斷開' },
      error: { color: 'danger', icon: 'fas fa-exclamation-triangle', text: '連接錯誤' }
    };
    return statusMap[connectionStatus] || statusMap.disconnected;
  };

  // 獲取位置樣式
  const getPositionClass = () => {
    const positionMap = {
      'top-right': 'top-0 end-0',
      'top-left': 'top-0 start-0',
      'bottom-right': 'bottom-0 end-0',
      'bottom-left': 'bottom-0 start-0'
    };
    return positionMap[position];
  };

  return (
    <>
      {/* 連接狀態指示器 */}
      {showConnectionStatus && (
        <div 
          className={`position-fixed ${getPositionClass()} m-3`}
          style={{ zIndex: 9999 }}
        >
          <div className={`badge bg-${getConnectionStatusStyle().color} d-flex align-items-center`}>
            <i className={`${getConnectionStatusStyle().icon} me-1`}></i>
            <span className="small">{getConnectionStatusStyle().text}</span>
          </div>
        </div>
      )}

      {/* 通知容器 */}
      <div 
        className={`position-fixed ${getPositionClass()} m-3`}
        style={{ 
          zIndex: 9998, 
          marginTop: showConnectionStatus ? '3rem' : '1rem',
          width: '350px' 
        }}
      >
        {/* 清除按鈕 */}
        {notifications.length > 0 && (
          <div className="d-flex justify-content-end mb-2">
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={clearAllNotifications}
              title="清除所有通知"
            >
              <i className="fas fa-times"></i> 清除全部
            </button>
          </div>
        )}

        {/* 通知列表 */}
        <div className="notification-list">
          {notifications.map((notification, index) => (
            <div
              key={notification.id}
              className={`alert alert-${getNotificationColor(notification.type)} alert-dismissible fade show shadow-sm mb-2`}
              style={{ 
                animation: `slideInRight 0.3s ease-out ${index * 0.1}s both`,
                maxWidth: '100%',
                wordWrap: 'break-word'
              }}
              role="alert"
            >
              <div className="d-flex align-items-start">
                <i className={`${getNotificationIcon(notification.type)} me-2 mt-1`}></i>
                <div className="flex-grow-1">
                  <div className="fw-bold">{notification.title}</div>
                  <div className="small">{notification.message}</div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>
                    {new Date(notification.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => removeNotification(notification.id)}
                  aria-label="關閉"
                ></button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CSS動畫 */}
      <style jsx>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        .notification-list {
          max-height: 80vh;
          overflow-y: auto;
        }
        
        .notification-list::-webkit-scrollbar {
          width: 4px;
        }
        
        .notification-list::-webkit-scrollbar-track {
          background: transparent;
        }
        
        .notification-list::-webkit-scrollbar-thumb {
          background: rgba(0,0,0,0.2);
          border-radius: 2px;
        }
      `}</style>
    </>
  );
};

// 實時系統狀態組件
interface RealtimeSystemStatusProps {
  showDetails?: boolean;
  refreshInterval?: number;
}

export const RealtimeSystemStatus: React.FC<RealtimeSystemStatusProps> = ({
  showDetails = false,
  refreshInterval = 10000
}) => {
  const [systemStatus, setSystemStatus] = useState<any>({
    overall: 'unknown',
    components: []
  });
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  useEffect(() => {
    // 監聽系統更新
    const handleSystemUpdate = (update: any) => {
      setSystemStatus(prev => ({
        ...prev,
        components: prev.components.map(comp => 
          comp.name === update.component 
            ? { ...comp, status: update.status, details: update.details }
            : comp
        )
      }));
      setLastUpdate(Date.now());
    };

    globalWebSocketManager.onSystemUpdate(handleSystemUpdate);

    // 定期請求系統狀態
    const statusTimer = setInterval(async () => {
      try {
        // 這裡可以調用API獲取系統狀態
        // const status = await adminApiService.getSystemStatus();
        // setSystemStatus(status.data);
      } catch (error) {
        console.error('獲取系統狀態失敗:', error);
      }
    }, refreshInterval);

    return () => {
      clearInterval(statusTimer);
    };
  }, [refreshInterval]);

  const getStatusColor = (status: string) => {
    const colorMap = {
      online: 'success',
      offline: 'danger',
      degraded: 'warning',
      unknown: 'secondary'
    };
    return colorMap[status] || colorMap.unknown;
  };

  return (
    <div className="realtime-system-status">
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h6 className="mb-0">系統狀態</h6>
          <small className="text-muted">
            更新時間: {new Date(lastUpdate).toLocaleTimeString()}
          </small>
        </div>
        <div className="card-body">
          <div className="d-flex align-items-center mb-3">
            <span 
              className={`badge bg-${getStatusColor(systemStatus.overall)} me-2`}
            >
              整體狀態: {systemStatus.overall}
            </span>
            <i 
              className={`fas fa-circle text-${getStatusColor(systemStatus.overall)}`}
              style={{ animation: 'pulse 2s infinite' }}
            ></i>
          </div>

          {showDetails && systemStatus.components.length > 0 && (
            <div className="system-components">
              <h6 className="small mb-2">組件狀態:</h6>
              {systemStatus.components.map((component: any, index: number) => (
                <div key={index} className="d-flex justify-content-between align-items-center mb-1">
                  <span className="small">{component.name}</span>
                  <span className={`badge bg-${getStatusColor(component.status)}`}>
                    {component.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default RealtimeNotifications;