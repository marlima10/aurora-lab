> Atualizacao v15: o ambiente atual usa HomeBoard no lugar do CasaOS. Nao execute a etapa de instalacao CasaOS para reproduzir o estado atual; siga [HOMEBOARD.md](HOMEBOARD.md), incluindo o overlay Compose, backup e acesso Tailscale. As instrucoes CasaOS abaixo ficam como referencia de instalacoes anteriores.

# AuroraServer — instalação e operação no Linux

Guia do ambiente completo da versão 14.0.0. Para apagar uma instalação anterior e todos os seus dados antes de começar, siga primeiro [REINSTALACAO.md](REINSTALACAO.md). Os comandos partem da raiz do repositório. O caminho `~/srv/docker/aurora-lab` é um exemplo; use a pasta real do seu clone. A documentação não comprova que um serviço esteja instalado ou saudável em outra máquina.

## Requisitos e escolha de configuração

- Linux amd64 (`uname -m` deve mostrar `x86_64`); os artefatos OctoPrint/CasaOS incluem componentes específicos dessa arquitetura.
- Docker Engine funcionando e plugin Compose: `sudo docker info` e `docker compose version`.
- Git e Python 3. O alvo dos scripts de instalação é Debian; a instalação relatada no projeto usa Debian 13.
- Internet para baixar imagens, pacotes e fontes; espaço em disco para imagens, dados e backups.

O arquivo `compose.server.yaml` é independente do portátil `compose.yaml`. Não combine esses dois arquivos. Os módulos adicionais devem ser combinados com o arquivo de servidor.

## 1. Obter e preparar o projeto

Para uma instalação nova:

```sh
mkdir -p ~/srv/docker
cd ~/srv/docker
git clone https://github.com/marlima10/aurora-lab.git
cd aurora-lab
sudo sh docker/server/prepare.sh
```

O clone usa a branch padrão do repositório. Para desenvolvimento, escolha sua branch explicitamente; a cópia em trabalho nesta revisão usa `marcelo`. Não use `sudo git clone` para contornar uma pasta sem permissão: clone numa pasta do seu usuário.

`prepare.sh` cria os diretórios base, copia `.env.example` apenas quando `.env` não existe e solicita a senha Samba sem eco. Ele preserva dados existentes e não redefine a senha de uma base Samba já inicializada. O usuário Samba continua sendo **rafael**, definido em `entrypoint.sh` e `smb.conf`; o texto do prompt ou o nome do usuário Linux não mudam essa conta.

O preparador valida `.env`, `secrets/octoprint-api.key` e `secrets/samba-users.txt`. Quando um desses caminhos é um diretório vazio criado por um bind mount ausente, ele usa apenas rmdir e depois cria o arquivo correto. Se houver conteúdo, link simbólico, arquivo especial ou diretório ocupado, ele interrompe sem apagar esses dados e informa o caminho. Pare o serviço que monta o caminho antes de reparar e recrie-o depois para atualizar o tipo da montagem.

Arquivo Samba vazio sem uma base passdb.tdb inicializada exige nova senha em terminal interativo; uma base existente não exige redefinição. Arquivos regulares de configuração, chave e senha existentes são preservados. Não use `touch` para contornar a necessidade da senha.

## 2. Ajustar o ambiente local

```sh
ip -br -4 addr
sudo nano .env
```

Exemplo, substituindo o IP pelo da interface Ethernet/Wi-Fi do servidor:

```dotenv
SERVER_IP=192.168.0.145
BIND_IP=0.0.0.0
COMPOSE_FILE=compose.server.yaml
```

`SERVER_IP` deve ser o IP LAN, não o endereço Tailscale `100.x`: ele alimenta o monitor, a descoberta da rede e a preparação/bind do Cockpit. Reserve esse IP no DHCP quando possível. `BIND_IP` controla publicações que usam essa variável; `0.0.0.0` escuta em todas as interfaces IPv4. Ele não configura automaticamente os serviços em rede host.

`COMPOSE_FILE` registra os arquivos da instalação. No Linux, separe múltiplos arquivos com `:`. Acrescente somente módulos já preparados, por exemplo `compose.server.yaml:compose.homeassistant.yaml:compose.opengym.yaml`. A opção `-f` prevalece sobre essa seleção; omitir um overlay pode gerar aviso de contêiner órfão. [Referência do Compose](https://docs.docker.com/compose/how-tos/environment-variables/envvars/).

## 3. Escolher uma única instalação Tailscale

Antes de iniciar o stack:

```sh
systemctl is-active tailscaled
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}'
```

Se o Debian já tem Tailscale funcionando, siga o [modo host](REDE-E-TAILSCALE.md) para manter a identidade e impedir que o contêiner seja iniciado por um futuro `up`. O Compose atual não tem essa seleção automática. Não desligue a VPN usada pelo seu SSH.

Se escolheu o contêiner e não há outra instância usando `tailscale0`:

```sh
sudo docker compose up -d tailscale
sudo docker compose exec tailscale tailscale up --hostname=auroraserver --accept-dns=false
sudo docker compose exec tailscale tailscale status
```

Autorize o link exibido. Esse processo depende de `/dev/net/tun`. `TS_*` no YAML não substitui a autorização manual, pois a entrada configurada executa `tailscaled` diretamente.

## 4. Iniciar os serviços base

Depois de conferir `COMPOSE_FILE` no `.env`:

```sh
sudo docker compose config --quiet
sudo docker compose up -d --build php monitor web octoprint samba backup
sudo docker compose ps
sudo docker compose logs --tail=100 php web
curl -I --connect-timeout 5 http://127.0.0.1:8088/
```

A lista explícita evita iniciar o proxy Cockpit antes de preparar os certificados e o backend Debian. Não execute um `up -d` geral enquanto houver serviços sem pré-requisitos preparados. A dependência `depends_on` do portal não garante que o monitor já tenha produzido sua primeira amostra.

Abra o OctoPrint na porta 5000, conclua o assistente e crie seu usuário. Para o monitor ler a impressora, grave a chave de API em `secrets/octoprint-api.key` no próprio servidor; não a publique. O diretório `secrets/` permanece restrito, enquanto esse arquivo recebe leitura para o processo do monitor.

## 5. Preparar e iniciar o Cockpit

Este passo pressupõe o Tailscale no contêiner autenticado e estável. Se manteve a VPN no host, leia a limitação do preparador em [COCKPIT.md](COCKPIT.md) antes de executar.

```sh
sudo python3 docker/server/cockpit/prepare.py
sudo docker compose up -d --no-deps cockpit
sudo docker compose exec cockpit nginx -t
```

O script instala o backend no Debian, cria certificados e configuração local. Abra `https://IP-LAN:9090` e use seu usuário/senha Debian. A entrada usa certificado autoassinado; o backend é 9091, não a porta para acesso público. Não habilite senha no SSH para resolver o login.

## 6. Instalar ou verificar o CasaOS

Confira primeiro se já existe uma instalação:

```sh
test -e /usr/bin/casaos && echo 'Instalação existente: seguir diagnóstico, não reinstalar'
```

Somente em instalação nova, sem o binário e após backup:

```sh
sudo python3 docker/server/casaos/install.py --stage "$PWD/deploy-state/casaos-stage" --install
```

Verifique `sudo systemctl is-active casaos-gateway casaos rclone` e `curl -I http://127.0.0.1:81/`. Abra `http://IP-LAN:81/` e crie uma conta CasaOS. Se houve falha depois da instalação, use o [diagnóstico CasaOS](CASAOS.md), sem forçar uma instalação nova sobre a anterior. O script não instala Portainer.

## 7. Preparar o Home Assistant

```sh
sudo python3 docker/server/homeassistant/prepare.py
sudo nano .env
```

Acrescente seu overlay à seleção existente, por exemplo:

```dotenv
COMPOSE_FILE=compose.server.yaml:compose.homeassistant.yaml
```

Se houver override VPN host ou outros módulos, mantenha-os na lista. Então:

```sh
sudo docker compose config --quiet
sudo docker compose up -d homeassistant
curl -I --connect-timeout 5 http://127.0.0.1:8123/
```

Abra `http://IP-LAN:8123` para criar o proprietário. Consulte [HOMEASSISTANT.md](HOMEASSISTANT.md) se a configuração já existia; o preparador preserva arquivos e não corrige automaticamente um IP antigo.

## 8. Preparar openGym e o volume Garmin

Com o Tailscale do contêiner autenticado:

```sh
sudo python3 docker/server/opengym/prepare.py
sudo install -d -m 700 -o 65534 -g 65534 data/garmin
sudo nano .env
```

Mantenha OPENGYM_ORIGIN criada pelo preparador e acrescente o overlay:

```dotenv
COMPOSE_FILE=compose.server.yaml:compose.homeassistant.yaml:compose.opengym.yaml
```

```sh
sudo docker compose config --quiet
sudo docker compose up -d --build opengym-api opengym-garmin opengym-web
sudo docker compose up -d --no-deps --force-recreate monitor
curl -I --connect-timeout 5 http://127.0.0.1:8081/
```

Esse preparador depende do nome `auroralab-tailscale-1` quando não há ambiente openGym existente. Para VPN no host, faça a preparação alternativa de [OPENGYM.md](OPENGYM.md). Não altere RP_ID/ORIGIN de perfis existentes por tentativa.

## 9. Configurar os endereços HTTPS privados

Na instalação com VPN no contêiner, examine as rotas existentes e configure somente os serviços ativos:

```sh
sudo docker compose exec tailscale tailscale serve status
sudo docker compose exec tailscale tailscale serve --bg --https=443 http://127.0.0.1:8088
sudo docker compose exec tailscale tailscale serve --bg --https=81 http://127.0.0.1:81
sudo docker compose exec tailscale tailscale serve --bg --https=8123 http://127.0.0.1:8123
sudo docker compose exec tailscale tailscale serve --bg --https=8081 http://127.0.0.1:8081
```

Para o proxy Cockpit autoassinado, após avaliar a confiança do trecho local conforme [COCKPIT.md](COCKPIT.md):

```sh
sudo docker compose exec tailscale tailscale serve --bg --https=9090 https+insecure://127.0.0.1:9090
sudo docker compose exec tailscale tailscale serve status
```

Siga a ativação de HTTPS solicitada pelo Tailscale e use os domínios reais exibidos. Não ative Funnel neste roteiro. No celular/computador de origem, mantenha Tailscale conectado e abra o domínio HTTPS, com a porta de cada serviço. Em openGym, crie o primeiro perfil e uma segunda passkey de recuperação. O botão Garmin usa a mesma sessão; conecte a conta Garmin somente na página privada. Veja [GARMIN.md](GARMIN.md) para prévia e importação.

## 10. Adicionar energia e dispositivos opcionais

Energia requer sensores e um dispositivo de brilho compatível. Leia a seção USB/energia abaixo, ajuste BACKLIGHT_PATH e prepare:

```sh
sudo sh docker/server/power/prepare.sh
```

Só então acrescente `compose.power.yaml` à lista COMPOSE_FILE e execute `sudo docker compose up -d --build power`. Se o hardware não existe, omita esse overlay: instalar todos os serviços não cria sensores nem dispositivos USB.

Para a impressora, acrescente `compose.printer.yaml` após configurar PRINTER_DEVICE. Para câmera, configure CAMERA_DEVICE e habilite o perfil `camera`. Não teste a instalação iniciando uma impressão sem supervisão.

## 11. Criar os atalhos CasaOS

Depois de criar a conta na interface, descubra seu ID:

```sh
sudo find /var/lib/casaos -mindepth 2 -maxdepth 2 -name app_order.json
sudo install -d -m 700 deploy-state
```

Substitua o ID 1 se necessário; confira a prévia antes de aplicar:

```sh
sudo python3 docker/server/casaos/sync-shortcuts.py --user-id 1
sudo python3 docker/server/casaos/sync-shortcuts.py --user-id 1 --apply
```

O sincronizador não cria novos contêineres e usa destinos LAN. Alguns componentes internos apontam para Portainer, que precisa existir separadamente; os atalhos não exibem estado vivo. Limites, backup e reversão: [CASAOS.md](CASAOS.md).

## 12. Validar a instalação completa

Depois de preparar todos os módulos selecionados:

```sh
sudo docker compose config --quiet
sudo docker compose ps -a
sudo docker compose logs --tail=100
sudo docker compose run --rm --no-deps --entrypoint php php tests/run.php
sudo cat data/backup-status/fitness-backup.json
```

Confirme cada login, leitura de dados, rede/VPN, proxy, backup verificado e cópia externa. Serviços em `restarting` ou `exited` precisam de diagnóstico antes de declarar a instalação concluída. Registre o commit, a versão e os testes realmente feitos. Para erros conhecidos, use [SOLUCAO-DE-PROBLEMAS.md](SOLUCAO-DE-PROBLEMAS.md).

## Portas e serviços

| Recurso | Acesso configurado |
| --- | --- |
| Portal Nginx | HTTP 80 e 8088, conforme BIND_IP |
| PHP-FPM | 9000 interna à rede Docker; sem publicação no host |
| OctoPrint | HTTP 5000 |
| Samba | TCP 445, compartilhamento Prints, usuário rafael |
| Monitor | HTTP 9101 na rede host; preferir o proxy do portal |
| CasaOS | HTTP 81 no Debian, após instalação |
| Cockpit | HTTPS 9090 no loopback e SERVER_IP; backend 9091 restrito |
| Home Assistant | HTTP 8123 no loopback e IP configurado, após preparação |
| openGym | HTTP 8081 apenas em 127.0.0.1; HTTPS privado depende de Serve |
| Garmin | Sem nova porta no host; `/garmin/` no openGym |
| Energia | HTTP 9110 apenas em 127.0.0.1, encaminhado pelo monitor |
| Câmera | HTTP 8080 quando o perfil estiver ativo |

Veja [rede e firewall](REDE-E-TAILSCALE.md). HTTPS via Tailscale Serve e autenticação dos aplicativos são configurações distintas. As portas de administração não devem ser liberadas indiscriminadamente para a internet.

## USB e energia

Identifique dispositivos por caminhos persistentes, como `/dev/serial/by-id/...` e `/dev/v4l/by-id/...`, e ajuste `.env`. Acrescente `compose.printer.yaml` à lista `COMPOSE_FILE` somente quando a impressora estiver pronta; ela será exposta ao OctoPrint como `/dev/ttyPrinter`.

```sh
sudo docker compose up -d octoprint
sudo docker compose --profile camera up -d --build camera
```

A câmera é opcional; o caminho padrão é propositalmente inexistente. O portal usa `/camera-stream`; confirme a imagem e a conexão serial antes de iniciar uma impressão.

Para energia, confira `/sys/class/backlight` e defina `BACKLIGHT_PATH` para um dispositivo existente. O overlay padrão supõe `intel_backlight`, que não existe em todo hardware.

```sh
sudo sh docker/server/power/prepare.sh
```

Acrescente `compose.power.yaml` a `COMPOSE_FILE`, valide e inicie `sudo docker compose up -d --build power`. A chave administrativa fica em `secrets/power-admin.key`; não é a senha Linux. Leituras RAPL/bateria não representam necessariamente o consumo da tomada. Perfis e brilho só estão disponíveis quando suportados. Suspensão automática e mudanças de drivers não fazem parte dessa preparação. Testes locais: `python3 docker/server/power/test_power.py`.

## Persistência e backup

`data/fitness/`, `data/octoprint/`, `data/prints/`, `data/samba/`, `data/monitor/`, `data/power/`, `data/homeassistant/`, `data/opengym/` e `data/garmin/` guardam estados separados. `data/tailscale/` é a identidade do contêiner; não é o estado da VPN instalada no Debian.

O backup automático roda ao iniciar e a cada 24 horas, inclui os volumes/configurações montados, snapshots SQLite e a pasta `docs/`. Não há criptografia, cópia externa nem retenção automática. O estado Tailscale do host, `deploy-state/` e dados de novos aplicativos CasaOS em `/DATA/AppData` não são cobertos automaticamente. Confira o escopo antes de depender da cópia. Procedimento de verificação e restauração: [ATUALIZACAO.md](ATUALIZACAO.md).

O portátil usa `data/fitness.sqlite3`. Para migrar esse banco ao servidor, faça cópia consistente com os escritores parados e restaure em `data/fitness/fitness.sqlite3`. Não há sincronização automática com outra máquina, nem migração automática de Fitness para openGym.

## Diagnóstico

Consulte [SOLUCAO-DE-PROBLEMAS.md](SOLUCAO-DE-PROBLEMAS.md) para erros de socket Docker, contêiner reiniciando, arquivos ausentes, órfãos e falhas de acesso. Não use `--remove-orphans`, remoção de volumes ou reinstalação completa como tentativa genérica de reparo.
