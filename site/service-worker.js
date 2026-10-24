const CACHE_NAME='aurora-shell-20261024-v22';
const APP_SHELL=['/operations.js?v=20261024-v22','/aurora.js?v=20261020-v16','/power.css?v=20261024-v22','/power.js?v=20261024-v22','/aurora-layout.css?v=20261007-1','/aurora-layout.js?v=20261020-v16','/','/aurora.css?v=20261007-2','/portal-health.css?v=20261007-1','/fitness.css?v=20261013-fitness-upgrades-1','/fitness.js?v=20261020-v16','/fitness-guided.js?v=20261013-fitness-upgrades-1','/fitness-planos.css?v=20261007-3','/fitness-planos.js?v=20261007-3','/fitness-exercicios.css?v=20261007-2','/fitness-exercicios.js?v=20261007-1','/fitness-plan-card.js?v=20261013-fitness-upgrades-1','/mobile-nav.js?v=20261007-1','/pwa.js?v=20261007-1','/manifest.json','/icons/app-192.png','/icons/app-512.png'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('aurora-shell-')&&key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin||url.pathname==='/fitness-api'||url.pathname==='/opengym'||url.pathname==='/opengym.html'||url.pathname==='/garmin'||['/homeboard','/octoprint','/cockpit','/homeassistant','/camera-stream'].includes(url.pathname))return;
  if(request.mode==='navigate'){
    event.respondWith(fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(request,copy))}return response}).catch(async()=>await caches.match(request)||await caches.match(url.pathname==='/fitness.html'?'/fitness.html':'/')));
    return;
  }
  if(/\.(?:css|js|svg|webmanifest)$/.test(url.pathname))event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(request,copy))}return response})));
});
