(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const apps = { manyfold:'Manyfold', mealie:'Mealie', actual:'Actual Budget', opengym:'openGym', octoprint:'OctoPrint', homeassistant:'Home Assistant', homeboard:'HomeBoard', cockpit:'Cockpit' };
  let session = null;
  function status(text, error=false) { $('status').textContent=text; $('status').classList.toggle('error',error); }
  function hideKey() { $('new-key').value=''; $('generated').hidden=true; }
  async function request(path, data) {
    const response=await fetch('/auth/'+path,{method:data?'POST':'GET',cache:'no-store',credentials:'same-origin',headers:data?{'Content-Type':'application/json','X-Aurora-CSRF':session?.csrf||''}:{},body:data?JSON.stringify(data):undefined});
    const result=await response.json();
    if (!response.ok) throw Error(result.error||'Não foi possível concluir.');
    return result;
  }
  async function users() {
    const data=await request('users'); $('users').replaceChildren();
    for (const user of data.users) {
      const row=document.createElement('div');row.className='user';
      const name=document.createElement('span');name.textContent=user.email+(user.enabled?' · Ativo':' · Revogado');row.append(name);
      if (user.email!=='aurora@server.local' && user.enabled) {
        const button=document.createElement('button');button.className='secondary';button.textContent='Revogar acesso';
        button.addEventListener('click',async()=>{if(!confirm('Revogar as sessões e a chave de '+user.email+'?'))return;try{await request('revoke',{email:user.email});await users();status('Acesso revogado para novas requisições.')}catch(e){status(e.message,true)}});row.append(button);
      }
      $('users').append(row);
    }
  }
  async function refresh() {
    try { session=await request('session'); }
    catch { session=null; }
    $('login').hidden=Boolean(session);$('account').hidden=!session;$('admin').hidden=!session?.admin;
    if (!session) return;
    $('identity').textContent=session.email;$('applications').replaceChildren();
    for (const app of Object.keys(session.grants)) {
      if (!apps[app]) continue;
      const link=document.createElement('a');link.href='/'+app;link.textContent=apps[app]+' ↗';$('applications').append(link);
    }
    if (session.admin) {
      await users();
      const registry=await request('apps');
      for (const check of $('permissions').querySelectorAll('input[type=checkbox]')) {
        const select=check.closest('.permission').querySelector('select');select.replaceChildren();
        for(const option of registry.apps[check.dataset.app]||[]){const item=document.createElement('option');item.value=option.identity;item.textContent=option.label;select.append(item);}
        if(!select.options.length){check.disabled=true;check.checked=false;select.disabled=true;}
      }
    }
  }
  for (const [id,name] of Object.entries(apps)) {
    const row=document.createElement('div');row.className='permission';
    const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.dataset.app=id;
    const text=document.createElement('span');text.textContent=name;label.append(check,text);
    const identityLabel=document.createElement('label');identityLabel.textContent='Identidade existente no aplicativo';
    const identity=document.createElement('select');identity.disabled=true;identityLabel.append(identity);
    check.addEventListener('change',()=>{identity.disabled=!check.checked;identity.required=check.checked;});
    row.append(label,identityLabel);$('permissions').append(row);
  }
  $('login-form').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget,button=form.querySelector('button');button.disabled=true;status('Verificando acesso…');try{await request('login',{email:form.elements.email.value,key:form.elements.key.value});form.elements.key.value='';await refresh();status('Sessão iniciada. Seus aplicativos autorizados estão disponíveis.')}catch(e){status(e.message,true)}finally{button.disabled=false}});
  $('issue-form').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget,button=form.querySelector('button'),email=form.elements.email.value;const grants={};for(const check of $('permissions').querySelectorAll('input[type=checkbox]:checked'))grants[check.dataset.app]=check.closest('.permission').querySelector('select').value;if(!confirm('Gerar uma chave para '+email+'? Se já existir, a chave e as sessões anteriores serão revogadas.'))return;button.disabled=true;hideKey();try{const result=await request('issue',{email,grants});$('key-email').textContent=email;$('new-key').value=result.key;$('generated').hidden=false;status('Chave criada. Copie agora e distribua somente ao titular.');if(email.toLowerCase()===session.email){status('Sua chave foi renovada. Copie agora; entre novamente usando a nova chave.')}else await users()}catch(e){status(e.message,true)}finally{button.disabled=false}});
  $('copy-key').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('new-key').value);status('Chave copiada.')}catch{$('new-key').focus();$('new-key').select();status('Use Ctrl+C ou a opção Copiar do aparelho.')}});
  $('clear-key').addEventListener('click',hideKey);
  $('logout').addEventListener('click',async()=>{try{await request('logout',{});hideKey();session=null;await refresh();status('Sessão central encerrada.')}catch(e){status(e.message,true)}});
  window.addEventListener('pagehide',hideKey);
  refresh().catch(e=>status(e.message,true));
})();
