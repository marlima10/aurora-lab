# openGym AuroraLAB — gráficos de treino

Personalização do frontend openGym 1.4.1, upstream AGPL-3.0-or-later:
https://github.com/DuarteSantos8/openGym/tree/464355ef43d4c8f8a4e0bb6db9c2af7f240593b5

`Dockerfile` obtém exatamente esse commit em checkout esparso, aplica `charts.patch` e acrescenta os arquivos legíveis em `frontend/`. Instala pelo package-lock upstream, sem scripts de pós-instalação. A imagem final herda o frontend oficial fixado por digest, incluindo suas mídias licenciadas, proxy e usuário sem privilégios; troca somente o bundle compilado. O backend e seu formato de sincronização permanecem os da imagem oficial. Não há dados pessoais no contexto.

O código correspondente à alteração está neste diretório e no patch; fontes originais e licenças estão no commit acima. A interface oferece o link Código desta versão. Para reconstruir: da raiz Aurora, com o ambiente servidor configurado, `docker compose build opengym-web`. O serviço usa a imagem local `auroralab-opengym-web:20.0.0`. APP_BUILD identifica a variante; Vite renova o cache do service worker pelo hash do conteúdo.

As páginas inicial e Estatísticas usam o mesmo gráfico de progresso existente e os mesmos componentes de tempo/calorias. Exercício, unidade, modalidades e filtros originais de progresso continuam disponíveis. Tempo/calorias somam por data local do treino, com 7/30/90 dias ou todo o histórico; datas futuras e inválidas são ignoradas. Duração usa end-start da sessão (incluindo pausas); sem esses valores, soma somente séries cardio/tempo concluídas. Calorias vêm exclusivamente de garminActivity.calories, validadas no importador. Dados ausentes não viram zero; zeros reais são aceitos. A cobertura e uma tabela diária acompanham os gráficos. Treinos com o mesmo ID não são contados duas vezes. Sem estimativas de calorias para treinos manuais.

`Stats.jsx` expõe ExerciseProgress usando o mesmo render e cálculos de progresso, sem copiar regras por modalidade. LineChart usa IDs React únicos para os gradientes de múltiplos gráficos. O CSS usa o tema do próprio openGym e container queries: cartões empilhados no celular e lado a lado quando há espaço.

Validação sintética: `node --test docker/server/opengym/test_metrics.mjs`. Na fonte upstream personalizada, execute `npm ci --ignore-scripts`, `npm run build` e Vitest para `TrainingMetrics.test.jsx`, `Home.weight-card.test.jsx`, `Stats.speed.test.jsx`, `Stats.ex-range.test.jsx` e `LineChart.test.jsx`. O patch do teste de faixa remove a suposição antiga de que o último gráfico azul da página sempre é o de progresso. Nenhuma instalação, migração ou teste usa banco pessoal.


## Fundo e organização da página inicial (20.0.0)

`frontend/public/aurora-background.jpg` é a imagem fornecida pelo titular, preservada sem edição. O fundo fixo cobre a janela em todas as páginas; uma camada ajustada ao tema e superfícies legíveis mantêm o contraste. A imagem é incluída no cache offline como recurso opcional, sem impedir o aplicativo de abrir se faltar. Vite renova o cache pelo hash do build.

`HomePanels.jsx` mostra controles apenas em Organizar painéis. Arraste pela alça usando mouse/toque; ↑/↓ e botões permitem mover pelo teclado e no celular. Esc ou cancelamento do ponteiro descartam o arraste. A prévia não grava a cada movimento; somente ao soltar. As ações dos cartões continuam normais fora do modo de organização.

`home-panels.js` valida IDs, remove duplicatas e mantém posições de painéis temporariamente ocultos. A lista `auroraHomePanels` fica no estado do perfil, passando pelo update/persist/merge nativo e seus carimbos por preferência. Novos cartões entram na ordem padrão. Não se usa uma chave global de navegador compartilhada por contas. Restaurar ordem padrão altera somente essa preferência. Agenda, check-in, boas-vindas, progresso, minutos, calorias, peso e sequência são painéis independentes; minutos/calorias mantêm os mesmos cálculos, com filtros próprios no Início.

Testes React adicionais: `HomePanels.test.jsx`, `Home.startdoor.test.jsx` e `Home.queue.test.jsx`. Cobrem persistência, separação entre perfis, atualização Garmin concorrente sem perder layout, teclado, limites, restauração, arraste com uma gravação e cancelamento. Execute junto dos testes anteriores.
