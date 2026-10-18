# AuroraLAB 13.0.0

Portal de Home Lab com impressora 3D, monitoramento, backups e acesso a serviços independentes. O módulo de treinos atual é o **openGym**, com passkeys e importação opcional de atividades Garmin. O Fitness original e sua API PHP permanecem disponíveis para acesso direto e recuperação dos registros anteriores, sem migração automática.

Este README acompanha a versão registrada em [`VERSION`](VERSION). Os guias operacionais ficam em [`docs/`](docs/); os padrões de trabalho, em [`skills/`](skills/).

## Escolha o ambiente

| Ambiente | Configuração | Conteúdo |
| --- | --- | --- |
| Portátil | `compose.yaml` | Nginx, interface e API Fitness PHP/SQLite; sem os serviços do servidor |
| Servidor Linux | `compose.server.yaml` | Portal, Fitness, OctoPrint, Samba, monitoramento e backup; Tailscale e proxy Cockpit dependem de preparação |
| Módulos adicionais | Arquivos `compose.*.yaml` | Home Assistant, openGym/Garmin, energia e dispositivo da impressora |

Os dois ambientes usam a porta 8088. Escolha um por instalação. O servidor completo usa recursos do Linux amd64 e scripts destinados ao Debian; o portátil pode rodar no Docker Desktop com contêineres Linux.

## Execução portátil

Com Git e Docker/Compose disponíveis:

```sh
git clone https://github.com/marlima10/aurora-lab.git
cd aurora-lab
docker compose -f compose.yaml up -d --build
docker compose -f compose.yaml ps
```

Abra [o portal](http://localhost:8088/). PHP e Composer são preparados na imagem. Esse modo não instala openGym, CasaOS ou monitoramento de hardware. Os antigos registros Fitness ficam em `data/fitness.sqlite3`; páginas legadas podem ser abertas diretamente em `/fitness.html`, `/fitness-planos.html` e `/fitness-exercicios.html`, embora tenham saído da navegação principal.

Para o servidor Debian, siga a [instalação completa](docs/AURORASERVER.md), inclusive a escolha entre Tailscale no host e no contêiner. Não use o comando do portátil para atualizar uma instalação completa.

## Serviços e recursos

- Portal responsivo, temas, atalhos e cache PWA.
- OctoPrint para impressora 3D, catálogo de plugins fixados e câmera USB opcional.
- Métricas do host, rede, armazenamento e status de backup.
- Samba autenticado para arquivos de impressão.
- CasaOS instalado no Debian, com atalhos para serviços existentes.
- Cockpit com autenticação local Debian e proxy HTTPS, sem habilitar senha no SSH.
- Home Assistant Container e openGym em serviços separados.
- Garmin → openGym com prévia, seleção e proteção contra duplicatas.
- Módulo opcional de energia; disponibilidade depende dos sensores e dispositivos do host.

Cada módulo exige sua preparação. Portainer é apenas um destino de alguns atalhos CasaOS; não é instalado pelos arquivos Compose deste repositório.

## Arquitetura e dados

```text
aurora-lab/
├── backend/       # API Fitness: Controllers, Requests, Services e Repositories
├── site/          # HTML, CSS, JavaScript, ícones e PWA
├── docker/        # Imagens, proxies e preparação dos serviços
├── docs/          # Instalação, operação, arquitetura e histórico
├── skills/        # Padrões visuais e de desenvolvimento
├── data/          # Dados locais; fora do Git
├── secrets/       # Credenciais locais; fora do Git
├── backups/       # Cópias locais; fora do Git
├── deploy-state/  # Registros e materiais locais de implantação; fora do Git
├── compose.yaml
├── compose.server.yaml
├── VERSION
└── README.md
```

Dados e segredos não acompanham o clone. O servidor usa `data/fitness/fitness.sqlite3`; o portátil usa `data/fitness.sqlite3`. openGym usa arquivos próprios em `data/opengym/`. Preserve esses caminhos e os domínios usados pelas passkeys ao mover uma instalação.

## Operação e testes

No portátil, mantenha `-f compose.yaml` nos comandos. No servidor, registre a combinação de arquivos em `COMPOSE_FILE`, conforme o [guia do servidor](docs/AURORASERVER.md), e use essa mesma combinação em todas as operações.

```sh
docker compose -f compose.yaml logs --tail=100
docker compose -f compose.yaml stop
docker compose -f compose.yaml start
docker compose -f compose.yaml run --rm --no-deps --entrypoint php php tests/run.php
```

A suíte PHP cria bancos temporários. Testes do importador Garmin usam dados sintéticos:

```sh
python3 -m unittest discover -s docker/server/garmin -p 'test_*.py' -v
```

Alterações no backend exigem rebuild. Antes de atualizar serviços com dados, siga o procedimento de [backup e atualização](docs/ATUALIZACAO.md). A publicação de uma release não atualiza automaticamente o servidor.

## Acesso

Na LAN, use o IP local do servidor e a porta correspondente. IPs `100.x` e domínios privados Tailscale exigem o cliente conectado à tailnet e permissão para o serviço. A publicação de HTTPS privado via Serve é uma configuração separada.

Portal e Fitness não têm login; CasaOS, Cockpit, Home Assistant e openGym possuem autenticação própria. Não publique o portal/Fitness na internet sem definir controle de acesso. Veja [rede, portas e Tailscale](docs/REDE-E-TAILSCALE.md).

## Documentação

| Guia | Conteúdo |
| --- | --- |
| [AuroraServer](docs/AURORASERVER.md) | Instalação Linux, configuração, serviços e persistência |
| [Reinstalação do zero](docs/REINSTALACAO.md) | Exclusão deliberada dos dados e troca da VPN do host pelo contêiner |
| [Atualização](docs/ATUALIZACAO.md) | Git, backup, implantação, retorno, PR e release |
| [Estrutura](docs/ESTRUTURA.md) | Arquitetura, API, módulos e caminhos |
| [Rede e Tailscale](docs/REDE-E-TAILSCALE.md) | LAN, VPN, portas, firewall e conflito de instâncias |
| [Solução de problemas](docs/SOLUCAO-DE-PROBLEMAS.md) | Erros de Git, Docker, preparação e acesso |
| [CasaOS](docs/CASAOS.md) | Instalação nova, diagnóstico e atalhos |
| [Cockpit](docs/COCKPIT.md) | Preparação do backend Debian e proxy HTTPS |
| [Home Assistant](docs/HOMEASSISTANT.md) | Configuração, acesso e recuperação |
| [openGym](docs/OPENGYM.md) | Passkeys, preparação, HTTPS e dados |
| [Garmin](docs/GARMIN.md) | Instalação, importação e limites |
| [OctoPrint/Python](docs/UPGRADE-PYTHON-OCTOPRINT.md) | Build, plugins e retorno de imagem |
| [Docker portátil](docs/LEIA-ME-DOCKER-PORTATIL.md) | Ambiente reduzido para outro computador |
| [Histórico](docs/CHANGELOG.md) | Alterações por versão |

Padrões: [desenvolvimento](skills/aurora-development/SKILL.md) e [visual](skills/aurora-visual/SKILL.md). As skills ficam versionadas no projeto; não pressupõem instalação global.
