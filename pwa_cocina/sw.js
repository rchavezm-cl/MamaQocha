// ==============================================================================
// SERVICE WORKER - MAMÁ QOCHA TERMINAL COCINA
// Estrategia: Network-First para activos HTML/JS (siempre actualizado online)
//             con Cache-Fallback automático para apertura 100% offline.
// ==============================================================================

const CACHE_NAME = 'mamaqocha-cocina-v3';
const ASSETS_TO_CACHE = [
  '/cocina/',
  '/cocina/index.html',
  '/cocina/app.js?v=3',
  '/cocina/manifest.json',
  'https://cdn.jsdelivr.net/npm/dexie@3.2.4/dist/dexie.min.js',
  'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css'
];

// Instalación: Precarga de la interfaz en disco local del navegador
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW v3] Precargando activos estáticos de Cocina...');
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('[SW] Aviso al cachear recursos externos:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activación: Limpieza inmediata de versiones antiguas
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Purgando caché obsoleta:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Intercepción de peticiones de red
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. No interceptar peticiones POST ni llamadas dinámicas a la API (/api/)
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return;
  }

  // 2. Estrategia Network-First con fallback inmediato a caché en offline
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request, { ignoreSearch: true }).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          if (event.request.mode === 'navigate') {
            return caches.match('/cocina/index.html', { ignoreSearch: true });
          }
        });
      })
  );
});
