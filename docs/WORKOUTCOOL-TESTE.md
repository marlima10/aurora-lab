# Workout Cool — avaliação com cópia do openGym/Garmin

O ambiente é privado, independente e destinado à avaliação. Não substitui openGym, não sincroniza novos treinos automaticamente e não compartilha gravações com o aplicativo atual. Endereço desta instalação: https://auroraserver.tail7d26f7.ts.net:8444/pt/profile . Conecte Tailscale e entre no AuroraLAB como administrador; depois reabra esse endereço. O login central é na porta padrão 443, não um cadastro novo no Workout Cool.

## Arquitetura

Quatro serviços no projeto `auroralab-workoutcool-test`: `app`, `db`, `gateway`, `backup`. PostgreSQL sem porta publicada; app/db/backup em rede interna sem internet. Somente gateway participa da rede `auroralab_auth` e de uma rede de entrada. A porta publicada fica restrita ao loopback. Não acrescente este arquivo ao COMPOSE_FILE de produção.

A configuração atual delega somente `aurora@server.local` ao perfil local Rafael da cópia. Não reutilize o adaptador para vários usuários sem implementar associação individual por identidade. Credenciais do PostgreSQL e segredo de delegação são exclusivos do teste; os cookies AuroraLAB são validados e removidos no gateway.

## Preparar e iniciar

A partir de `/srv/auroralab`, após revisar o código e guardar o backup anterior:

1. Exporte, por uma conexão já autorizada e somente de leitura, o perfil existente para `deploy-state/workoutcool-test/source-opengym.json`, no formato `{ "state": ... }`. Guarde o arquivo com acesso privado. Não use dados reais em testes unitários nem os envie ao Git.
2. Prepare `data/workoutcool-test/import/catalogue.json` com os nomes e traduções do catálogo da versão openGym utilizada. O importador combina esse catálogo público com os exercícios personalizados do snapshot; nome ausente aborta a importação.
3. Execute `python3 docker/server/workoutcool-test/prepare.py`. Esse comando preserva os segredos existentes; não muda a autenticação de produção.
4. Garanta UID 10001 e permissão 600 no catálogo copiado para o diretório de importação. Não coloque exportações de usuário no diretório da imagem.

```sh
docker compose -p auroralab-workoutcool-test -f compose.workoutcool-test.yaml config --quiet
docker compose -p auroralab-workoutcool-test -f compose.workoutcool-test.yaml build app
docker compose -p auroralab-workoutcool-test -f compose.workoutcool-test.yaml up -d db app gateway
```

Espere o app saudável e as migrações concluídas antes da importação. A migração adicional `1_aurora_schema_completion` corrige somente a coluna onboardingPreferences ausente no 0_init oficial; não há db push destrutivo na inicialização.

```sh
docker compose -p auroralab-workoutcool-test -f compose.workoutcool-test.yaml exec -T app node /app/aurora/import.mjs
docker compose -p auroralab-workoutcool-test -f compose.workoutcool-test.yaml up -d backup
```

O importador verifica o nome exato do banco de teste, exige o esquema nativo, usa transação e valida nomes/timestamps/tipos. Uma cópia já importada com o mesmo SHA-256 é ignorada; outra cópia é recusada para preservar modificações feitas na avaliação. Não apague o snapshot para forçar uma nova importação sobre dados existentes.

Após validar a importação, adicione somente esta rota Tailscale, preservando as demais:

```sh
docker compose exec -T tailscale tailscale --socket=/var/run/tailscale/tailscaled.sock serve --bg --https=8444 http://127.0.0.1:18444
```

Sem sessão, o gateway redireciona para o login central; origem externa recebe 403. Testes com o segredo interno são verificações de serviço executadas no servidor, nunca uma forma de abrir sessão no navegador.

## Mapeamento e limites

- Sessões: horários originais, duração em segundos, exercícios e séries. Títulos/notas e metadados Garmin disponíveis vão aos comentários da sessão e ao snapshot.
- Séries: tempo em segundos, peso inteiro e repetições inteiras. Frações de peso são recusadas para revisão em vez de arredondadas. Campos originais permanecem no snapshot.
- Rotinas: programas livres com uma semana e uma sessão; ordem e sugestões das séries preservadas. O nível Iniciante obrigatório é apenas um padrão técnico declarado na descrição.
- Peso corporal: histórico preservado no relatório `/pt/aurora-import`, sem simular um recurso nativo inexistente.
- Calorias, velocidade, distância e outros campos sem equivalente: snapshot privado completo; calorias disponíveis também no relatório. Não há promessa de gráficos nativos para esses campos.
- Nenhum novo treinamento é buscado no Garmin. Não são copiadas chaves Garmin, passkeys openGym ou senhas para o aplicativo.
- Português depende das traduções upstream; alguns termos do projeto podem permanecer em inglês.
- Cobrança e analytics desativados, recursos premium não concedidos. Vídeos externos podem depender da rede do navegador; o servidor da aplicação permanece sem saída externa.

## Backup e recuperação

O serviço backup cria um pg_dump diário em `data/workoutcool-test/backups/` com SHA-256. Não tem retenção automática; monitore espaço. O backup geral do AuroraLAB inclui fontes e secrets, mas não é uma cópia consistente desse PostgreSQL. Execute o ensaio independente:

```sh
python3 docker/server/workoutcool-test/backup-verify.py
```

Ele faz dump customizado e restaura em um PostgreSQL temporário com `--network none`, sem montar o banco ativo. Produz comprovante `.restore.json`, confere as tabelas de sessões/séries/programas/snapshot e remove somente o container temporário que criou. Copie dump, checksum, comprovante e secrets necessários para armazenamento privado fora do servidor. Eles contêm dados pessoais; não são cifrados automaticamente.

Uma recuperação definitiva deve ocorrer em outro banco/projeto, com os escritores parados e credenciais preservadas, seguida de conferência dos totais e do login. Não execute pg_restore sobre o teste ativo sem plano de recuperação. Não use down -v como atualização.

## Parar sem apagar dados

```sh
docker compose -p auroralab-workoutcool-test -f compose.workoutcool-test.yaml stop
```

O aplicativo atual continua funcionando. Desativar a rota :8444 ou remover os dados é uma operação separada; não reinicialize a configuração Serve inteira. Código upstream, fixações e licença: [SOURCE.md](../docker/server/workoutcool-test/SOURCE.md).
