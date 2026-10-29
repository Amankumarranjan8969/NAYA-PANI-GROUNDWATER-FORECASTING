/* Naya Pani — Progressive Web App Service Worker */
const CACHE_NAME = 'naya-pani-pwa-v4';
const ASSETS_TO_CACHE = [
  '/',
  '/nayapani_manifest.json?v=4',
  '/nayapani-icon-192.png?v=4',
  '/nayapani-icon-512.png?v=4',
  '/favicon.ico?v=4',
];

const OFFLINE_FALLBACK_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Naya Pani — Offline</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #F5F5F7; color: #1D1D1F; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 24px; }
    .card { background: #FFFFFF; border-radius: 18px; padding: 32px; max-width: 420px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.08); }
    img { width: 72px; height: 72px; border-radius: 14px; margin-bottom: 16px; object-fit: contain; }
    h1 { font-size: 20px; margin: 0 0 8px; }
    p { font-size: 14px; color: #6E6E73; line-height: 1.5; margin: 0 0 20px; }
    button { background: #0071E3; color: #FFFFFF; border: none; border-radius: 10px; padding: 10px 20px; font-weight: 600; cursor: pointer; }
  </style>
</head>
<body>
  <div class="card">
    <img src="/nayapani-icon-192.png?v=4" alt="Naya Pani">
    <h1>Naya Pani is Offline</h1>
    <p>Your device is currently disconnected from the network. Reconnect to sync live Rajasthan groundwater telemetry and model forecasts.</p>
    <button onclick="window.location.reload()">Retry Connection</button>
  </div>
</body>
</html>`;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Never cache non-GET requests, WebSocket/Streamlit state streams, API keys, or admin routes
  if (
    req.method !== 'GET' ||
    url.searchParams.has('api_key') ||
    url.searchParams.get('page') === 'admin' ||
    url.pathname.includes('/_stcore/') ||
    url.pathname.includes('/admin')
  ) {
    return;
  }

  // Network-first so fresh icons, manifests, and app shell always load when online, falling back to cache offline
  event.respondWith(
    fetch(req)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(req, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(req).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          if (req.mode === 'navigate') {
            return new Response(OFFLINE_FALLBACK_HTML, {
              headers: { 'Content-Type': 'text/html; charset=utf-8' },
            });
          }
          return Response.error();
        });
      })
  );
});
