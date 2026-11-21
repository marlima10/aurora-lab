(() => {
 'use strict';
 const $=id=>document.getElementById(id);let session=null,lastReply='',recorder=null,recordTimer=null,audioURL=null;
 const status=(message,error=false)=>{$('status').textContent=message;$('status').classList.toggle('error',error)};
 async function request(path,data){
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),170000);
   try{
     const r=await fetch('/jarvis/api/'+path,{method:data?'POST':'GET',credentials:'same-origin',cache:'no-store',signal:controller.signal,
       headers:data?{'Content-Type':'application/json','X-Aurora-CSRF':session?.csrf||''}:{},body:data?JSON.stringify(data):undefined});
     if(r.status===401){status('Sua sessão expirou. Entre novamente pelo portal.',true);throw Error('Autenticação necessária.');}
     const result=await r.json();if(!r.ok)throw Error(result.error||'Não foi possível concluir.');return result;
   }catch(e){if(e.name==='AbortError')throw Error('O serviço demorou para responder. Confira o histórico antes de repetir.');throw e}
   finally{clearTimeout(timer)}
 }
 function item(parent,content){const el=document.createElement('div');el.className='item';el.textContent=content;parent.append(el);return el}
 const toolNames={note_save:'Salvar nota',report_save:'Salvar relatório',reminder_create:'Agendar lembrete',finance_add_transaction:'Registrar lançamento',food_add_recipe:'Criar receita',print_pause:'Pausar impressão'};
 function details(p){const a=p.args||{},preview=p.preview||{};if(p.tool==='finance_add_transaction')return ['Conta: '+(preview.account||a.accountId),'Categoria: '+(preview.category||'Sem categoria'),'Data: '+a.date,(a.amount<0?'Despesa: ':'Receita: ')+(Math.abs(a.amount)/100).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+' na moeda do orçamento','Favorecido: '+a.payee,a.notes?'Observação: '+a.notes:''].filter(Boolean).join('\n');if(p.tool==='reminder_create')return a.content+'\n'+new Date(a.due).toLocaleString('pt-BR');if(p.tool==='print_pause')return 'Pausar: '+(preview.file||'impressão atual');return a.content||a.name||'';}
 function download(content){const blob=new Blob([content],{type:'text/markdown;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='relatorio-jarvis.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 async function history(){
   const data=await request('history');$('messages').replaceChildren();
   for(const m of data.messages){const el=item($('messages'),''),label=document.createElement('b'),body=document.createElement('span');label.textContent=m.role==='user'?'VOCÊ':'JARVIS';body.textContent=m.content;el.className='message';el.append(label,body);if(m.role==='assistant')lastReply=m.content}
   $('speak').disabled=!lastReply;$('notes').replaceChildren();for(const n of data.notes){const el=item($('notes'),n.content),button=document.createElement('button');button.type='button';button.className='secondary';button.textContent='Baixar Markdown';button.onclick=()=>download(n.content);el.append(document.createElement('br'),button)}
   $('reminders').replaceChildren();for(const r of data.reminders)item($('reminders'),(r.delivered?'Disponível na caixa · ':'Agendado · ')+new Date(r.due*1000).toLocaleString('pt-BR')+'\n'+r.content);
   $('proposals').replaceChildren();if(!data.proposals.length)item($('proposals'),'Nenhuma ação pendente.');
   for(const p of data.proposals){const el=item($('proposals'),(toolNames[p.tool]||'Ação')+'\n'+details(p)),button=document.createElement('button');button.type='button';button.textContent='Revisar e confirmar';button.onclick=()=>confirmProposal(p,button);el.append(document.createElement('br'),button)}
 }
 async function confirmProposal(p,button){
   $('confirm-details').textContent=(toolNames[p.tool]||'Ação')+'\n'+details(p);$('confirm').returnValue='';$('confirm').showModal();
   const choice=await new Promise(resolve=>$('confirm').addEventListener('close',()=>resolve($('confirm').returnValue),{once:true}));if(choice!=='confirm')return;
   button.disabled=true;try{const result=await request('confirm',{proposal_id:p.id});status(result.saved?'Operação concluída e confirmada pelo serviço.':'Resultado: '+JSON.stringify(result));await history()}catch(e){status(e.message,true);await history().catch(()=>{})}finally{button.disabled=false}
 }
 $('chat').onsubmit=async e=>{
   e.preventDefault();if($('send').disabled)return;$('send').disabled=true;status('Jarvis está preparando a resposta…');
   try{const job=await request('chat',{message:$('message').value,allow_web_search:$('allow-web').checked});$('message').value='';let done=false;
     for(let i=0;i<360;i++){await new Promise(r=>setTimeout(r,2500));const state=await request('jobs/'+job.job_id);if(state.status==='error')throw Error(state.error);if(state.status==='done'){done=true;break}}
     if(!done)throw Error('A resposta ainda não terminou. Consulte o histórico antes de repetir.');await history();status('Resposta pronta.');$('messages').scrollTop=$('messages').scrollHeight;
   }catch(error){status(error.message,true)}finally{$('send').disabled=false}
 };
 document.querySelectorAll('[data-prompt]').forEach(button=>button.onclick=()=>{$('message').value=button.dataset.prompt;$('message').focus()});
 $('note-form').onsubmit=async e=>{e.preventDefault();try{await request('tool',{tool:'note_save',args:{content:$('note').value}});$('note').value='';await history();status('Revise a nota e confirme para salvar.')}catch(e){status(e.message,true)}};
 $('reminder-form').onsubmit=async e=>{e.preventDefault();try{const due=new Date($('due').value);if(!Number.isFinite(due.getTime()))throw Error('Escolha uma data válida.');await request('tool',{tool:'reminder_create',args:{content:$('reminder').value,due:due.toISOString()}});await history();status('Revise o lembrete e confirme.')}catch(e){status(e.message,true)}};
 $('speak').onclick=async()=>{ $('speak').disabled=true;try{status('Preparando áudio local…');const r=await request('speak',{text:lastReply.slice(0,2500)});const bytes=Uint8Array.from(atob(r.audio),c=>c.charCodeAt(0));if(audioURL)URL.revokeObjectURL(audioURL);audioURL=URL.createObjectURL(new Blob([bytes],{type:r.mime}));$('player').src=audioURL;$('player').hidden=false;await $('player').play().catch(()=>status('Áudio pronto. Toque no player para ouvir.'));status('Áudio pronto.')}catch(e){status(e.message,true)}finally{$('speak').disabled=false}};
 $('record').onclick=async()=>{
   if(recorder?.state==='recording'){recorder.stop();return}
   if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){status('Este navegador não oferece gravação. Use texto.',true);return}
   let stream;
   try{stream=await navigator.mediaDevices.getUserMedia({audio:true});const choices=['audio/mp4','audio/webm;codecs=opus','audio/webm'];const type=choices.find(t=>MediaRecorder.isTypeSupported(t));recorder=type?new MediaRecorder(stream,{mimeType:type}):new MediaRecorder(stream);const chunks=[];
     recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
     recorder.onstop=async()=>{clearTimeout(recordTimer);stream.getTracks().forEach(t=>t.stop());$('record').textContent='🎙 Gravar voz';$('record').disabled=true;
       try{const blob=new Blob(chunks,{type:recorder.mimeType});if(blob.size>8*1024*1024)throw Error('Áudio acima de 8 MiB.');const bytes=new Uint8Array(await blob.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));status('Transcrevendo no servidor…');const result=await request('transcribe',{audio:btoa(binary)});$('message').value=result.text;status('Revise a transcrição e toque em Enviar.')}catch(e){status(e.message,true)}finally{$('record').disabled=false;recorder=null}};
     recorder.start();$('record').textContent='⏹ Parar gravação';status('Gravando…');recordTimer=setTimeout(()=>{if(recorder?.state==='recording')recorder.stop()},85000);
   }catch(e){stream?.getTracks().forEach(t=>t.stop());status('Não foi possível gravar. Verifique a permissão do microfone no Safari.',true)}
 };
 setInterval(()=>{if(session&&!document.hidden&&!$('send').disabled&&!$('confirm').open)history().catch(()=>{})},30000);
 window.addEventListener('pagehide',()=>{if(recorder?.state==='recording')recorder.stop();if(audioURL)URL.revokeObjectURL(audioURL)});
 (async()=>{try{session=await request('status');$('identity').textContent=session.email;$('model').textContent='IA local · Dados processados no AuroraServer';await history();status('Pronto para conversar.')}catch(e){status(e.message,true)}})();
})();
