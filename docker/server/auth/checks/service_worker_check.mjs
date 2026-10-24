import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync(new URL('../../../../site/service-worker.js',import.meta.url),'utf8');
function fixture(session,response={ok:true,redirected:false,clone(){return this;}}){
  const events={},added=[],writes=[];
  const cache={async addAll(requests){added.push(...requests)},async put(...args){writes.push(args)}};
  const ctx=vm.createContext({URL,Request:class extends Request{constructor(url,options){super(new URL(url,'https://fixture.local'),options)}},fetch:async(url)=>url==='/auth/session'?session:response,
    caches:{open:async()=>cache,match:async()=>undefined},
    self:{location:{origin:'https://fixture.local'},addEventListener:(name,handler)=>events[name]=handler}});
  vm.runInContext(source,ctx);return {ctx,events,added,writes};
}
const session=admin=>({ok:true,headers:new Headers({'content-type':'application/json'}),json:async()=>({admin})});
for(const admin of [false,true]){
  const f=fixture(session(admin));await vm.runInContext('installShell()',f.ctx);
  assert.equal(f.added.some(r=>new URL(r.url).pathname.startsWith('/fitness')),admin);
  assert.ok(f.added.every(r=>r.redirect==='error'&&r.credentials==='same-origin'));
}
const standalone=fixture({ok:false,headers:new Headers()});await vm.runInContext('installShell()',standalone.ctx);
assert.ok(standalone.added.some(r=>new URL(r.url).pathname.startsWith('/fitness')));
for(const mode of ['navigate','cors']){
  const f=fixture(session(false),{ok:true,redirected:true,clone(){throw Error('redirect must not be cached')}});
  let pending;f.events.fetch({request:{method:'GET',url:'https://fixture.local/'+(mode==='navigate'?'':'aurora.js'),mode},respondWith(p){pending=p}});
  await pending;assert.equal(f.writes.length,0);
}
const f=fixture(session(false));f.events.fetch({request:{method:'GET',url:'https://fixture.local/auth/admin',mode:'navigate'},respondWith(){throw Error('auth must bypass service worker')}});
console.log('6 PWA scenarios passed: roles, standalone, redirects and authentication bypass.');
