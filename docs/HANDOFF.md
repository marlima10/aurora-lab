# Passagem de trabalho

## 27/11/2026 — Configuração inicial do contexto

- **Agente responsável** — OpenAI Codex.
- **Tarefa** — AUR-001, criar o contexto compartilhado para Claude Code, OpenAI Codex e Google Antigravity.
- **Arquivos criados** — `AGENTS.md`, `CLAUDE.md`, `docs/CONTEXT.md`, `docs/HANDOFF.md` e `docs/TASKS.md`.
- **Validação** — Conferência de UTF-8, links relativos, importação `@AGENTS.md` e comparação de `git status` antes e depois. O escopo foi documental e as suítes da aplicação ficaram fora desta rodada. Os resultados anteriores da Release 50 constam em [RELEASE-50.md](RELEASE-50.md).
- **Pendências** — Confirmar a branch para o próximo trabalho da Release 50 e concluir a conferência visual da agenda com dados sintéticos.
- **Riscos** — O Git indica `terminal` como branch ativa, enquanto `rafael` foi informada como branch atual. Já havia alterações locais em README, VERSION, Compose, autenticação e MagicMirror, além de três arquivos não rastreados da Release 50. A autoria dessas mudanças não foi verificada.
- **Próximos passos** — Registrar a branch confirmada em CONTEXT.md e combinar o responsável pela validação visual antes de iniciar AUR-003. Abrir a próxima sessão com a leitura dos quatro arquivos centrais, conforme [AGENTS.md](../AGENTS.md).

## 27/11/2026 — Confirmação da branch oficial

- **Agente responsável** — Claude Code.
- **Tarefa** — AUR-002, confirmar a branch de continuidade da Release 50. Também foi registrada a AUR-004 para o OpenAI Codex.
- **Decisão** — O usuário confirmou `rafael` como branch oficial de desenvolvimento.
  - `git branch --show-current` retornou `rafael`, rastreando `origin/rafael`.
  - O reflog mostra que a troca de `terminal` para `rafael` foi feita fora desta sessão.
  - As duas branches apontam para o mesmo commit, `51ced03`.
- **Arquivos alterados** — `docs/CONTEXT.md`, `docs/TASKS.md` e `docs/HANDOFF.md`, somente texto. Código-fonte e outros arquivos não foram tocados.
- **Validação** — Comparação de `git status --short --branch --untracked-files=all` antes e depois. Não houve troca de branch, commit, push ou deploy. As suítes da aplicação não foram executadas, porque o escopo era apenas documental.
- **Riscos** — As alterações locais da Release 50 continuam sem autoria verificada. Os cinco arquivos de memória continuam não rastreados no Git.
- **Pendências** — AUR-003, sem responsável definido. AUR-004 atribuída ao OpenAI Codex, com requisitos e critérios de aceitação em [TASKS.md](TASKS.md).
- **Próximos passos** — Codex executa a AUR-004. Combinar com o usuário o responsável pela AUR-003 na branch `rafael`.

## 27/11/2026 — Revisão da memória compartilhada

- **Agente responsável** — OpenAI Codex.
- **Tarefa** — AUR-004. Status inicial **Em andamento**.
- **Arquivos previstos** — AGENTS.md, CLAUDE.md, docs/CONTEXT.md, docs/HANDOFF.md e docs/TASKS.md, conforme as inconsistências encontradas.

- **Resultado** — Concluída. A última tarefa anteriormente registrada para o Codex foi a AUR-001, criação da memória compartilhada. A revisão aplicou os critérios da AUR-004 registrados pelo Claude Code.
- **Inconsistências e correções** — AGENTS.md passou a identificar os quatro arquivos da rotina e o quinto arquivo, CLAUDE.md, que contém a importação. A leitura explícita no Claude Code ficou documentada para sessões em que o conteúdo importado não esteja disponível. O histórico da AUR-001 foi preservado. A observação de que a branch ativa era terminal descreve aquela sessão e foi superada pela confirmação da branch rafael na AUR-002.
- **Arquivos alterados** — AGENTS.md, docs/HANDOFF.md e docs/TASKS.md.
- **Validação** — Git confirmou rafael com rastreamento de origin/rafael, remoto oficial marlima10/aurora-lab e ambas as branches locais em 51ced03. VERSION confirmou 50.0.0. IDs, responsáveis, dependências e status foram conferidos com o histórico. As regras de segurança e autorização foram conferidas contra AGENTS.md. Os cinco arquivos passaram na leitura UTF-8 e na verificação dos links relativos. CLAUDE.md contém @AGENTS.md. O git status antes e depois foi idêntico. Os hashes dos arquivos já modificados ou não rastreados fora da memória permaneceram iguais. As suítes da aplicação ficaram fora da revisão documental.
- **Riscos** — Os cinco arquivos continuam não rastreados. A verificação da diretiva de importação foi estática. O carregamento automático no Claude Code permanece sem confirmação nesta revisão.
- **Fora do escopo e próximos passos** — Alinhar CHANGELOG.md e o título de ESTRUTURA.md com a versão da Release 50 quando a atualização desses documentos for autorizada. AUR-003 segue pendente, com responsável a definir e dependência de um navegador disponível no DEV.

## 27/11/2026 — Revisão da última tarefa executada pelo OpenAI Codex

- **Agente responsável** — Google Antigravity.
- **Tarefa** — AUR-005, identificar a última tarefa executada pelo OpenAI Codex e revisar o resultado conforme os critérios de aceitação da AUR-004 registrados pelo Claude Code em [TASKS.md](TASKS.md).
- **Última tarefa executada pelo Codex** — **AUR-004** (*Revisar a consistência dos cinco arquivos de memória compartilhada*, status **Concluída**), que sucedeu a **AUR-001** durante esta sessão.
- **Resultado da revisão frente aos critérios de aceitação da AUR-004 (Aprovada)**:
  - **Coerência entre os cinco arquivos e `git status` (Atendido)** — Branch (`rafael...origin/rafael` em `51ced03`), versão (`50.0.0`), responsáveis, IDs, dependências, regras de segurança/autorização e a distinção entre os quatro arquivos centrais da rotina e o quinto arquivo ([CLAUDE.md](../CLAUDE.md)) estão consistentes entre `AGENTS.md`, `CLAUDE.md`, `docs/CONTEXT.md`, `docs/HANDOFF.md` e `docs/TASKS.md`. O alinhamento de `CHANGELOG.md` e do título de `ESTRUTURA.md` (`49.0.0`) foi corretamente tratado fora do escopo.
  - **Links relativos válidos (Atendido)** — Todos os links relativos dos cinco arquivos apontam para arquivos existentes (`AGENTS.md`: 7; `CLAUDE.md`: 0; `CONTEXT.md`: 5; `HANDOFF.md`: 3 antes desta entrada; `TASKS.md`: 3), sem links quebrados.
  - **Codificação UTF-8 e escopo de arquivos (Atendido)** — Os cinco arquivos estão em UTF-8 válido sem BOM e a AUR-004 alterou somente arquivos da memória compartilhada (`AGENTS.md`, `docs/HANDOFF.md` e `docs/TASKS.md`), sem tocar código-fonte, skills, Compose, `README.md` ou `VERSION`.
  - **Entrada da AUR-004 no `HANDOFF.md` (Atendido)** — Seção registrada com inconsistências encontradas, correções aplicadas, itens fora do escopo, validação, riscos e próximos passos.
  - **Status da AUR-004 em `TASKS.md` (Atendido)** — Tarefa marcada como **Concluída** na tabela de controle.
- **Arquivos alterados** — `docs/HANDOFF.md` e `docs/TASKS.md` (somente documentação; código-fonte e demais arquivos intactos).
- **Validação** — Leitura dos cinco arquivos após a conclusão da AUR-004; conferência de UTF-8 (sem BOM) e resolução de todos os links relativos via PowerShell; conferência de `git status --short --branch --untracked-files=all` antes e depois, `git branch -vv`, `git worktree list` e `git log -n 3 --oneline`. Não houve alteração de código, commit, push ou deploy.
- **Riscos** — Os cinco arquivos de memória compartilhada e os arquivos da Release 50 continuam não rastreados ou com alterações locais sem autoria verificada; a importação `@AGENTS.md` em `CLAUDE.md` segue com leitura explícita recomendada no Claude Code caso o conteúdo não carregue automaticamente.
- **Pendências** — `AUR-003` (conferência visual da agenda da Release 50 no DEV com dados sintéticos) segue **Pendente**, sem responsável definido; atualização futura de `CHANGELOG.md` e `ESTRUTURA.md` quando autorizada.
- **Próximos passos** — Definir com o usuário o responsável pela `AUR-003` na branch `rafael` (com navegador disponível no DEV e dados sintéticos) e alinhar `CHANGELOG.md` e `ESTRUTURA.md` para `50.0.0` quando autorizado.

## 27/11/2026 — Fechamento da Release 50

- **Agente responsável** — Claude Code, autorizado pelo usuário.
- **Tarefas** — AUR-006, AUR-007 e AUR-003. Status inicial **Em andamento**.
- **Arquivos previstos** — `docker/server/auth/mirror.py`, `docker/server/auth/test_mirror_facade.py`, `docs/CHANGELOG.md`, `docs/ESTRUTURA.md`, `docs/MAGICMIRROR.md`, `docs/ATUALIZACAO.md`, `docs/RELEASE-50.md`, `docs/TASKS.md` e `docs/HANDOFF.md`.

- **Resultado** — AUR-006 e AUR-007 concluídas. AUR-003 bloqueada. Aberta a AUR-008.
- **Correções** — `image()` em `docker/server/auth/mirror.py` referenciava `action`, que não existe naquela função. Isso fazia toda imagem da galeria retornar 503, uma regressão da 49. O tempo limite voltou a 20 s. Em `test_mirror_facade.py` entrou um teste novo de encaminhamento de miniatura. O teste de clima, desatualizado desde a 48 porque esperava `lat`/`lon` encaminhados, passou a verificar que as coordenadas do cliente são descartadas.
- **Documentação** — Entrada 50.0.0 (não publicada) no CHANGELOG. Título e seção da agenda em ESTRUTURA.md. Seção `#agenda-unificada` em MAGICMIRROR.md, que o README já referenciava sem que ela existisse. Revisão de fechamento e pré-requisitos de implantação em RELEASE-50.md. CONTEXT.md atualizado. ATUALIZACAO.md é genérico e não foi alterado.
- **Validação** — Imagem `auth` 50.0.0 construída localmente como `auroralab-auth:50.0.0-dev`. `test_auth` e `test_mirror_facade` rodados em container `--network none`, somente leitura: 37 testes aprovados. Verificações Node `check_calendar`, `check_settings`, `check_backgrounds` e `check_pwa` aprovadas. Compose: sem `compose.mealie.yaml`, a seleção falha com `mirror-api refers to undefined network mealie`. A seleção completa parou apenas no `secrets/sso/manyfold.env` ausente no DEV.
- **Testes omitidos** — Os testes Python do Mirror, que importam Pillow. A imagem `mirror-api` não foi construída porque o `pip` falhou com `CERTIFICATE_VERIFY_FAILED` ao acessar PyPI, o que indica interceptação TLS na rede do DEV. A verificação não foi contornada. Pelo mesmo motivo não houve prévia visual (AUR-003).
- **Riscos** — `prepare.py` exige `mealie.secret` em `apps.json` e `mirror-api` exige a rede `mealie`. Em instalações sem o Mealie, a 50 não sobe sem ajuste. Nada foi commitado. Os arquivos de memória continuam não rastreados.
- **Próximos passos** — Resolver o TLS do `pip` no DEV ou rodar a AUR-008 no Aurora Server. Depois, fazer a AUR-003 com navegador. Por fim, commit, merge e implantação, mediante autorização explícita.

## 27/11/2026 — Pendências da Release 50 resolvidas

- **Agente responsável** — Claude Code, com autorização do usuário ("resolva tudo").
- **Tarefas** — AUR-008, AUR-003 e AUR-009 concluídas. Aberta a AUR-010, que depende de autorização.
- **AUR-008** — A falha TLS do `pip` vem do AVG Web/Mail Shield, que reassina o HTTPS com uma raiz que só o Windows conhece. O wheel do Pillow 13.0.0 (cp313, manylinux x86_64) foi baixado pelo `curl.exe` do Windows e conferido com o SHA-256 publicado pelo PyPI. Depois foi instalado com `--no-index` na imagem local `auroralab-mirror-test:50.0.0-dev`, sobre a base fixada do `Dockerfile.api`. A verificação de certificado não foi desativada.
- **AUR-003** — A prévia em Chrome headless (`--headless=new`) usou o `MMM-Aurora.js` e o CSS reais, com respostas sintéticas geradas pelo próprio `api.Data`/`agenda.collect`. O harness, o gerador e as capturas ficaram fora do repositório, no scratchpad da sessão. Foram verificados mês, semana, agenda do período, lista de um dia e falha parcial, em 1280×800, 1180×820, 1920×1080, 820×1180 e 390×844. A janela headless tem largura mínima de 512 px, por isso o celular foi simulado com iframe.
- **AUR-009** — No layout de altura fixa, os itens do dia eram cortados sem aviso, inclusive o **＋N**. Foram criados `dayRows`, que prioriza compromissos e lembretes, e `fitCalendar`, que move para **＋N** o que não couber, também após redimensionar. Um único item oculto é exibido no lugar do botão. O `prepare.py` aceita a ausência de `mealie` em `apps.json`, e a agenda trata fonte sem segredo como `unauthorized`, sem fazer a consulta.
- **Arquivos alterados nesta etapa** — `docker/server/mirror/MMM-Aurora/MMM-Aurora.js`, `docker/server/mirror/agenda.py`, `docker/server/mirror/prepare.py`, `docker/server/mirror/test_agenda.py`, `docker/server/mirror/check_calendar.mjs`, `docs/RELEASE-50.md`, `docs/MAGICMIRROR.md`, `docs/ESTRUTURA.md`, `docs/CHANGELOG.md`, `docs/CONTEXT.md`, `docs/TASKS.md` e `docs/HANDOFF.md`. No `test_agenda.py`, o teste de falha parcial passou a informar o segredo do openGym, para continuar exercitando o caso `unavailable`.
- **Validação final** — Testes Python do Mirror: 36 OK. Autenticação: 33 OK. Fachada: 4 OK. Todos em container `--network none`. As verificações Node `check_calendar`, `check_settings`, `check_backgrounds` e `check_pwa` passaram, e `node --check` aprovou `MMM-Aurora.js`.
- **Riscos** — A prévia não roda o servidor MagicMirror nem foi feita em aparelho físico. `fitCalendar` depende das medidas do layout, por isso convém conferir no tablet real após a implantação. Imagens locais de teste mantidas: `auroralab-auth:50.0.0-dev` e `auroralab-mirror-test:50.0.0-dev`.
- **Próximos passos** — AUR-010: commit na `rafael`, incluindo os arquivos de memória e os novos `agenda.py` e `test_agenda.py`, seguido de push, merge na `main` e implantação conforme RELEASE-50 e ATUALIZACAO.md. Tudo isso depende de autorização explícita.

## 27/11/2026 — Commit e push da Release 50

- **Agente responsável** — Claude Code, com autorização do usuário para commit e push.
- **Tarefa** — AUR-010, concluída. Aberta a AUR-011 para merge, release e implantação, que dependem de nova autorização.
- **Escopo** — Todas as alterações locais da Release 50 e os cinco arquivos de memória compartilhada foram para um único commit na `rafael`, com push para `origin/rafael`. Não houve merge, tag, release nem deploy.
- **Próximos passos** — Revisar e fazer o merge na `main`, conforme ATUALIZACAO.md seção 8. Depois, implantar no Aurora Server com backup prévio e conferir o calendário no tablet real.

## 27/11/2026 — Fluxo iniciado no Claude

- **Responsável** — OpenAI Codex.
- **Tarefa** — AUR-012. Arquivos previstos: CLAUDE.md, FLUXO-DE-TRABALHO.md, docs/TASKS.md e docs/HANDOFF.md.
- **Validação** — Nove testes no gerenciador passaram, incluindo entrega do plano externo ao Codex e revisão do Antigravity com adaptadores de teste. A API local confirmou disponibilidade da entrada e a raiz DEV correta. A execução pelo Claude Code interativo está pendente de validação.

## 27/11/2026 — Preparação do merge e da release 50.0.0

- **Agente responsável** — Claude Code, com autorização do usuário para executar a AUR-011.
- **Tarefa** — AUR-011, **Em andamento**. Arquivos alterados: `docs/CHANGELOG.md` (50.0.0 datada de 2026-11-27), `docs/TASKS.md` e `docs/HANDOFF.md`. Os registros da AUR-012 do Codex foram preservados.
- **Verificação** — `origin/main` em `51ced03` (49.0.0) e `origin/rafael` em `922ab67` (50.0.0). A `rafael` está um commit à frente da `main` e não há divergência, então o merge não tem conflito.
- **Bloqueio** — A sessão do Claude não recebeu permissão de push no GitHub, e o Aurora Server não é acessível a partir dela. O commit, o merge `--no-ff` na `main`, a tag `v50.0.0`, a release e a implantação ficam com o usuário, pelos comandos entregues no chat.
- **Atenção** — A `main` local rastreia o remoto `fork` (`rafaellima2222/aurora-lab`). O push da `main` precisa usar explicitamente `origin`.
- **Próximos passos** — Depois do push, marcar a release no GitHub e implantar no servidor com backup prévio, conforme ATUALIZACAO.md seções 1 a 6 e RELEASE-50.md. Atualizar só `magicmirror`, `mirror-api` e `auth`, e conferir o calendário no tablet real. Ao final, marcar a AUR-011 como **Concluída** e atualizar o CONTEXT.md.

## 27/11/2026 — Release 50.0.0 publicada e implantada

- **Agente responsável** — Claude Code. Merge, release e implantação executados pelo usuário a partir dos comandos preparados.
- **Tarefa** — AUR-011, **Concluída**.
- **Resultado** — `origin/main` em `ebeb06d` (merge `--no-ff` da `rafael`, que inclui `3f9731a` da AUR-012 e `3936835` com o CHANGELOG datado). A tag `v50.0.0` aponta para `ebeb06d`, e a release "Aurora LAB 50.0.0 — Agenda unificada" está publicada como Latest. O usuário confirmou a conclusão da implantação no Aurora Server.
- **Arquivos alterados** — `docs/TASKS.md`, `docs/HANDOFF.md` e `docs/CONTEXT.md`, somente texto.
- **Não verificado pelo Claude** — Esta sessão não acessa o Aurora Server. Backup prévio, serviços recriados e conferência no tablet foram informados pelo usuário e não foram observados diretamente.
- **Próximos passos** — Commit destes três arquivos na `rafael`, se autorizado. Acompanhar no tablet real o `fitCalendar` e a agenda com dados reais.

## 27/11/2026 — Validação da agenda no tablet físico

- **Responsável pelo registro** — OpenAI Codex.
- **Validação em produção** — O usuário confirmou no tablet físico que a agenda do MagicMirror abriu nos modos Mês e Semana e que o botão **＋N** abriu a lista nos dias com itens excedentes.
- **Fechamento** — AUR-011 marcada como **Concluída** em TASKS.md. A versão v50.0.0 foi confirmada como a mais recente no GitHub. Os três serviços atualizados estavam saudáveis no Aurora Server, e o backup pós-implantação passou na restauração isolada.

## 27/11/2026 — Backlog de UX/UI e início da AUR-013

- **Agente responsável** — Claude Code, com autorização do usuário para registrar o backlog e iniciar a AUR-013.
- **Tarefas** — AUR-013 a AUR-017 registradas a partir das propostas de UX/UI do Claude Code e de outro agente, conferidas no código da `rafael` em `07c4f5e`. O modal diário do Fitness legado ficou fora do backlog, porque o openGym é o aplicativo de treinos atual.
- **AUR-013, Em andamento** — Arquivos previstos: `site/index.html`, `site/monitor-processos.html`, `site/fitness.html`, `site/fitness-planos.html`, `site/fitness-exercicios.html`, `site/pwa.js`, `site/aurora.css`, `site/power.css`, `site/service-worker.js`, `docs/TASKS.md` e `docs/HANDOFF.md`.
- **Resultado da AUR-013** — Concluída no DEV, sem commit.
  - O topo do Monitor começa em "Consultando servidor…", cinza, e passa a verde (Sistema Online), laranja (serviço offline ou dados desatualizados, com a contagem) ou vermelho (Dados indisponíveis). Antes, a bolinha ficava verde mesmo com erro.
  - O botão de instalação saiu de baixo do título e virou uma pílula ao lado do h1. `pwa.js` só mostra o botão quando há o que instalar: depois de `beforeinstallprompt`, ou no iOS fora do modo app. Ele fica oculto sem HTTPS ou com o app já instalado. As mensagens agora aparecem em linha, sem `alert()`.
  - O rodapé lateral perdeu "AURORA LAB 23.0", "V6.5" e "rk322x-box". Ele fica oculto pela barra compacta, então a mudança é só de limpeza.
  - A legenda da tabela de energia ficou visualmente oculta (continua acessível) e foi exibida como texto acima da área com rolagem, sem corte.
  - `aurora.css`, `power.css` e `pwa.js` passaram para `?v=20261127-v51` nas páginas e no APP_SHELL, e `CACHE_NAME` passou para `auroralab-51.0.0`. `index.html` e `monitor-processos.html` continuam idênticos.
- **Arquivos alterados** — `site/index.html`, `site/monitor-processos.html`, `site/fitness.html`, `site/fitness-planos.html`, `site/fitness-exercicios.html`, `site/pwa.js`, `site/aurora.css`, `site/power.css`, `site/service-worker.js`, `docs/TASKS.md` e `docs/HANDOFF.md`.
- **Validação** — `node --check` em `pwa.js`, `service-worker.js` e nos scripts em linha das duas páginas. `check_pwa.mjs` e `check_portal_removal.mjs` aprovados. `test_nginx_security` e `test_service_links`: 10 OK. Chrome headless com `status.json` sintético: estados ok, aviso e erro, botão oculto até `beforeinstallprompt`, celular a 390×844 e tema ice.
- **Não validado** — Instalação real em Android e iOS e o comportamento no Aurora Server.
- **Próximos passos** — Commit na `rafael` quando autorizado. AUR-014 e AUR-015 completam a Release 51.

## 27/11/2026 — Continuidade das releases 51 e 52

- **Responsável** — OpenAI Codex. AUR-014 a AUR-017 em implementação. Arquivos previstos no módulo MagicMirror, configuração e login, portal, energia e navegação.

- **Implementação no DEV** — AUR-014: legenda e filtro, criação pela data do dia, agenda agrupada, confirmação no diálogo e destaque de hoje. AUR-015: posição das imagens selecionadas, prévia reativa, indicação de alterações não salvas e controle de visibilidade e contagem da chave. AUR-016: resumo de saúde, energia compacta e página energia.html, estados de consulta e painéis móveis. AUR-017: ícones SVG com rótulos e tooltips, cores dos temas por tokens e cache atualizado.
- **Validação** — Sintaxe Node, verificações existentes de calendário, fundos, configurações, PWA e portal. Dez testes Python de rotas e links no Docker isolado. Teste sintético das leituras de energia, com sucesso e falha em ambas as entradas do portal e na página de detalhes.
- **Escopo de validação** — Sem conferência visual em navegador para as mudanças recém-implementadas, instalação real em dispositivos ou validação em produção. As alterações da AUR-013 foram preservadas. As mudanças permanecem locais na rafael.

## 27/11/2026 — Implantação consolidada da Release 52

- **Responsável** — OpenAI Codex. AUR-013 a AUR-017 implantadas juntas como 52.0.0.
- **Produção** — MagicMirror e autenticação recriados com as imagens 52.0.0. Portal e página Energia servidos pelo Nginx. A API do Mirror permanece com a imagem 50.0.0 porque o pacote alterou apenas seu frontend. Os quatro serviços estavam saudáveis após a atualização.
- **Validação** — 37 testes de autenticação e fachada no build de produção. Verificação do conteúdo servido no Monitor e na página Energia, conferência dos arquivos novos dentro dos contêineres e teste de resposta HTTPS do login e das rotas protegidas sem sessão.
- **Recuperação** — Snapshot dos arquivos e imagens anteriores preservado. Backup anterior verificado. Backup posterior auroralab-data-20261128-004426.tar.gz (data UTC), SHA-256 conferido e restauração isolada aprovada com 991 arquivos, 27 bancos SQLite e 88 JSON.
- **Limites** — Instalação do PWA em Android e iOS e conferência visual interativa com sessão real não foram observadas nesta implantação. Pacote implantado a partir do checkout DEV. Depois, o código foi integrado à main em ef97f83 e a [release v52.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v52.0.0) foi publicada.

## 27/11/2026 — Fechamento documental e revisão visual

- README, CHANGELOG e CONTEXT apontam para a documentação da versão. Criado RELEASE-52.md.
- Conferência visual em Chrome headless (1280 × 900), com dados sintéticos: agenda do MagicMirror, Energia, configuração do MagicMirror e login. Conferidas a legenda e o seletor de fonte, as leituras de energia, a prévia de aparência e os controles de chave exibidos.
- A nota pública da 50.0.0 agora registra a confirmação do tablet físico. O usuário confirmou separadamente a instalação e a abertura do PWA pelo ícone da tela inicial em Android e iOS.

## 28/11/2026 — Planejamento de UX/UI do openGym (Release 53)

- **Agente responsável** — Claude Code. Somente planejamento, sem alteração de código.
- **Tarefas** — AUR-018 a AUR-024 registradas como **Pendente**, com responsável OpenAI Codex. Requisitos e critérios de aceitação estão no [TASKS.md](TASKS.md#release-53--opengym--requisitos-e-critérios-de-aceitação-aur-018-a-aur-024).
- **Base da análise** — `rafael` em `ff07f43`. openGym 1.4.5 (`2d70e026`) gerado no ambiente do Claude com `charts.patch` e a camada Aurora, em `VITE_DEMO=1`, com pt-BR, a 390 px e 1024 px. O SSO e o Garmin reais não foram exercitados.
- **Achados principais**
  - A Início tem cerca de 3.500 px no celular e 10 painéis.
  - O card Garmin mostra "Consultando" e "indisponível" juntos.
  - Os cards Aurora não têm o ícone do CardHead e têm texto de aviso excessivo.
  - O card de calorias vazio ocupa espaço, e "Código desta versão" aparece duplicado.
  - Tempo e calorias usam seletores de período separados.
  - Os cards Aurora vêm antes do resumo nativo nas Estatísticas.
  - O tablet fica em coluna única.
  - No openGym oficial, os dias da semana em pt-BR usam uma letra.
- **Arquivos alterados** — `docs/TASKS.md` e `docs/HANDOFF.md`.
- **Próximo passo** — O Codex começa pela AUR-018 e pela AUR-019, que são independentes e de risco baixo.

## 28/11/2026 — Execução da Release 53

- OpenAI Codex assumiu AUR-018 a AUR-024. Arquivos previstos: overlay, patch, testes e Dockerfile do openGym, Compose, VERSION e documentação. O planejamento local do Claude foi preservado.

- AUR-018 a AUR-022 implementadas no frontend. AUR-023 entregue em OPENGYM-UPSTREAM.md como três rascunhos para o projeto oficial.
- Validação DEV: 82 testes Vitest em dez suítes, cinco testes Node de métricas, patch aplicado no commit upstream fixado, build Vite de demonstração e imagem 53.0.0 construída pelo Compose em staging do Aurora Server. Docker Desktop não confiou no certificado do Alpine; o build de staging passou sem desabilitar a verificação TLS.
- Chrome headless pt-BR, temas claro e escuro: capturas a 390, 820, 1024 e 1280 px em tmp/opengym53-visual do workspace DEV. Uma coluna nas duas primeiras larguras e duas nas demais, sem rolagem horizontal. Na Visão geral, o resumo nativo precedeu os cards Aurora.
- Validação sintética. Sessão SSO real, pareamento Garmin e dados pessoais ficaram fora dos ensaios.
