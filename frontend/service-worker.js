const CACHE_NAME = "vanaly-v6"; // 버전 올려서 구 캐시 강제 삭제
const STATIC_ASSETS = [
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting(); // 즉시 activate
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // API 요청 + HTML + JS — 항상 네트워크 우선 (캐시 안 함)
  if (
    url.pathname.startsWith("/health") ||
    url.pathname.startsWith("/users") ||
    url.pathname.startsWith("/meals") ||
    url.pathname.endsWith(".html") ||
    url.pathname.endsWith(".js") ||
    url.pathname === "/"
  ) {
    return; // 브라우저 기본 네트워크 요청으로 위임
  }

  // 정적 에셋만 캐시 사용
  event.respondWith(
    caches.match(event.request).then((cached) => cached ?? fetch(event.request))
  );
});
