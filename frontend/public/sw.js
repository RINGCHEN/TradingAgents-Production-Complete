// TradingAgents Service Worker
// 實現PWA功能、快取策略和離線支持

const CACHE_NAME = 'tradingagents-v2.0.0';
const STATIC_CACHE = 'tradingagents-static-v2.0.0';
const API_CACHE = 'tradingagents-api-v2.0.0';

// 需要快取的靜態資源
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/assets/icons/icon-192x192.png',
  '/assets/icons/icon-512x512.png',
  '/offline.html'
];

// API路由模式
const API_ROUTES = [
  /\/api\//,
  /\/health/,
  /\/finmind/
];

// 安裝事件 - 預快取靜態資源
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing...');
  
  event.waitUntil(
    Promise.all([
      // 快取靜態資源
      caches.open(STATIC_CACHE).then((cache) => {
        return cache.addAll(STATIC_ASSETS.map(url => new Request(url, {
          credentials: 'same-origin'
        })));
      }),
      
      // 立即激活新的Service Worker
      self.skipWaiting()
    ])
  );
});

// 激活事件 - 清理舊快取
self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker: Activating...');
  
  event.waitUntil(
    Promise.all([
      // 清理舊版本快取
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== STATIC_CACHE && 
                cacheName !== API_CACHE) {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // 立即控制所有客戶端
      self.clients.claim()
    ])
  );
});

// 獲取事件 - 實施快取策略
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 只處理GET請求
  if (request.method !== 'GET') {
    return;
  }
  
  // 根據資源類型選擇不同的快取策略
  if (isStaticAsset(request)) {
    // 靜態資源：快取優先 (Cache First)
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (isAPIRequest(request)) {
    // API請求：網路優先 (Network First)
    event.respondWith(networkFirst(request, API_CACHE));
  } else if (isNavigationRequest(request)) {
    // 頁面導航：網路優先，失敗時返回離線頁面
    event.respondWith(navigationHandler(request));
  } else {
    // 其他資源：瀏覽器默認處理
    return;
  }
});

// 判斷是否為靜態資源
function isStaticAsset(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  
  return pathname.startsWith('/assets/') ||
         pathname.endsWith('.js') ||
         pathname.endsWith('.css') ||
         pathname.endsWith('.png') ||
         pathname.endsWith('.jpg') ||
         pathname.endsWith('.jpeg') ||
         pathname.endsWith('.svg') ||
         pathname.endsWith('.ico') ||
         pathname === '/manifest.json';
}

// 判斷是否為API請求
function isAPIRequest(request) {
  const url = new URL(request.url);
  return API_ROUTES.some(pattern => pattern.test(url.pathname));
}

// 判斷是否為頁面導航請求
function isNavigationRequest(request) {
  return request.mode === 'navigate' ||
         (request.method === 'GET' && request.headers.get('accept').includes('text/html'));
}

// 快取優先策略
async function cacheFirst(request, cacheName) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache first strategy failed:', error);
    // 返回離線頁面或預設響應
    return new Response('資源暫時無法使用', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// 網路優先策略
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      // 只快取GET請求的成功響應
      if (request.method === 'GET') {
        cache.put(request, networkResponse.clone());
      }
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network request failed, trying cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 返回離線響應
    return new Response(JSON.stringify({
      error: 'Network unavailable',
      message: '網路連接失敗，請檢查網路設定',
      offline: true
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

// 頁面導航處理
async function navigationHandler(request) {
  try {
    // 先嘗試網路請求
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    // 網路失敗時，返回快取的首頁或離線頁面
    const cachedResponse = await caches.match('/index.html') ||
                          await caches.match('/offline.html');
    
    return cachedResponse || new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>TradingAgents - 離線模式</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .offline { color: #666; }
          </style>
        </head>
        <body>
          <div class="offline">
            <h1>🔌 離線模式</h1>
            <p>您目前處於離線狀態，部分功能可能無法使用。</p>
            <p>請檢查網路連接後重新載入頁面。</p>
          </div>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// 後台同步 - 處理用戶在離線時的操作
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// 執行後台同步
async function doBackgroundSync() {
  // 這裡可以實現離線時的數據同步邏輯
  console.log('Performing background sync...');
}

// 推送通知處理
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : '您有新的交易分析報告',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '查看詳情',
        icon: '/assets/icons/checkmark.png'
      },
      {
        action: 'close',
        title: '關閉',
        icon: '/assets/icons/xmark.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('TradingAgents', options)
  );
});

// 通知點擊處理
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('🚀 TradingAgents Service Worker loaded successfully');