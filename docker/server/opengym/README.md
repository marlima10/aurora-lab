# openGym AuroraLAB — gráficos de treino

Personalização do frontend openGym 1.4.1, upstream AGPL-3.0-or-later:
https://github.com/DuarteSantos8/openGym/tree/464355ef43d4c8f8a4e0bb6db9c2af7f240593b5

`Dockerfile` obtém exatamente esse commit em checkout esparso, aplica `charts.patch` e acrescenta os arquivos legíveis em `frontend/`. Instala pelo package-lock upstream, sem scripts de pós-instalação. A imagem final herda o frontend oficial fixado por digest, incluindo suas mídias licenciadas, proxy e usuário sem privilégios; troca somente o bundle compilado. O backend e seu formato de sincronização permanecem os da imagem oficial. Não há dados pessoais no contexto.

O código correspondente à alteração está neste diretório e no patch; fontes originais e licenças estão no commit acima. A interface oferece o link Código desta versão. Para reconstruir: da raiz Aurora, com o ambiente servidor configurado, `docker compose build opengym-web`. O serviço usa a imagem local `auroralab-opengym-web:19.0.0`. APP_BUILD identifica a variante; Vite renova o cache do service worker pelo hash do conteúdo.

As páginas inicial e Estatísticas usam o mesmo gráfico de progresso existente e os mesmos componentes de tempo/calorias. Exercício, unidade, modalidades e filtros originais de progresso continuam disponíveis. Tempo/calorias somam por data local do treino, com 7/30/90 dias ou todo o histórico; datas futuras e inválidas são ignoradas. Duração usa end-start da sessão (incluindo pausas); sem esses valores, soma somente séries cardio/tempo concluídas. Calorias vêm exclusivamente de garminActivity.calories, validadas no importador. Dados ausentes não viram zero; zeros reais são aceitos. A cobertura e uma tabela diária acompanham os gráficos. Treinos com o mesmo ID não são contados duas vezes. Sem estimativas de calorias para treinos manuais.

`Stats.jsx` expõe ExerciseProgress usando o mesmo render e cálculos de progresso, sem copiar regras por modalidade. LineChart usa IDs React únicos para os gradientes de múltiplos gráficos. O CSS usa o tema do próprio openGym e container queries: cartões empilhados no celular e lado a lado quando há espaço.

Validação sintética: `node --test docker/server/opengym/test_metrics.mjs`. Na fonte upstream personalizada, execute `npm ci --ignore-scripts`, `npm run build` e Vitest para `TrainingMetrics.test.jsx`, `Home.weight-card.test.jsx`, `Stats.speed.test.jsx`, `Stats.ex-range.test.jsx` e `LineChart.test.jsx`. O patch do teste de faixa remove a suposição antiga de que o último gráfico azul da página sempre é o de progresso. Nenhuma instalação, migração ou teste usa banco pessoal.
