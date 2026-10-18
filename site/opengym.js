(async () => {
  const status = document.getElementById('gymStatus');
  const link = document.getElementById('gymLink');
  try {
    const response = await fetch('/api/status.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Monitor indisponível');
    const data = await response.json();
    const url = new URL(data.opengym_url);
    if (url.protocol !== 'https:' || !url.hostname.endsWith('.ts.net') || url.port !== '8081' || url.username || url.password) throw new Error('Endereço seguro não configurado');
    link.href = url.href;
    link.hidden = false;
    status.textContent = data.opengym === 'online' ? 'openGym está pronto. Abra pelo endereço seguro abaixo.' : 'openGym está iniciando ou indisponível. Tente novamente em instantes.';
  } catch (_) {
    status.textContent = 'Não foi possível preparar o acesso. Atualize a página ou confira a configuração do servidor.';
  }
})();
