/**
 * WebSocket管理器 - 實時通信系統
 * 提供即時通知、數據更新和系統狀態同步
 * 天工 - 第三優先級WebSocket整合任務
 */

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
  id: string;
}

interface NotificationMessage {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: number;
  persistent?: boolean;
}

interface SystemUpdateMessage {
  component: string;
  status: 'online' | 'offline' | 'degraded';
  details?: any;
  timestamp: number;
}

interface DataUpdateMessage {
  resource: string;
  action: 'create' | 'update' | 'delete';
  data: any;
  timestamp: number;
}

type MessageHandler = (message: WebSocketMessage) => void;
type NotificationHandler = (notification: NotificationMessage) => void;
type SystemUpdateHandler = (update: SystemUpdateMessage) => void;
type DataUpdateHandler = (update: DataUpdateMessage) => void;

interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  enableDebug: boolean;
}

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private messageHandlers = new Map<string, MessageHandler[]>();
  private connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';
  private reconnectAttempts = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;

  // 專用處理器
  private notificationHandlers: NotificationHandler[] = [];
  private systemUpdateHandlers: SystemUpdateHandler[] = [];
  private dataUpdateHandlers: DataUpdateHandler[] = [];

  // 消息隊列（離線時存儲）
  private messageQueue: WebSocketMessage[] = [];

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = {
      url: this.getWebSocketUrl(),
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      enableDebug: false,
      ...config
    };

    this.setupEventListeners();
  }

  /**
   * 建立WebSocket連接
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.debug('WebSocket已經連接');
      return;
    }

    this.connectionStatus = 'connecting';
    this.debug(`嘗試連接到 ${this.config.url}`);

    try {
      this.ws = new WebSocket(this.config.url);
      this.setupWebSocketHandlers();
    } catch (error) {
      console.error('WebSocket連接失敗:', error);
      this.handleConnectionError();
    }
  }

  /**
   * 斷開WebSocket連接
   */
  disconnect(): void {
    this.connectionStatus = 'disconnected';
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.debug('WebSocket已斷開連接');
  }

  /**
   * 發送消息
   */
  send(message: Omit<WebSocketMessage, 'timestamp' | 'id'>): boolean {
    const fullMessage: WebSocketMessage = {
      ...message,
      timestamp: Date.now(),
      id: this.generateMessageId()
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(fullMessage));
        this.debug('發送消息:', fullMessage);
        return true;
      } catch (error) {
        console.error('發送消息失敗:', error);
        return false;
      }
    } else {
      // 離線時加入隊列
      this.messageQueue.push(fullMessage);
      this.debug('消息已加入離線隊列');
      return false;
    }
  }

  /**
   * 註冊消息處理器
   */
  on(messageType: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * 移除消息處理器
   */
  off(messageType: string, handler?: MessageHandler): void {
    if (!handler) {
      this.messageHandlers.delete(messageType);
      return;
    }

    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * 註冊通知處理器
   */
  onNotification(handler: NotificationHandler): void {
    this.notificationHandlers.push(handler);
  }

  /**
   * 註冊系統更新處理器
   */
  onSystemUpdate(handler: SystemUpdateHandler): void {
    this.systemUpdateHandlers.push(handler);
  }

  /**
   * 註冊數據更新處理器
   */
  onDataUpdate(handler: DataUpdateHandler): void {
    this.dataUpdateHandlers.push(handler);
  }

  /**
   * 獲取連接狀態
   */
  getConnectionStatus(): string {
    return this.connectionStatus;
  }

  /**
   * 檢查是否已連接
   */
  isConnected(): boolean {
    return this.connectionStatus === 'connected';
  }

  /**
   * 發送心跳
   */
  private sendHeartbeat(): void {
    this.send({
      type: 'heartbeat',
      payload: { timestamp: Date.now() }
    });
  }

  /**
   * 設置WebSocket事件處理器
   */
  private setupWebSocketHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.connectionStatus = 'connected';
      this.reconnectAttempts = 0;
      this.debug('WebSocket連接成功');

      // 開始心跳
      this.startHeartbeat();

      // 發送離線期間的消息
      this.flushMessageQueue();

      // 發送連接成功通知
      this.notifyConnectionStatus('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('解析WebSocket消息失敗:', error);
      }
    };

    this.ws.onclose = (event) => {
      this.connectionStatus = 'disconnected';
      this.debug(`WebSocket連接關閉: ${event.code} - ${event.reason}`);
      
      if (this.heartbeatTimer) {
        clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = null;
      }

      this.notifyConnectionStatus('disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket錯誤:', error);
      this.handleConnectionError();
    };
  }

  /**
   * 處理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    this.debug('收到消息:', message);

    // 處理專用消息類型
    switch (message.type) {
      case 'notification':
        this.handleNotification(message.payload);
        break;
      case 'system_update':
        this.handleSystemUpdate(message.payload);
        break;
      case 'data_update':
        this.handleDataUpdate(message.payload);
        break;
      case 'heartbeat_response':
        this.debug('收到心跳響應');
        break;
    }

    // 調用註冊的處理器
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('消息處理器錯誤:', error);
        }
      });
    }
  }

  /**
   * 處理通知消息
   */
  private handleNotification(notification: NotificationMessage): void {
    this.notificationHandlers.forEach(handler => {
      try {
        handler(notification);
      } catch (error) {
        console.error('通知處理器錯誤:', error);
      }
    });
  }

  /**
   * 處理系統更新消息
   */
  private handleSystemUpdate(update: SystemUpdateMessage): void {
    this.systemUpdateHandlers.forEach(handler => {
      try {
        handler(update);
      } catch (error) {
        console.error('系統更新處理器錯誤:', error);
      }
    });
  }

  /**
   * 處理數據更新消息
   */
  private handleDataUpdate(update: DataUpdateMessage): void {
    this.dataUpdateHandlers.forEach(handler => {
      try {
        handler(update);
      } catch (error) {
        console.error('數據更新處理器錯誤:', error);
      }
    });
  }

  /**
   * 開始心跳
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.config.heartbeatInterval);
  }

  /**
   * 發送離線期間的消息
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!;
      this.send(message);
    }
  }

  /**
   * 嘗試重新連接
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('超過最大重連次數，停止重連');
      this.connectionStatus = 'error';
      return;
    }

    this.reconnectAttempts++;
    this.debug(`嘗試重新連接 (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.config.reconnectInterval);
  }

  /**
   * 處理連接錯誤
   */
  private handleConnectionError(): void {
    this.connectionStatus = 'error';
    this.notifyConnectionStatus('error');
  }

  /**
   * 通知連接狀態變化
   */
  private notifyConnectionStatus(status: string): void {
    const notification: NotificationMessage = {
      id: this.generateMessageId(),
      title: 'WebSocket狀態',
      message: `連接狀態: ${status}`,
      type: status === 'connected' ? 'success' : 'warning',
      timestamp: Date.now(),
      persistent: false
    };

    this.handleNotification(notification);
  }

  /**
   * 獲取WebSocket URL
   */
  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/admin`;
  }

  /**
   * 生成消息ID
   */
  private generateMessageId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 設置頁面事件監聽器
   */
  private setupEventListeners(): void {
    // 頁面可見性變化
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.debug('頁面隱藏，暫停心跳');
        if (this.heartbeatTimer) {
          clearInterval(this.heartbeatTimer);
          this.heartbeatTimer = null;
        }
      } else if (this.isConnected()) {
        this.debug('頁面可見，恢復心跳');
        this.startHeartbeat();
      }
    });

    // 頁面卸載
    window.addEventListener('beforeunload', () => {
      this.disconnect();
    });

    // 網路狀態變化
    window.addEventListener('online', () => {
      this.debug('網路已連接，嘗試重新連接WebSocket');
      if (!this.isConnected()) {
        this.connect();
      }
    });

    window.addEventListener('offline', () => {
      this.debug('網路已斷開');
      this.connectionStatus = 'disconnected';
    });
  }

  /**
   * 調試輸出
   */
  private debug(message: string, data?: any): void {
    if (this.config.enableDebug) {
      console.log(`[WebSocketManager] ${message}`, data || '');
    }
  }

  /**
   * 獲取統計信息
   */
  getStats(): any {
    return {
      connectionStatus: this.connectionStatus,
      reconnectAttempts: this.reconnectAttempts,
      messageHandlers: this.messageHandlers.size,
      queuedMessages: this.messageQueue.length,
      isHeartbeatActive: !!this.heartbeatTimer
    };
  }
}

// 全局WebSocket管理器實例
export const globalWebSocketManager = new WebSocketManager({
  enableDebug: process.env.NODE_ENV === 'development',
  reconnectInterval: 3000,
  maxReconnectAttempts: 15,
  heartbeatInterval: 30000
});

// 自動連接
globalWebSocketManager.connect();