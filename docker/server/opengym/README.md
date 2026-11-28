# openGym AuroraLAB — gráficos de treino

Personalização do frontend openGym 1.4.5, upstream AGPL-3.0-or-later:
https://github.com/DuarteSantos8/openGym/tree/2d70e026effc6602f513555166a97443520f0572

`Dockerfile` obtém exatamente esse commit em checkout esparso, aplica `charts.patch` e acrescenta os arquivos legíveis em `frontend/`. Instala pelo package-lock upstream, sem scripts de pós-instalação. A imagem final herda o frontend oficial fixado por digest, incluindo suas mídias licenciadas, proxy e usuário sem privilégios; troca somente o bundle compilado. O backend parte da API oficial da mesma versão; o overlay de autenticação acrescenta o SSO AuroraLAB com verificação exata do arquivo server.js. Não há dados pessoais no contexto.

O código correspondente à alteração está neste diretório e no patch; fontes originais e licenças estão no commit acima. O link Código desta versão fica no fim da Visão geral em Estatísticas. Para reconstruir: da raiz Aurora, com o ambiente servidor configurado, `docker compose build opengym-web`. O serviço usa a imagem local `auroralab-opengym-web:53.0.0`. APP_BUILD identifica a variante; Vite renova o cache do service worker pelo hash do conteúdo.

As páginas inicial e Estatísticas usam o mesmo gráfico de progresso existente e os mesmos componentes de tempo/calorias. Exercício, unidade, modalidades e filtros originais de progresso continuam disponíveis. Tempo/calorias somam por data local do treino, com 7/30/90 dias ou todo o histórico; datas futuras e inválidas são ignoradas. Duração usa end-start da sessão (incluindo pausas); sem esses valores, soma somente séries cardio/tempo concluídas. Calorias vêm exclusivamente de garminActivity.calories, validadas no importador. Dados ausentes não viram zero; zeros reais são aceitos. A cobertura e uma tabela diária acompanham os gráficos. Treinos com o mesmo ID não são contados duas vezes. Sem estimativas de calorias para treinos manuais.

`Stats.jsx` expõe ExerciseProgress usando o mesmo render e cálculos de progresso, sem copiar regras por modalidade. LineChart usa IDs React únicos para os gradientes de múltiplos gráficos. O CSS usa o tema do próprio openGym e container queries: cartões empilhados no celular e lado a lado quando há espaço.

Validação sintética: `node --test docker/server/opengym/test_metrics.mjs`. Na fonte upstream personalizada, execute `npm ci --ignore-scripts`, `npm run build` e Vitest para `TrainingMetrics.test.jsx`, `Home.weight-card.test.jsx`, `Stats.speed.test.jsx`, `Stats.ex-range.test.jsx` e `LineChart.test.jsx`. O teste dos gráficos localiza o cartão de progresso por data-tour, sem depender de ele ser o último gráfico azul na página. Nenhuma instalação, migração ou teste usa banco pessoal.


## Fundo e organização da página inicial (20.0.0)

`frontend/public/aurora-background.jpg` é a imagem fornecida pelo titular, preservada sem edição. O fundo fixo cobre a janela em todas as páginas; uma camada ajustada ao tema e superfícies legíveis mantêm o contraste. A imagem é incluída no cache offline como recurso opcional, sem impedir o aplicativo de abrir se faltar. Vite renova o cache pelo hash do build.

`HomePanels.jsx` mostra controles apenas em Organizar painéis. Arraste pela alça usando mouse/toque; ↑/↓ e botões permitem mover pelo teclado e no celular. Esc ou cancelamento do ponteiro descartam o arraste. A prévia não grava a cada movimento; somente ao soltar. As ações dos cartões continuam normais fora do modo de organização.

`home-panels.js` valida IDs, remove duplicatas e mantém posições de painéis temporariamente ocultos. A lista `auroraHomePanels` fica no estado do perfil, passando pelo update/persist/merge nativo e seus carimbos por preferência. Novos cartões entram na ordem padrão. Não se usa uma chave global de navegador compartilhada por contas. Restaurar ordem padrão altera somente essa preferência. Agenda, check-in, boas-vindas, progresso, Tempo e calorias, peso e sequência são painéis independentes. As métricas mantêm os cálculos existentes e compartilham o período no Início. IDs antigos minutes e calories são convertidos para metrics na posição mais antiga da ordem salva.

Testes React adicionais: `HomePanels.test.jsx`, `Home.startdoor.test.jsx` e `Home.queue.test.jsx`. Cobrem persistência, separação entre perfis, atualização Garmin concorrente sem perder layout, teclado, limites, restauração, arraste com uma gravação e cancelamento. Execute junto dos testes anteriores.

## Metas e resumo Garmin (22.0.0)

WeeklyGoals/weekly-goals.js usam a semana local de segunda a hoje e a preferência auroraWeeklyGoals do perfil. Zero desativa metas; limites são 100 treinos, 10.080 minutos e 100.000 kcal semanais. São limites de entrada, não recomendações de saúde. GarminSummary usa a sessão da mesma origem, atualiza status a cada 30 segundos e permite solicitar consulta; /garmin/ fica fora do cache do service worker. Os novos IDs goals/garmin são acrescentados à ordem válida sem mudar a ordem dos cartões existentes. Testes sintéticos em AuroraUpgrades.test.jsx cobrem calendário, duplicatas, metas, merge concorrente e contrato/erros de consulta. Detalhes em docs/RELEASE-22.md.

## Evolução visual 1.4.5 (47.0.0)

Os componentes Aurora usam CardHead nativo; fontes relativas e contraste reforçado preservam o fundo fornecido pelo titular. Home mantém MiniBodyMap e agenda nativos. Stats conserva seu índice fixo e as seções nativas, com metas e gráficos Aurora na Visão geral. A seção Esforço depende de haver dados/módulo aplicável. Cartões opcionais sem conteúdo são ocultados sem lacunas nem alças vazias; a ordem antiga continua válida e novos cartões são acrescentados.

A construção usa dependências do lock upstream antes de copiar o overlay, permitindo reutilizar o cache de dependências em ajustes de interface. As imagens oficiais e a base de construção são fixadas por digest. Nenhuma dependência visual adicional é instalada.

Validação desta atualização: 171 testes Vitest de Home/Stats/componentes/módulos/service worker, quatro testes do adaptador SSO e 45 testes Garmin. Ensaio real de API com perfil sintético comprova token legado, SSO, negação de cabeçalho forjado, novo pareamento, revisão/conflito 409 e escrita Garmin sem duplicar. Conferência pelo navegador em 390 e 820 px, temas claro/escuro, ordem persistida e módulos ocultos. Não se trata de teste em iPhone/tablet físicos nem de nova autenticação real no Garmin.
