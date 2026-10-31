const CACHE_NAME = 'manya-servicioti-v7.1-mobile-pts';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/css/styles.css',
  '/js/app.js',
  '/manifest.json',
  '/data/live_status.json',
  '/data/news_digest.json',
  '/data/instagram_feed.json',
  '/data/galleries.json',
  '/data/squad_2026.json',
  '/data/history_1891.json',
  '/data/escudos_uruguay.json',
  '/data/historial_activo.json',
  '/data/historial_wanderers.json',
  '/data/efemerides_hoy.json',
  '/data/rival_intelligence.json',
  '/data/blogger_pagina_historica.json'
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

// ESTRATEGIA NETWORK-FIRST:
// Prioriza siempre datos en vivo y código actualizado desde la red.
// Solo recurre a la caché local cuando el dispositivo se queda sin conexión (offline).
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  
  event.respondWith(
    fetch(event.request)
      .then(res => {
        if (res && res.status === 200) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(event.request, { ignoreSearch: true }))
  );
});
