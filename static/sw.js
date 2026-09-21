const CACHE_NAME = "todo-v1";
const STATIC = ["/", "/static/css/style.css", "/static/js/app.js", "/static/manifest.json"];

self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(STATIC)));
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
    if (e.request.url.includes("/api/")) return;
    e.respondWith(
        caches.match(e.request).then((cached) => cached || fetch(e.request))
    );
});
