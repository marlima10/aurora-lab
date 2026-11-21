(() => {
  const banner=document.createElement('aside');banner.id='aurora-mode';banner.setAttribute('aria-label','Integração AuroraLAB');
  const title=document.createElement('strong');title.textContent='AuroraLAB · Claude Desktop';
  const body=document.createElement('span');body.textContent='Converse no aplicativo Claude deste computador. Este painel organiza notas e conexões; o plano gratuito não ativa o chat interno. Os aplicativos do AuroraLAB estão disponíveis para consulta.';
  const back=document.createElement('a');back.textContent='Voltar ao AuroraLAB';back.href=new URL('/',location.href).href.replace(':7777','');
  const notes=document.createElement('a');notes.textContent='Notas';notes.href='#p=files';
  const connections=document.createElement('a');connections.textContent='Conexões';connections.href='#p=mcp';
  banner.append(title,body,notes,connections,back);document.body.prepend(banner);
  const resize=()=>document.documentElement.style.setProperty('--aurora-banner-height',banner.offsetHeight+'px');
  new ResizeObserver(resize).observe(banner);resize();
  if(!location.hash)location.hash='#p=files';
})();
