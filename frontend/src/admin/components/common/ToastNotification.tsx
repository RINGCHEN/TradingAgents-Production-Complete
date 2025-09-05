/**
 * Toast通知系統組件
 * 基於 functional_admin.html 的優秀通知設計
 * 提供多類型、自動關閉、堆疊顯示的專業通知功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastNotificationProps {
  messages: ToastMessage[];
  onRemove: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  maxVisible?: number;
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({
  messages,
  onRemove,
  position = 'top-right',
  maxVisible = 5
}) => {
  const [visibleMessages, setVisibleMessages] = useState<ToastMessage[]>([]);
  const [animatingOut, setAnimatingOut] = useState<Set<string>>(new Set());

  // 管理可見消息
  useEffect(() => {
    const sortedMessages = [...messages]
      .sort((a, b) => (a.persistent === b.persistent ? 0 : a.persistent ? 1 : -1))
      .slice(0, maxVisible);
    
    setVisibleMessages(sortedMessages);
  }, [messages, maxVisible]);

  // 自動移除非持久化消息
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    visibleMessages.forEach(message => {
      if (!message.persistent && !animatingOut.has(message.id)) {
        const duration = message.duration ?? getDefaultDuration(message.type);
        const timer = setTimeout(() => {
          handleRemove(message.id);
        }, duration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [visibleMessages, animatingOut]);

  const getDefaultDuration = (type: ToastMessage['type']): number => {
    const durations = {
      success: 4000,
      info: 5000,
      warning: 6000,
      error: 8000
    };
    return durations[type];
  };

  const handleRemove = useCallback((id: string) => {
    setAnimatingOut(prev => new Set(prev).add(id));
    
    setTimeout(() => {
      onRemove(id);
      setAnimatingOut(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }, 300); // 動畫時間
  }, [onRemove]);

  const getPositionClasses = (position: string) => {
    const classes = {
      'top-right': 'toast-position-top-right',
      'top-left': 'toast-position-top-left',
      'bottom-right': 'toast-position-bottom-right',
      'bottom-left': 'toast-position-bottom-left',
      'top-center': 'toast-position-top-center',
      'bottom-center': 'toast-position-bottom-center'
    };
    return classes[position as keyof typeof classes] || classes['top-right'];
  };

  const getToastClasses = (message: ToastMessage) => {
    const baseClasses = 'toast-notification';
    const typeClass = `toast-${message.type}`;
    const animatingClass = animatingOut.has(message.id) ? 'toast-animating-out' : 'toast-animating-in';
    
    return `${baseClasses} ${typeClass} ${animatingClass}`;
  };

  const getIconClass = (type: ToastMessage['type']) => {
    const icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-exclamation-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle'
    };
    return icons[type];
  };

  if (visibleMessages.length === 0) return null;

  const toastContainer = (
    <div className={`toast-container ${getPositionClasses(position)}`}>
      {visibleMessages.map(message => (
        <div
          key={message.id}
          className={getToastClasses(message)}
          role="alert"
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="toast-header">
            <div className="toast-icon">
              <i className={getIconClass(message.type)}></i>
            </div>
            <div className="toast-content">
              {message.title && (
                <div className="toast-title">{message.title}</div>
              )}
              <div className="toast-message">{message.message}</div>
              {message.action && (
                <div className="toast-actions">
                  <button
                    className="toast-action-btn"
                    onClick={message.action.onClick}
                  >
                    {message.action.label}
                  </button>
                </div>
              )}
            </div>
            <button
              className="toast-close-btn"
              onClick={() => handleRemove(message.id)}
              aria-label="關閉通知"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
          
          {/* 進度條 (僅非持久化消息) */}
          {!message.persistent && (
            <div className="toast-progress">
              <div
                className="toast-progress-bar"
                style={{
                  animationDuration: `${message.duration ?? getDefaultDuration(message.type)}ms`
                }}
              ></div>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  // 使用 Portal 渲染到 body
  return createPortal(toastContainer, document.body);
};

// Toast管理器
export class ToastManager {
  private static instance: ToastManager;
  private listeners: Set<(messages: ToastMessage[]) => void> = new Set();
  private messages: ToastMessage[] = [];
  private messageId = 0;

  static getInstance(): ToastManager {
    if (!ToastManager.instance) {
      ToastManager.instance = new ToastManager();
    }
    return ToastManager.instance;
  }

  subscribe(listener: (messages: ToastMessage[]) => void): () => void {
    this.listeners.add(listener);
    listener(this.messages); // 立即發送當前狀態
    
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.messages]));
  }

  show(options: Omit<ToastMessage, 'id'>): string {
    const id = `toast-${++this.messageId}-${Date.now()}`;
    const message: ToastMessage = {
      id,
      ...options
    };

    this.messages.push(message);
    this.notify();
    return id;
  }

  success(message: string, title?: string, options?: Partial<ToastMessage>): string {
    return this.show({
      type: 'success',
      title,
      message,
      ...options
    });
  }

  error(message: string, title?: string, options?: Partial<ToastMessage>): string {
    return this.show({
      type: 'error',
      title,
      message,
      ...options
    });
  }

  warning(message: string, title?: string, options?: Partial<ToastMessage>): string {
    return this.show({
      type: 'warning',
      title,
      message,
      ...options
    });
  }

  info(message: string, title?: string, options?: Partial<ToastMessage>): string {
    return this.show({
      type: 'info',
      title,
      message,
      ...options
    });
  }

  remove(id: string): void {
    this.messages = this.messages.filter(message => message.id !== id);
    this.notify();
  }

  clear(): void {
    this.messages = [];
    this.notify();
  }

  // 批量操作
  showBatch(messages: Omit<ToastMessage, 'id'>[]): string[] {
    const ids = messages.map(message => {
      const id = `toast-${++this.messageId}-${Date.now()}`;
      return {
        id,
        ...message
      };
    });

    this.messages.push(...ids);
    this.notify();
    return ids.map(msg => msg.id);
  }
}

// Hook for using Toast in components
export const useToast = () => {
  const [messages, setMessages] = useState<ToastMessage[]>([]);
  const toastManager = ToastManager.getInstance();

  useEffect(() => {
    return toastManager.subscribe(setMessages);
  }, []);

  return {
    messages,
    show: toastManager.show.bind(toastManager),
    success: toastManager.success.bind(toastManager),
    error: toastManager.error.bind(toastManager),
    warning: toastManager.warning.bind(toastManager),
    info: toastManager.info.bind(toastManager),
    remove: toastManager.remove.bind(toastManager),
    clear: toastManager.clear.bind(toastManager)
  };
};

// React組件用於渲染所有Toast
export const ToastProvider: React.FC = () => {
  const { messages, remove } = useToast();

  return (
    <ToastNotification
      messages={messages}
      onRemove={remove}
      position="top-right"
      maxVisible={5}
    />
  );
};