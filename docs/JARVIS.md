# Jarvis no AuroraLAB — IA local

Módulo opcional em `compose.jarvis.yaml`. Usa o motor Ollama original do OpenJarvis, fonte fixada no commit `5a9b5268f2432f7ea4fe402e384ecb6b64a649bb`, com a camada Aurora de autenticação, coordenação e interface. Não publica o servidor administrativo nem a interface de desktop upstream. Não usa Claude, Gemini ou API paga, nem faz fallback para nuvem.

## Componentes

| Serviço | Papel |
| --- | --- |
| jarvis-web | Interface responsiva com texto, gravação e reprodução |
| jarvis-api | Sessão central, permissões, histórico por e-mail e coordenação de ferramentas |
| jarvis-engine | Adapter sem estado que usa `openjarvis.engine.ollama.OllamaEngine` |
| jarvis-ollama | Inferência local, um modelo e uma solicitação por vez |
| jarvis-whisper | Faster Whisper base, CPU INT8, português, limite de 90 segundos |
| jarvis-piper | Síntese local pt_BR-faber-medium |
| jarvis-worker | Entrega lembretes na caixa persistente Jarvis a cada 15 segundos |
| jarvis-fitness | Resumos de treinos existentes no openGym, sem nova importação Garmin |
| jarvis-finance | Biblioteca oficial @actual-app/api, cache privado e sincronização nativa |
| jarvis-food | Receitas e listas Mealie; proposta de criação de receita pelo nome |
| jarvis-print | Biblioteca Manyfold e estado OctoPrint; pausa por confirmação |
| jarvis-research | Pesquisa pública por DDGS; requer opt-in explícito em cada conversa |

Todos são containers separados. Não existe um container Claude: a escolha desta instalação é IA local. Notas e relatórios pertencem ao Jarvis; não são uma integração com um aplicativo externo de notas.

## Rede, sessão e escopo

A entrada é `https://HOST_PRIVADO/jarvis/`, atrás do gateway e da sessão Aurora existentes. Nenhum serviço Jarvis publica porta no host. `/jarvis` e seus endpoints ficam fora do service worker e não são armazenados em cache offline.

A API consulta `/auth/session` diretamente e exige origem principal e CSRF para POST. Cabeçalhos de identidade enviados pelo navegador não autenticam o usuário. O grant nativo de cada app é verificado antes de toda ferramenta e novamente na confirmação. As identidades compartilhadas existentes nos aplicativos continuam compartilhadas: o Jarvis não cria separação de dados dentro de um perfil nativo que já é comum.

Conectores recebem apenas sua configuração/segredo e pertencem às redes dos apps necessários. O API/coordenador não recebe o inventário de segredos dos aplicativos. Motor e voz usam redes internas; Ollama possui saída para download de modelos, com recursos de nuvem desativados. Apenas o pesquisador recebe rede para busca pública. Ao habilitar a pesquisa, os termos da consulta saem do servidor; não inclua dados privados na solicitação de pesquisa.

O motor não recebe shell, Docker socket, SQL, execução de código, ferramentas de desktop ou acesso genérico aos arquivos do host. Perfis e skills de terceiros não são instalados automaticamente. As credenciais nunca entram no contexto do modelo.

## Ações e confirmações

O modelo pode propor nota, relatório, lembrete, lançamento financeiro, receita e pausa de impressão. A proposta não executa a ação. O usuário revisa os campos e confirma na interface. Confirmações são por usuário, expiram em 15 minutos e são reivindicadas atomicamente antes da execução. Resultado incerto não é repetido automaticamente: confira o aplicativo antes de criar outro pedido.

Financeiro usa valores inteiros em centavos, valida conta/categoria e utiliza `imported_id=aurora-jarvis-ID_DA_CONFIRMACAO` para impedir duplicidade. Transferências são excluídas dos totais resumidos. Conta e categoria devem ser obtidas da ferramenta, nunca inventadas. Não há pagamento, movimentação bancária ou sincronização bancária automática neste módulo.

No Actual, configure `budgets` por identidade no arquivo privado se houver mais de um orçamento. Seleção automática só é aceita quando existe exatamente um orçamento remoto. Orçamentos criptografados precisam de configuração privada adicional; a senha não deve ser enviada no chat.

Lembretes são entregues na caixa do Jarvis. **Não há push no iPhone com o navegador fechado nesta versão.** Piper gera áudio no servidor; o navegador pode exigir um toque para reproduzir. O microfone funciona por gravação manual, não escuta permanente nem palavra de ativação.

Whisper/Piper não exigem acesso ao microfone do notebook: o áudio vem do navegador. Uma transcrição preenche o campo de texto para revisão e não executa ações sozinha. Áudio é processado em memória, não persistido. O histórico contém apenas mensagens textuais.

## Preparação e ativação

1. Faça backup, restauração isolada e cópia externa com SHA conferido conforme ATUALIZACAO.md.
2. Insira `compose.jarvis.yaml` em COMPOSE_FILE **antes** de `compose.auth.yaml`, preservando todos os overlays/overrides existentes.
3. Execute `python3 docker/server/jarvis/prepare.py --root /srv/auroralab`. O preparador gera apenas arquivos privados e diretórios novos; não ativa os serviços nem modifica bancos nativos.
4. Valide `docker compose config --quiet`, construa as imagens Jarvis e inicie somente os serviços novos.
5. Execute `docker compose --profile jarvis-setup run --rm --no-deps jarvis-models-init` para os modelos de voz e `docker compose exec jarvis-ollama ollama pull qwen3:1.7b` para o modelo textual. Depois execute `docker compose exec jarvis-ollama ollama create aurora-jarvis:1.7b -f /etc/aurora/Modelfile`. O perfil fixa duas threads para evitar disputa excessiva de CPU. Confirme as revisões/digests baixados no registro da implantação.
6. Valide consultas e inferência local, gere o gateway com `render_gateway.py`, teste Nginx e só então recrie o gateway para entrar na nova rede. Não reinicie todos os aplicativos.
7. Ative o atalho público somente depois dos testes e registre limitações reais.

As imagens base e o arquivo upstream têm digest/SHA fixados. O adaptador instala somente a dependência necessária para o motor selecionado; recursos extras do OpenJarvis como treinamento, desktop e agentes de código não são instalados. O arquivo original com sua licença Apache 2.0 permanece na imagem. Piper é distribuído sob GPL; o modelo faber possui cartão de modelo e dataset CC0. Consulte as licenças upstream antes de redistribuir imagens/modelos.

## Dados e recuperação

`data/jarvis/app/jarvis.sqlite3` guarda mensagens, notas, lembretes, propostas e auditoria. `data/jarvis/finance` é cache reconstruível do cliente Actual; modelos ficam em `data/jarvis/models` e `data/jarvis/ollama`. `secrets/jarvis` guarda tokens separados por serviço e mapeamentos, fora do Git.

O overlay inclui banco Jarvis, configuração e segredos no backup privado. Não arquiva áudio transitório, modelos grandes ou cache financeiro. A restauração isolada exige o banco Jarvis quando o compose correspondente está presente. O backup aquece a conexão nativa Manyfold antes de ler seu SQLite WAL: após reinício, os arquivos SHM/WAL podem ainda não existir numa origem montada somente para leitura. Não se ignora WAL nem se copia banco ativo sem snapshot.

Para retorno, remova apenas o overlay Jarvis da seleção, restaure o gateway anterior e pare os serviços Jarvis. Preserve os dados. Não use `down -v`, não restaure bancos antigos sobre aplicativos em execução e não reverta a autenticação central.

## Validação

`python3 -m unittest discover -s docker/server/jarvis/tests -v` usa usuários e bancos fictícios temporários. Verifique também `node --check` nos arquivos JS/MJS, Compose, Nginx, voz e inferência real. Não faça lançamentos financeiros, alterações de receitas ou comandos físicos de impressão em dados reais como teste.

A suíte não substitui medição no iPhone. Modelos pequenos podem escolher ferramentas incorretamente ou não chamar uma ferramenta: valide a saída e use os formulários/atalhos quando necessário. O software não afirma sucesso em gravação sem resposta do aplicativo. Pesquisa retorna fontes públicas e resumos, não garante leitura integral das páginas.

As migrações 1 e 2 preservam registros e propostas; a segunda acrescenta a prévia legível da ação. Prévia financeira consulta nomes antes de gerar a proposta e não importa transações. Propostas iguais ainda pendentes reutilizam a mesma confirmação.
