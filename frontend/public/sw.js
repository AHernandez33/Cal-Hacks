// Cache public app assets only. API responses, photos, and tokens are never cached.
const CACHE = "vigiloforge-shell-v8";
const SHELL = [
  "/",
  "/offline",
  "/field",
  "/icon.svg",
  "/icon-192.png",
  "/icon-512.png",
  "/manifest.webmanifest",
];
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting()),
  );
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k.startsWith("vigiloforge-shell-") && k !== CACHE)
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});
self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (
    request.method !== "GET" ||
    url.origin !== self.location.origin ||
    request.headers.has("Authorization")
  )
    return;
  if (
    request.mode === "navigate" &&
    ["/", "/offline", "/field"].includes(url.pathname)
  ) {
    event.respondWith(
      fetch(request).catch(
        async () =>
          (await caches.match(url.pathname)) ||
          (await caches.match("/offline")),
      ),
    );
    return;
  }
  if (
    !url.pathname.startsWith("/_next/static/") &&
    !SHELL.includes(url.pathname)
  )
    return;
  // Ignore React server-component requests; only HTML navigations and static assets belong here.
  if (request.headers.has("RSC")) return;
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(request);
      if (cached) return cached;
      const response = await fetch(request);
      if (response.ok && response.type === "basic")
        await cache.put(request, response.clone());
      return response;
    }),
  );
});
