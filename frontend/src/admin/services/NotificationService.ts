/**
 * 通知服務
 * 統一管理所有用戶通知
 */

export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
  timestamp: Date;
}

class NotificationService {
  private notifications: Notification[] = [];
  private listeners: ((notifications: Notification[]) => void)[] = [];

  show(notification: Omit<Notification, 'id' | 'timestamp'>): string {
    const id = Date.now().toString();
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      duration: notification.duration || 5000
    };

    this.notifications.push(newNotification);
    this.notifyListeners();

    // 自動移除通知
    if (newNotification.duration > 0) {
      setTimeout(() => {
        this.remove(id);
      }, newNotification.duration);
    }

    return id;
  }

  remove(id: string): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notifyListeners();
  }

  clear(): void {
    this.notifications = [];
    this.notifyListeners();
  }

  subscribe(listener: (notifications: Notification[]) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener([...this.notifications]));
  }

  // 便捷方法
  success(title: string, message: string): string {
    return this.show({ type: NotificationType.SUCCESS, title, message });
  }

  error(title: string, message: string): string {
    return this.show({ type: NotificationType.ERROR, title, message, duration: 0 });
  }

  warning(title: string, message: string): string {
    return this.show({ type: NotificationType.WARNING, title, message });
  }

  info(title: string, message: string): string {
    return this.show({ type: NotificationType.INFO, title, message });
  }
}

export const notificationService = new NotificationService();