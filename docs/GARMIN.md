# Garmin → openGym

Conector AuroraLAB em container separado, com acesso à API oficial Garmin Connect Personal e manutenção opcional do conector comunitário `garminconnect` 0.3.19. Não é um plugin publicado pela Garmin ou pelo openGym. Não requer aplicativo Strava.

## Uso

Conecte o Tailscale, entre no openGym e abra o botão **Garmin → openGym** no portal ou `/garmin/` no mesmo endereço HTTPS do openGym. Use o mesmo navegador da sessão openGym. Para a API oficial, informe sua chave no formulário privado, conforme a seção de migração abaixo. A conexão comunitária anterior fica na opção expansível; somente nela são usados e-mail, senha e eventual código de verificação.

Escolha até um ano por consulta, carregue a prévia e selecione as atividades. Só o botão **Importar selecionadas** grava no openGym. Até 1.000 atividades recentes são examinadas por consulta; a tela avisa se atingir esse limite. A importação manual não é automática; a opção de atualização horária está descrita abaixo. Não há envio para Garmin.

Importa resumos de data local, nome, duração e distância (metros convertidos para quilômetros e velocidade canônica em km/h). Não importa séries detalhadas de musculação, repetições, cargas, calorias, frequência cardíaca, mapas ou coordenadas. A duração aparece como resumo cardio neutro, inclusive para musculação; não representa uma série de resistência nem calcula músculos/carga.

IDs Garmin estáveis evitam duplicatas. Um registro persistente também impede recriar uma atividade que já foi importada e depois apagada no openGym. Planos, registros existentes e demais campos são preservados. Escrita usa a API autenticada do openGym com revisão e tentativa de mesclagem em conflitos. Não use restauração manual de um perfil antigo sem avaliar o registro de importações.

## Instalação

Conclua primeiro a preparação de [openGym](OPENGYM.md). Ela define OPENGYM_ORIGIN no `.env` e o arquivo local secrets/opengym.env. Selecione compose.opengym.yaml em COMPOSE_FILE, mantendo os overlays ativos. Prepare o volume antes de iniciar:

```sh
sudo install -d -m 700 -o 65534 -g 65534 data/garmin
sudo docker compose config --quiet
sudo docker compose up -d --build opengym-api opengym-garmin opengym-web
```

O template Nginx parte do openGym v1.4.1 e acrescenta `/garmin/`; revisar junto de futuras atualizações upstream. Não publica porta adicional. Container sem root, sistema de arquivos somente leitura e nenhuma capability. A página usa sessão openGym, sem nova chave administrativa; cada perfil possui diretório próprio identificado por hash. POST exige Origin HTTPS configurado para evitar solicitações de outros sites. A API interna não recebe credenciais Garmin.

A senha e código de verificação não são gravados nem registrados em logs; são usados em memória durante o login. Tokens de sessão persistem em `data/garmin/<hash>/tokens/garmin_tokens.json`, com diretórios 700 e arquivos 600. A prévia permanece em memória por 30 minutos, até reiniciar ou desconectar. O registro de IDs e uma cópia do perfil anterior à última importação também ficam no volume privado, incluído no backup. **Desconectar** apaga o token local; cópias anteriores de backup podem ainda contê-lo. Não remove atividades do Garmin nem as já importadas.

## Validação

```sh
python3 -m unittest discover -s docker/server/garmin -p 'test_*.py' -v
```

Testes usam dados sintéticos e API simulada. Login real e primeira importação dependem do titular da conta e devem ser confirmados separadamente. Nenhum dado pessoal é necessário para testar o código.

Para validar o contêiner iniciado, use `sudo docker compose ps opengym-garmin` e `sudo docker compose logs --tail=80 opengym-garmin`. O healthcheck interno testa `/health`; acesso à conta Garmin é uma validação distinta. Confira os imports de test_garmin.py e use um ambiente Python de teste com as dependências necessárias se faltar um módulo; não instale pacotes de teste no Python do sistema indiscriminadamente.


## API oficial pessoal — migração

Referências consultadas em 21/10/2026: [chave e autenticação](https://developer.garmin.com/gc-developer-program/personal/personal-api/), [FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq/) e [OpenAPI](https://developer.garmin.com/gc-developer-program/personal/swagger-docs/). A chave é criada pelo titular no Garmin Connect e mostrada uma única vez. Nunca envie pelo chat/Git. No painel privado `/garmin/`, entre no perfil openGym existente e informe a chave no campo **Chave pessoal Garmin**. Use a mesma conta Garmin do histórico anterior.

**Validar e salvar chave** faz POST ao endpoint oficial `/personalapitoken-service/personal-api/personal-api-key/token`, com `Authorization: ApiKey ...`, e valida a leitura de uma atividade antes de substituir a credencial. Uma falha preserva a chave anterior e os dados. A chave validada fica em `data/garmin/<hash>/personal-api.json`, modo 600, no volume privado do perfil; status e logs não devolvem a chave. O navegador limpa o campo ao enviar e não a guarda em localStorage. O volume/backup pode conter essa chave; proteja os backups. A conexão comunitária anterior permanece disponível até **Desconectar**, que remove ambas as credenciais locais, mantendo importações e registro de duplicatas. Revogação na Garmin é separada.

O token de acesso vale até 24 horas ou até a expiração da chave, o que ocorrer primeiro; não há refresh token. O conector obtém novo token em memória a cada operação de consulta. Uma chave de um ano precisa ser renovada pelo titular antes do vencimento. Somente o host HTTPS `personal.connectapi.garmin.com` é usado; redirects são recusados. O conector não consulta endpoints de saúde, sono ou localização.

As atividades são consultadas em `/activitylist-service/activities/search/activities`, com filtros locais `startDate`/`endDate`, paginação de 25 registros na API oficial e ordem decrescente por `startLocal`. Mantém o limite de 1.000 registros por consulta e um ano por período. A prévia usa o mesmo `activityId`, conversão e registro persistente do conector anterior: atividades existentes/depois apagadas não reaparecem como novas. Salvar a chave/carregar a prévia não grava treinos no openGym. A importação continua manual, após selecionar as atividades; não inventa cargas ou séries. O funcionamento real depende da validação da chave do titular; testes sintéticos não comprovam acesso à conta real.

O endpoint de token usa POST sem corpo e `Accept: */*`, como no exemplo cURL oficial. O cliente aceita token em texto simples, string JSON ou objeto OAuth; as consultas de atividades pedem JSON. Recusas ficam identificadas por código HTTP/etapa em `personal-api-status.json`, sem corpo remoto ou credenciais. Os tokens não são gravados em disco.

O tamanho de 25 foi validado na conta real após a API devolver HTTP 500 para páginas de 99/100 registros. O conector não ignora páginas com erro nem registra uma consulta incompleta como pronta. Mantém até 1.000 atividades por consulta e avisa quando atingir o limite.


## Atualização automática do treino mais recente

No perfil openGym já autenticado, **Ativar atualização a cada 1 hora** autoriza o conector a usar o pareamento nativo (`POST /api/pair/create` e `/api/pair/redeem`). O código de uso único é resgatado somente no servidor e o token resultante é guardado em `auto-auth.json`, modo 600, separado por perfil. Não há cópia de cookies do navegador, assinatura manual de tokens ou montagem do segredo global da API. O token nativo dá acesso ao perfil (não é um token com escopo reduzido); o conector usa apenas `/api/me` e `/api/data`. `GET /api/me` permite a renovação prevista pelo backend; uma sessão revogada/expirada pausa a automação até reativar pelo perfil autenticado.

A primeira consulta é imediata. Depois, o próprio container Garmin verifica os horários persistidos a cada 15 segundos e executa a próxima consulta 3.600 segundos após o término da anterior. `auto-sync.json` registra perfil, ativação, próximo horário, última execução e resultado. Reiniciar o container conserva a agenda, sem depender de navegador ou de agendamento no Codex. Só a atividade mais recente é consultada (`start=0`, `limit=1`), e só é adicionada se ainda não existir no histórico/registro de IDs. Não atualiza nem sobrescreve treinos existentes e não recupera automaticamente atividades anteriores quando houver várias entre duas consultas: use a importação manual nesses casos.

A gravação reutiliza a API oficial do openGym, revisão/conflito, mesclagem e snapshot anteriores à importação; planos, pesos e outros treinos são mantidos. Operações manuais e automáticas do mesmo perfil não se sobrepõem. Em falha da Garmin/rede não há gravação parcial; a próxima consulta é agendada para uma hora depois e a falha aparece no painel. Uma resposta ambígua de gravação é verificada pela leitura e pelo ID estável na próxima tentativa, evitando duplicatas.

**Pausar atualização** remove o token local pareado e preserva a chave Garmin e os treinos. **Desconectar Garmin** também pausa e remove as credenciais Garmin. Cópias anteriores de backup podem conter esses tokens; a revogação global de sessões no próprio openGym também encerra a autorização do conector. Configuração, chave e autorização pareada ficam no volume Garmin já incluído no backup privado; nunca entram no Git. Testes adicionais: `test_auto_sync.py`.
