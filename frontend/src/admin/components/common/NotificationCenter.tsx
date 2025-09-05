/**
 * NotificationCenter - 即時通知中心組件
 * 提供即時系統通知、用戶消息和警報管理
 * 支援WebSocket即時推送和本地通知管理
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { adminApiService } from '../../services/AdminApiService_Fixed';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'system';
  title: string;
  message: string;
  timestamp: string;
  isRead: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category?: string;
  actionUrl?: string;
  actionLabel?: string;
  metadata?: Record<string, any>;
}

export interface NotificationFilter {
  type?: Notification['type'][];
  priority?: Notification['priority'][];
  isRead?: boolean;
  category?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface NotificationCenterProps {
  maxNotifications?: number;
  enableSound?: boolean;
  enableWebSocket?: boolean;
  autoRefreshInterval?: number;
  showCompactMode?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onNotificationClick?: (notification: Notification) => void;
  onNotificationAction?: (notification: Notification) => void;
}

/**
 * NotificationCenter - 通知中心組件
 * 提供完整的通知管理和即時推送功能
 */
export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  maxNotifications = 100,
  enableSound = true,
  enableWebSocket = true,
  autoRefreshInterval = 30000,
  showCompactMode = false,
  className = '',
  style = {},
  onNotificationClick,
  onNotificationAction
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<NotificationFilter>({});
  const [isExpanded, setIsExpanded] = useState(!showCompactMode);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  const websocketRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 生成模擬通知數據
  const generateMockNotifications = useCallback((): Notification[] => {
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'system',
        title: '系統維護通知',
        message: '系統將於今晚11:00-02:00進行例行維護，請提前保存工作。',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        isRead: false,
        priority: 'high',
        category: 'system',
        actionUrl: '/admin/system_monitor',
        actionLabel: '查看詳情'
      },
      {
        id: '2',
        type: 'warning',
        title: 'CPU使用率過高',
        message: '伺服器CPU使用率已達到85%，建議檢查系統負載。',
        timestamp: new Date(Date.now() - 1800000).toISOString(),
        isRead: false,
        priority: 'urgent',
        category: 'performance',
        actionUrl: '/admin/system_monitor',
        actionLabel: '立即檢查'
      },
      {
        id: '3',
        type: 'success',
        title: '備份完成',
        message: '每日數據備份已成功完成，備份檔案大小: 2.3GB。',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        isRead: true,
        priority: 'medium',
        category: 'backup'
      },
      {
        id: '4',
        type: 'info',
        title: '新用戶註冊',
        message: '今日已有23位新用戶註冊，較昨日增長15%。',
        timestamp: new Date(Date.now() - 10800000).toISOString(),
        isRead: false,
        priority: 'low',
        category: 'users'
      },
      {
        id: '5',
        type: 'error',
        title: 'API調用失敗',
        message: '外部API服務連接失敗，影響交易數據獲取功能。',
        timestamp: new Date(Date.now() - 14400000).toISOString(),
        isRead: false,
        priority: 'urgent',
        category: 'api',
        actionUrl: '/admin/system_monitor',
        actionLabel: '查看日誌'
      }
    ];

    return mockNotifications;
  }, []);

  // 載入通知數據
  const loadNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 模擬API延遲
      await new Promise(resolve => setTimeout(resolve, 500));

      const mockData = generateMockNotifications();
      setNotifications(mockData);
      
      // 計算未讀數量
      const unread = mockData.filter(n => !n.isRead).length;
      setUnreadCount(unread);

    } catch (err) {
      setError(err instanceof Error ? err.message : '載入通知失敗');
    } finally {
      setIsLoading(false);
    }
  }, [generateMockNotifications]);

  // 標記通知為已讀
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      // 模擬API調用
      await new Promise(resolve => setTimeout(resolve, 200));

      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId ? { ...n, isRead: true } : n
        )
      );

      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('標記已讀失敗:', err);
    }
  }, []);

  // 標記所有通知為已讀
  const markAllAsRead = useCallback(async () => {
    try {
      setNotifications(prev => 
        prev.map(n => ({ ...n, isRead: true }))
      );
      setUnreadCount(0);
    } catch (err) {
      console.error('標記所有已讀失敗:', err);
    }
  }, []);

  // 刪除通知
  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      const notification = notifications.find(n => n.id === notificationId);
      
      setNotifications(prev => 
        prev.filter(n => n.id !== notificationId)
      );

      if (notification && !notification.isRead) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (err) {
      console.error('刪除通知失敗:', err);
    }
  }, [notifications]);

  // 播放通知聲音
  const playNotificationSound = useCallback(() => {
    if (enableSound && audioRef.current) {
      audioRef.current.play().catch(err => {
        console.warn('無法播放通知聲音:', err);
      });
    }
  }, [enableSound]);

  // 處理新通知
  const handleNewNotification = useCallback((notification: Notification) => {
    setNotifications(prev => {
      const updated = [notification, ...prev].slice(0, maxNotifications);
      return updated;
    });

    if (!notification.isRead) {
      setUnreadCount(prev => prev + 1);
      playNotificationSound();
    }
  }, [maxNotifications, playNotificationSound]);

  // WebSocket連接管理
  const initializeWebSocket = useCallback(() => {
    if (!enableWebSocket) return;

    try {
      // 模擬WebSocket連接 (實際應用中需要真實的WebSocket URL)
      const ws = new WebSocket('wss://echo.websocket.org');
      
      ws.onopen = () => {
        console.log('WebSocket連接已建立');
      };

      ws.onmessage = (event) => {
        try {
          const notification: Notification = JSON.parse(event.data);
          handleNewNotification(notification);
        } catch (err) {
          console.warn('無法解析WebSocket消息:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket錯誤:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket連接已關閉');
        // 重連邏輯
        setTimeout(initializeWebSocket, 5000);
      };

      websocketRef.current = ws;
    } catch (err) {
      console.error('WebSocket初始化失敗:', err);
    }
  }, [enableWebSocket, handleNewNotification]);

  // 篩選通知
  const filteredNotifications = notifications.filter(notification => {
    if (filter.type && !filter.type.includes(notification.type)) return false;
    if (filter.priority && !filter.priority.includes(notification.priority)) return false;
    if (filter.isRead !== undefined && notification.isRead !== filter.isRead) return false;
    if (filter.category && !filter.category.includes(notification.category || '')) return false;
    if (selectedCategory !== 'all' && notification.category !== selectedCategory) return false;
    return true;
  });

  // 獲取通知圖標
  const getNotificationIcon = (type: Notification['type'], priority: Notification['priority']) => {
    const icons = {
      info: '💡',
      success: '✅',
      warning: '⚠️',
      error: '❌',
      system: '🔧'
    };

    const priorityIcons = {
      urgent: '🚨',
      high: '🔥',
      medium: '📢',
      low: '📝'
    };

    return priority === 'urgent' ? priorityIcons.urgent : icons[type];
  };

  // 格式化時間
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return '剛剛';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分鐘前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小時前`;
    return date.toLocaleDateString('zh-TW');
  };

  // 初始化效果
  useEffect(() => {
    loadNotifications();
    
    if (enableWebSocket) {
      initializeWebSocket();
    }

    // 設置自動刷新
    const interval = setInterval(loadNotifications, autoRefreshInterval);

    return () => {
      clearInterval(interval);
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [loadNotifications, initializeWebSocket, enableWebSocket, autoRefreshInterval]);

  return (
    <div 
      className={`notification-center ${className}`}
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* 音頻元素 */}
      <audio ref={audioRef} preload="auto">
        <source src="data:audio/wav;base64,UklGRvIBAABXQVZFZm10IBAAAAABAAABAC..." type="audio/wav" />
      </audio>

      {/* 標題欄 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>
            📢 通知中心
          </h3>
          {unreadCount > 0 && (
            <span style={{
              backgroundColor: '#ff4444',
              color: 'white',
              borderRadius: '12px',
              padding: '2px 8px',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              {unreadCount}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={markAllAsRead}
            disabled={unreadCount === 0}
            style={{
              background: 'none',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: 'rgba(255, 255, 255, 0.7)',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer',
              opacity: unreadCount === 0 ? 0.5 : 1
            }}
          >
            全部已讀
          </button>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'none',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: 'rgba(255, 255, 255, 0.7)',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            {isExpanded ? '收起' : '展開'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* 篩選器 */}
          <div style={{
            padding: '12px 16px',
            backgroundColor: 'rgba(0, 0, 0, 0.05)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'inherit',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '12px'
              }}
            >
              <option value="all">所有分類</option>
              <option value="system">系統</option>
              <option value="performance">性能</option>
              <option value="backup">備份</option>
              <option value="users">用戶</option>
              <option value="api">API</option>
            </select>
          </div>

          {/* 通知列表 */}
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            padding: '8px'
          }}>
            {isLoading && (
              <div style={{
                textAlign: 'center',
                padding: '20px',
                color: 'rgba(255, 255, 255, 0.7)'
              }}>
                正在載入通知...
              </div>
            )}

            {error && (
              <div style={{
                color: 'red',
                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                padding: '12px',
                borderRadius: '4px',
                margin: '8px 0',
                fontSize: '14px'
              }}>
                錯誤: {error}
              </div>
            )}

            {!isLoading && !error && filteredNotifications.length === 0 && (
              <div style={{
                textAlign: 'center',
                padding: '20px',
                color: 'rgba(255, 255, 255, 0.5)'
              }}>
                暫無通知
              </div>
            )}

            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                style={{
                  backgroundColor: notification.isRead 
                    ? 'rgba(255, 255, 255, 0.05)' 
                    : 'rgba(255, 255, 255, 0.1)',
                  border: notification.priority === 'urgent' 
                    ? '1px solid #ff4444' 
                    : '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  padding: '12px',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onClick={() => {
                  if (!notification.isRead) {
                    markAsRead(notification.id);
                  }
                  if (onNotificationClick) {
                    onNotificationClick(notification);
                  }
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '16px' }}>
                      {getNotificationIcon(notification.type, notification.priority)}
                    </span>
                    <span style={{
                      fontWeight: 'bold',
                      fontSize: '14px',
                      color: notification.isRead ? 'rgba(255, 255, 255, 0.7)' : 'white'
                    }}>
                      {notification.title}
                    </span>
                    {!notification.isRead && (
                      <span style={{
                        width: '8px',
                        height: '8px',
                        backgroundColor: '#4CAF50',
                        borderRadius: '50%'
                      }} />
                    )}
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteNotification(notification.id);
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'rgba(255, 255, 255, 0.5)',
                      cursor: 'pointer',
                      padding: '0',
                      fontSize: '16px'
                    }}
                  >
                    ✕
                  </button>
                </div>

                <p style={{
                  margin: '0 0 8px 0',
                  fontSize: '13px',
                  color: 'rgba(255, 255, 255, 0.8)',
                  lineHeight: '1.4'
                }}>
                  {notification.message}
                </p>

                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.5)'
                  }}>
                    {formatTimestamp(notification.timestamp)}
                  </span>

                  {notification.actionLabel && notification.actionUrl && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onNotificationAction) {
                          onNotificationAction(notification);
                        }
                      }}
                      style={{
                        backgroundColor: 'rgba(74, 144, 226, 0.8)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        fontSize: '11px',
                        cursor: 'pointer',
                        fontWeight: 'bold'
                      }}
                    >
                      {notification.actionLabel}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationCenter;