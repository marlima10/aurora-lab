# Cockpit com SSH somente por chave

O container oficial cockpit/ws usa SSH para entrar no host; bloquear senhas no SSH impede seu login por senha. A partir de 11.0, o componente de autenticação Cockpit é instalado no Debian, conforme autorização do responsável. O acesso 9090 continua publicado por um container Nginx. Nenhuma exceção para senha no SSH é criada.

## Preparação

```sh
cd /srv/auroralab
sudo python3 docker/server/cockpit/prepare.py
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml config --quiet
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml up -d --no-deps cockpit
```

O script instala cockpit-ws do repositório Debian, mantém a política SSH, cria certificado/chave locais em `secrets/cockpit-tls.*` e restringe o backend 9091 ao loopback e ao gateway da bridge Docker. O proxy 9090 usa HTTPS e verifica o certificado do backend com nome `auroraserver`. Nenhuma senha ou chave SSH é colocada no container. O tráfego WebSocket é encaminhado para a sessão local PAM.

O certificado interno e sua chave ficam fora do Git e também são usados na entrada LAN. São autoassinados para uso interno; o endereço HTTPS Tailscale continua sendo o acesso com certificado público válido. A política de confiança do trecho Tailscale até a entrada local permanece a da implantação existente. Não há exposição pública via Funnel.

## Entrar

Com Tailscale conectado, abra o domínio HTTPS do servidor com porta 9090. Use seu usuário Debian (`rafael` no AuroraServer) e a senha do Debian. Esse login é pelo PAM local, independente do SSH. Para administração, clique em Acesso limitado/Ativar acesso administrativo e confirme a senha quando solicitado. A condição necessária é o usuário pertencer ao grupo sudo, já configurado no AuroraServer. Não entre como root e não envie senhas pelo chat.

O login remoto por SSH continua aceitando apenas chave. Sessões existentes e credenciais não são substituídas por esta alteração.

## Persistência, backup e reversão

`/etc/cockpit`, `/etc/systemd/system/cockpit.socket.d` e `secrets/` entram no backup. Dados pessoais e certificados privados não entram no repositório. A preparação salva as configurações anteriores em `deploy-state/cockpit-local-before-*.tar.gz`. O certificado interno precisa ser renovado antes do vencimento (825 dias na geração inicial); copie o par renovado para `/etc/cockpit/ws-certs.d/99-aurora.*` e recrie/recarregue os componentes após validar.

Para voltar à imagem cockpit/ws, restaure o Compose anterior e mantenha uma imagem anterior disponível; com SSH somente por chave, seu login por senha continuará bloqueado. Para desativar o backend local, pare/desabilite cockpit.socket e cockpit.service, preservando arquivos para recuperação. Não reative senhas no SSH como parte da reversão.

Fonte oficial: https://cockpit-project.org/guide/latest/authentication.html .
