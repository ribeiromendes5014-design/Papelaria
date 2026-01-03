const STATIC_CACHE = "papelaria-static-v2";
const HTML_CACHE = "papelaria-html-v1";
const IMAGE_CACHE = "papelaria-img-v1";
const PRECACHE_URLS = ["/", "/catalogo/"];
const ASSETS = [
  "/static/manifest.json",
  "/static/img/icon.png",
  ...PRECACHE_URLS,
];

const cacheFirst = async (cacheName, request) => {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  cache.put(request, response.clone());
  return response;
};

const staleWhileRevalidate = async (cacheName, request) => {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response && response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);
  return cached || (await fetchPromise);
};

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener("activate", (event) => {
  const allow = [STATIC_CACHE, HTML_CACHE, IMAGE_CACHE];
  self.clients.claim();
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (!allow.includes(key)) {
            return caches.delete(key);
          }
          return null;
        })
      )
    )
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);

  if (url.origin === self.location.origin && PRECACHE_URLS.includes(url.pathname)) {
    event.respondWith(staleWhileRevalidate(HTML_CACHE, request));
    return;
  }

  if (request.url.includes("/static/")) {
    event.respondWith(cacheFirst(STATIC_CACHE, request));
    return;
  }

  if (request.destination === "image" || request.url.includes("/media/") || request.url.includes(".jpg")) {
    event.respondWith(staleWhileRevalidate(IMAGE_CACHE, request));
    return;
  }
});
