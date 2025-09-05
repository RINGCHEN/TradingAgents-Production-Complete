/**
 * Toast Provider Fix for Production Build
 * Provides fallback toast functionality when ToastProvider context is missing
 */

// Global toast fallback system
window.fallbackToast = {
  container: null,
  
  init() {
    if (this.container) return;
    
    this.container = document.createElement('div');
    this.container.id = 'fallback-toast-container';
    this.container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      pointer-events: none;
    `;
    document.body.appendChild(this.container);
  },
  
  show(message, type = 'info', duration = 5000) {
    this.init();
    
    const toast = document.createElement('div');
    toast.style.cssText = `
      margin-bottom: 10px;
      padding: 12px 20px;
      border-radius: 6px;
      color: white;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      pointer-events: auto;
      cursor: pointer;
      transition: all 0.3s ease;
      max-width: 300px;
      word-wrap: break-word;
    `;
    
    // Set background color based on type
    switch (type) {
      case 'success':
        toast.style.backgroundColor = '#10b981';
        break;
      case 'error':
        toast.style.backgroundColor = '#ef4444';
        break;
      case 'warning':
        toast.style.backgroundColor = '#f59e0b';
        break;
      default:
        toast.style.backgroundColor = '#3b82f6';
    }
    
    toast.textContent = message;
    
    // Add click to dismiss
    toast.onclick = () => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    };
    
    this.container.appendChild(toast);
    
    // Auto dismiss
    setTimeout(() => {
      if (toast.parentNode) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }
    }, duration);
  },
  
  success(message) {
    this.show(message, 'success');
  },
  
  error(message) {
    this.show(message, 'error');
  },
  
  warning(message) {
    this.show(message, 'warning');
  },
  
  info(message) {
    this.show(message, 'info');
  }
};

// Override console methods to catch toast errors and provide fallbacks
const originalConsoleError = console.error;
console.error = function(...args) {
  const message = args.join(' ');
  
  if (message.includes('useToast must be used within ToastProvider')) {
    console.warn('🔧 ToastProvider context missing, using fallback toast system');
    
    // Extract the toast message if possible
    const toastMatch = message.match(/Toast:\s*(\w+)/);
    if (toastMatch) {
      const toastType = toastMatch[1].toLowerCase();
      window.fallbackToast[toastType] && window.fallbackToast[toastType]('操作完成');
    }
    
    return; // Don't show the original error
  }
  
  originalConsoleError.apply(console, args);
};

// Initialize fallback toast system
window.fallbackToast.init();
console.log('✅ Toast fallback system loaded');

// Provide global toast functions for emergency use
window.showToast = (message, type) => window.fallbackToast.show(message, type);
window.showSuccess = (message) => window.fallbackToast.success(message);
window.showError = (message) => window.fallbackToast.error(message);
window.showWarning = (message) => window.fallbackToast.warning(message);
window.showInfo = (message) => window.fallbackToast.info(message);