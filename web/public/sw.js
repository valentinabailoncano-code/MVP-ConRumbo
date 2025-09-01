const CACHE_NAME = 'conrumbo-v1';
const CRITICAL_PROTOCOLS = [
  '/api/conrumbo/protocol/pa_rcp_adulto_v1',
  '/api/conrumbo/protocol/pa_asfixia_adulto_v1',
  '/api/conrumbo/protocol/pa_hemorragias_v1'
];

const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Instalar Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Cache abierto');
        return cache.addAll(STATIC_ASSETS);
      })
  );
});

// Activar Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Interceptar requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Estrategia para protocolos críticos: Cache First
  if (CRITICAL_PROTOCOLS.some(protocol => url.pathname.includes(protocol))) {
    event.respondWith(
      caches.match(request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(request).then((response) => {
            if (response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(request, responseClone);
                });
            }
            return response;
          });
        })
        .catch(() => {
          // Fallback para protocolos críticos offline
          return new Response(JSON.stringify({
            error: 'Protocolo no disponible offline',
            fallback: true
          }), {
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }

  // Estrategia para assets estáticos: Cache First
  if (request.destination === 'script' || 
      request.destination === 'style' || 
      request.destination === 'image') {
    event.respondWith(
      caches.match(request)
        .then((response) => {
          return response || fetch(request);
        })
    );
    return;
  }

  // Estrategia para API: Network First
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(request, responseClone);
              });
          }
          return response;
        })
        .catch(() => {
          return caches.match(request)
            .then((response) => {
              if (response) {
                return response;
              }
              return new Response(JSON.stringify({
                error: 'Sin conexión',
                offline: true
              }), {
                headers: { 'Content-Type': 'application/json' }
              });
            });
        })
    );
    return;
  }

  // Estrategia por defecto: Network First con fallback a cache
  event.respondWith(
    fetch(request)
      .catch(() => {
        return caches.match(request);
      })
  );
});

