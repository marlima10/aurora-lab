import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=process.argv[2],handlers={};
const context={self:{location:{origin:'https://portal.example.test'},addEventListener:(name,fn)=>{handlers[name]=fn}},URL};
vm.runInNewContext(fs.readFileSync(root+'/site/service-worker.js','utf8'),context);
for(const path of ['/','/index.html','/mirror/','/mirror/js/main.js','/auth/session']){
  let intercepted=false;handlers.fetch({request:{url:'https://portal.example.test'+path,method:'GET',mode:'navigate'},respondWith(){intercepted=true}});
  assert.equal(intercepted,false,'A navegação deve chegar ao navegador: '+path);
}
const manifest=JSON.parse(fs.readFileSync(root+'/site/manifest.json','utf8'));
assert.equal(manifest.start_url,'/mirror/');
const installer=fs.readFileSync(root+'/docker/server/mirror/install.mjs','utf8');
assert(installer.includes('<base href="/mirror/">'));
assert.equal(new URL('js/main.js','https://portal.example.test/mirror/').pathname,'/mirror/js/main.js');
console.log('PWA navigation preserves redirects, starts at /mirror/, and retains absolute asset base for older installed apps.');
