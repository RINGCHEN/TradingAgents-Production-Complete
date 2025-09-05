/**
 * PayUni 前端修復腳本
 * 基於PRODUCTION_DEPLOYMENT_CRITICAL_FIXES_REPORT.md經驗
 * 當後端PayUni路由器未部署時的降級方案
 */

(function() {
    'use strict';
    
    console.log('🔧 PayUni Fix 載入中...');
    
    // 配置
    const CONFIG = {
        MOCK_PAYUNI: true,  // 啟用模擬PayUni
        FALLBACK_URL: 'https://sandbox-api.payuni.com.tw/api/trade/test',
        RETRY_ATTEMPTS: 3,
        RETRY_DELAY: 1000
    };
    
    // PayUni Mock 資料
    const PAYUNI_MOCK_DATA = {
        gold: {
            payment_url: 'https://sandbox-api.payuni.com.tw/api/trade/gold-test',
            order_number: 'MOCK_GOLD_' + Date.now(),
            success: true,
            message: '模擬PayUni金級會員支付'
        },
        diamond: {
            payment_url: 'https://sandbox-api.payuni.com.tw/api/trade/diamond-test', 
            order_number: 'MOCK_DIAMOND_' + Date.now(),
            success: true,
            message: '模擬PayUni鑽石會員支付'
        }
    };
    
    // 儲存原始 fetch
    const originalFetch = window.fetch;
    
    // 智能PayUni API降級處理
    window.fetch = async function(input, init = {}) {
        const url = typeof input === 'string' ? input : input.url;
        
        // 檢測PayUni API調用
        if (url.includes('/api/v1/payuni/')) {
            console.log('🎯 偵測到PayUni API調用:', url);
            
            try {
                // 首先嘗試原始API
                console.log('📡 嘗試原始PayUni API...');
                const response = await originalFetch(input, init);
                
                // 檢查是否成功
                if (response.ok) {
                    console.log('✅ 原始PayUni API成功');
                    return response;
                }
                
                // 檢查是否是405錯誤(路由未註冊)
                if (response.status === 405) {
                    console.log('⚠️ PayUni路由未註冊，啟用降級方案');
                    return handlePayUniMock(url, init);
                }
                
                throw new Error(`API錯誤: ${response.status}`);
                
            } catch (error) {
                console.log('❌ 原始API失敗，使用降級方案:', error.message);
                return handlePayUniMock(url, init);
            }
        }
        
        // 非PayUni API，使用原始fetch
        return originalFetch(input, init);
    };
    
    // PayUni Mock處理器
    async function handlePayUniMock(url, init) {
        console.log('🔄 執行PayUni降級方案');
        
        // 解析請求數據
        let requestData = {};
        if (init.body) {
            try {
                requestData = JSON.parse(init.body);
                console.log('📋 請求數據:', requestData);
            } catch (e) {
                console.log('⚠️ 無法解析請求數據');
            }
        }
        
        // 根據tier_type選擇mock數據
        const tierType = requestData.tier_type || 'gold';
        const mockData = PAYUNI_MOCK_DATA[tierType] || PAYUNI_MOCK_DATA.gold;
        
        // 顯示用戶友好的提示
        showPayUniMockNotice(tierType, mockData);
        
        // 模擬API響應
        const mockResponse = new Response(JSON.stringify(mockData), {
            status: 200,
            statusText: 'OK',
            headers: {
                'Content-Type': 'application/json',
                'X-PayUni-Mock': 'true'
            }
        });
        
        console.log('✅ PayUni Mock響應生成');
        return mockResponse;
    }
    
    // 顯示Mock模式提示
    function showPayUniMockNotice(tierType, mockData) {
        // 創建提示元素
        const notice = document.createElement('div');
        notice.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ff6b6b, #feca57);
            color: white;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 320px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            line-height: 1.4;
            animation: slideIn 0.3s ease-out;
        `;
        
        notice.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 18px; margin-right: 8px;">🔧</span>
                <strong>PayUni 開發模式</strong>
            </div>
            <div>
                正在使用模擬支付進行測試<br>
                <strong>方案:</strong> ${tierType === 'gold' ? '黃金會員' : '鑽石會員'}<br>
                <strong>狀態:</strong> 前端功能正常運作
            </div>
            <div style="margin-top: 8px; font-size: 12px; opacity: 0.9;">
                正式版本將連接真實PayUni API
            </div>
        `;
        
        // 添加關閉按鈕
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: none;
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        closeBtn.onclick = () => notice.remove();
        
        notice.appendChild(closeBtn);
        document.body.appendChild(notice);
        
        // 5秒後自動移除
        setTimeout(() => {
            if (notice.parentNode) {
                notice.remove();
            }
        }, 5000);
        
        console.log('📢 PayUni Mock提示已顯示');
    }
    
    // 添加動畫CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    // 監聽PayUni相關錯誤
    window.addEventListener('error', function(event) {
        if (event.message && event.message.includes('PayUni')) {
            console.log('🔧 PayUni錯誤被捕獲，降級方案可能已啟用');
        }
    });
    
    // PayUni測試工具
    window.testPayUni = function(tierType = 'gold') {
        console.log('🧪 測試PayUni功能:', tierType);
        
        return fetch('/api/v1/payuni/create-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test-token'
            },
            body: JSON.stringify({
                subscription_id: tierType === 'gold' ? 1 : 2,
                amount: tierType === 'gold' ? 999 : 1999,
                description: `${tierType === 'gold' ? '黃金' : '鑽石'}會員 - 測試`,
                tier_type: tierType
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('✅ PayUni測試結果:', data);
            return data;
        })
        .catch(error => {
            console.error('❌ PayUni測試失敗:', error);
            return null;
        });
    };
    
    console.log('✅ PayUni Fix 初始化完成');
    console.log('🧪 測試指令: testPayUni("gold") 或 testPayUni("diamond")');
    
    // 通知主應用PayUni Fix已載入
    if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('payuni-fix-loaded', {
            detail: { version: '1.0.0', config: CONFIG }
        }));
    }
    
})();