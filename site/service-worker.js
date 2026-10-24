const CACHE_NAME='aurora-shell-20261024-v25';
const APP_SHELL=['/operations.js?v=20261024-v23','/aurora.js?v=20261024-v23','/power.css?v=20261024-v24','/power.js?v=20261024-v24','/aurora-layout.css?v=20261024-v25','/aurora-layout.js?v=20261024-v25','/','/aurora.css?v=20261007-2','/portal-health.css?v=20261007-1','/fitness.css?v=20261013-fitness-upgrades-1','/fitness.js?v=20261024-v24','/fitness-guided.js?v=20261024-v24','/fitness-planos.css?v=20261007-3','/fitness-planos.js?v=20261024-v24','/fitness-exercicios.css?v=20261007-2','/fitness-exercicios.js?v=20261024-v24','/fitness-plan-card.js?v=20261024-v24','/mobile-nav.js?v=20261007-1','/pwa.js?v=20261007-1','/manifest.json','/icons/app-192.png','/icons/app-512.png'];
async function installShell(){
  let urls=APP_SHELL;
  try{
    const response=await fetch('/auth/session',{cache:'no-store',credentials:'same-origin'});
    if(response.ok&&(response.headers.get('content-type')||'').includes('application/json')){
      const session=await response.json();
      if(!session.admin)urls=urls.filter(url=>!url.startsWith('/fitness'));
    }
  }catch(_){} // Preserve the standalone, non-SSO installation when discovery is unavailable.
  const cache=await caches.open(CACHE_NAME);
  await cache.addAll(urls.map(url=>new Request(url,{cache:'reload',redirect:'error',credentials:'same-origin'})));
}
self.addEventListener('install',event=>{event.waitUntil(installShell().then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('aurora-shell-')&&key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(url.pathname.startsWith('/auth/')||request.method!=='GET'||url.origin!==self.location.origin||url.pathname==='/fitness-api'||url.pathname==='/opengym'||url.pathname==='/opengym.html'||url.pathname==='/garmin'||['/manyfold','/mealie','/actual','/homeboard','/octoprint','/cockpit','/homeassistant','/camera-stream'].includes(url.pathname))return;
  if(request.mode==='navigate'){
    event.respondWith(fetch(request).then(response=>{if(response.ok&&!response.redirected){const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(request,copy))}return response}).catch(async()=>await caches.match(request)||await caches.match(url.pathname==='/fitness.html'?'/fitness.html':'/')));
    return;
  }
  if(/\.(?:css|js|svg|webmanifest)$/.test(url.pathname))event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{if(response.ok&&!response.redirected){const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(request,copy))}return response})));
});
