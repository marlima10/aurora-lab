# Controle de tarefas

Use os estados **Pendente**, **Em andamento**, **Bloqueada** e **Concluída**. Registre em [HANDOFF.md](HANDOFF.md) os arquivos sob responsabilidade de cada agente e o resultado ao concluir.

| ID | Descrição | Prioridade | Responsável | Dependências | Status |
| --- | --- | --- | --- | --- | --- |
| AUR-001 | Criar o contexto compartilhado e o fluxo de passagem de trabalho | Alta | OpenAI Codex | Nenhuma | Concluída |
| AUR-002 | Confirmar a branch de continuidade da Release 50 diante da divergência entre a branch informada e a ativa | Alta | Claude Code | Nenhuma | Concluída |
| AUR-003 | Concluir a conferência visual da agenda da Release 50 no DEV com dados sintéticos | Alta | Claude Code | AUR-002 (concluída) | Concluída |
| AUR-004 | Revisar a consistência dos cinco arquivos de memória compartilhada | Média | OpenAI Codex | AUR-002 (concluída) | Concluída |
| AUR-005 | Revisar a última tarefa executada pelo OpenAI Codex conforme critérios de aceitação registrados pelo Claude Code | Média | Google Antigravity | AUR-002 (concluída) e AUR-004 (concluída) | Concluída |
| AUR-006 | Corrigir o timeout indefinido em `image()` da fachada Mirror, que devolve 503 para toda imagem da galeria, e cobrir com teste | Alta | Claude Code | Nenhuma | Concluída |
| AUR-007 | Alinhar CHANGELOG.md, ESTRUTURA.md, MAGICMIRROR.md e RELEASE-50.md à versão 50.0.0 | Média | Claude Code | AUR-006 | Concluída |
| AUR-008 | Reexecutar os testes Python do Mirror com Pillow apesar da interceptação TLS do AVG no DEV | Alta | Claude Code | Nenhuma | Concluída |
| AUR-009 | Corrigir os itens do calendário cortados sem aviso no layout de altura fixa e tornar o segredo Mealie opcional na preparação | Alta | Claude Code | AUR-003 | Concluída |
| AUR-010 | Commit e push da 50.0.0 na branch `rafael` | Alta | Claude Code | Autorização do usuário (concedida em 27/11/2026) | Concluída |
| AUR-011 | Merge na `main`, release e implantação da 50.0.0 no Aurora Server | Alta | Claude Code | AUR-010 e autorização explícita do usuário (concedida em 27/11/2026) | Concluída |
| AUR-012 | Documentar a entrada pelo Claude no Aurora AI Manager | Alta | OpenAI Codex | Aurora AI Manager local | Concluída |
| AUR-013 | Release 51 · Portal: status do topo com a cor real do estado, botão de instalação estilizado na topbar e oculto quando não se aplica, sem `alert()`, textos legados do rodapé e legenda da tabela de energia sem corte | Alta | Claude Code | Nenhuma | Concluída |
| AUR-014 | Release 51 · MagicMirror: legenda colorida e filtro por fonte, criar compromisso pela data do dia, agenda do período agrupada por dia, confirmação de exclusão no próprio diálogo e realce da célula de hoje | Alta | OpenAI Codex | Nenhuma | Concluída |
| AUR-015 | Release 51 · Configurar Mirror e login: ordem #1, #2… na galeria, prévia ao vivo da aparência, barra fixa de alterações não salvas, contador 0/151 e mostrar/ocultar chave | Média | OpenAI Codex | Nenhuma | Concluída |
| AUR-016 | Release 52 · Portal: resumo de saúde no topo, energia compacta na home com detalhes em página própria, painéis recolhíveis no celular e estados de carregamento e erro | Média | OpenAI Codex | AUR-013 | Concluída |
| AUR-017 | Release 52 · Visual: ícones SVG únicos com tooltip na barra compacta e tokens de tema no lugar dos `!important` dos cinco temas | Média | OpenAI Codex | AUR-013 | Concluída |
| AUR-018 | Release 53 · openGym: card Garmin com um único estado por vez, motivo do botão desabilitado e "Tentar de novo" | Alta | OpenAI Codex | Nenhuma | Concluída |
| AUR-019 | Release 53 · openGym: cards Aurora com ícone no CardHead, avisos resumidos em "Como é calculado", calorias vazio compacto e um único link "Código desta versão" | Alta | OpenAI Codex | Nenhuma | Concluída |
| AUR-020 | Release 53 · openGym: Tempo e Calorias num único painel da Início, com abas e período único, preservando a ordem salva dos painéis | Média | OpenAI Codex | AUR-019 | Concluída |
| AUR-021 | Release 53 · openGym: resumo nativo antes dos cards Aurora na Visão geral das Estatísticas | Média | OpenAI Codex | AUR-019 | Concluída |
| AUR-022 | Release 53 · openGym: Início em duas colunas a partir de 900 px e véu do fundo mais forte entre os cards | Média | OpenAI Codex | AUR-020 | Concluída |
| AUR-023 | openGym oficial: rascunhar sugestões ao projeto (dias da semana em pt-BR, nomes de exercício duplicados, dias de descanso compactos no Plano) | Baixa | OpenAI Codex | Nenhuma | Concluída |
| AUR-024 | Release 53 · Fechamento: versão 53.0.0, documentação, testes, commit, release e implantação do openGym | Alta | OpenAI Codex | AUR-018 a AUR-022 e autorização explícita do usuário | Concluída |
| AUR-025 | Nova numeração de versões a partir da 5.4: `X.Y.Z` com tags `aurora-X.Y.Z`, tabela de correspondência com as tags `vNN.0.0` e guia de release atualizado | Alta | OpenAI Codex | Decisão do usuário (opção 3, 28/11/2026) | Concluída |
| AUR-026 | README com a seção "Aurora LAB em imagens": 4 capturas com dados de demonstração em `docs/images/` (MagicMirror, openGym, Monitor e Energia) | Alta | OpenAI Codex | Nenhuma | Concluída |
| AUR-027 | Apresentação geral do Aurora LAB em 8 slides, em PowerPoint e PDF, com as capturas da AUR-026 e as complementares | Média | OpenAI Codex | AUR-026 | Em andamento |

## AUR-004 — Requisitos e critérios de aceitação

**Escopo** — `AGENTS.md`, `CLAUDE.md`, `docs/CONTEXT.md`, `docs/HANDOFF.md` e `docs/TASKS.md`.

### Requisitos

1. Siga o fluxo de início do [AGENTS.md](../AGENTS.md). Antes de editar, registre neste arquivo e no [HANDOFF.md](HANDOFF.md) o status **Em andamento** e os arquivos previstos.
2. Compare os cinco arquivos entre si e com o estado real do Git: branch, versão, remoto, IDs, status e responsáveis das tarefas.
3. Verifique a coerência das referências:
   - quantidade de arquivos centrais citada, pois o AGENTS.md menciona quatro e a memória tem cinco;
   - links relativos válidos;
   - importação `@AGENTS.md` no CLAUDE.md;
   - menções a skills e documentos existentes.
4. Verifique se as regras de segurança e autorização estão descritas da mesma forma em todos os arquivos, sem contradições ou lacunas.
5. Corrija somente inconsistências de texto nesses cinco arquivos. Não altere código-fonte, skills, Compose, README, VERSION ou outros documentos. Proponha no HANDOFF.md as mudanças que forem necessárias fora do escopo.
6. Mantenha português brasileiro, UTF-8 e o formato atual das tabelas e seções. Preserve integralmente o histórico do HANDOFF.md e os registros de outros agentes.
7. Não troque de branch e não faça commit, push, pull, reset, checkout ou deploy sem autorização explícita.

### Critérios de aceitação

- Nenhuma contradição entre os cinco arquivos ou entre eles e `git status --short --branch --untracked-files=all`.
- Todos os links relativos dos cinco arquivos apontam para arquivos existentes.
- Os cinco arquivos continuam em UTF-8 e são os únicos alterados pela tarefa, o que deve ser confirmado pela comparação de `git status` antes e depois.
- O HANDOFF.md tem uma nova entrada da AUR-004 com as inconsistências encontradas, as correções feitas, os itens deixados fora do escopo, a validação, os riscos e os próximos passos.
- AUR-004 marcada como **Concluída** nesta tabela, ou **Bloqueada** com o motivo.

### Observações iniciais para a revisão

Registradas pelo Claude Code e ainda não verificadas pelo Codex:

- Os cinco arquivos de memória estão como não rastreados no Git.
- Em uma sessão do Claude Code em 27/11/2026, o conteúdo do AGENTS.md não apareceu carregado automaticamente pela importação do CLAUDE.md e precisou ser lido de forma explícita.
- O CHANGELOG.md e o ESTRUTURA.md ainda indicam 49.0.0, mas a correção deles está fora do escopo da AUR-004.

## Release 53 · openGym — Requisitos e critérios de aceitação (AUR-018 a AUR-024)

Planejamento registrado pelo Claude Code em 28/11/2026 para execução pelo OpenAI Codex. Base da análise: `rafael` em `ff07f43`. O openGym 1.4.5 (commit upstream `2d70e026`) foi gerado com `charts.patch` e a camada `docker/server/opengym/frontend/`, em modo demonstração (`VITE_DEMO=1`), com idioma pt-BR, a 390 px e 1024 px. Garmin e SSO não estavam disponíveis nesse ensaio.

### Regras comuns

1. Siga o [AGENTS.md](../AGENTS.md). Antes de editar, marque a tarefa como **Em andamento** aqui e registre no [HANDOFF.md](HANDOFF.md) os arquivos previstos.
2. Prefira alterar a camada Aurora: `frontend/src/components/*`, `frontend/src/lib/*` e os CSS. Toque em `charts.patch` (Home.jsx, Stats.jsx) só quando a tarefa exigir. O patch precisa continuar aplicando com `git apply --check` sobre `2d70e026`.
3. Não altere o código oficial além do patch, nem a API, os dados em `data/opengym/`, o importador Garmin ou o SSO.
4. Mantenha português brasileiro nos textos, contraste legível sobre o fundo nos temas claro e escuro, alvos de toque de pelo menos 44 px e navegação por teclado.
5. Cada tarefa precisa de teste Vitest novo ou ajustado. Rode também a suíte citada em [docker/server/opengym/README.md](../docker/server/opengym/README.md).
6. Validação visual em build de demonstração, a 390, 820, 1024 e 1280 px: no checkout upstream com o patch e a camada aplicados, rode `VITE_DEMO=1 npx vite build` e sirva a pasta `dist/`. Para ver em português, troque `"lang":"en"` por `"lang":"pt-BR"` em `localStorage.gym_state_v1` e recarregue.
7. Sem commit, push, merge, release ou deploy antes da AUR-024 e da autorização explícita do usuário.

### AUR-018 — Card Garmin

**Problema** — Em `GarminSummary.jsx`, quando a primeira consulta falha, `state` continua `null`. O card mostra ao mesmo tempo "Consultando sincronização…" e "Garmin indisponível…". O botão fica desabilitado em cinza, sem explicação.

**Requisitos**
- O card mostra um único estado por vez: consultando (só antes da primeira resposta); sem sessão (401); erro (com "Tentar de novo"); conectado, com a última consulta e o resultado; ou desconectado (com "Abrir conexão Garmin").
- O botão "Sincronizar agora" só aparece habilitado quando pode agir. Desabilitado, deve ter um motivo visível, como "Ative a atualização automática na conexão Garmin".
- O texto fixo de rodapé deve ter no máximo uma linha.
- Os erros continuam em `role="alert"`, sem duplicação.

**Aceite** — Teste com `fetch` simulado para 200 (conectado, automático ligado e desligado), 401, 500 e falha de rede. Em cada caso, o card exibe exatamente uma mensagem de estado.

### AUR-019 — Cards Aurora

**Arquivos** — `TrainingMetrics.jsx`, `WeeklyGoals.jsx`, `GarminSummary.jsx`, `training-metrics.css`, `aurora-upgrades.css` e testes.

**Requisitos**
- Passar `icon` (e `tint`, se preciso) ao `CardHead` nos cards Tempo, Calorias, Metas semanais e Garmin, usando nomes já existentes em `Icon.jsx`. Não adicionar biblioteca de ícones.
- Deixar uma frase curta por card e mover as regras (como semana de segunda a hoje, sessão contada uma vez, calorias só do Garmin, sem estimativas, zeros reais aceitos) para um `<details>` "Como é calculado". Nenhuma regra pode ser removida.
- Usar no máximo dois tamanhos de texto por card: o corpo e o `small`.
- Calorias sem dados no período vira uma linha compacta ("Sem calorias do Garmin neste período"), sem o bloco do gráfico.
- "Código desta versão" aparece uma vez por tela. Ele sai dos cards da Início e fica no fim da Visão geral das Estatísticas. A obrigação de oferecer o código-fonte (AGPL) continua atendida, e o `README.md` do openGym deve ser atualizado.

**Aceite** — Testes de ícone, de `<details>` presente, de calorias vazio compacto e de link único. Visualmente, nenhum card Aurora tem mais de duas linhas de texto auxiliar visíveis sem expandir.

### AUR-020 — Tempo e Calorias num painel

**Requisitos**
- Na Início, um painel "Tempo e calorias" com abas Tempo/Calorias e um único seletor de período (7, 30 ou 90 dias, ou Todos).
- Ordem dos painéis (`home-panels.js` e `auroraHomePanels` do perfil):
  - nova ID `metrics`, que ocupa a posição da primeira entre `minutes`/`calories` na ordem salva;
  - `minutes` e `calories` continuam aceitas na leitura e são convertidas sem duplicar;
  - ocultar o painel novo equivale a ocultar os dois antigos.
- Cálculos de `training-metrics.js` inalterados.

**Aceite** — Testes de migração da ordem: só `minutes`, só `calories`, ambas, nenhuma, ordem com IDs inválidas, e dois perfis separados. Testes de troca de aba e período. `HomePanels.test.jsx` continua passando.

### AUR-021 — Ordem da Visão geral das Estatísticas

**Requisitos** — Em `Stats.jsx`, pelo `charts.patch`, o bloco `aurora-stats-summary` (Metas e Tempo/Calorias) passa a ficar depois do resumo nativo da Visão geral (Treinos, Este mês, Peso 30 d, Total levantado), e não no topo da seção. O índice fixo e as âncoras das seções continuam iguais.

**Aceite** — Teste que localiza o resumo nativo antes do bloco Aurora na Visão geral. `Stats.ex-range.test.jsx` e `Stats.speed.test.jsx` continuam passando. `git apply --check` limpo.

### AUR-022 — Tablet e fundo

**Requisitos**
- A partir de 900 px, a Início usa duas colunas, com a agenda e o treino de hoje primeiro. A ordem de leitura e de tabulação segue a ordem salva dos painéis.
- Abaixo de 900 px, o layout atual fica inalterado. Somente a página Início muda: o `max-width` de 560 px do openGym continua nas demais páginas.
- O modo Organizar painéis funciona nas duas colunas, com arrastar, teclado e botões ↑/↓.
- O véu sobre `aurora-background.jpg` fica mais forte entre os cards, para que textos da foto não apareçam entre eles. A imagem fornecida pelo titular não é editada.

**Aceite** — Capturas a 820, 1024 e 1280 px nos temas claro e escuro, registradas no HANDOFF, e teste de que a ordem no DOM segue a preferência.

### AUR-023 — Sugestões ao openGym oficial

**Entregável** — Rascunho em `docs/OPENGYM-UPSTREAM.md`, com uma issue ou PR por item, cada uma com evidência e proposta. A publicação no GitHub do projeto é feita pelo usuário.

**Itens**
1. Em `frontend/src/locales/pt-BR.js` (linha ~1352), os dias da semana usam uma letra (`'Mo': 'S'`, `'Tu': 'T'`…). Isso gera "S T Q Q S S D", ambíguo na agenda da Início e no Plano. A proposta é usar "Seg Ter Qua Qui Sex Sáb Dom" ou duas letras.
2. Os nomes traduzidos repetem o original entre parênteses, como "Leg Press 45 Graus No Sled (Sled 45° Leg Press)".
3. No Plano, cada dia de descanso ocupa uma linha inteira. A proposta é usar linhas compactas.

Não criar patch local para esses itens sem decisão do usuário.

### AUR-024 — Fechamento da Release 53

**Requisitos**
- `VERSION` 53.0.0, `APP_BUILD=auroralab-53` e a tag da imagem `auroralab-opengym-web` atualizada em `compose.opengym.yaml`.
- `docs/RELEASE-53.md`, CHANGELOG, README, `docs/OPENGYM.md` e CONTEXT atualizados.
- Validação:
  - `node --test docker/server/opengym/test_metrics.mjs`;
  - Vitest da camada Aurora e das suítes citadas no README do openGym;
  - `docker compose build opengym-web`;
  - conferência visual da regra 6.
- Commit, merge, release e implantação somente com autorização explícita. Fazer backup antes e recriar apenas `opengym-web`. Dados e API não mudam.

**Aceite** — Release `v53.0.0` publicada, o HANDOFF com resultado, validação, limites e retorno, e a AUR-024 marcada como **Concluída**.

## AUR-025 — Nova numeração de versões

**Decisão do usuário (28/11/2026, opção 3)** — Os títulos das releases no GitHub foram renomeados: a antiga N passou a se chamar X.Y, com X = N ÷ 10 e Y = resto (53 → 5.3, 49 → 4.9, 5 → 0.5). As tags `vNN.0.0` continuam iguais. Como `v5.0.0` a `v9.0.0` já existem e correspondem às releases 0.5 a 0.9, as próximas tags usam um prefixo próprio, sem conflito.

**Situação de partida** — A 5.3 foi publicada antes desta tarefa, ainda no padrão antigo (`VERSION 53.0.0`, tag `v53.0.0`, `RELEASE-53.md`, imagem `auroralab-opengym-web:53.0.0`). Ela fica como histórico. O padrão novo começa na **5.4**.

### Convenção a partir da 5.4

| Item | Padrão | Exemplo |
| --- | --- | --- |
| `VERSION` e CHANGELOG | `X.Y.Z`. Z fica reservado para correções sem novidade | `5.4.0`, `## 5.4.0 — AAAA-MM-DD` |
| Tag Git | `aurora-X.Y.Z` | `aurora-5.4.0` |
| Título da release | `Aurora LAB X.Y — tema` | `Aurora LAB 5.4 — …` |
| Documento da release | `docs/RELEASE-X.Y.md` | `docs/RELEASE-5.4.md` |
| Imagens Docker locais | `auroralab-<serviço>:X.Y.Z` | `auroralab-opengym-web:5.4.0` |
| Cache do PWA e `APP_BUILD` | `auroralab-X.Y.Z` / `auroralab-X.Y` | `auroralab-5.4.0` / `auroralab-5.4` |

Tags históricas `vNN.0.0`, documentos `RELEASE-NN.md` e títulos antigos do CHANGELOG ficam como estão: não mover, apagar nem recriar tags.

### Requisitos

1. Criar `docs/VERSOES.md` com:
   - a convenção acima;
   - a tabela completa de correspondência (tag `vNN.0.0` → versão X.Y → documento da release, quando houver), incluindo `v53.0.0` → 5.3;
   - a explicação do conflito com `v5.0.0` a `v9.0.0`.
   Incluir links para ele no README, no CHANGELOG (nota no topo, sem reescrever entradas antigas), no CONTEXT e no ATUALIZACAO.
2. No `docs/ATUALIZACAO.md`, seção 8:
   - trocar o parágrafo da "convenção histórica" (`v12.0.0` → `v13.0.0`) pela nova convenção, com exemplo de `git tag -a aurora-5.4.0` e título "Aurora LAB 5.4";
   - corrigir os comandos que ainda usam a branch removida `marcelo` (linhas ~57 e ~114) para `rafael`.
3. `VERSION` continua `53.0.0` até a próxima release, que passa direto para `5.4.0`. Registrar isso no VERSOES.md, porque `5.4.0` é numericamente menor que `53.0.0`.
4. Procurar no repositório comparações ou ordenações de versão que quebrariam com `5.4.0 < 53.0.0`: scripts, testes, `sort -V`, `git describe` e checagens de atualização. A busca inicial do Claude Code não encontrou nenhum leitor programático de `VERSION`, mas é preciso confirmar. Isso inclui o retorno de imagem do deploy, que na 5.3 voltou à 47.0.0 numa tentativa.
5. Registrar o risco das imagens Docker: antes de usar tags `6.0.0` a `9.0.0` (a partir da série 6.0), conferir no servidor com `docker image ls 'auroralab-*'` se não existem imagens antigas com essas tags.
6. Os cabeçalhos internos das releases antigas no GitHub (por exemplo, a 49 ainda mostra "AuroraLAB 49.0.0" no corpo) ficam opcionais. Só editar com autorização do usuário.

### Aceite

- `docs/VERSOES.md` existe e tem uma linha por tag existente (`git tag -l 'v*'`).
- Todos os links relativos novos funcionam.
- O ATUALIZACAO não menciona mais `marcelo`.
- Nenhuma tag foi criada, movida ou apagada.
- `VERSION` continua `53.0.0`.
- O HANDOFF tem o resultado da busca do item 4.

## AUR-026 e AUR-027 — README em imagens e apresentação geral

**Proposta do usuário (28/11/2026)** — O README ajuda quem acabou de chegar a entender o Aurora LAB em poucos segundos, e a apresentação mostra como os módulos se conectam no uso diário. A primeira captura a preparar é a do MagicMirror, que serve de capa no GitHub e nos slides.

### Regras de privacidade (valem para as duas tarefas)

1. Todas as capturas públicas usam um perfil de demonstração, com agenda, lembretes, treinos, refeições, peso e leituras de energia fictícios.
2. Nenhuma imagem pode mostrar e-mails, chaves, tokens, IPs (local, Tailscale ou gateway), domínios `.ts.net`, hostnames reais, nomes de dispositivos, nomes reais de pessoas ou dados pessoais.
   - Onde o layout exige um valor, usar fictícios: IPs da faixa de documentação `192.0.2.x`/`198.51.100.x`, host `aurora-demo`.
3. Fontes de dados sintéticos já existentes:
   - MagicMirror: `docker/server/mirror/check_calendar.mjs` e `check_settings.mjs`;
   - openGym: build `VITE_DEMO=1`, idioma pt-BR, conforme a regra 6 da Release 5.3;
   - portal e Monitor: `status.json` simulado, sem tocar no Aurora Server.
4. Nenhuma captura é tirada da produção com dados reais. Antes de adicionar ao Git, conferir cada imagem ampliada e também os metadados (EXIF e nomes de arquivo).

### AUR-026 — README com 4 capturas

**Entregáveis**
- Seção **"Aurora LAB em imagens"** perto do início do README, logo depois da apresentação: uma captura principal e três complementares.
- Imagens em `docs/images/`, com nomes estáveis, sem a versão no nome. Mudar o nome quebraria links antigos.

| Arquivo | O que mostrar |
| --- | --- |
| `docs/images/magicmirror-agenda.png` (principal) | Tela inicial do MagicMirror com a agenda do dia: compromissos, lembretes, treinos e refeições. Mostra a integração entre os módulos |
| `docs/images/opengym-inicio.png` | Tela Início do openGym em duas colunas, com o painel Tempo e calorias da 5.3 |
| `docs/images/monitor-saude.png` | Resumo dos serviços, recursos e estado do backup |
| `docs/images/energia-historico.png` | Histórico de potência e simulação de custo, com um selo visível "Dados de demonstração" |

**Requisitos**
- Cada imagem tem uma legenda curta e texto alternativo descritivo em português (o `alt` não repete a legenda).
- A captura principal ocupa a largura do README. As três complementares ficam em grade (tabela de 3 colunas ou `<p>` com largura reduzida) e cada uma abre a imagem inteira.
- Tamanho:
  - desktop com no máximo 1600 px de largura e celular com 780 px;
  - cada arquivo com até ~400 KB (PNG otimizado; WebP só se o GitHub exibir corretamente);
  - total da pasta abaixo de 2 MB.
- Para manter o README fácil de percorrer, as capturas extras não entram nele: ficam na AUR-027.
- Tema escuro padrão, com textos legíveis na miniatura.

**Aceite**
- O README mostra as 4 imagens no GitHub, com legenda e `alt`, e os links relativos funcionam.
- O HANDOFF registra como cada captura foi gerada (dados, resolução, tema) e a conferência de privacidade de cada uma.
- Commit somente com autorização do usuário.

### AUR-027 — Apresentação de 8 slides

**Entregáveis** — `docs/apresentacao/aurora-lab.pptx` e `docs/apresentacao/aurora-lab.pdf`, gerado a partir do PPTX, mais as capturas complementares em `docs/apresentacao/imagens/`.

| Slide | Conteúdo e visual |
| --- | --- |
| 1. Aurora LAB | Capa com o MagicMirror e a frase "Agenda, treinos e monitoramento em um só portal." |
| 2. Como tudo se conecta | Diagrama simples: portal, autenticação central, módulos (MagicMirror, openGym, Mealie, Monitor, Energia e demais) e Aurora Server. Desenhado com formas editáveis no PowerPoint, não como imagem |
| 3. Sua rotina no MagicMirror | Print da agenda com três chamadas: compromissos e lembretes, treinos e refeições |
| 4. Treinos no openGym | Print da tela Início e detalhe de Tempo e calorias. Explica o papel do Garmin na importação: somente leitura, sem calorias estimadas |
| 5. Operação do servidor | Print do Monitor com serviços, recursos e backup |
| 6. Energia e autonomia | Print do histórico e da simulação, separando as leituras medidas no notebook das estimativas de custo pela tarifa |
| 7. Uso no celular e no tablet | Duas capturas lado a lado mostrando como o layout se adapta e como o PWA aparece no uso diário |
| 8. Código, releases e documentação | Links para o repositório, a documentação e a release 5.3 (tag `v53.0.0`) |

**Requisitos**
- Formato 16:9, com identidade visual da skill `skills/aurora-visual` (cores e tipografia do tema Aurora).
- No máximo uma ideia por slide, com títulos curtos e texto mínimo. Os detalhes vão nas notas do apresentador.
- As mesmas regras de privacidade, com as capturas extras geradas pelos mesmos dados de demonstração.
- Os textos devem ser editáveis: nada de slides inteiros como imagem.
- Usar fontes que o PDF incorpore corretamente.
- Os links do slide 8 devem ser clicáveis no PPTX e no PDF.
- O PDF tem 8 páginas e é conferido página a página, sem texto cortado ou sobreposto.

**Aceite**
- PPTX abre sem aviso de reparo, e o PDF tem 8 páginas legíveis.
- O HANDOFF registra a conferência visual e a de privacidade.
- Decidir com o usuário se os arquivos ficam no repositório ou só como anexo de release (o PPTX com imagens pode passar de alguns MB). Commit somente com autorização.
