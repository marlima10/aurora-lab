(()=>{
  if('serviceWorker' in navigator&&window.isSecureContext){const register=()=>navigator.serviceWorker.register('/service-worker.js').catch(error=>console.error('PWA:',error));if(document.readyState==='complete')register();else window.addEventListener('load',register,{once:true});}
  const button=document.getElementById('installApp');
  if(!button)return;
  const standalone=()=>window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
  const ios=/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  let installPrompt=null,hint=null,hintTimer=0;
  const show=visible=>{button.hidden=!visible;if(!visible&&hint)hint.hidden=true};
  const say=message=>{if(!hint){hint=document.createElement('p');hint.className='install-hint';hint.setAttribute('role','status');button.after(hint)}hint.textContent=message;hint.hidden=false;clearTimeout(hintTimer);hintTimer=setTimeout(()=>{hint.hidden=true},12000)};
  show(false);
  // Sem HTTPS ou já instalado, não há instalação a oferecer.
  if(!window.isSecureContext||standalone())return;
  // O Safari do iOS não dispara beforeinstallprompt; o botão mostra as instruções.
  if(ios)show(true);
  window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event;show(true)});
  window.addEventListener('appinstalled',()=>{installPrompt=null;show(false)});
  button.addEventListener('click',async()=>{
    if(installPrompt){const prompt=installPrompt;installPrompt=null;prompt.prompt();const choice=await prompt.userChoice.catch(()=>null);if(choice?.outcome!=='accepted')show(false);return}
    say(ios?'No Safari, toque em Compartilhar e escolha “Adicionar à Tela de Início”.':'No menu do navegador, escolha “Instalar aplicativo” ou “Adicionar à tela inicial”.');
  });
})();
