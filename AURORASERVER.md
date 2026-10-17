# AuroraLAB 2.0 — ambiente completo no Linux

O ambiente completo usa `compose.server.yaml`. O `compose.yaml` original continua disponível para executar somente portal e Fitness. A interface, a PWA, os recursos Fitness e o contrato `/fitness-api` permanecem compatíveis.

## Requisitos

Linux amd64 com Docker Engine e plugin Compose. Ambiente validado no Debian 13. Docker, SSH, kernel e drivers são recursos do host; Cockpit requer também `cockpit-bridge` e `cockpit-system` no host. Não é necessário executar um servidor de banco separado: SQLite persiste em arquivos.

## Instalação nova

```sh
git clone https://github.com/marlima10/aurora-lab.git
cd aurora-lab
git checkout rafael
sudo sh docker/server/prepare.sh
```

Revise `SERVER_IP` em `.env` para o endereço deste servidor. A preparação solicita uma senha Samba sem exibi-la, cria os diretórios necessários e preserva arquivos existentes. Não adicione `.env` ou `secrets/` ao Git.

```sh
sudo docker compose -f compose.server.yaml config --quiet
sudo docker compose -f compose.server.yaml up -d --build
sudo docker compose -f compose.server.yaml ps
```

O primeiro build baixa as fontes dos plugins OctoPrint pelos commits de `plugins.lock.json` e verifica SHA-256. Os arquivos ZIP não precisam ser versionados. Essa imagem de OctoPrint usa s6-overlay amd64; não é uma imagem ARM.

Abra o OctoPrint para concluir o assistente e criar seu usuário. Para o monitor ler o estado da impressora, copie a chave da API do OctoPrint para `secrets/octoprint-api.key`, mantendo esse arquivo fora do Git. O arquivo é montado somente para leitura pelo monitor; o diretório `secrets/` é restrito no host.

## Serviços separados

| Serviço | Função | Acesso no IP do servidor |
| --- | --- | --- |
| web | Nginx, portal e proxy | HTTP 80 ou 8088 |
| php | API Fitness PHP-FPM | `/fitness-api` pelo Nginx |
| octoprint | OctoPrint 1.11.8, Python 3.12 e plugins | HTTP 5000 |
| samba | Compartilhamento Prints autenticado, usuário rafael | SMB 445, compartilhamento Prints |
| monitor | CPU, RAM, swap, disco, histórico e descoberta da rede | Dashboard; HTTP 9101 |
| backup | Snapshots SQLite, arquivos e configurações | `backups/`; status no dashboard |
| tailscale | VPN com identidade própria | Autorização separada |
| cockpit | Administração web por SSH ao host | HTTPS 9090 |
| camera | uStreamer para câmera USB | Perfil opcional `camera`, HTTP 8080 |

Configure o acesso Tailscale após iniciar:

```sh
sudo docker compose -f compose.server.yaml exec tailscale tailscale up --hostname=auroraserver --accept-dns=false
```

Autorize o link exibido pelo Tailscale. Cada instalação cria uma identidade nova; não copie o estado de outra máquina. Cockpit usa SSH ao host: informe o IP do servidor e um usuário Linux com as permissões necessárias. O certificado local é autoassinado.

## Persistência e migração

- Fitness: `data/fitness/fitness.sqlite3`.
- OctoPrint: `data/octoprint/`, incluindo configuração, usuários, uploads, timelapses e histórico de impressão.
- Prints: `data/prints/`; Samba: `data/samba/`.
- Tailscale: `data/tailscale/`; monitoramento: `data/monitor/`.
- Credenciais locais: `secrets/`; ambiente: `.env`.

Faça backup antes de migrar. Pare os serviços escritores antes de restaurar e extraia o backup primeiro para uma pasta temporária. Restaure snapshots SQLite nos caminhos corretos, sem journals antigos. Não sobreponha um banco ativo. Preserve permissões e execute novamente `prepare.sh` se necessário.

A migração de Armbian para amd64 recompõe os programas e plugins para a arquitetura nova; não reutilize ambientes Python ARM nem substitua `/etc` do Debian pelo sistema antigo. A identidade VPN deve ser recriada. Dados de origem não sincronizam automaticamente após a migração.

## Plugins OctoPrint

As 12 fontes e versões estão registradas em `docker/server/octoprint/plugins.lock.json`. Incluem DisplayLayerProgress, HomeAssistant, PrintTimeGenius, CameraSettings, PrintHistory, FirmwareUpdater, Power Failure Recovery, CrealityCloud With Video, Cost Estimation, Creality2x Temperature Reporting Fix, UI Customizer e Dashboard.

HomeAssistant fica desativado até configurar o provedor MQTT e corrigir a compatibilidade de API. Power Failure Recovery recebeu uma guarda para temporizadores ausentes; Cost Estimation usa a identificação estática de versão 3.6.0. Consulte [atualização Python](UPGRADE-PYTHON-OCTOPRINT.md).

## Câmera e impressora USB

A câmera é opcional. Defina `CAMERA_DEVICE=/dev/v4l/by-id/...` em `.env` após identificar o dispositivo USB. O caminho padrão não existe para evitar ativar uma câmera integrada por engano.

```sh
sudo docker compose -f compose.server.yaml --profile camera up -d --build camera
```

O portal usa `/camera-stream`; o OctoPrint usa `/webcam/stream`. Para a impressora, defina `PRINTER_DEVICE=/dev/serial/by-id/...` e execute:

```sh
sudo docker compose -f compose.server.yaml -f compose.printer.yaml up -d octoprint
```

Selecione `/dev/ttyPrinter` no OctoPrint. Confirme a imagem da câmera e a conexão da impressora antes de iniciar uma impressão.

## Backups e operação

O serviço backup executa ao iniciar e a cada 24 horas. Usa a API de backup SQLite, valida os bancos extraídos do arquivo final e cria SHA-256. Inclui arquivos de configuração e credenciais: mantenha os arquivos restritos e configure cópia externa. As cópias locais não são criptografadas e não há exclusão automática das antigas.

```sh
sudo docker compose -f compose.server.yaml logs --tail=100
sudo docker compose -f compose.server.yaml stop
sudo docker compose -f compose.server.yaml up -d
sudo docker compose -f compose.server.yaml run --rm --no-deps --entrypoint php php tests/run.php
```

O monitor usa rede do host e montagens de `/proc` e `/sys` somente para leitura, sem socket Docker. A descoberta usa ICMP na rede /24 do servidor; equipamentos que bloqueiam ping podem não aparecer. Métricas são coletadas a cada 5 segundos, com até 1.440 amostras, uma por minuto. Algumas medidas de diretórios e diagnósticos ainda são limitadas.

## Atualização da versão portátil

O banco portátil continua em `data/fitness.sqlite3`; o ambiente completo usa `data/fitness/fitness.sqlite3`. Faça uma cópia consistente e mova para o caminho correspondente com os serviços parados. Não execute os dois ambientes ao mesmo tempo apontando para o mesmo banco. Para continuar no portátil, mantenha `docker compose up -d --build`, sem adicionar o arquivo de servidor.
