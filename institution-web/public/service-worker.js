/**
 * Service Worker
 * Handles offline caching and background sync
 */

const CACHE_NAME = 'assisi-social-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/offline.html',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );

  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');

  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
          .map((key) => caches.delete(key))
      );
    })
  );

  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and non-HTTP schemes (like chrome-extension://)
  if (request.method !== 'GET' || !request.url.startsWith('http')) {
    return;
  }

  // Skip API calls (let them go to network)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() => {
        return new Response(
          JSON.stringify({ error: 'Offline' }),
          {
            headers: { 'Content-Type': 'application/json' },
            status: 503,
          }
        );
      })
    );
    return;
  }

  // Network-first for HTML pages
  if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone and cache the response
          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cachedResponse) => {
            return cachedResponse || caches.match('/offline.html');
          });
        })
    );
    return;
  }

  // Cache-first for other assets
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(request).then((response) => {
        // Clone and cache the response
        const responseClone = response.clone();
        caches.open(DYNAMIC_CACHE).then((cache) => {
          cache.put(request, responseClone);
        });
        return response;
      });
    })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-reservations') {
    event.waitUntil(syncReservations());
  }
});

async function syncReservations() {
  // Sync logic would go here
  console.log('[SW] Syncing reservations...');
}

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};

  const options = {
    body: data.body || 'New notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: data.actions || [],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Hotel PMS', options)
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/')
  );
});
