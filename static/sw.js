// sw.js - Service Worker para PublicTrack PWA
// Versión 1.0

const CACHE_NAME = 'publictrack-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
  console.log('[Service Worker] Instalando...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Cacheando archivos');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[Service Worker] Instalación completa');
        return self.skipWaiting();
      })
      .catch(err => {
        console.error('[Service Worker] Error en instalación:', err);
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activando...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Limpiando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[Service Worker] Activación completa');
      return self.clients.claim();
    })
  );
});

// Interceptar peticiones
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Si encuentra en cache, lo devuelve
        if (response) {
          return response;
        }
        // Si no, hace la petición normal
        return fetch(event.request);
      })
      .catch(err => {
        console.error('[Service Worker] Error en fetch:', err);
      })
  );
});

console.log('[Service Worker] Archivo cargado');