{% load static %}/*
 * Kolê Service Worker
 * Stratégies :
 *   - Pages HTML : network-first avec fallback offline
 *   - Ressources statiques (CSS/JS/images/polices) : stale-while-revalidate
 *   - API/POST : toujours online (bypass)
 */

const VERSION = 'kwalok-v7';
const STATIC_CACHE = `static-${VERSION}`;
const PAGES_CACHE = `pages-${VERSION}`;
const RUNTIME_CACHE = `runtime-${VERSION}`;
const OFFLINE_URL = '/hors-ligne/';

const PRECACHE_URLS = [
  OFFLINE_URL,
  '{% static "css/style.css" %}',
  '{% static "images/logo-kwalokwakole.png" %}',
  '{% static "images/icons/icon-192.png" %}',
  '{% static "images/icons/icon-512.png" %}',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => ![STATIC_CACHE, PAGES_CACHE, RUNTIME_CACHE].includes(key))
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

function isHtmlRequest(request) {
  if (request.mode === 'navigate') return true;
  const accept = request.headers.get('accept') || '';
  return accept.includes('text/html');
}

function isStaticAsset(url) {
  return (
    url.pathname.startsWith('/static/') ||
    url.pathname.startsWith('/media/') ||
    /\.(?:css|js|woff2?|ttf|eot|svg|png|jpg|jpeg|webp|gif|ico)$/.test(url.pathname)
  );
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (
    url.pathname.startsWith('/admin/') ||
    url.pathname.startsWith('/paiement/') ||
    url.pathname.startsWith('/compte/') ||
    url.pathname.startsWith('/social/') ||
    url.pathname.includes('csrf')
  ) {
    return;
  }

  if (isHtmlRequest(request)) {
    event.respondWith(networkFirstHtml(request));
    return;
  }

  if (isStaticAsset(url)) {
    event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE));
  }
});

async function networkFirstHtml(request) {
  try {
    const response = await fetch(request);
    const copy = response.clone();
    caches.open(PAGES_CACHE).then((cache) => cache.put(request, copy)).catch(() => {});
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    const offline = await caches.match(OFFLINE_URL);
    return offline || new Response('Hors ligne', { status: 503, statusText: 'Offline' });
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkFetch = fetch(request)
    .then((response) => {
      if (response && response.ok) {
        cache.put(request, response.clone()).catch(() => {});
      }
      return response;
    })
    .catch(() => cached);
  return cached || networkFetch;
}

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
