# Home Assistant Container

`compose.homeassistant.yaml` fixa Home Assistant Container **2026.10.2** por digest. Essa modalidade não inclui Supervisor nem loja de complementos; outros serviços são contêineres independentes.

## Preparação

Na raiz do projeto, com SERVER_IP definido para o IP LAN correto:

```sh
sudo python3 docker/server/homeassistant/prepare.py
```

O script cria apenas arquivos ausentes em `data/homeassistant/`, incluindo `configuration.yaml` e `.storage/http`. Para a versão fixada, a configuração HTTP inicial é JSON nativo versão 2.2, com escuta em 127.0.0.1 e SERVER_IP, porta 8123 e proxies confiáveis 127.0.0.1/32 e ::1/128. Ele não atualiza uma configuração já existente nem migra automaticamente uma configuração de outra versão.

Acrescente `compose.homeassistant.yaml` a COMPOSE_FILE, preservando os overlays ativos conforme [AURORASERVER.md](AURORASERVER.md):

```sh
sudo docker compose config --quiet
sudo docker compose up -d homeassistant
sudo docker compose logs --tail=100 homeassistant
curl -I --connect-timeout 5 http://127.0.0.1:8123/
```

O serviço usa rede host para descoberta, sem Docker socket nem modo privileged. Mantenha o IP LAN estável; se ele mudar, revise a escuta em Configurações > Sistema > Rede. Não edite `.storage` enquanto o aplicativo escreve nela nem mantenha simultaneamente um bloco HTTP legado conflitante no YAML. USB/Bluetooth precisam de preparação específica quando o hardware for definido.

## Acesso e conta

- LAN: `http://IP-LAN:8123`.
- VPN: `https://DOMINIO-TAILSCALE:8123`, somente depois de configurar Serve para `http://127.0.0.1:8123` na instância VPN escolhida.

Veja [REDE-E-TAILSCALE.md](REDE-E-TAILSCALE.md). O preparador não configura Serve. Crie a conta de proprietário no primeiro acesso, defina fuso e dispositivos. A conta é independente do Linux e do CasaOS. Não há senha padrão criada pelo projeto.

## Dados e recuperação

`data/homeassistant/` contém autenticação, configuração e histórico, fora do Git. O backup do servidor inclui arquivos comuns e snapshots SQLite; novos serviços ou dispositivos externos não ganham backup automaticamente.

Para restaurar, pare homeassistant, preserve o estado atual e recoloque os arquivos e snapshots `sqlite-snapshots/homeassistant/` nos locais correspondentes. Não misture WAL/SHM antigos com um snapshot restaurado. Confira permissões, inicie e valide. Use a seleção Compose da instalação para parar/reiniciar, evitando aviso de órfãos.

Desativar o serviço não remove seus dados. Remova somente a rota Serve 8123 quando ela não for mais usada. Não recrie uma segunda instância pela loja CasaOS.

Referência da modalidade: [Home Assistant Container](https://www.home-assistant.io/installation/linux).
