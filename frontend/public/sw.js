// PWA shell cache only: NEVER cache API requests, photos, agent outputs, or private data.
const CACHE='vigiloforge-shell-v1';
const SHELL=['/','/offline','/icon.svg','/manifest.webmanifest'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET'||new URL(request.url).origin!==self.location.origin||request.url.includes('/api/')) return;
  if(request.mode==='navigate') {
    event.respondWith(fetch(request).catch(async()=>await caches.match(request)||await caches.match('/offline')));
    return;
  }
  if(SHELL.some(path=>new URL(request.url).pathname===path)) event.respondWith(caches.match(request).then(r=>r||fetch(request)));
});
