#!/usr/bin/env python3
"""
統一管理後台生成器
基於分析結果生成統一的管理後台架構
"""

import os
import json
from pathlib import Path

def create_unified_admin_system():
    """創建統一管理後台系統"""
    
    # 創建輸出目錄
    output_dir = Path("unified_admin_system")
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 開始生成統一管理後台架構...")
    
    # 1. 創建基礎HTML模板
    create_base_template(output_dir)
    
    # 2. 創建統一API客戶端
    create_api_client(output_dir)
    
    # 3. 創建錯誤處理系統
    create_error_handler(output_dir)
    
    # 4. 創建主應用
    create_main_app(output_dir)
    
    # 5. 創建統一樣式
    create_unified_styles(output_dir)
    
    # 6. 創建模組配置
    create_modules_config(output_dir)
    
    print(f"✅ 統一管理後台架構已生成到: {output_dir}")
    print("📁 生成的文件:")
    print("  - index.html (統一基礎模板)")
    print("  - unified-api-client.js (統一API客戶端)")
    print("  - unified-error-handler.js (統一錯誤處理)")
    print("  - unified-admin-app.js (主應用)")
    print("  - unified-admin.css (統一樣式)")
    print("  - modules-config.json (模組配置)")

def create_base_template(output_dir):
    """創建基礎HTML模板"""
    template = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>不老傳說 統一管理後台</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <!-- React -->
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <!-- 統一樣式 -->
    <link href="unified-admin.css" rel="stylesheet">
</head>
<body>
    <!-- 載入畫面 -->
    <div id="loadingScreen" class="loading-screen">
        <div class="loading-content">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">載入中...</span>
            </div>
            <h4 class="mt-3">不老傳說 統一管理後台</h4>
            <p>正在載入系統...</p>
        </div>
    </div>

    <!-- 主要內容 -->
    <div id="adminApp" class="d-none">
        <!-- React 應用將在這裡渲染 -->
    </div>

    <!-- 統一API客戶端 -->
    <script src="unified-api-client.js"></script>
    
    <!-- 統一錯誤處理 -->
    <script src="unified-error-handler.js"></script>
    
    <!-- 主應用 -->
    <script type="text/babel" src="unified-admin-app.js"></script>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
    
    with open(output_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(template)
def 
create_api_client(output_dir):
    """創建統一API客戶端"""
    api_client_code = '''/**
 * 統一API客戶端
 * 基於486個API端點分析結果創建的標準化API調用系統
 */

class UnifiedAPIClient {
    constructor(config = {}) {
        this.baseURL = config.baseURL || '/api';
        this.timeout = config.timeout || 30000;
        this.retryAttempts = config.retryAttempts || 3;
        this.retryDelay = config.retryDelay || 1000;
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...config.headers
        };
        
        // 載入狀態管理
        this.loadingStates = new Map();
    }
    
    /**
     * 設置載入狀態
     */
    setLoadingState(key, isLoading) {
        this.loadingStates.set(key, isLoading);
        const event = new CustomEvent('loadingStateChange', {
            detail: { key, isLoading }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * 執行HTTP請求
     */
    async request(method, url, data = null, options = {}) {
        const requestKey = `${method}:${url}`;
        
        try {
            this.setLoadingState(requestKey, true);
            
            const config = {
                method: method.toUpperCase(),
                headers: { ...this.headers, ...options.headers },
                ...options
            };
            
            if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
                config.body = JSON.stringify(data);
            }
            
            const response = await this.executeWithRetry(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            window.errorHandler?.handleError(error, { method, url, data });
            throw error;
            
        } finally {
            this.setLoadingState(requestKey, false);
        }
    }
    
    /**
     * 帶重試機制的請求執行
     */
    async executeWithRetry(url, config, attempt = 1) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            return response;
            
        } catch (error) {
            if (attempt < this.retryAttempts && this.shouldRetry(error)) {
                console.warn(`請求失敗，第 ${attempt} 次重試: ${url}`);
                await this.delay(this.retryDelay * attempt);
                return this.executeWithRetry(url, config, attempt + 1);
            }
            throw error;
        }
    }
    
    shouldRetry(error) {
        return error.name === 'AbortError' || 
               error.message.includes('fetch') ||
               error.message.includes('network');
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // HTTP方法快捷方式
    get(url, options = {}) { return this.request('GET', url, null, options); }
    post(url, data, options = {}) { return this.request('POST', url, data, options); }
    put(url, data, options = {}) { return this.request('PUT', url, data, options); }
    delete(url, options = {}) { return this.request('DELETE', url, null, options); }
    patch(url, data, options = {}) { return this.request('PATCH', url, data, options); }
}

// 全局API客戶端實例
window.apiClient = new UnifiedAPIClient();

// 添加認證攔截器
const originalRequest = window.apiClient.request.bind(window.apiClient);
window.apiClient.request = async function(method, url, data, options = {}) {
    const token = localStorage.getItem('auth_token');
    if (token) {
        options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    }
    
    try {
        return await originalRequest(method, url, data, options);
    } catch (error) {
        if (error.message.includes('401')) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }
        throw error;
    }
};'''
    
    with open(output_dir / "unified-api-client.js", 'w', encoding='utf-8') as f:
        f.write(api_client_code)def 
create_error_handler(output_dir):
    """創建統一錯誤處理系統"""
    error_handler_code = '''/**
 * 統一錯誤處理系統
 */

class UnifiedErrorHandler {
    constructor() {
        this.userFriendlyMessages = {
            'network_error': '網路連接失敗，請檢查網路連接',
            'server_error': '服務器錯誤，請稍後再試',
            'auth_error': '認證失敗，請重新登入',
            'permission_error': '權限不足，請聯繫管理員',
            'validation_error': '輸入數據有誤，請檢查後重試',
            'timeout_error': '請求超時，請稍後再試',
            'unknown_error': '發生未知錯誤，請聯繫技術支援'
        };
        
        this.errorStats = new Map();
        this.initGlobalErrorHandling();
    }
    
    initGlobalErrorHandling() {
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, { type: 'unhandled_promise' });
        });
        
        window.addEventListener('error', (event) => {
            this.handleError(event.error, { 
                type: 'javascript_error',
                filename: event.filename,
                lineno: event.lineno
            });
        });
    }
    
    handleError(error, context = {}) {
        const errorType = this.classifyError(error);
        this.recordErrorStats(errorType, context);
        this.logError(error, errorType, context);
        this.showUserFriendlyError(errorType, error, context);
    }
    
    classifyError(error) {
        if (!error) return 'unknown_error';
        
        const message = error.message || error.toString();
        
        if (message.includes('fetch') || message.includes('network')) return 'network_error';
        if (message.includes('timeout') || message.includes('AbortError')) return 'timeout_error';
        if (error.status === 401) return 'auth_error';
        if (error.status === 403) return 'permission_error';
        if (error.status >= 400 && error.status < 500) return 'validation_error';
        if (error.status >= 500) return 'server_error';
        
        return 'unknown_error';
    }
    
    recordErrorStats(errorType, context) {
        const key = `${errorType}:${context.method || 'unknown'}`;
        const current = this.errorStats.get(key) || { count: 0 };
        this.errorStats.set(key, { count: current.count + 1, lastOccurred: new Date() });
    }
    
    logError(error, errorType, context) {
        console.error('統一錯誤處理:', {
            timestamp: new Date().toISOString(),
            errorType,
            message: error.message,
            context
        });
    }
    
    showUserFriendlyError(errorType, error, context) {
        const message = this.userFriendlyMessages[errorType] || this.userFriendlyMessages['unknown_error'];
        this.showErrorToast(message);
    }
    
    showErrorToast(message) {
        const toastContainer = this.getOrCreateToastContainer();
        
        const toastElement = document.createElement('div');
        toastElement.className = 'toast align-items-center text-white bg-danger border-0';
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastElement);
        
        const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
    }
    
    getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }
}

window.errorHandler = new UnifiedErrorHandler();'''
    
    with open(output_dir / "unified-error-handler.js", 'w', encoding='utf-8') as f:
        f.write(error_handler_code)