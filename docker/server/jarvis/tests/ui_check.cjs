const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const {JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'../static');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const code=fs.readFileSync(path.join(root,'app.js'),'utf8');
const pending=[];let saved=false,checks=0;
const dom=new JSDOM(html,{url:'https://fixture.invalid/jarvis/',runScripts:'outside-only'});
const w=dom.window;
w.HTMLDialogElement.prototype.showModal=function(){this.open=true};
w.HTMLDialogElement.prototype.close=function(value){this.returnValue=value;this.open=false;this.dispatchEvent(new w.Event('close'))};
w.fetch=async(url,options={})=>{
 const endpoint=url.split('/').pop();const data=options.body?JSON.parse(options.body):{};
 let result;
 if(endpoint==='status')result={email:'fixture@example.invalid',csrf:'fixture-only',provider:'Local',model:'fixture'};
 else if(endpoint==='history')result={messages:[{role:'assistant',content:'<img src=x onerror=alert(1)>'}],notes:saved?[{content:'Nota fictícia'}]:[],reminders:[],proposals:pending};
 else if(endpoint==='tool'){assert.equal(options.headers['X-Aurora-CSRF'],'fixture-only');assert.equal(data.tool,'note_save');pending.push({id:'fixture-proposal',tool:data.tool,args:data.args});result={confirmation_required:true};}
 else if(endpoint==='confirm'){assert.equal(data.proposal_id,'fixture-proposal');pending.length=0;saved=true;result={saved:true};}
 else throw Error('Unexpected fixture route');
 return {ok:true,status:200,json:async()=>result};
};
w.eval(code);
const tick=()=>new Promise(r=>setTimeout(r,15));
(async()=>{
 await tick();assert.equal(w.document.querySelector('#identity').textContent,'fixture@example.invalid');checks++;
 assert.equal(w.document.querySelector('#messages img'),null);assert.match(w.document.querySelector('#messages').textContent,/<img/);checks++;
 w.document.querySelector('#note').value='Nota fictícia';w.document.querySelector('#note-form').dispatchEvent(new w.Event('submit',{cancelable:true}));await tick();
 assert.equal(saved,false);assert.equal(pending.length,1);checks++;
 w.document.querySelector('#proposals button').click();await tick();assert.equal(w.document.querySelector('#confirm').open,true);checks++;
 w.document.querySelector('#confirm').close('cancel');await tick();assert.equal(saved,false);checks++;
 w.document.querySelector('#proposals button').click();await tick();w.document.querySelector('#confirm').close('confirm');await tick();
 assert.equal(saved,true);assert.match(w.document.querySelector('#notes').textContent,/Nota fictícia/);assert.equal(pending.length,0);checks++;
 assert.equal(w.document.querySelector('#allow-web').checked,false);checks++;
 console.log(checks+' DOM checks passed with fictitious data.');dom.window.close();
})().catch(e=>{console.error(e);process.exitCode=1;dom.window.close()});
