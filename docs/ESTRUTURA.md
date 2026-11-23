# Estrutura e arquitetura — AuroraLAB 48.0.0

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
├── compose.opengym.yaml       # API/web openGym e importador Garmin
├── compose.power.yaml
├── compose.mirror.yaml
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
| samba | Prints autenticado; conta rafael fixada nos arquivos atuais |
| tailscale | Daemon em rede host; pode conflitar com a instalação Debian |
| cockpit | Nginx HTTPS 9090 para backend Cockpit/PAM nativo 9091 |
| CasaOS | Serviços systemd no Debian, não um serviço Compose Aurora |
| opengym-api/web | Rede Docker dedicada, API interna e web loopback 8081 |
| opengym-garmin | Serviço Python sem porta extra no host, integrado pelo proxy web |
| power | Telemetria/controles locais, mounts específicos de CPU/brilho |

Os preparadores openGym/Cockpit ainda consultam o nome fixo do contêiner VPN. Os atalhos CasaOS são LinkApps, não monitoramento vivo. Monitor usa SERVER_IP e varredura ICMP /24; alguns diagnósticos são textos estáticos de referência e não comprovam hardware conectado. Sensores ausentes devem continuar indisponíveis, sem inventar zero.

## Persistência e backup

Os estados ficam separados em `data/fitness`, `prints`, `samba`, `monitor`, `power`, `opengym`, `garmin` e `tailscale`. CasaOS e Cockpit também têm configuração nativa em `/etc` e `/var/lib`. `.env`, `secrets`, `backups` e `deploy-state` não entram no Git.

O backup monta explicitamente suas origens no Compose, incluindo `docs/`. Usa snapshots dos SQLite reconhecidos e valida JSON openGym individualmente. Não há transação global entre todos os aplicativos. Ele exige o banco Fitness e valida o histórico PrintHistory quando presente. Estado VPN do host, deploy-state e aplicativos CasaOS novos não são incluídos automaticamente. Restauração e cópia externa: [ATUALIZACAO.md](ATUALIZACAO.md).

## Validação e evolução

Testes PHP: `docker compose run --rm --no-deps --entrypoint php php tests/run.php`, com a seleção correta do ambiente e imagem construída. Alternativa local em backend: `composer dump-autoload` e `php tests/run.php`, com PHP/PDO SQLite. Energia: `python3 docker/server/power/test_power.py` em Linux. Garmin: `python3 -m unittest discover -s docker/server/garmin -p 'test_*.py' -v`, com dependências de teste disponíveis conforme [GARMIN.md](GARMIN.md).

Os testes sintéticos não substituem login real, restore real ou impressão física. Verifique Compose com config --quiet e use fixtures temporárias; não teste gravando dados pessoais.

Padrões: [desenvolvimento](../skills/aurora-development/SKILL.md) e [visual](../skills/aurora-visual/SKILL.md). Procedimentos operacionais: [servidor](AURORASERVER.md), [rede](REDE-E-TAILSCALE.md), [CasaOS](CASAOS.md), [Cockpit](COCKPIT.md), [openGym](OPENGYM.md), [Garmin](GARMIN.md).


## Aplicativos retirados

Home Assistant e HomeBoard foram removidos na versão 31. Os guias antigos registram somente o histórico. Portainer e Cockpit permanecem disponíveis.

## Atalhos HTTPS e câmera USB (16.0.0)

`openPort` encaminha 9090 para `/cockpit`. O Nginx do servidor repassa ao monitor, que usa o hostname HTTPS privado de `OPENGYM_ORIGIN` e a porta própria de cada serviço. Isso funciona mesmo com o portal aberto por HTTP/IP e evita certificados incompatíveis com o IP Tailscale. Os serviços precisam estar publicados no Tailscale Serve; o portátil não oferece esses módulos. Origem ausente/inválida retorna 503, sem redirecionar para HTTP. `/garmin` e `/opengym` mantêm seus destinos. Testes isolados: `python3 -m unittest discover -s docker/server -p test_service_links.py` em Linux, sem acesso aos bancos.



## Garmin Personal API

`docker/server/garmin/personal_api.py` concentra o cliente oficial de leitura; `server.py` valida a chave por perfil em `/garmin/personal`, mantém a credencial fora do Git e reutiliza mapeamento/ledger de importações. A interface privada aceita a chave sem solicitar senha Garmin. O conector comunitário continua como opção anterior, sem fallback automático quando a chave oficial falha. Validação: suíte `test_personal_api.py` junto de `test_garmin.py`. Veja [GARMIN.md](GARMIN.md).


`docker/server/garmin/auto_sync.py` agenda a leitura dos 5 treinos mais recentes a cada hora e usa o pareamento nativo openGym. Configuração e autorização ficam por perfil no volume Garmin, sem segredo global do backend. `write_records` em server.py centraliza importação manual/automática com a mesma proteção de revisão/duplicatas. O painel expõe ativação, pausa e execução imediata; o container retoma a agenda após reiniciar.


## Gráficos openGym (19.0.0)

`docker/server/opengym/` reconstrói somente o frontend do commit upstream 1.4.1 fixado, aplicando patch e componentes React versionados. Home e Stats compartilham progresso, tempo de sessão e calorias Garmin. O backend segue a imagem oficial. O importador acrescenta calorias válidas aos novos resumos; enrich_calories/backfill_calories preenchem somente calorias ausentes em treinos Garmin existentes, com controle de revisão e snapshot antes da gravação, sem recriar exclusões ou modificar outras propriedades. A agenda horária mantém o comportamento de consultar os 5 treinos mais recentes. Ver [personalização e testes](../docker/server/opengym/README.md).


## Fundo e painéis openGym (20.0.0)

O frontend personalizado inclui a foto original em public/aurora-background.jpg e estilos de fundo para temas claro/escuro. HomePanels e home-panels.js organizam cada cartão do Início com arraste por ponteiro e controles acessíveis. A preferência auroraHomePanels usa o estado e a sincronização por perfil existentes; não há mudança na API ou nos treinos. TrainingMetrics aceita um filtro de métrica para minutos/calorias independentes no Início; Estatísticas mantém o conjunto anterior. O service worker acrescenta a foto ao cache opcional. Veja o README da personalização e testes HomePanels.test.jsx.


## Janela Garmin (21.0.0)

AutoSync usa ACTIVITY_LIMIT=5, preservando intervalo de 3600 segundos, pareamento e agenda persistida. Respostas acima do limite e lotes com atividades inválidas falham antes de gravar. Novos registros são enviados em ordem cronológica, mantendo deduplicação e proteção de exclusões. A interface e o status público informam o limite.


## Operação e metas (22.0.0)

`WeeklyGoals` e `weekly-goals.js` calculam metas por semana local, usando os mesmos registros e métricas existentes. A preferência auroraWeeklyGoals usa update/stampChange/merge nativo. `GarminSummary` consulta /garmin/status e envia /garmin/sync na mesma origem autenticada; o service worker exclui /garmin/ do cache. Os dois cartões integram HomePanels; metas aparecem também em Stats.

`alerts.py`, montado no monitor, persiste transições em data/monitor/alerts.json sem Docker socket. /api/alerts.json expõe eventos sanitizados ao portal; operações não são comandos remotos. `restore_check.py` valida restauração em diretório temporário privado e o backup grava data/backup-status/restore-check.json, servido pelo monitor como /api/restore-check.json. Os endpoints continuam no acesso privado existente do portal.

PowerService mantém data/power/daily-energy.json, até 90 datas America/Sao_Paulo, com CPU e descarga separadas e segundos de cobertura. /api/power inclui daily_energy; power.js aplica a tarifa local somente como custo parcial das leituras. Histórico não retroativo, sem extrapolação dos períodos ausentes. Consulte [release 22](RELEASE-22.md).


## Manyfold, Mealie e Actual Budget (23.0.0)

Três overlays opcionais acrescentam os aplicativos, redes e volumes independentes. Manyfold usa a imagem padrão com SQLite e Redis separado; Mealie e Actual usam SQLite local. docker/server/apps/ contém preparação idempotente, bootstrap restrito à instalação nova e images.lock.json. Dados em data/manyfold, data/manyfold-redis, data/mealie e data/actual; credenciais somente em secrets/.

Os overlays estendem os mounts do backup e as flags MANYFOLD_ENABLED/MEALIE_ENABLED/ACTUAL_ENABLED do monitor. O coletor adiciona status somente dos módulos ativos; novos redirects usam o mesmo hostname HTTPS privado validado. Portal/menu/PWA acrescentam atalhos, sem mudar os aplicativos existentes. restore_check.py exige banco de cada módulo declarado por seu Compose arquivado. Detalhes em APPS.md e RELEASE-23.md.


## Cabeçalhos de segurança e limites do Nginx (24.0.0)

`docker/server/nginx-security-headers.conf` é montado em `/etc/nginx/aurora-security-headers.conf` pelo serviço `web` e incluído no bloco `server` e em todo `location` que declara `add_header`, porque o Nginx não herda os cabeçalhos do `server` quando o `location` define algum próprio. Um novo `location` com `add_header` precisa repetir o `include`; `test_nginx_security.py` falha caso contrário. `server_tokens` fica desligado.

POST em `/api/power` e `/fitness-api` tem limite por IP (`aurora_power_post`: 6/min com rajada 5; `aurora_api_post`: 120/min com rajada 40). GET não é limitado, então o polling de status continua livre. O excesso retorna 429 em JSON (`@aurora_rate_limited`), com `Retry-After`. A tela de energia avisa quando é aberta por HTTP fora de localhost; o portal continua funcionando por HTTP. A estrutura de rede e as portas não mudam. Detalhes e passos manuais opcionais: [RELEASE-24.md](RELEASE-24.md).


## Autenticação central opcional (24.0.0)

`compose.auth.yaml` acrescenta `auth`, `auth-gateway` e `ha-sso`, configura os adaptadores nativos e retira publicações de portas antigas. Só participa da seleção Compose após migração explícita. `docker/server/auth/` contém Store SQLite, HTTP/CSRF, interface administrativa, renderizador do gateway, preparador privado, Dockerfiles fixados, adaptadores e unidades do socket Unix Cockpit.

`data/auth/auth.sqlite3` guarda hashes de chaves e sessões, cadastros, permissões e auditoria; `secrets/sso/` guarda inventário, segredos de comunicação e chave inicial. Nenhum desses caminhos entra no Git. O preparador não altera a seleção Compose nem os bancos nativos e deixa as integrações bloqueadas até validação. Backup/restore incluem autenticação quando o overlay está ativo.

`/auth/` serve a entrada e a conta; somente o administrador `aurora@server.local` acessa cadastro/geração/revogação. A chave tem 151 caracteres; o cookie central é HTTPS/HttpOnly e não chega aos aplicativos nativos. O gateway protege as nove interfaces (portal e oito apps), vincula identidades existentes e reserva o Fitness legado compartilhado ao administrador. SSH/SMB/clientes de máquina continuam independentes.

O modo anterior, sem o overlay SSO, conserva seus acessos. A rede/portas descritas na seção anterior referem-se a esse modo base. Consulte [LOGIN-UNICO.md](LOGIN-UNICO.md) para migração e retorno e [REVISAO-24.md](REVISAO-24.md) para evidências e limites de homologação.


### Ajustes de operação e interface em 25.0.0

O evento `aurora:session` do layout informa a sessão ao dashboard. `#user-management-shortcut` permanece oculto até a confirmação administrativa e abre `/auth/admin`; a autorização efetiva continua no backend. O cache PWA é específico da versão e não armazena redirects de autenticação; a instalação considera o papel do usuário para os arquivos Fitness legados.

`ha_proxy.py` valida a identidade em um WebSocket separado e mantém a sequência de comandos nativa do navegador. Remove cabeçalhos de compressão do handshake encaminhado e trata respostas vazias de revogação e formulários multipart. `auth-gateway` monta tmpfs em `/run`, preservando o bind mount filho do socket Cockpit.

As particularidades HTTP do HA 2026.10, diretório XDG do Cockpit e suspensão de dispositivos USB ausentes estão no [guia de migração](LOGIN-UNICO.md). O overlay continua opcional para outras instalações; não habilite o gateway sem validar todos os aplicativos.

`Dockerfile.actual` reutiliza a imagem Actual 26.10.0 fixada. `adapters/actual-login.mjs` verifica o SHA-256 do bundle nativo e ajusta apenas a descoberta do método configurado nas rotas de bootstrap/métodos, preservando a validação nativa da senha/cabeçalho e os métodos fora do SSO. Não altera bancos nem o frontend compilado. `checks/actual_check.mjs` valida esse contrato com cenários sintéticos.

Na 26, `BoundedHTTPServer` mantém no máximo 24 trabalhadores, mas espera uma vaga por até 15 segundos em vez de encerrar imediatamente a conexão excedente. A fila TCP aceita até 128 conexões pendentes. O prazo de leitura por conexão permanece em 15 segundos e a autorização continua obrigatória; não há cache de permissões. O teste HTTP utiliza a mesma classe da produção e inclui 64 conexões simultâneas, validando respostas e o teto de trabalhadores.

Na release 27, `Store` aplica a migração versionada 1 em `schema_migrations`, acrescentando `users.deleted` sem trocar hashes ou sessões existentes. `/auth/delete` exige administrador, CSRF e origem válida; a exclusão marca o cadastro, desativa sua chave, encerra sessões e preserva vínculos para recuperação. A listagem omite excluídos; emitir outra chave para o mesmo e-mail restaura o cadastro. O administrador inicial não pode ser excluído.

A interface usa diálogos acessíveis para confirmação e exibição da chave. As chaves emitidas nesta página ficam apenas em um `Map` em memória, permitindo “Ver chave gerada” até sair/recarregar. Nunca são salvas em localStorage, banco ou logs. `checks/admin_ui_check.js` usa jsdom 30.1.3 com respostas fictícias e simulação apenas da camada de diálogo, não implementada nessa biblioteca.

Na 28, a interface posiciona `#admin` antes de `#account` depois de confirmar a sessão administrativa. `#users`, `#user-count`, `#users-state` e `#refresh-users` apresentam listagem, contagem e atualização no topo. Uma falha mantém os últimos dados disponíveis e mostra erro/retry na própria seção. O formulário preserva seu ID e contrato em `details#registration`. A captura de `invalid` apresenta uma indicação para campos obrigatórios, sem enviar cadastro incompleto. Não há mudança de esquema ou backend nesta versão.

Na 29, `/auth/apps` informa `adminOnly`, mantendo o contrato `apps` existente. O formulário combina essa política com a disponibilidade de identidades e o e-mail de destino antes de habilitar permissões; campos desabilitados não são enviados. O servidor mantém sua própria recusa a permissões administrativas indevidas, sem mudança na autorização.

`#issue-status` mostra confirmação, progresso e erros junto ao cadastro. O botão fica bloqueado desde a confirmação para evitar envios duplicados e cada requisição tem prazo de 20 s, com orientação para conferir a lista antes de repetir uma operação sem resposta. `checks/ui_fixture.py` executa o handler HTTP e Store/SQLite reais com identidades fictícias em diretório temporário, exclusivamente em 127.0.0.1:8489; seu adaptador modela a terminação TLS/cookie para esse HTTP local. Não encaminha chamadas a produção, não aceita escolher endereço público ou banco e não altera o protocolo seguro em produção.



## Remoção de aplicativos — 31.0.0

Home Assistant e HomeBoard foram retirados dos overlays, autenticação central, navegação, monitoramento e escopo de novos backups. Adaptadores e preparadores exclusivos foram removidos. Migration 2 do autenticador remove apenas os grants desses aplicativos; usuários, chaves e demais permissões são preservados. Documentos antigos e releases anteriores registram a arquitetura histórica e não devem ser usados para reinstalá-los.

## Javis OS com Gemini (39.0.0)

Conversa no próprio Javis do AuroraServer, com Gemini API, login único, sete consultas aos aplicativos e túnel TLS limitado ao Google. Navegador/celular com Tailscale; sem dependência do Claude Desktop ou PC particular. Consulte [JAVIS.md](JAVIS.md) para configuração privada, arquitetura, escopo de ferramentas, dados enviados e limitações do Free Tier.

Desde a 39.0.0, o módulo Javis inclui tradução nativa brasileira, correções guardadas de reconhecimento/ditado e voz Edge TTS pelo destino TLS restrito. Dicionário e adaptações ficam em docker/server/javis; detalhes e limites em JAVIS.md.

## Remoção de OctoPrint e câmera (39.0.0)

Os dois serviços, seus builds, dispositivos, portas, atalhos, painéis, coleta e permissões foram retirados. O conector Javis mantém apenas a biblioteca Manyfold no papel print; o catálogo Gemini possui nove ferramentas autorizadas, incluindo leitura de notas. A migração 3 da autenticação remove somente os grants OctoPrint. Backups novos não incluem os aplicativos removidos; a higienização histórica autorizada utiliza sanitize_print_backups.py e registra novos hashes, preservando os demais membros. Não reescreve o histórico Git.

## MagicMirror e leitura web (40.0.0)

`docker/server/mirror/` contém a imagem oficial server-only, o módulo visual MMM-Aurora e o conector privado de dados. `compose.mirror.yaml` declara MagicMirror e mirror-api sem portas públicas, rede de saída separada e persistência em `data/mirror`. A fachada autenticada fica em `docker/server/auth/mirror.py`; toda identidade vem da sessão central. O novo proxy `/mirror/` é descrito na [release 40](RELEASE-40.md). O painel anterior está em `site/monitor-processos.html`; o index estático mantém o modo portátil.

O conector Javis `web_reader.py` atende duas ferramentas de leitura pública, em `javis-web`. A rede do motor Gemini continua restrita às duas origens existentes; pesquisas e leitura externa passam pelo conector sem segredos de aplicativos.

Na release 41 o HTML declara base `/mirror/`, o manifest inicia nesse caminho e o service worker não intercepta a raiz nem o index, preservando redirecionamentos de navegação.

Na release 42, Monitor de processos não tem grade de atalhos de aplicativos; mantém os indicadores e o botão compacto de instalação do app.

## Configuração visual do MagicMirror (43.0.0)

`docker/server/auth/static/mirror-config.*` contém a página administrativa, servida em `/auth/mirror/configurar`. GET/POST `/auth/mirror/settings` passam pela sessão administrativa e pelo conector interno. `docker/server/mirror/settings.py` define o esquema limitado e os padrões; a tabela `display_settings` compartilha o banco mirror.sqlite3, incluído no backup. O módulo MMM-Aurora aplica preferências retornadas com seu estado, preservando grants dos aplicativos. O MMM-Remote-Control não é dependência desta implementação.


## Avaliação Workout Cool (44.0.0) — encerrada na 45

O Compose e os adaptadores abaixo foram removidos do estado atual; esta seção é histórica. O teste atual é o wger descrito a seguir.

`compose.workoutcool-test.yaml` define um projeto independente `auroralab-workoutcool-test`: app Next.js, db PostgreSQL 15, gateway Nginx e backup. Não compõe o COMPOSE_FILE do portal. Rede lab interna para app/db/backup; apenas o gateway acessa a rede auth existente e a rede de entrada com porta ligada ao loopback. HTTPS privado :8444 encaminha para 127.0.0.1:18444. O único perfil delegado é o administrador autorizado do portal.

Adaptadores, importador, preparação privada e ensaio de restauração: `docker/server/workoutcool-test/`. Dados/credenciais em `data/workoutcool-test/` e `secrets/workoutcool-test/`, ignorados pelo Git. Guia: [WORKOUTCOOL-TESTE.md](WORKOUTCOOL-TESTE.md).


## Avaliação wger (45.0.0) — encerrada na 46

O projeto independente auroralab-wger-test foi removido. Seu Compose, adaptadores, banco, uploads, credenciais e backups próprios não compõem a implantação atual. A rota privada :8444 também foi retirada. O backup misto que incluía configurações do teste foi higienizado preservando os demais arquivos. As fontes antigas continuam disponíveis somente no histórico Git/release 45.

## Treinos após a release 46

OpenGym e o serviço Garmin existentes permanecem independentes e ativos, conforme compose.opengym.yaml e os overlays de produção. A retirada do teste não altera seu armazenamento, identidades, sincronização ou endereço de acesso. [Registro](RELEASE-46.md).

## openGym 1.4.5 — release 47

Frontend reconstruído do commit upstream `2d70e026effc6602f513555166a97443520f0572` e API oficial 1.4.5 com adaptador SSO verificado por SHA-256. `docker/server/opengym/charts.patch` adapta Home/Stats/LineChart/service worker; os componentes Aurora ficam no overlay frontend. A navegação nativa de Estatísticas conserva Visão geral, Corpo, Exercícios e Esforço quando aplicável aos dados/módulos. Metas, minutos e calorias ficam na Visão geral; o progresso continua em Exercícios e no Início.

Os cartões nativos respeitam os módulos do perfil. HomePanels conserva IDs/ordem anteriores e remove visualmente os espaços de componentes que retornam vazio, sem desmontá-los para sempre. Recapitulacão, resumo anual, recuperação, deload e desafios são identificadores adicionais. Não há migração para outro banco nem substituição do conector Garmin pelo suporte nativo a relógios.

A API 1.4.5 pede confirmação adicional em operações sensíveis. O adaptador aceita a identidade central validada somente para `pair`, necessário à autorização existente do agendador Garmin. Alterações de senha, e-mail, passkey e conta mantêm as verificações nativas. Tokens existentes e o segredo de sessão devem ser preservados. Consulte [release 47](RELEASE-47.md).

## MagicMirror — cidade persistente e calendário (48.0.0)

O esquema limitado de display_settings ganha weatherLocation, calendarView e holidayRegion. A inicialização estende preferências antigas sem repor escolhas já feitas. A cidade escolhida é compartilhada pelo servidor; nenhum código chama geolocalização do navegador. POST /auth/mirror/locations exige administrador, sessão, CSRF e origem exata, e consulta somente o geocodificador Open-Meteo. A previsão usa as coordenadas salvas pelo administrador, ignorando coordenadas enviadas por clientes.

A tabela holiday_events recebe um catálogo idempotente de 2026–2030 definido em docker/server/mirror/holidays.py, com escopo e fonte legal. É separado de entries e goals, não ocupa a cota de eventos pessoais e não é apagado pela exclusão de um evento particular. Os escopos disponíveis são Brasil, Brasil/SP e Brasil/SP/Jacareí. Mês/Semana pode ser alternado durante a sessão; a opção administrativa define o padrão persistido.

O módulo MMM-Aurora oculta visualmente os títulos redundantes dos três blocos superiores, preservando seus nomes acessíveis; remove suas superfícies/bordas e reduz as fontes. A barra de aplicativos quebra linhas e o Jarvis usa SVG local com nome acessível. A restrição administrativa do Jarvis e as permissões dos outros aplicativos permanecem vigentes. Consulte [MAGICMIRROR.md](MAGICMIRROR.md).
