# AuroraLAB 45.0.0 — substituição do teste Workout Cool pelo wger

## Entrega

O ambiente de avaliação passa a usar **wger 2.7 estável**, a partir da imagem oficial `wger/server:2.7`, fixada pelo digest `sha256:1c5789b93bfe5eed0b7287255782d9177027b255de2b22b59f511a693a48db04`. A interface web nativa abre em português brasileiro e usa o fuso America/Sao_Paulo. Uma faixa identifica o teste e oferece atalhos para o relatório da cópia e o AuroraLAB.

Projeto Docker independente `auroralab-wger-test`, com aplicação Django/Gunicorn, PostgreSQL, gateway Nginx e backup. O COMPOSE_FILE de produção permanece separado. O endereço HTTPS privado :8444 passa a atender o wger; o openGym e sua sincronização Garmin permanecem ativos, sem mudança de banco ou aplicativo.

## Remoção do teste anterior

Retirados os containers e redes próprios do Workout Cool, a imagem nomeada do teste, o banco ativo e suas credenciais. Removidos do código atual o Compose e os adaptadores do aplicativo anterior. Os backups privados de recuperação e o histórico Git/release 44 foram preservados; não houve reescrita de histórico nem limpeza global de imagens compartilhadas.

## Cópia dos dados

- Mesma cópia privada autorizada do perfil openGym/Garmin, sem transferência para terceiros e sem reutilizar chaves Garmin, passkeys ou senhas.
- Sessões nativas com horários originais, exercícios correspondentes e notas/metadados da origem. IDs estáveis e checksum evitam duplicação; uma origem diferente é recusada para não sobrepor alterações da avaliação.
- Somente séries marcadas como concluídas viram WorkoutLog. Séries não concluídas ficam no snapshot e nas notas, sem contaminar o histórico executado.
- Cardio usa as unidades nativas de tempo e velocidade. Séries de força mantêm repetições, peso e unidade. O wger usa campos decimais com duas casas; os valores brutos permanecem no snapshot privado para auditar eventual precisão adicional.
- Rotinas viram rotinas/dias/séries nativos. As datas de vigência são técnicas da avaliação, declaradas na descrição; a programação original permanece no snapshot. O limite nativo de nomes curtos é acompanhado do nome completo na descrição.
- Um agrupador técnico separado reúne sessões sem rotina equivalente. Ele não é apresentado como plano de exercícios recomendado.
- Peso corporal vai para a categoria nativa de medidas, mantendo a data original. Calorias e campos Garmin sem equivalente permanecem no snapshot e no relatório `/aurora-import/`.
- Cópia pontual: não há sincronização automática futura nem gravação de volta no openGym/Garmin.

## Login e proteção

O gateway verifica a sessão administrativa central e a origem antes de delegar a identidade. Apenas o administrador AuroraLAB configurado acessa o perfil de avaliação. O aplicativo exige segredo exclusivo e identidade esperada em cada requisição; o cookie central e o Authorization não são enviados ao Django. Somente o cookie CSRF nativo é encaminhado.

O perfil local tem senha inutilizável; os usuários padrão do bootstrap ficam inativos. Cadastro, login, logout e fluxos de credenciais locais são recusados pelo adaptador. Não é uma implantação multiusuário e não habilita os clientes móveis nativos via JWT/PowerSync. O login web é o AuroraLAB; gerenciamento da sessão deve ocorrer no portal.

Banco sem porta publicada, app/db/backup em rede interna sem saída de internet; somente gateway participa das redes de entrada e de autenticação. Porta de entrada ligada ao loopback e HTTPS Tailscale privado, sem Funnel. Aplicação sem root, com filesystem somente leitura, limites de recursos e volumes próprios. Analytics/SMTP externo e sincronizações externas não são habilitados. Recursos Celery/Redis não são necessários ao teste web; USE_CELERY=False é a opção oficial utilizada.

## Verificações realizadas

- Imagem oficial fixada; Django check sem erros de configuração e aplicação/banco saudáveis.
- Três testes sintéticos de conversão: tempo/velocidade, peso fracionado/repetições e ausência de valores sem zeros fictícios.
- Três testes sintéticos do adaptador: cabeçalho falso recusado, identidade incorreta recusada e delegação válida preservando a página nativa e a faixa de avaliação.
- Importação real conferida por totais privados; histórico pelas rotas REST nativas e página inicial traduzida responderam 200.
- Acesso anônimo e identidade falsa redirecionados 302; origem externa recusada 403. POST sem CSRF recusado 403; POST com CSRF válido e corpo deliberadamente incompleto chegou à validação nativa 400, sem criar registros.
- Backup PostgreSQL customizado restaurado em container temporário sem rede, com comparação dos totais de sessões, séries, rotinas, medidas e snapshot. Dados e comprovantes pessoais ficam fora do Git.

## Limites e operação

A interface visual autenticada no navegador depende da sessão do titular; a implantação não deve registrar aprovação visual que não foi observada. O relatório privado distingue os testes de serviço dessa avaliação pessoal.

Backups próprios do PostgreSQL e dos uploads/media são separados do backup geral do portal. Guarde ambos e os secrets necessários em armazenamento privado fora do servidor. Código/adaptadores e procedimentos: [WGER-TESTE.md](WGER-TESTE.md). Fontes e licença AGPL: [SOURCE.md](../docker/server/wger-test/SOURCE.md).
