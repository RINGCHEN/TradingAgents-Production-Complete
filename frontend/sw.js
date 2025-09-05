/**
 * Service Worker - 第二階段Week 3 性能調優與監控
 * 提供快取策略、離線支援、背景同步、推送通知
 * 支援多種快取策略、版本控制、智能更新
 */

const CACHE_VERSION = 'v1.2.0';
const STATIC_CACHE = `tradingagents-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `tradingagents-dynamic-${CACHE_VERSION}`;
const API_CACHE = `tradingagents-api-${CACHE_VERSION}`;
const IMAGE_CACHE = `tradingagents-images-${CACHE_VERSION}`;

// 需要預快取的靜態資源
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/vendor.js',
  '/manifest.json',
  '/favicon.ico'
];

// API 端點快取配置
const API_CACHE_CONFIG = {
  // 長期快取（1天）
  longTerm: {
    patterns: [
      /\/api\/markets$/,
      /\/api\/stocks\/info/,
      /\/api\/config\//
    ],
    maxAge: 24 * 60 * 60 * 1000 // 24小時
  },
  // 中期快取（1小時）
  mediumTerm: {
    patterns: [
      /\/api\/stocks\/prices/,
      /\/api\/news/,
      /\/api\/analysis\//
    ],
    maxAge: 60 * 60 * 1000 // 1小時
  },
  // 短期快取（5分鐘）
  shortTerm: {
    patterns: [
      /\/api\/users\/portfolio/,
      /\/api\/alerts/,
      /\/api\/notifications/
    ],
    maxAge: 5 * 60 * 1000 // 5分鐘
  }
};

// 不快取的資源
const NO_CACHE_PATTERNS = [
  /\/api\/auth\//,
  /\/api\/admin\//,
  /\/api\/realtime\//,
  /websocket/
];

// 安裝 Service Worker
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Pre-caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets pre-cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Error pre-caching static assets:', error);
      })
  );
});

// 啟動 Service Worker
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => {
              // 刪除舊版本快取
              return cacheName !== STATIC_CACHE &&
                     cacheName !== DYNAMIC_CACHE &&
                     cacheName !== API_CACHE &&
                     cacheName !== IMAGE_CACHE;
            })
            .map(cacheName => {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated');
        return self.clients.claim();
      })
      .catch(error => {
        console.error('[SW] Error activating Service Worker:', error);
      })
  );
});

// 攔截網路請求
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // 跳過非 HTTP(S) 請求
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // 檢查是否為不快取的資源
  if (NO_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(
      fetch(request).catch(() => {
        // 網路失敗時返回離線頁面
        if (request.destination === 'document') {
          return caches.match('/offline.html');
        }
      })
    );
    return;
  }

  // 根據請求類型選擇快取策略
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (request.destination === 'image') {
    event.respondWith(handleImageRequest(request));
  } else if (STATIC_ASSETS.some(asset => url.pathname.endsWith(asset))) {
    event.respondWith(handleStaticRequest(request));
  } else {
    event.respondWith(handleDynamicRequest(request));
  }
});

// 處理 API 請求
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const cacheConfig = getCacheConfig(url.pathname);
  
  if (!cacheConfig) {
    // 網路優先策略
    return networkFirst(request, API_CACHE);
  }

  try {
    const cache = await caches.open(API_CACHE);
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
      const cacheTime = new Date(cachedResponse.headers.get('sw-cache-time') || 0);
      const now = Date.now();
      
      // 檢查快取是否過期
      if (now - cacheTime.getTime() < cacheConfig.maxAge) {
        console.log('[SW] Serving API request from cache:', url.pathname);
        
        // 背景更新快取（stale-while-revalidate）
        updateCacheInBackground(request, cache);
        
        return cachedResponse;
      }
    }

    // 快取過期或不存在，從網路獲取
    console.log('[SW] Fetching API request from network:', url.pathname);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // 複製回應以供快取
      const responseToCache = networkResponse.clone();
      
      // 添加快取時間標頭
      const headers = new Headers(responseToCache.headers);
      headers.append('sw-cache-time', new Date().toISOString());
      
      const cachedResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers
      });
      
      cache.put(request, cachedResponse);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('[SW] API request failed:', error);
    
    // 網路失敗時嘗試從快取返回
    const cache = await caches.open(API_CACHE);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('[SW] Serving stale API response from cache:', url.pathname);
      return cachedResponse;
    }
    
    // 返回錯誤回應
    return new Response(JSON.stringify({
      error: '網路連接失敗，請檢查網路連接後重試',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// 處理圖片請求
async function handleImageRequest(request) {
  return cacheFirst(request, IMAGE_CACHE);
}

// 處理靜態資源請求
async function handleStaticRequest(request) {
  return cacheFirst(request, STATIC_CACHE);
}

// 處理動態內容請求
async function handleDynamicRequest(request) {
  return networkFirst(request, DYNAMIC_CACHE);
}

// 快取優先策略
async function cacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('[SW] Serving from cache:', request.url);
      return cachedResponse;
    }
    
    console.log('[SW] Fetching from network:', request.url);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('[SW] Cache first strategy failed:', error);
    
    // 如果是導航請求，返回離線頁面
    if (request.destination === 'document') {
      const cache = await caches.open(STATIC_CACHE);
      return cache.match('/offline.html');
    }
    
    throw error;
  }
}

// 網路優先策略
async function networkFirst(request, cacheName) {
  try {
    console.log('[SW] Fetching from network:', request.url);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok && cacheName) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('[SW] Network first strategy failed:', error);
    
    if (cacheName) {
      const cache = await caches.open(cacheName);
      const cachedResponse = await cache.match(request);
      
      if (cachedResponse) {
        console.log('[SW] Serving from cache after network failure:', request.url);
        return cachedResponse;
      }
    }
    
    throw error;
  }
}

// 背景更新快取
async function updateCacheInBackground(request, cache) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const headers = new Headers(networkResponse.headers);
      headers.append('sw-cache-time', new Date().toISOString());
      
      const responseToCache = new Response(networkResponse.body, {
        status: networkResponse.status,
        statusText: networkResponse.statusText,
        headers
      });
      
      cache.put(request, responseToCache);
      console.log('[SW] Cache updated in background:', request.url);
    }
  } catch (error) {
    console.error('[SW] Background cache update failed:', error);
  }
}

// 獲取 API 快取配置
function getCacheConfig(pathname) {
  for (const [_, config] of Object.entries(API_CACHE_CONFIG)) {
    if (config.patterns.some(pattern => pattern.test(pathname))) {
      return config;
    }
  }
  return null;
}

// 背景同步
self.addEventListener('sync', event => {
  console.log('[SW] Background sync event:', event.tag);
  
  if (event.tag === 'portfolio-sync') {
    event.waitUntil(syncPortfolioData());
  } else if (event.tag === 'analytics-sync') {
    event.waitUntil(syncAnalyticsData());
  }
});

// 同步投資組合數據
async function syncPortfolioData() {
  try {
    console.log('[SW] Syncing portfolio data');
    
    // 獲取待同步的數據
    const pendingData = await getStoredData('pending-portfolio-updates');
    
    if (pendingData && pendingData.length > 0) {
      for (const data of pendingData) {
        const response = await fetch('/api/portfolio/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data)
        });
        
        if (response.ok) {
          console.log('[SW] Portfolio data synced successfully');
        }
      }
      
      // 清除已同步的數據
      await clearStoredData('pending-portfolio-updates');
    }
    
  } catch (error) {
    console.error('[SW] Portfolio sync failed:', error);
  }
}

// 同步分析數據
async function syncAnalyticsData() {
  try {
    console.log('[SW] Syncing analytics data');
    
    const pendingAnalytics = await getStoredData('pending-analytics');
    
    if (pendingAnalytics && pendingAnalytics.length > 0) {
      const response = await fetch('/api/analytics/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(pendingAnalytics)
      });
      
      if (response.ok) {
        console.log('[SW] Analytics data synced successfully');
        await clearStoredData('pending-analytics');
      }
    }
    
  } catch (error) {
    console.error('[SW] Analytics sync failed:', error);
  }
}

// 推送通知
self.addEventListener('push', event => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: '您有新的交易提醒',
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'view',
        title: '查看詳情',
        icon: '/view-icon.png'
      },
      {
        action: 'close',
        title: '關閉',
        icon: '/close-icon.png'
      }
    ]
  };
  
  if (event.data) {
    try {
      const payload = event.data.json();
      options.body = payload.body || options.body;
      options.data = { ...options.data, ...payload.data };
    } catch (error) {
      console.error('[SW] Error parsing push payload:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('TradingAgents', options)
  );
});

// 通知點擊處理
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      self.clients.openWindow('/dashboard')
    );
  } else if (event.action === 'close') {
    // 僅關閉通知
    return;
  } else {
    // 預設行為：打開應用
    event.waitUntil(
      self.clients.openWindow('/')
    );
  }
});

// 訊息處理
self.addEventListener('message', event => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'CACHE_UPDATE') {
    // 手動更新快取
    event.waitUntil(updateCaches());
  } else if (event.data && event.data.type === 'CLEAR_CACHE') {
    // 清除快取
    event.waitUntil(clearAllCaches());
  }
});

// 更新快取
async function updateCaches() {
  try {
    console.log('[SW] Updating caches');
    
    const cache = await caches.open(STATIC_CACHE);
    await cache.addAll(STATIC_ASSETS);
    
    console.log('[SW] Caches updated successfully');
    
    // 通知所有客戶端
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'CACHE_UPDATED'
      });
    });
    
  } catch (error) {
    console.error('[SW] Cache update failed:', error);
  }
}

// 清除所有快取
async function clearAllCaches() {
  try {
    console.log('[SW] Clearing all caches');
    
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => caches.delete(cacheName))
    );
    
    console.log('[SW] All caches cleared');
    
  } catch (error) {
    console.error('[SW] Cache clearing failed:', error);
  }
}

// IndexedDB 輔助函數
async function getStoredData(key) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TradingAgentsDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['sync_data'], 'readonly');
      const store = transaction.objectStore('sync_data');
      const getRequest = store.get(key);
      
      getRequest.onsuccess = () => {
        resolve(getRequest.result ? getRequest.result.data : null);
      };
      
      getRequest.onerror = () => reject(getRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('sync_data')) {
        db.createObjectStore('sync_data', { keyPath: 'key' });
      }
    };
  });
}

async function clearStoredData(key) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TradingAgentsDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['sync_data'], 'readwrite');
      const store = transaction.objectStore('sync_data');
      const deleteRequest = store.delete(key);
      
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
  });
}

// 定期清理過期快取
setInterval(async () => {
  try {
    console.log('[SW] Cleaning expired caches');
    
    const cache = await caches.open(API_CACHE);
    const requests = await cache.keys();
    
    for (const request of requests) {
      const response = await cache.match(request);
      if (response) {
        const cacheTime = new Date(response.headers.get('sw-cache-time') || 0);
        const now = Date.now();
        
        // 檢查是否超過最大快取時間（24小時）
        if (now - cacheTime.getTime() > 24 * 60 * 60 * 1000) {
          await cache.delete(request);
          console.log('[SW] Deleted expired cache:', request.url);
        }
      }
    }
    
  } catch (error) {
    console.error('[SW] Cache cleanup failed:', error);
  }
}, 60 * 60 * 1000); // 每小時執行一次