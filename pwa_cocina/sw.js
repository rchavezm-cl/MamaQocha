// ==============================================================================
// SERVICE WORKER - MAMÁ QOCHA TERMINAL COCINA
// Estrategia: Cache-First para UI (Garantiza apertura sin conexión)
// ==============================================================================

const CACHE_NAME = 'mamaqocha-cocina-v1';
const ASSETS_TO_CACHE = [
  '/cocina/',
  '/cocina/index.html',
  '/cocina/app.js',
  '/cocina/manifest.json',
  'https://cdn.jsdelivr.net/npm/dexie@3.2.4/dist/dexie.min.js',
  'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css'
];

// Instalación: Precarga de la interfaz en disco local del navegador
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Precargando activos estáticos de Cocina...');
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('[SW] Aviso al cachear recursos externos:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activación: Limpieza de versiones antiguas
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

  // No interceptar peticiones de sincronización POST (se manejan vía Outbox en app.js)
  if (event.request.method !== 'GET') {
    return;
  }

  // Para navegación y recursos estáticos: Cache-First con fallback de red
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // En segundo plano busca si hay una versión más nueva en red (Stale-While-Revalidate)
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
          }
        }).catch(() => {/* Offline, ignorar */});

        return cachedResponse;
      }

      // Si no estaba en caché, intenta obtenerlo de red
      return fetch(event.request).catch(() => {
        // Si falló y es la página principal, retornar index.html
        if (event.request.mode === 'navigate') {
          return caches.match('/cocina/index.html');
        }
      });
    })
  );
});
