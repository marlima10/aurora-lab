const fs=require('node:fs'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const root=require('node:path').resolve(__dirname,'../static')+'/';
(async()=>{
 const dom=new JSDOM(fs.readFileSync(root+'index.html','utf8'),{url:'https://fixture.invalid/auth/admin',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,doc=w.document;let signed=true,calls=0,failUsers=false,failIssue=false,lastGrants=null;
 // jsdom does not implement the browser dialog top layer. Model only open/close.
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true};
 w.HTMLDialogElement.prototype.close=function(){this.open=false};
 const records=new Map([['aurora@server.local',{email:'aurora@server.local',enabled:true}]]);
 w.fetch=async(url,options={})=>{
  const data=options.body?JSON.parse(options.body):null;let status=200,value={};
  switch(new URL(url,w.location).pathname){
   case '/auth/session':status=signed?200:401;value={email:'aurora@server.local',admin:true,csrf:'fixture',grants:{}};break;
   case '/auth/users':status=failUsers?503:200;value=failUsers?{error:'fixture unavailable'}:{users:[...records.values()]};break;
   case '/auth/apps':value={adminOnly:['cockpit'],apps:Object.fromEntries(['manyfold','mealie','actual','opengym','octoprint','homeassistant','homeboard','cockpit'].map(app=>[app,[{identity:'fixture-identity',label:'Fixture'}]]))};break;
   case '/auth/issue':lastGrants=data.grants;if(failIssue||(data.email!=='aurora@server.local'&&data.grants?.cockpit)){status=403;value={error:'fixture registration rejected'};break;}calls++;records.set(data.email,{email:data.email,enabled:true});value={key:String.fromCharCode(65+calls).repeat(151)};break;
   case '/auth/delete':records.delete(data.email);break;
   case '/auth/logout':signed=false;break;
  }
  return {ok:status===200,status,json:async()=>value};
 };
 const tick=async()=>{for(let i=0;i<8;i++)await new Promise(setImmediate)};
 w.eval(fs.readFileSync(root+'app.js','utf8'));await tick();
 assert.equal(doc.querySelector('#user-count').textContent,'1');
 assert.ok(doc.querySelector('#admin').compareDocumentPosition(doc.querySelector('#account')) & w.Node.DOCUMENT_POSITION_FOLLOWING);
 assert.equal(doc.querySelector('#registration').open,false);
 failUsers=true;doc.querySelector('#refresh-users').click();await tick();assert.ok(doc.querySelector('#users-state').textContent.includes('Não foi possível'));assert.equal(doc.querySelector('#user-count').textContent,'1');
 failUsers=false,failIssue=false,lastGrants=null;doc.querySelector('#refresh-users').click();await tick();assert.equal(doc.querySelector('#users-state').textContent,'1 usuário cadastrado.');

 const form=doc.querySelector('#issue-form'),cockpit=doc.querySelector('input[data-app=cockpit]');
 form.elements.email.value='aurora@server.local';form.elements.email.dispatchEvent(new w.Event('input'));assert.equal(cockpit.disabled,false);cockpit.checked=true;cockpit.dispatchEvent(new w.Event('change'));
 form.elements.email.value='teste@example.invalid';form.elements.email.dispatchEvent(new w.Event('input'));assert.equal(cockpit.disabled,true);assert.equal(cockpit.checked,false);
 for(const check of doc.querySelectorAll('#permissions input')){if(!check.disabled){check.checked=true;check.dispatchEvent(new w.Event('change'));}}
 failIssue=true;form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();assert.equal(form.querySelector('button').disabled,true);
 form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();doc.querySelector('#confirm-yes').click();await tick();assert.equal(calls,0);assert.ok(doc.querySelector('#issue-status').textContent.includes('fixture registration rejected'));assert.equal(doc.querySelector('#issue-status').hidden,false);assert.equal(doc.querySelector('#generated').open,false);failIssue=false;

 form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();
 assert.ok(doc.querySelector('#confirm-dialog').open);assert.equal(calls,0);
 doc.querySelector('#confirm-yes').click();await tick();
 assert.ok(doc.querySelector('#generated').open);assert.equal(doc.querySelector('#new-key').value.length,151);assert.equal(doc.activeElement.id,'new-key');assert.equal(lastGrants.cockpit,undefined);assert.equal(Object.keys(lastGrants).length,7);
 doc.querySelector('#clear-key').click();assert.equal(doc.querySelector('#new-key').value,'');
 const button=text=>[...doc.querySelectorAll('#users button')].find(b=>b.textContent===text);
 button('Ver chave gerada').click();await tick();assert.ok(doc.querySelector('#generated').open);assert.equal(doc.querySelector('#new-key').value.length,151);doc.querySelector('#clear-key').click();
 button('Gerar nova chave').click();await tick();doc.querySelector('#confirm-no').click();await tick();assert.equal(calls,1);
 button('Gerar nova chave').click();await tick();doc.querySelector('#confirm-yes').click();await tick();assert.equal(calls,2);assert.ok(doc.querySelector('#generated').open);doc.querySelector('#clear-key').click();
 button('Excluir usuário').click();await tick();doc.querySelector('#confirm-no').click();await tick();assert.ok(records.has('teste@example.invalid'));
 button('Excluir usuário').click();await tick();doc.querySelector('#confirm-yes').click();await tick();assert.ok(!records.has('teste@example.invalid'));assert.equal(doc.querySelectorAll('#users button').length,0);
 doc.querySelector('#logout').click();await tick();assert.ok(doc.querySelector('#admin').hidden);assert.equal(doc.querySelector('#new-key').value,'');
 dom.window.close();console.log('13 DOM scenarios passed: permission policy, visible registration error, duplicate submit, top-list/count, retry/error, confirmation, key display/focus, reopen, cancel/renew, cancel/delete and logout.');
})().catch(e=>{console.error(e);process.exitCode=1});
