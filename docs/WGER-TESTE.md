# wger — avaliação privada no AuroraLAB

A release 45 substitui o Workout Cool pelo wger 2.7 estável. O openGym/Garmin continua sendo o aplicativo atual; o teste usa somente uma cópia independente dos dados.

## Acesso

Com Tailscale conectado, entre como administrador no portal https://auroraserver.tail7d26f7.ts.net/auth/ e abra https://auroraserver.tail7d26f7.ts.net:8444/ . O aplicativo encaminha à página inicial em português brasileiro. Não crie outra conta e não use uma senha local do wger. A faixa superior identifica a avaliação e abre `/aurora-import/`, o relatório privado.

Este adaptador delega apenas aurora@server.local ao perfil local Rafael. Não é um mapa multiusuário: não o amplie sem criar associação individual por identidade. Para encerrar a sessão, use o AuroraLAB; fluxos locais de senha, login e cadastro são recusados. Clientes móveis nativos JWT/PowerSync não foram habilitados; o uso avaliado é pelo navegador autenticado.

## Organização

`compose.wger-test.yaml`, projeto `auroralab-wger-test`: app Django/Gunicorn, db PostgreSQL 15, gateway Nginx e backup. Aplicação/banco/backup compartilham somente a rede interna lab. Gateway também acessa a rede externa de autenticação existente e uma rede de entrada, publicando somente `127.0.0.1:18444`. Tailscale Serve HTTPS :8444 encaminha para esse loopback. Nunca acrescente o overlay ao COMPOSE_FILE de produção.

`data/wger-test/postgres`, `static`, `media`, `import`, `backups` e `secrets/wger-test` ficam fora do Git. A aplicação não monta o banco ou a pasta ativa do openGym. Sem saída de internet, sincronizações remotas, SMTP real ou cadastro de convidados. A opção oficial USE_CELERY=False mantém a avaliação web sem Redis/Celery. O catálogo inicial é o fornecido pela imagem mais os exercícios necessários à cópia; não se afirma ter sincronizado todo o catálogo online ou os ingredientes externos.

O gateway exige sessão administrativa e origem válida. Somente identidade validada e segredo privado chegam ao Django; Authorization e cookie central são descartados. O cookie `csrftoken` é encaminhado para preservar a proteção nativa de formulários/React. CSRF não foi desabilitado. Perfis padrão ficam inativos e o perfil de avaliação tem senha inutilizável.

## Preparar uma instalação

A partir de `/srv/auroralab`, com backup anterior verificado:

1. Prepare uma exportação autorizada somente de leitura do openGym, no formato `{ "state": ... }`, em `deploy-state/wger-test/import-source/source-opengym.json`.
2. Coloque em `deploy-state/wger-test/import-source/catalogue.json` o catálogo público da versão openGym utilizada, incluindo nomes/traduções. Exercícios personalizados vêm do próprio snapshot; nome ausente aborta a importação.
3. Proteja esses arquivos e execute `python3 docker/server/wger-test/prepare.py`. O comando copia apenas se o destino ainda não existe e preserva os segredos já criados. Não copie dados pessoais para a pasta Docker.

```sh
docker compose -p auroralab-wger-test -f compose.wger-test.yaml config --quiet
docker compose -p auroralab-wger-test -f compose.wger-test.yaml build app
docker compose -p auroralab-wger-test -f compose.wger-test.yaml up -d db app
```

Espere o bootstrap/migrations/arquivos estáticos e o app saudável. Em seguida:

```sh
docker compose -p auroralab-wger-test -f compose.wger-test.yaml exec -T app python3 manage.py check
docker compose -p auroralab-wger-test -f compose.wger-test.yaml exec -T app python3 manage.py shell -c "exec(open('/home/wger/src/import_data.py').read())"
docker compose -p auroralab-wger-test -f compose.wger-test.yaml up -d gateway backup
```

Nunca exponha o aplicativo antes da preparação/importação. O importador exige o nome exato wger_test, executa em transação e recusa outra origem sobre um teste existente. Uma segunda execução com o mesmo checksum apenas informa que já foi importado, sem recriar treinos.

Para uma instalação nova, configure somente a rota necessária, preservando as demais:

```sh
docker compose exec -T tailscale tailscale --socket=/var/run/tailscale/tailscaled.sock serve --bg --https=8444 http://127.0.0.1:18444
```

No AuroraServer a rota anterior foi reutilizada para o wger; não se reinicializou Serve e não se habilitou Funnel.

## Dados e limites

Sessões e horários reais vão para o histórico nativo. Apenas séries com done=true viram registros executados. Cardio usa minutos e km/h; força usa repetições e peso. Os campos decimais do wger têm duas casas, e o snapshot privado conserva a precisão original. A data dos registros de peso vem do dia original, preservando também o timestamp bruto como metadado.

Rotinas copiam nome, exercícios, ordem, número de séries e sugestões representáveis. Como a origem não contém a mesma programação de vigência do wger, cada plano recebe um dia e uma janela técnica de 120 dias para avaliação. Isso é declarado na descrição, sem inferir uma recomendação de exercícios. Nomes que excedem o limite nativo de 25 caracteres permanecem completos na descrição e no snapshot.

Um agrupador Histórico openGym/Garmin recebe sessões sem rotina correspondente; suas datas técnicas não substituem os horários reais das sessões. A agenda, progressões e demais campos originais ficam preservados no snapshot, sem inventar equivalências nativas.

Peso corporal foi copiado como medida nativa. Calorias e detalhes Garmin sem campo equivalente ficam nas notas das sessões e no relatório. Não há sincronização contínua com o Garmin, envio a terceiros ou alterações de volta no aplicativo atual. Nenhuma chave Garmin, passkey ou senha foi importada.

A imagem avisa que não há par de chaves JWT configurado; esse método não é usado nesta avaliação, cuja autenticação REST é a sessão delegada pelo gateway. Não confunda esse aviso com uma falha do login web nem tente contorná-lo criando um token exposto.

## Validação e backup

Testes de unidades com dados sintéticos:

```sh
python3 docker/server/wger-test/test_import_values.py
```

Os testes de delegação em `test_adapter.py` usam usuários simulados, sem consultar o banco pessoal; execute-os no ambiente Django configurado. As sondagens operacionais verificam página inicial, relatório, totais pela API e rejeição de origens/cabeçalhos inválidos. Um POST deliberadamente inválido permite verificar CSRF sem criar registro no perfil.

Backup diário próprio via pg_dump e arquivo separado de uploads/media, com checksum, em `data/wger-test/backups`. Não há retenção automática. O backup geral do portal não inclui uma cópia consistente deste PostgreSQL. Ensaio manual adicional:

```sh
python3 docker/server/wger-test/backup-verify.py
```

O script restaura em um PostgreSQL temporário sem rede e compara sessões, séries, rotinas, medidas e snapshot com os totais anteriores ao dump. Execute sem alterações concorrentes, pois uma mudança durante a janela de cópia pode gerar divergência e exigir nova execução. O resultado fica em `.restore.json`; o container temporário é removido ao final. Nunca há restauração sobre o banco ativo.

Copie dump, uploads/media, SHA-256, comprovante, exportação original e secrets para armazenamento privado fora do servidor. Esses arquivos contêm dados pessoais e não são cifrados automaticamente. Para recuperação definitiva, crie outro banco/projeto, preserve o estado atual e valide o login e os totais antes de qualquer substituição.

Para parar reversivelmente:

```sh
docker compose -p auroralab-wger-test -f compose.wger-test.yaml stop
```

Não use down -v ou exclusão de data como atualização. O teste anterior Workout Cool foi removido com cópia privada de recuperação preservada; seu histórico Git não foi reescrito. [Fontes e licença](../docker/server/wger-test/SOURCE.md).
