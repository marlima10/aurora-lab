(() => {
  'use strict';
  const list=document.getElementById('serverAlerts'),history=document.getElementById('serverAlertHistory'),summary=document.getElementById('serverAlertSummary');
  const stamp=t=>new Date(t).toLocaleString('pt-BR');
  async function refresh(){
    if(document.hidden)return;
    try{
      const response=await fetch('/api/alerts.json',{cache:'no-store',signal:AbortSignal.timeout(8000)});if(!response.ok)throw Error();const data=await response.json();
      summary.textContent=data.active.length ? data.active.length+' alerta(s) ativo(s)' : 'Nenhum alerta ativo';summary.dataset.state=data.active.length?'warning':'ok';
      list.replaceChildren();for(const item of data.active){const p=document.createElement('p');p.className='server-alert';p.dataset.level=item.level;p.textContent=(item.level==='critical'?'⚠ ':'● ')+item.message+' · '+stamp(item.time);list.append(p);}
      history.replaceChildren();for(const item of data.events.slice(0,30)){const p=document.createElement('p');p.textContent=(item.state==='resolved'?'✓ ':'⚠ ')+item.message+' · '+stamp(item.time);history.append(p);}
      if(!data.events.length)history.textContent='Ainda não há ocorrências registradas.';
    }catch(_){summary.textContent='Monitor de alertas indisponível; tente novamente.';summary.dataset.state='unknown';}
    try{
      const response=await fetch('/api/restore-check.json',{cache:'no-store',signal:AbortSignal.timeout(8000)});if(!response.ok)throw Error();const d=await response.json(),el=document.getElementById('restoreHealth');
      if(d.status==='ok'){el.textContent='✓ Restauração isolada conferida · '+stamp(d.time)+' · '+d.files_verified+' arquivos · '+d.sqlite_verified+' bancos SQLite · '+d.json_verified+' JSON. Ambiente de produção preservado.';el.dataset.state='ok';}
      else{el.textContent='⚠ Falha no teste de restauração · '+stamp(d.time)+'. Confira o relatório privado.';el.dataset.state='error';}
    }catch(_){document.getElementById('restoreHealth').textContent='Teste de restauração ainda não disponível.';}
  }
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});refresh();setInterval(refresh,30000);
})();
