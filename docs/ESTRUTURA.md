# Estrutura e arquitetura — AuroraLAB 20.0.0

Este documento descreve o código atual, não o estado de uma máquina específica. Os caminhos de código são relativos à raiz do repositório; os links entre guias são relativos a `docs/`.

## Mapa do projeto

```text
aurora-lab/
├── backend/
│   ├── public/index.php       # Entrada HTTP da API Fitness
│   ├── bootstrap.php          # Composição de dependências
│   ├── config/database.php    # Caminho SQLite
│   ├── routes/api.php         # Método/action → controller
│   ├── src/
│   │   ├── Http/              # Controllers, Requests, Application e JsonResponse
│   │   ├── Services/          # Regras e sincronização
│   │   ├── Repositories/      # SQL e mapeamento
│   │   ├── Database/          # Conexão, transações, Migrator
│   │   └── Exceptions/        # Validação e conflitos
│   ├── database/              # Migrations e seed
│   ├── bin/migrate.php
│   ├── tests/run.php
│   └── composer.json
├── site/                      # Interface, PWA e ícones
├── docker/
│   ├── Dockerfile             # PHP portátil e servidor
│   ├── nginx.conf             # Proxy portátil
│   └── server/                # Monitor, backup, preparação e imagens dos módulos
├── docs/                      # Guias, histórico e diagnóstico
├── skills/                    # Padrões reutilizáveis
├── compose.yaml               # Portátil: web e php
├── compose.server.yaml        # Servidor Linux: projeto auroralab
├── compose.homeassistant.yaml
├── compose.opengym.yaml       # API/web openGym e importador Garmin
├── compose.power.yaml
├── compose.printer.yaml
├── VERSION
└── README.md
```

## Interface e módulos

O frontend usa HTML/CSS/JavaScript sem build obrigatório. Layout compacto, temas e atalhos são compartilhados. A PWA versiona o cache; endpoints dinâmicos e redirects externos não devem ser tratados como dados offline permanentes.

Desde a versão 7, Fitness/planos/exercícios saíram da navegação; os arquivos e a API continuam no repositório. O módulo atual openGym usa imagens externas fixadas por digest e dados próprios. O servidor redireciona `/opengym`, o legado `/opengym.html` e `/garmin` pelo monitor para a origem HTTPS configurada. O portátil não possui esse monitor nem instala esses serviços.

## API Fitness em camadas

`/fitness-api → public/index.php → Application → Controller → Request → Service → Repository → SQLite`

Controllers adaptam entrada/chamada; Requests validam tipos e limites; Services aplicam regras e coordenam transações; Repositories concentram SQL. JsonResponse produz cabeçalhos/status/JSON, e Application converte erros conhecidos ou registra falhas internas. Não há Views PHP: a apresentação está no frontend. Autoload PSR-4 usa namespace Aurora.

| Método | action | Operação |
| --- | --- | --- |
| GET | ausente ou desconhecida | Estado de perfis/registros, por compatibilidade |
| GET | catalog | Catálogo de exercícios |
| GET | plans | Planos; exige query person |
| POST | save ou ausente | Salvar estado com expectedRevision |
| POST | import | Inicializar apenas se ainda não houver estado |
| POST | merge | Mesclar por id/updatedAt, servidor vence empate |
| POST | save_plans | Fichas A/B/C/D e agenda |
| POST | save_catalog_exercise | Criar/editar exercício |
| POST | delete_catalog_exercise | Excluir quando não está em planos |

Validação retorna 400; conflito 409; corpo acima de 2 MB 413; método não suportado 405; falha interna 500. Nomes JSON camelCase e revisões independentes de estado/planos são preservados. `save` valida calendário, datas futuras, duplicidade pessoa/data e peso; import/merge mantêm compatibilidade legada. Exclusões lógicas são preservadas e a exclusão de perfil remove seus planos.

## SQLite e migrations

FITNESS_DB_PATH escolhe o banco, por padrão `/var/lib/fitness/fitness.sqlite3`. O portátil monta `data/`; o servidor monta `data/fitness/`. Transaction usa BEGIN IMMEDIATE e rollback em exceções. A inicialização aplica migrations como www-data antes de iniciar PHP-FPM. `schema_migrations` registra versões; o seed inicial roda uma vez. Não há seed executado em toda requisição nem migração automática para openGym.

O backend fica na imagem, fora da raiz pública Nginx. Rebuild é necessário para suas alterações; `site/` continua montado do host. Os contextos Docker têm regras próprias: o contexto PHP inclui apenas backend e arquivos necessários; imagens dos módulos usam seus diretórios como contextos. Não acrescente dados/segredos aos contextos de build.

## Serviços e limites

| Componente | Papel e implementação |
| --- | --- |
| web | Conteúdo estático, API FastCGI e proxies/redirects do ambiente |
| monitor | Python em rede host; /proc e /sys somente leitura, sem Docker socket |
| backup | Python, snapshots SQLite, validação e arquivo com SHA-256 |
| octoprint | Python 3.12, OctoPrint 1.11.8, s6-overlay e plugins fixados |
| samba | Prints autenticado; conta rafael fixada nos arquivos atuais |
| camera | Perfil opcional, uStreamer e dispositivo USB explícito |
| tailscale | Daemon em rede host; pode conflitar com a instalação Debian |
| cockpit | Nginx HTTPS 9090 para backend Cockpit/PAM nativo 9091 |
| CasaOS | Serviços systemd no Debian, não um serviço Compose Aurora |
| homeassistant | Container com rede host e configuração própria |
| opengym-api/web | Rede Docker dedicada, API interna e web loopback 8081 |
| opengym-garmin | Serviço Python sem porta extra no host, integrado pelo proxy web |
| power | Telemetria/controles locais, mounts específicos de CPU/brilho |

Os preparadores openGym/Cockpit ainda consultam o nome fixo do contêiner VPN. Os atalhos CasaOS são LinkApps, não monitoramento vivo. Monitor usa SERVER_IP e varredura ICMP /24; alguns diagnósticos são textos estáticos de referência e não comprovam hardware conectado. Sensores ausentes devem continuar indisponíveis, sem inventar zero.

## Persistência e backup

Os estados ficam separados em `data/fitness`, `octoprint`, `prints`, `samba`, `monitor`, `power`, `homeassistant`, `opengym`, `garmin` e `tailscale`. CasaOS e Cockpit também têm configuração nativa em `/etc` e `/var/lib`. `.env`, `secrets`, `backups` e `deploy-state` não entram no Git.

O backup monta explicitamente suas origens no Compose, incluindo `docs/`. Usa snapshots dos SQLite reconhecidos e valida JSON openGym individualmente. Não há transação global entre todos os aplicativos. Ele exige o banco Fitness e valida o histórico PrintHistory quando presente. Estado VPN do host, deploy-state e aplicativos CasaOS novos não são incluídos automaticamente. Restauração e cópia externa: [ATUALIZACAO.md](ATUALIZACAO.md).

## Validação e evolução

Testes PHP: `docker compose run --rm --no-deps --entrypoint php php tests/run.php`, com a seleção correta do ambiente e imagem construída. Alternativa local em backend: `composer dump-autoload` e `php tests/run.php`, com PHP/PDO SQLite. Energia: `python3 docker/server/power/test_power.py` em Linux. Garmin: `python3 -m unittest discover -s docker/server/garmin -p 'test_*.py' -v`, com dependências de teste disponíveis conforme [GARMIN.md](GARMIN.md).

Os testes sintéticos não substituem login real, restore real ou impressão física. Verifique Compose com config --quiet e use fixtures temporárias; não teste gravando dados pessoais.

Padrões: [desenvolvimento](../skills/aurora-development/SKILL.md) e [visual](../skills/aurora-visual/SKILL.md). Procedimentos operacionais: [servidor](AURORASERVER.md), [rede](REDE-E-TAILSCALE.md), [CasaOS](CASAOS.md), [Cockpit](COCKPIT.md), [Home Assistant](HOMEASSISTANT.md), [openGym](OPENGYM.md), [Garmin](GARMIN.md) e [OctoPrint](UPGRADE-PYTHON-OCTOPRINT.md).


## HomeBoard e retirada do CasaOS (v15)

`compose.homeboard.yaml` acrescenta HomeBoard na rede Docker com porta local 8090. `docker/server/homeboard/prepare.py` confere a fonte upstream fixada e constroi a imagem sem versionar o arquivo de terceiros. Portal/monitor possuem atalho e status HomeBoard. Dados em `data/homeboard/` e `data/homeboard-photos/`, incluidos no backup; logind e a configuracao XFCE tambem sao copiados. CasaOS foi retirado do escopo atual; seus scripts anteriores ficam como historico/retorno. Administracao de containers permanece no Portainer e do host no Cockpit. Consulte [HOMEBOARD.md](HOMEBOARD.md).


## Atalhos HTTPS e câmera USB (16.0.0)

`openPort` encaminha 5000, 9090 e 8123 para `/octoprint`, `/cockpit` e `/homeassistant`. O Nginx do servidor repassa ao monitor, que usa o hostname HTTPS privado de `OPENGYM_ORIGIN` e a porta própria de cada serviço. Isso funciona mesmo com o portal aberto por HTTP/IP e evita certificados incompatíveis com o IP Tailscale. Os serviços precisam estar publicados no Tailscale Serve; o portátil não oferece esses módulos. Origem ausente/inválida retorna 503, sem redirecionar para HTTP. `/homeboard` usa `HOMEBOARD_ORIGIN`; `/garmin` e `/opengym` mantêm seus destinos. Testes isolados: `python3 -m unittest discover -s docker/server -p test_service_links.py` em Linux, sem acesso aos bancos.

A câmera fica no perfil Compose `camera`: configure `CAMERA_DEVICE` com `/dev/v4l/by-id/<camera-externa>-video-index0` e acrescente `camera` a `COMPOSE_PROFILES` no `.env`, preservando os demais perfis. Inicie apenas `docker compose up -d --build camera`. Nunca selecione automaticamente a câmera integrada. O container recebe somente esse dispositivo como `/dev/video0`; `/camera-stream` transmite pelo proxy da mesma origem do portal, sem cache offline. Confirme a captura em `http://127.0.0.1:8080/snapshot` no servidor e o estado `webcam` no monitor. Após desconectar/reconectar USB, pode ser necessário recriar somente `camera` com `docker compose up -d --no-deps --force-recreate camera`. Sem o dispositivo, mantenha esse perfil desativado. Acesso direto à porta 8080 é HTTP; prefira o stream do portal pelo Tailscale.


## Garmin Personal API

`docker/server/garmin/personal_api.py` concentra o cliente oficial de leitura; `server.py` valida a chave por perfil em `/garmin/personal`, mantém a credencial fora do Git e reutiliza mapeamento/ledger de importações. A interface privada aceita a chave sem solicitar senha Garmin. O conector comunitário continua como opção anterior, sem fallback automático quando a chave oficial falha. Validação: suíte `test_personal_api.py` junto de `test_garmin.py`. Veja [GARMIN.md](GARMIN.md).


`docker/server/garmin/auto_sync.py` agenda a leitura do treino mais recente a cada hora e usa o pareamento nativo openGym. Configuração e autorização ficam por perfil no volume Garmin, sem segredo global do backend. `write_records` em server.py centraliza importação manual/automática com a mesma proteção de revisão/duplicatas. O painel expõe ativação, pausa e execução imediata; o container retoma a agenda após reiniciar.


## Gráficos openGym (19.0.0)

`docker/server/opengym/` reconstrói somente o frontend do commit upstream 1.4.1 fixado, aplicando patch e componentes React versionados. Home e Stats compartilham progresso, tempo de sessão e calorias Garmin. O backend segue a imagem oficial. O importador acrescenta calorias válidas aos novos resumos; enrich_calories/backfill_calories preenchem somente calorias ausentes em treinos Garmin existentes, com controle de revisão e snapshot antes da gravação, sem recriar exclusões ou modificar outras propriedades. A agenda horária mantém o comportamento de importar somente o último treino. Ver [personalização e testes](../docker/server/opengym/README.md).


## Fundo e painéis openGym (20.0.0)

O frontend personalizado inclui a foto original em public/aurora-background.jpg e estilos de fundo para temas claro/escuro. HomePanels e home-panels.js organizam cada cartão do Início com arraste por ponteiro e controles acessíveis. A preferência auroraHomePanels usa o estado e a sincronização por perfil existentes; não há mudança na API ou nos treinos. TrainingMetrics aceita um filtro de métrica para minutos/calorias independentes no Início; Estatísticas mantém o conjunto anterior. O service worker acrescenta a foto ao cache opcional. Veja o README da personalização e testes HomePanels.test.jsx.
