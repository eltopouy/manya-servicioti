const CACHE_NAME = 'manya-servicioti-v11.0-unified';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/css/styles.css?v=11.0',
  '/js/app.js?v=11.0',
  '/manifest.json',
  '/data/live_status.json',
  '/data/news_digest.json',
  '/data/instagram_feed.json',
  '/data/galleries.json',
  '/data/squad_2026.json',
  '/data/history_1891.json',
  '/data/escudos_uruguay.json',
  '/data/historial_activo.json',
  '/data/efemerides_hoy.json',
  '/data/rival_intelligence.json',
  '/data/influencers_feed.json',
  '/data/tatuajes_manya.json'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      for (const asset of CORE_ASSETS) {
        try {
          await cache.add(asset);
        } catch (_) {}
      }
    })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// ESTRATEGIA NETWORK-FIRST v11.0:
// Prioriza siempre los datos en vivo y activos frescos desde la red, con respaldo offline resiliente.
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || !event.request.url.startsWith('http')) return;

  event.respondWith(
    fetch(event.request)
      .then(res => {
        if (res && res.status === 200 && res.type === 'basic') {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return res;
      })
      .catch(async () => {
        const cached = await caches.match(event.request, { ignoreSearch: true });
        if (cached) return cached;
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
        return Response.error();
      })
  );
});
