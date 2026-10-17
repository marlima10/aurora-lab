(()=>{
  if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(error=>console.error('PWA:',error)));
  const button=document.getElementById('installApp');
  if(!button)return;
  if(window.matchMedia('(display-mode: standalone)').matches)button.textContent='✓ App instalado';
  let installPrompt=null;
  window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event;button.textContent='⬇ Instalar app'});
  window.addEventListener('appinstalled',()=>{installPrompt=null;button.textContent='✓ App instalado'});
  button.addEventListener('click',async()=>{
    if(!window.isSecureContext){alert('Para instalar o Aurora Lab como aplicativo, o portal precisa abrir por HTTPS. A conexão atual não é segura para instalação.');return}
    if(installPrompt){installPrompt.prompt();await installPrompt.userChoice;installPrompt=null;return}
    if(window.matchMedia('(display-mode: standalone)').matches){alert('Aurora Lab já está instalado neste aparelho.');return}
    const ios=/iPad|iPhone|iPod/.test(navigator.userAgent)&&!window.MSStream;
    alert(ios?'No Safari, toque em Compartilhar e escolha “Adicionar à Tela de Início”.':'No menu do navegador, escolha “Instalar aplicativo” ou “Adicionar à tela inicial”.');
  });
})();
