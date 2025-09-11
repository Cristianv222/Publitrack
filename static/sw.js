// serviceworker.js - Service Worker para PublicTrack PWA con django-pwa
// Versión 2.0 - Mejorado para django-pwa

const CACHE_NAME = 'publictrack-v2';
const CACHE_STATIC_NAME = 'publictrack-static-v2';
const CACHE_DYNAMIC_NAME = 'publictrack-dynamic-v2';

// URLs esenciales para cachear
const urlsToCache = [
  '/',
  '/offline/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  // Bootstrap y librerías desde CDN
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://code.jquery.com/jquery-3.6.0.min.js'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
  console.log('[ServiceWorker] Instalando versión', CACHE_NAME);
  
  event.waitUntil(
    caches.open(CACHE_STATIC_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Pre-cacheando archivos esenciales');
        // Intentar cachear cada URL individualmente para evitar que un fallo cancele todo
        return Promise.all(
          urlsToCache.map(url => {
            return cache.add(url).catch(err => {
              console.warn(`[ServiceWorker] No se pudo cachear ${url}:`, err);
            });
          })
        );
      })
      .then(() => {
        console.log('[ServiceWorker] Instalación completa');
        return self.skipWaiting(); // Activa inmediatamente
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activando nueva versión');
  
  const cacheWhitelist = [CACHE_NAME, CACHE_STATIC_NAME, CACHE_DYNAMIC_NAME];
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('[ServiceWorker] Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[ServiceWorker] Activación completa');
      // Toma control inmediato de todos los clientes
      return self.clients.claim();
    })
  );
});

// Estrategias de cache para diferentes tipos de contenido
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // No intentar cachear peticiones POST, PUT, DELETE, etc.
  if (request.method !== 'GET') {
    return;
  }
  
  // Estrategia para archivos estáticos (Cache First)
  if (url.pathname.startsWith('/static/') || 
      url.pathname.startsWith('/media/') ||
      url.pathname.includes('.css') || 
      url.pathname.includes('.js') ||
      url.pathname.includes('.png') ||
      url.pathname.includes('.jpg') ||
      url.pathname.includes('.ico')) {
    
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            // Encontrado en cache, devolverlo
            return response;
          }
          // No está en cache, descargarlo
          return fetch(request).then(response => {
            // No cachear respuestas con error
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }
            
            // Clonar la respuesta para poder usarla y cachearla
            const responseToCache = response.clone();
            
            caches.open(CACHE_STATIC_NAME)
              .then(cache => {
                cache.put(request, responseToCache);
              });
            
            return response;
          });
        })
        .catch(() => {
          // Si falla, intentar devolver una imagen placeholder para imágenes
          if (request.destination === 'image') {
            return caches.match('/static/icons/icon-192x192.png');
          }
        })
    );
    return;
  }
  
  // Estrategia para API y páginas dinámicas (Network First)
  if (url.pathname.startsWith('/api/') || 
      url.pathname.startsWith('/auth/') ||
      url.pathname.startsWith('/admin/')) {
    
    event.respondWith(
      fetch(request)
        .then(response => {
          // Clonar la respuesta para cachearla
          const responseToCache = response.clone();
          
          caches.open(CACHE_DYNAMIC_NAME)
            .then(cache => {
              // Solo cachear respuestas exitosas
              if (response.status === 200) {
                cache.put(request, responseToCache);
              }
            });
          
          return response;
        })
        .catch(() => {
          // Si falla la red, buscar en cache
          return caches.match(request);
        })
    );
    return;
  }
  
  // Estrategia para el resto (documentos HTML) - Network First con fallback
  event.respondWith(
    fetch(request)
      .then(response => {
        // Solo cachear respuestas HTML exitosas
        if (response.status === 200 && response.headers.get('content-type')?.includes('text/html')) {
          const responseToCache = response.clone();
          
          caches.open(CACHE_DYNAMIC_NAME)
            .then(cache => {
              cache.put(request, responseToCache);
            });
        }
        
        return response;
      })
      .catch(() => {
        // Intentar encontrar en cache
        return caches.match(request)
          .then(response => {
            if (response) {
              return response;
            }
            
            // Si es una navegación y no hay cache, mostrar página offline
            if (request.mode === 'navigate') {
              return caches.match('/offline/').then(response => {
                if (response) {
                  return response;
                }
                // Si no hay página offline cacheada, crear una respuesta HTML básica
                return new Response(
                  `<!DOCTYPE html>
                  <html lang="es">
                  <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Sin Conexión - PublicTrack</title>
                    <style>
                      body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      }
                      .offline-container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        text-align: center;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                      }
                      h1 { color: #333; }
                      p { color: #666; }
                      button {
                        background: #1976d2;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        margin-top: 20px;
                      }
                    </style>
                  </head>
                  <body>
                    <div class="offline-container">
                      <h1>📡 Sin Conexión</h1>
                      <p>No hay conexión a Internet</p>
                      <p>PublicTrack necesita conexión para funcionar</p>
                      <button onclick="location.reload()">Reintentar</button>
                    </div>
                  </body>
                  </html>`,
                  {
                    headers: { 'Content-Type': 'text/html' }
                  }
                );
              });
            }
          });
      })
  );
});

// Manejo de mensajes del cliente
self.addEventListener('message', event => {
  console.log('[ServiceWorker] Mensaje recibido:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          console.log('[ServiceWorker] Limpiando cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('[ServiceWorker] Todo el cache ha sido limpiado');
    });
  }
});

// Sincronización en segundo plano (si el navegador lo soporta)
self.addEventListener('sync', event => {
  console.log('[ServiceWorker] Sincronización en segundo plano', event.tag);
  
  if (event.tag === 'sync-data') {
    event.waitUntil(
      // Aquí puedes agregar lógica para sincronizar datos cuando vuelva la conexión
      fetch('/api/sync/')
        .then(response => {
          console.log('[ServiceWorker] Datos sincronizados');
        })
        .catch(err => {
          console.error('[ServiceWorker] Error sincronizando:', err);
        })
    );
  }
});

// Notificaciones push (si las implementas en el futuro)
self.addEventListener('push', event => {
  console.log('[ServiceWorker] Push recibido');
  
  const title = 'PublicTrack';
  const options = {
    body: event.data ? event.data.text() : 'Nueva notificación',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver',
        icon: '/static/icons/icon-72x72.png'
      },
      {
        action: 'close',
        title: 'Cerrar',
        icon: '/static/icons/icon-72x72.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Click en notificación
self.addEventListener('notificationclick', event => {
  console.log('[ServiceWorker] Click en notificación');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    // Abrir la app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('[ServiceWorker] PublicTrack PWA Service Worker v2.0 cargado');