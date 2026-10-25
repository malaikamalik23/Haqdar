const CACHE = "haqdar-shell-v4";
const SHELL = [
  "./", "index.html", "ask.html", "notice.html", "about.html",
  "style.css", "site.js", "app.js", "manifest.json",
  "logo.svg", "logo-light.svg", "logo-stacked.svg", "hero.svg", "spot-ask.svg", "spot-notice.svg", "icon.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // Only same-origin GET requests: API calls go to another origin and are never cached,
  // so no question, document or answer is ever stored by the service worker.
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});