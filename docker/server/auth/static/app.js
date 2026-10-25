(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const apps = { manyfold:'Manyfold', mealie:'Mealie', actual:'Actual Budget', opengym:'openGym', octoprint:'OctoPrint', homeassistant:'Home Assistant', homeboard:'HomeBoard', cockpit:'Cockpit' };
  let session = null;
  let registrationReady = false;
  let adminOnlyApps = new Set(['cockpit']);
  const issuedKeys = new Map();
  function status(text, error=false) { $('status').textContent=text; $('status').classList.toggle('error',error); }
  function hideKey() { $('new-key').value=''; $('key-feedback').textContent=''; if($('generated').open)$('generated').close(); }
  function showKey(email, key) {
    if(typeof key!=='string'||!/^[A-Za-z0-9_-]{151}$/.test(key))throw Error('O servidor não devolveu uma chave válida. Tente renovar a chave.');
    issuedKeys.set(email.toLowerCase(),key);
    $('key-email').textContent=email;$('new-key').value=key;$('key-feedback').textContent='';
    if(!$('generated').open)$('generated').showModal();
    $('new-key').focus();$('new-key').select();
  }
  let confirmPending = null;
  function confirmAction(message) {
    $('confirm-message').textContent=message;
    return new Promise(resolve=>{confirmPending=resolve;$('confirm-dialog').showModal();$('confirm-no').focus();});
  }
  function finishConfirmation(accepted) {
    $('confirm-dialog').close();const resolve=confirmPending;confirmPending=null;resolve?.(accepted);
  }
  $('confirm-yes').addEventListener('click',()=>finishConfirmation(true));
  $('confirm-no').addEventListener('click',()=>finishConfirmation(false));
  $('confirm-dialog').addEventListener('cancel',event=>{event.preventDefault();finishConfirmation(false);});
  function registrationStatus(message,error=false) {
    $('issue-status').textContent=message;$('issue-status').hidden=!message;$('issue-status').classList.toggle('error',error);
    status(message,error);
  }
  function syncRegistrationPermissions() {
    const target=$('issue-form').elements.email.value.trim().toLowerCase();
    for(const check of $('permissions').querySelectorAll('input[type=checkbox]')) {
      const row=check.closest('.permission'),select=row.querySelector('select'),note=row.querySelector('.permission-note');
      const reserved=adminOnlyApps.has(check.dataset.app)&&target!=='aurora@server.local';
      const available=check.dataset.available==='true';
      check.disabled=!registrationReady||!available||reserved;
      if(check.disabled)check.checked=false;
      select.disabled=check.disabled||!check.checked;select.required=!select.disabled;
      note.textContent=reserved?'Reservado ao administrador principal.':!available?'Nenhuma identidade disponível.':'';
      note.hidden=!note.textContent;
    }
  }
  async function request(path, data) {
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),20000);
    try {
      const response=await fetch('/auth/'+path,{method:data?'POST':'GET',cache:'no-store',credentials:'same-origin',signal:controller.signal,headers:data?{'Content-Type':'application/json','X-Aurora-CSRF':session?.csrf||''}:{},body:data?JSON.stringify(data):undefined});
      let result;
      try { result=await response.json(); } catch { throw Error('Resposta inesperada do servidor (HTTP '+response.status+'). Recarregue a página.'); }
      if(!response.ok)throw Error(result.error||'Não foi possível concluir (HTTP '+response.status+').');
      return result;
    } catch(error) {
      if(error.name==='AbortError')throw Error('O servidor demorou para responder. Atualize a lista antes de repetir a operação.');
      throw error;
    } finally { clearTimeout(timeout); }
  }
  async function users() {
    $('refresh-users').disabled=true;$('users-state').textContent='Atualizando cadastros…';$('users-state').classList.remove('error');
    try {
    const data=await request('users');if(!Array.isArray(data.users))throw Error('Resposta de cadastros inválida.'); $('users').replaceChildren();
    $('user-count').textContent=String(data.users.length);
    $('users-state').textContent=data.users.length===1?'1 usuário cadastrado.':data.users.length+' usuários cadastrados.';
    for (const user of data.users) {
      const row=document.createElement('div');row.className='user';
      const name=document.createElement('span');name.textContent=user.email+(user.email==='aurora@server.local'?' · Administrador principal':'')+(user.enabled?' · Ativo':' · Revogado');row.append(name);
      if (user.email!=='aurora@server.local') {
        const actions=document.createElement('div');actions.className='user-actions';
        function action(label, run, danger=false){const button=document.createElement('button');button.type='button';button.className='secondary'+(danger?' danger':'');button.textContent=label;button.addEventListener('click',async()=>{button.disabled=true;try{await run()}catch(e){status(e.message,true)}finally{button.disabled=false}});actions.append(button);}
        if(issuedKeys.has(user.email))action('Ver chave gerada',()=>showKey(user.email,issuedKeys.get(user.email)));
        action('Gerar nova chave',async()=>{if(!await confirmAction('Gerar uma nova chave para '+user.email+'? A chave e as sessões anteriores serão encerradas. As permissões serão mantidas.'))return;const result=await request('issue',{email:user.email});showKey(user.email,result.key);status('Nova chave gerada. Copie na janela aberta.');await users();});
        if(user.enabled)action('Revogar acesso',async()=>{if(!await confirmAction('Revogar as sessões e a chave de '+user.email+'?'))return;await request('revoke',{email:user.email});issuedKeys.delete(user.email);await users();status('Acesso revogado para novas requisições.');});
        action('Excluir usuário',async()=>{if(!await confirmAction('Excluir o cadastro de '+user.email+'? O acesso será encerrado. Os dados dos aplicativos serão preservados.'))return;await request('delete',{email:user.email});issuedKeys.delete(user.email);await users();status('Usuário excluído da lista e acesso encerrado.');},true);
        row.append(actions);
      }
      $('users').append(row);
    }
    } catch(error) {
      $('users-state').textContent='Não foi possível atualizar os cadastros. '+error.message+' Use Atualizar lista para tentar novamente.';
      $('users-state').classList.add('error');
    } finally { $('refresh-users').disabled=false; }
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
      $('account').before($('admin'));
      await users();
      registrationReady=false;$('issue-form').querySelector('button').disabled=true;
      const registry=await request('apps');
      adminOnlyApps=new Set(registry.adminOnly||['cockpit']);
      for (const check of $('permissions').querySelectorAll('input[type=checkbox]')) {
        const select=check.closest('.permission').querySelector('select');select.replaceChildren();
        for(const option of registry.apps[check.dataset.app]||[]){const item=document.createElement('option');item.value=option.identity;item.textContent=option.label;select.append(item);}
        check.dataset.available=String(select.options.length>0);
      }
      registrationReady=true;syncRegistrationPermissions();$('issue-form').querySelector('button').disabled=false;
    }
  }
  for (const [id,name] of Object.entries(apps)) {
    const row=document.createElement('div');row.className='permission';
    const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.dataset.app=id;check.disabled=true;
    const text=document.createElement('span');text.textContent=name;label.append(check,text);
    const identityLabel=document.createElement('label');identityLabel.textContent='Identidade existente no aplicativo';
    const identity=document.createElement('select');identity.disabled=true;identityLabel.append(identity);
    check.addEventListener('change',syncRegistrationPermissions);
    const note=document.createElement('small');note.className='permission-note';note.hidden=true;
    row.append(label,identityLabel,note);$('permissions').append(row);
  }
  $('issue-form').elements.email.addEventListener('input',syncRegistrationPermissions);
  $('issue-form').elements.email.addEventListener('change',syncRegistrationPermissions);
  $('refresh-users').addEventListener('click',users);
  $('issue-form').addEventListener('invalid',()=>registrationStatus('Confira o e-mail cadastrado e os campos obrigatórios.',true),true);
  $('login-form').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget,button=form.querySelector('button');button.disabled=true;status('Verificando acesso…');try{await request('login',{email:form.elements.email.value,key:form.elements.key.value});form.elements.key.value='';await refresh();status('Sessão iniciada. Seus aplicativos autorizados estão disponíveis.')}catch(e){status(e.message,true)}finally{button.disabled=false}});
  $('issue-form').addEventListener('submit',async event=>{
    event.preventDefault();const form=event.currentTarget,button=form.querySelector('button');
    if(button.disabled||!registrationReady)return;
    syncRegistrationPermissions();
    const email=form.elements.email.value.trim().toLowerCase(),grants={};
    for(const check of $('permissions').querySelectorAll('input[type=checkbox]:checked')){
      if(!check.disabled)grants[check.dataset.app]=check.closest('.permission').querySelector('select').value;
    }
    button.disabled=true;registrationStatus('Confirme o cadastro na janela aberta.');
    try {
      if(!await confirmAction('Gerar uma chave para '+email+'? Se já existir, a chave e as sessões anteriores serão revogadas.')){
        registrationStatus('Cadastro cancelado.');return;
      }
      registrationStatus('Salvando cadastro e gerando a chave…');hideKey();
      const result=await request('issue',{email,grants});
      showKey(email,result.key);
      if(email===session.email)registrationStatus('Sua chave foi renovada. Copie agora; entre novamente com a nova chave.');
      else {await users();registrationStatus('Cadastro concluído. A chave está na janela aberta; copie antes de sair.');}
    } catch(error) { registrationStatus(error.message,true); }
    finally {button.disabled=false;}
  });
  $('copy-key').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('new-key').value);$('key-feedback').textContent='Chave copiada.';status('Chave copiada.')}catch{$('new-key').focus();$('new-key').select();$('key-feedback').textContent='Use Ctrl+C ou a opção Copiar do aparelho.';status('Use Ctrl+C ou a opção Copiar do aparelho.')}});
  $('clear-key').addEventListener('click',hideKey);
  $('logout').addEventListener('click',async()=>{try{await request('logout',{});hideKey();issuedKeys.clear();session=null;await refresh();status('Sessão central encerrada.')}catch(e){status(e.message,true)}});
  $('generated').addEventListener('cancel',event=>{event.preventDefault();hideKey();});
  window.addEventListener('pagehide',()=>{hideKey();issuedKeys.clear();});
  refresh().catch(e=>{registrationStatus(e.message,true);});
})();
