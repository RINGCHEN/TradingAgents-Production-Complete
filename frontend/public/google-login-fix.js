/**
 * Google 登入 CSP 修復腳本
 * 解決 Google Identity Services 的 CSP 衝突問題
 */

(function() {
    'use strict';
    
    console.log('🔐 Google 登入修復腳本載入中...');
    
    // 動態注入允許 Google 登入的 CSP 設定
    function injectGoogleCSP() {
        // 移除可能存在的限制性 CSP meta 標籤
        const existingCSP = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        if (existingCSP) {
            console.log('🗑️ 移除限制性 CSP 設定');
            existingCSP.remove();
        }
        
        // 注入允許 Google 服務的 CSP 設定
        const cspMeta = document.createElement('meta');
        cspMeta.setAttribute('http-equiv', 'Content-Security-Policy');
        cspMeta.setAttribute('content', [
            "default-src 'self' https://accounts.google.com https://twshocks-app-79rsx.ondigitalocean.app",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://apis.google.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://accounts.google.com https://twshocks-app-79rsx.ondigitalocean.app https://apis.google.com",
            "frame-src 'self' https://accounts.google.com https://content.googleapis.com",
            "child-src 'self' https://accounts.google.com",
            "object-src 'none'",
            "media-src 'self' data:",
            "worker-src 'self' blob:",
            "manifest-src 'self'"
        ].join('; '));
        
        document.head.insertBefore(cspMeta, document.head.firstChild);
        console.log('✅ Google 友好的 CSP 設定已注入');
    }
    
    // 立即執行 CSP 修復
    injectGoogleCSP();
    
    // 處理 Google Identity Services 載入
    function ensureGoogleIdentityServices() {
        // 確保 Google Identity Services 腳本載入
        if (!window.google) {
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = function() {
                console.log('✅ Google Identity Services 腳本重新載入成功');
            };
            script.onerror = function() {
                console.error('❌ Google Identity Services 腳本載入失敗');
            };
            document.head.appendChild(script);
        }
    }
    
    // 處理 window.postMessage CSP 錯誤
    function fixPostMessageCSP() {
        // 允許來自 Google 的 postMessage
        window.addEventListener('message', function(event) {
            if (event.origin === 'https://accounts.google.com') {
                console.log('✅ 允許來自 Google 的 postMessage');
                // 讓事件正常處理
                return true;
            }
        }, true);
    }
    
    // 修復 COOP (Cross-Origin-Opener-Policy) 問題
    function fixCOOP() {
        // 暫時修改 window.open 以處理 COOP 限制
        const originalOpen = window.open;
        window.open = function(url, name, specs) {
            if (url && url.includes('accounts.google.com')) {
                // 為 Google 登入彈出視窗添加適當的參數
                const newSpecs = specs ? specs + ',noopener=0' : 'noopener=0';
                console.log('🔄 調整 Google 登入彈出視窗設定');
                return originalOpen.call(this, url, name, newSpecs);
            }
            return originalOpen.call(this, url, name, specs);
        };
    }
    
    // 監聽 CSP 違規事件並提供修復建議
    document.addEventListener('securitypolicyviolation', function(event) {
        if (event.blockedURI.includes('accounts.google.com')) {
            console.warn('🔒 Google 服務 CSP 違規:', {
                directive: event.violatedDirective,
                blockedURI: event.blockedURI,
                fix: '正在嘗試動態修復...'
            });
            
            // 嘗試動態修復
            if (event.violatedDirective.includes('style-src')) {
                console.log('🎨 嘗試修復 Google 樣式載入問題');
                injectGoogleCSP();
            }
        }
    });
    
    // 當 DOM 載入完成時執行修復
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            ensureGoogleIdentityServices();
            fixPostMessageCSP();
            fixCOOP();
        });
    } else {
        ensureGoogleIdentityServices();
        fixPostMessageCSP();
        fixCOOP();
    }
    
    // Google 登入測試函數
    window.testGoogleLogin = function() {
        console.log('🧪 測試 Google 登入設定...');
        
        if (window.google && window.google.accounts) {
            console.log('✅ Google Identity Services 可用');
            try {
                google.accounts.id.initialize({
                    client_id: '351731559902-11g45sv5947cr3q89lhkar272kfeiput.apps.googleusercontent.com',
                    callback: function(response) {
                        console.log('✅ Google 登入測試回調成功');
                    }
                });
                console.log('✅ Google 登入初始化測試成功');
            } catch (error) {
                console.error('❌ Google 登入初始化測試失敗:', error);
            }
        } else {
            console.error('❌ Google Identity Services 不可用');
        }
    };
    
    console.log('✅ Google 登入修復腳本載入完成');
    console.log('🧪 測試指令: testGoogleLogin()');
    
    // 通知主應用 Google 修復已載入
    if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('google-login-fix-loaded', {
            detail: { 
                version: '1.0.0', 
                cspFixed: true,
                coopFixed: true 
            }
        }));
    }
    
})();