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

## Energia e bateria — versão 3.0

Bateria clicável, CPU/GPU, histórico e simulação de custos no dashboard. Tarifa, potências e horas de suspensão são editáveis e salvas somente no navegador. Valores financeiros são projeções de 30 dias.

O container opcional `power` usa `compose.power.yaml`. Instalação no Debian:

```sh
cd /srv/auroralab
sudo sh docker/server/power/prepare.sh
sudo docker compose -f compose.server.yaml -f compose.power.yaml config --quiet
sudo docker compose -f compose.server.yaml -f compose.power.yaml up -d --build power
sudo docker compose -f compose.server.yaml up -d --no-deps --force-recreate monitor
sudo docker compose -f compose.server.yaml exec web nginx -t
sudo docker compose -f compose.server.yaml exec web nginx -s reload
```

Em outra máquina, ajuste `BACKLIGHT_PATH` em `.env` para o dispositivo em `/sys/class/backlight`. O padrão é `intel_backlight`. O modo portátil indica sensores indisponíveis quando não há esse serviço.

`GET /api/power` oferece telemetria. `POST /api/power/settings` exige a chave aleatória de `secrets/power-admin.key`, acessível somente ao administrador. Informe a chave no pop-up; não use a senha Linux. A chave permanece somente na memória da aba, não em localStorage, URL ou código público. Acesse controles pela rede confiável ou VPN.

O serviço escuta somente em `127.0.0.1:9110`; o monitor encaminha chamadas pelo Nginx. Executa sem capabilities, sem socket Docker e sem modo privileged. `/sys` e `/proc` são somente leitura; os diretórios CPU e brilho têm escrita. Só são aceitos perfis fixos de CPU e brilho de 5–100%, com retorno em falha. Outro gerenciador ativo bloqueia os perfis da CPU. Ajustes aplicados são persistidos em `data/power/settings.json` e reaplicados ao iniciar o container.

Economia máxima: powersave, preferência power e turbo desativado. Equilibrado: powersave, balance_performance e turbo disponível. Desempenho: performance e turbo disponível. Rede, USB, Docker e drivers não são desligados.

A bateria fornece descarga/carregamento; somente a descarga é usada como aproximação do notebook ligado. Na tomada, a carga da bateria não é apresentada como consumo total. O pacote CPU usa diferenças de contadores RAPL, incluindo volta do contador e exclusão de lacunas maiores que 30 segundos. O domínio gráfico integrado não é somado novamente ao pacote CPU. Energia acompanhada representa somente os intervalos observados no dia.

A GeForce MX110 com nouveau nesta máquina não expõe watts nem uso por sysfs. São mostrados nome, driver e estado, com valores indisponíveis em vez de zero fictício. A Intel integrada mostra watts quando existe domínio gráfico RAPL. Histórico: até 1.440 amostras, uma por minuto; gráfico: últimas 90. O custo real na tomada exige wattímetro ou tomada medidora.

Suspensão automática 00h–07h permanece desativada. Testar RTC com acesso físico e implementar bloqueios de impressão, backup e atualização antes de automatizar. Não aplicar auto-tune genérico, trocar driver NVIDIA ou desligar o Wi-Fi sem diagnóstico.

Os backups incluem estado de energia e a chave privada; manter acesso restrito. Referências: [power_supply](https://www.kernel.org/doc/html/latest/power/power_supply_class.html), [powercap/RAPL](https://cdn.kernel.org/doc/html/latest/power/powercap/powercap.html).

Testes Linux de conversões, perfis, retorno e autenticação:

```sh
python3 docker/server/power/test_power.py
```
