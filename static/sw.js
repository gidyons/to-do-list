const CACHE_NAME = "todo-v2";
const STATIC = [
    "/",
    "/static/css/style.css",
    "/static/js/app.js",
    "/static/manifest.json",
    "/static/img/icon-192.svg",
    "/static/img/icon-512.svg",
];

self.addEventListener("install", (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((c) => c.addAll(STATIC)).catch(() => {})
    );
    self.skipWaiting();
});

self.addEventListener("activate", (e) => {
    e.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", (e) => {
    const url = new URL(e.request.url);
    // Don't cache API calls
    if (url.pathname.startsWith("/api/")) return;
    // Don't cache POST/PUT/DELETE
    if (e.request.method !== "GET") return;
    e.respondWith(
        caches.match(e.request).then((cached) => cached || fetch(e.request))
    );
});
