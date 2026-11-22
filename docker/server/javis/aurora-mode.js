(() => {
  const banner=document.createElement('aside');banner.id='aurora-mode';banner.setAttribute('aria-label','Integração AuroraLAB');
  const title=document.createElement('strong');title.textContent='AuroraLAB · Gemini no servidor';
  const body=document.createElement('span');body.textContent='Converse aqui com o Gemini no AuroraServer. As consultas autorizadas aos aplicativos são enviadas ao Google para gerar as respostas.';
  const back=document.createElement('a');back.textContent='Voltar ao AuroraLAB';back.href=new URL('/',location.href).href.replace(':7777','');
  const notes=document.createElement('a');notes.textContent='Notas';notes.href='#p=files';
  const connections=document.createElement('a');connections.textContent='Conexões';connections.href='#p=mcp';
  const setup=document.createElement('a');setup.textContent='Configurar Gemini';setup.href='/aurora-ai/setup';
  const chat=document.createElement('a');chat.textContent='Conversa';chat.href='#p=chat';
  banner.append(title,body,setup,chat,notes,back);document.body.prepend(banner);
  const resize=()=>document.documentElement.style.setProperty('--aurora-banner-height',banner.offsetHeight+'px');
  new ResizeObserver(resize).observe(banner);resize();
  if(!location.hash)location.hash='#p=chat';
})();
