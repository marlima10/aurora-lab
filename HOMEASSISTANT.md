# Home Assistant

A integração usa Home Assistant **Container 2026.10.2**, em serviço separado. A imagem está fixada por digest no `compose.homeassistant.yaml`. Essa modalidade não inclui Supervisor nem loja de complementos: serviços auxiliares são containers independentes.

## Preparação e execução

```sh
cd /srv/auroralab
sudo python3 docker/server/homeassistant/prepare.py
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml config --quiet
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml up -d --no-deps homeassistant
```

A preparação não substitui configuração existente. Para a versão fixada 2026.10, o HTTP é inicializado no formato nativo `.storage/http` (2.2), com escuta em loopback e no `SERVER_IP` do `.env`. Isso evita conflito entre o HTTP local e o HTTPS Tailscale na mesma porta. Mudanças futuras são feitas em Configurações > Sistema > Rede; não mantenha um bloco HTTP legado no YAML. Mantenha reserva DHCP do IP LAN e atualize a escuta caso esse IP mude. O container usa a rede do host para descoberta, escuta em 8123 e não recebe Docker socket nem modo privilegiado. Dispositivos USB/Bluetooth serão configurados quando houver hardware e integrações definidos.

## Acesso

Na LAN: `http://IP-DO-SERVIDOR:8123`. Na VPN: `https://DOMINIO-TAILSCALE:8123`. A rota Tailscale Serve encaminha para `http://127.0.0.1:8123`; os únicos proxies confiáveis na configuração inicial são 127.0.0.1 e ::1. Não use Funnel.

Crie o proprietário no primeiro acesso e defina local, fuso e dispositivos na própria tela. Não há senha padrão criada pelo AuroraLAB. A conta é independente do Linux e do CasaOS.

## Dados, backup e reversão

`data/homeassistant/` contém configuração, autenticação e histórico; fica fora do Git. O backup automático inclui o diretório, usando a API SQLite para bancos .db e verificando a integridade da cópia. Para restaurar, pare somente homeassistant, preserve o estado atual, recoloque arquivos comuns e o SQLite de `sqlite-snapshots/homeassistant/`, ajuste permissões e inicie novamente. Não restaure WAL/SHM de outra cópia.

Para desativar: `docker compose -f compose.server.yaml -f compose.homeassistant.yaml stop homeassistant`; mantenha os dados e desligue apenas a rota Serve 8123. O Fitness e os outros serviços continuam independentes.

Fonte: https://www.home-assistant.io/installation/linux .
