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
