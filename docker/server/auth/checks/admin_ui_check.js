const fs=require('node:fs'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const root=require('node:path').resolve(__dirname,'../static')+'/';
(async()=>{
 const dom=new JSDOM(fs.readFileSync(root+'index.html','utf8'),{url:'https://fixture.invalid/auth/admin',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,doc=w.document;let signed=true,calls=0;
 // jsdom does not implement the browser dialog top layer. Model only open/close.
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true};
 w.HTMLDialogElement.prototype.close=function(){this.open=false};
 const records=new Map([['aurora@server.local',{email:'aurora@server.local',enabled:true}]]);
 w.fetch=async(url,options={})=>{
  const data=options.body?JSON.parse(options.body):null;let status=200,value={};
  switch(new URL(url,w.location).pathname){
   case '/auth/session':status=signed?200:401;value={email:'aurora@server.local',admin:true,csrf:'fixture',grants:{}};break;
   case '/auth/users':value={users:[...records.values()]};break;
   case '/auth/apps':value={apps:{}};break;
   case '/auth/issue':calls++;records.set(data.email,{email:data.email,enabled:true});value={key:String.fromCharCode(65+calls).repeat(151)};break;
   case '/auth/delete':records.delete(data.email);break;
   case '/auth/logout':signed=false;break;
  }
  return {ok:status===200,status,json:async()=>value};
 };
 const tick=async()=>{for(let i=0;i<8;i++)await new Promise(setImmediate)};
 w.eval(fs.readFileSync(root+'app.js','utf8'));await tick();
 const form=doc.querySelector('#issue-form');form.elements.email.value='teste@example.invalid';
 form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();
 assert.ok(doc.querySelector('#confirm-dialog').open);assert.equal(calls,0);
 doc.querySelector('#confirm-yes').click();await tick();
 assert.ok(doc.querySelector('#generated').open);assert.equal(doc.querySelector('#new-key').value.length,151);assert.equal(doc.activeElement.id,'new-key');
 doc.querySelector('#clear-key').click();assert.equal(doc.querySelector('#new-key').value,'');
 const button=text=>[...doc.querySelectorAll('#users button')].find(b=>b.textContent===text);
 button('Ver chave gerada').click();await tick();assert.ok(doc.querySelector('#generated').open);assert.equal(doc.querySelector('#new-key').value.length,151);doc.querySelector('#clear-key').click();
 button('Gerar nova chave').click();await tick();doc.querySelector('#confirm-no').click();await tick();assert.equal(calls,1);
 button('Gerar nova chave').click();await tick();doc.querySelector('#confirm-yes').click();await tick();assert.equal(calls,2);assert.ok(doc.querySelector('#generated').open);doc.querySelector('#clear-key').click();
 button('Excluir usuário').click();await tick();doc.querySelector('#confirm-no').click();await tick();assert.ok(records.has('teste@example.invalid'));
 button('Excluir usuário').click();await tick();doc.querySelector('#confirm-yes').click();await tick();assert.ok(!records.has('teste@example.invalid'));assert.equal(doc.querySelectorAll('#users button').length,0);
 doc.querySelector('#logout').click();await tick();assert.ok(doc.querySelector('#admin').hidden);assert.equal(doc.querySelector('#new-key').value,'');
 dom.window.close();console.log('8 DOM scenarios passed: confirmation, key display/focus, reopen, cancel/renew, cancel/delete and logout.');
})().catch(e=>{console.error(e);process.exitCode=1});
