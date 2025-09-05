/**
 * 簡化的Toast通知系統
 * 修復循環依賴問題
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextType {
  messages: ToastMessage[];
  showSuccess: (message: string, title?: string) => void;
  showError: (message: string, title?: string) => void;
  showWarning: (message: string, title?: string) => void;
  showInfo: (message: string, title?: string) => void;
  remove: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

// 全局後備Toast系統
class GlobalToastFallback {
  private static instance: GlobalToastFallback;
  private container: HTMLDivElement | null = null;

  static getInstance() {
    if (!GlobalToastFallback.instance) {
      GlobalToastFallback.instance = new GlobalToastFallback();
    }
    return GlobalToastFallback.instance;
  }

  private createContainer() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
    return this.container;
  }

  show(type: 'success' | 'error' | 'warning' | 'info', message: string, title?: string) {
    const container = this.createContainer();
    const toast = document.createElement('div');
    
    const colors = {
      success: '#10b981',
      error: '#ef4444', 
      warning: '#f59e0b',
      info: '#3b82f6'
    };

    toast.style.cssText = `
      padding: 12px 16px;
      margin-bottom: 10px;
      border-radius: 8px;
      background-color: ${colors[type]};
      color: white;
      min-width: 300px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      pointer-events: auto;
      cursor: pointer;
      animation: slideInRight 0.3s ease-out;
    `;

    toast.innerHTML = `
      ${title ? `<div style="font-weight: bold; margin-bottom: 4px;">${title}</div>` : ''}
      <div>${message}</div>
    `;

    // 添加動畫樣式
    if (!document.querySelector('#toast-animations')) {
      const style = document.createElement('style');
      style.id = 'toast-animations';
      style.textContent = `
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
          from { transform: translateX(0); opacity: 1; }
          to { transform: translateX(100%); opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }

    toast.onclick = () => this.removeToast(toast);
    container.appendChild(toast);

    // 自動移除
    setTimeout(() => this.removeToast(toast), 5000);
  }

  private removeToast(toast: HTMLElement) {
    toast.style.animation = 'slideOutRight 0.3s ease-in';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }
}

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    console.warn('useToast called outside ToastProvider, using fallback implementation');
    const fallback = GlobalToastFallback.getInstance();
    
    // 返回後備實現
    return {
      messages: [],
      showSuccess: (message: string, title?: string) => fallback.show('success', message, title),
      showError: (message: string, title?: string) => fallback.show('error', message, title),
      showWarning: (message: string, title?: string) => fallback.show('warning', message, title),
      showInfo: (message: string, title?: string) => fallback.show('info', message, title),
      remove: () => {} // 後備實現中通過點擊移除
    };
  }
  return context;
};

interface ToastProviderProps {
  children: React.ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const addMessage = useCallback((type: ToastMessage['type'], message: string, title?: string) => {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    const newMessage: ToastMessage = {
      id,
      type,
      message,
      title,
      duration: 5000
    };

    setMessages(prev => [...prev, newMessage]);

    // 自動移除
    setTimeout(() => {
      setMessages(prev => prev.filter(msg => msg.id !== id));
    }, newMessage.duration);

    console.log(`Toast ${type}:`, title || '', message);
  }, []);

  const remove = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  }, []);

  const value: ToastContextType = {
    messages,
    showSuccess: (message, title) => addMessage('success', message, title),
    showError: (message, title) => addMessage('error', message, title),
    showWarning: (message, title) => addMessage('warning', message, title),
    showInfo: (message, title) => addMessage('info', message, title),
    remove
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer messages={messages} onRemove={remove} />
    </ToastContext.Provider>
  );
};

interface ToastContainerProps {
  messages: ToastMessage[];
  onRemove: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ messages, onRemove }) => {
  if (messages.length === 0) return null;

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '10px'
    }}>
      {messages.map(message => (
        <div
          key={message.id}
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: getBackgroundColor(message.type),
            color: 'white',
            minWidth: '300px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            cursor: 'pointer'
          }}
          onClick={() => onRemove(message.id)}
        >
          {message.title && (
            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
              {message.title}
            </div>
          )}
          <div>{message.message}</div>
        </div>
      ))}
    </div>
  );
};

function getBackgroundColor(type: ToastMessage['type']): string {
  switch (type) {
    case 'success': return '#10b981';
    case 'error': return '#ef4444';
    case 'warning': return '#f59e0b';
    case 'info': return '#3b82f6';
    default: return '#6b7280';
  }
}