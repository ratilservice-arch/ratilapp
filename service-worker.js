'use strict';

const CACHE_NAME = 'ratilapp-pwa-v1';
const APP_SHELL = [
  './index.html',
  './main.html',
  './maintenance.html',
  './store.html',
  './offline.html',
  './manifest.webmanifest',
  './pwa.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png'
].map((path) => new URL(path, self.registration.scope).href);
const OFFLINE_URL = new URL('./offline.html', self.registration.scope).href;
const SCOPE_PATH = new URL(self.registration.scope).pathname;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith('ratilapp-pwa-') && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const requestUrl = new URL(request.url);
  if (requestUrl.origin !== self.location.origin || !requestUrl.pathname.startsWith(SCOPE_PATH)) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(async () => {
          const cache = await caches.open(CACHE_NAME);
          return (await cache.match(request)) || (await cache.match(OFFLINE_URL)) || Response.error();
        })
    );
    return;
  }

  const cachePromise = caches.open(CACHE_NAME);
  const cachedPromise = cachePromise.then((cache) => cache.match(request));
  const networkPromise = fetch(request).then((response) => {
    if (response.ok && response.type === 'basic') {
      const copy = response.clone();
      event.waitUntil(cachePromise.then((cache) => cache.put(request, copy)));
    }
    return response;
  });

  event.waitUntil(networkPromise.catch(() => undefined));
  event.respondWith(
    cachedPromise.then((cached) => cached || networkPromise)
      .catch(async () => (await cachedPromise) || Response.error())
  );
});
