# AuroraLAB 30.0.0 — Jarvis com IA e voz locais

O AuroraLAB ganha um assistente pessoal no endereço `/jarvis/`, protegido pelo login central e acessível pelo atalho Jarvis na página inicial. A implantação usa o motor original OpenJarvis com Ollama e conectores controlados pelo AuroraLAB; não publica o servidor administrativo/desktop upstream e não utiliza Claude, Gemini ou qualquer API paga de IA.

## Componentes separados em Docker

Doze serviços: interface web, coordenador/API, motor OpenJarvis, Ollama, Whisper, Piper, worker de lembretes e conectores independentes para treinos, finanças, alimentação, impressão 3D e pesquisa. O overlay opcional `compose.jarvis.yaml` entra antes do overlay de autenticação, preservando os demais arquivos ativos. Nenhuma nova porta é publicada no host. Serviços internos têm tokens próprios, redes, volumes, verificações de saúde e limites de recursos; não recebem Docker socket, shell para o modelo ou privilégios de root.

## IA local e recursos

OpenJarvis fixado no commit `5a9b5268f2432f7ea4fe402e384ecb6b64a649bb`, com SHA-256 do arquivo upstream conferido no build. O adapter utiliza `openjarvis.engine.ollama.OllamaEngine`; a coordenação de sessão, ferramentas e interface é específica do AuroraLAB. Dependências Python e Node transitivas foram fixadas em manifests/lockfiles.

O perfil `aurora-jarvis:1.7b` utiliza Qwen3 1.7B quantizado com duas threads, contexto limitado e uma conversa processada por vez. O modelo inicial maior excedeu o tempo disponível no notebook; a configuração menor foi medida antes da liberação. Sem alteração da política de energia do Debian e sem fallback para provedores de nuvem.

## Conversa, notas, relatórios e lembretes

Histórico, notas e relatórios separados por e-mail da sessão. Relatórios podem ser baixados em Markdown. Lembretes persistem e são entregues na caixa Jarvis, atualizada enquanto a página está aberta. O worker retoma a agenda após reiniciar.

Lembretes não são notificações push no iPhone com o navegador fechado. Não há escuta permanente ou palavra de ativação. A interface tem estados de carregamento, erro e confirmação, tema claro/escuro e layout para telas estreitas. O service worker não armazena `/jarvis` nem seus endpoints.

## Voz

Whisper base via Faster Whisper em CPU INT8, com modelo fixado em uma revisão, português e limite de 90 segundos/8 MiB por gravação. O navegador envia áudio somente após a gravação manual; a transcrição preenche o campo para revisão antes do envio.

Piper usa a voz local `pt_BR-faber-medium`, com revisão e cartão do modelo preservados. A resposta falada é reproduzida pelo navegador, que pode exigir um toque. Áudio temporário permanece em memória; não é arquivado no histórico nem no backup.

## Aplicativos e ferramentas

- **openGym/Garmin:** consulta treinos por período ou últimos cinco dentro do período; totais de duração e calorias são calculados no conector. Calorias ausentes continuam ausentes, sem inventar séries, carga ou músculos. Não substitui nem altera a sincronização Garmin existente.
- **Actual Budget:** consulta contas/categorias e totais; prepara lançamentos com valores inteiros em centavos. Prévia resolve nomes de conta e categoria antes de propor a gravação. Biblioteca oficial sincroniza seu cache privado, sem editar diretamente o banco do aplicativo. `imported_id` vinculado à confirmação e exclusões respeitadas. Havendo vários orçamentos, exige mapeamento explícito; não escolhe um arbitrariamente.
- **Mealie:** busca receitas e listas de compras, além de propor a criação de uma receita pelo nome. Sugestões de cardápio usam informações disponíveis; não há migração ou substituição do aplicativo.
- **Manyfold/OctoPrint:** consulta biblioteca pelo formato nativo `application/vnd.manyfold.v0+json` e estado/progresso de impressão. Pausa é proposta apenas se houver impressão ativa e exige confirmação. Não inicia impressão, não envia G-code e não aquece a impressora automaticamente.
- **Pesquisa:** consulta fontes públicas por DDGS somente com opção habilitada pelo usuário naquele pedido. Termos de busca saem do servidor; dados privados não devem ser incluídos. A resposta da busca traz títulos, URLs e resumos, sem afirmar leitura integral das páginas.

## Confirmações e permissões

A API valida a sessão central, origem e CSRF. Reconfere grants antes de cada chamada de ferramenta e na confirmação; não aceita cabeçalho de identidade do navegador como autenticação. Conectores recebem apenas as credenciais necessárias ao seu domínio. Nenhum segredo é colocado no contexto do modelo.

Operações de escrita viram propostas revisáveis, válidas por 15 minutos e reivindicadas atomicamente por usuário. Propostas pendentes iguais reutilizam a mesma confirmação. Resultado incerto não é repetido automaticamente; a interface orienta conferir o aplicativo. As confirmações mostram ações e campos legíveis, em vez de apenas nomes internos de ferramentas.

Migrações versionadas criam o banco Jarvis e acrescentam metadados de prévia preservando propostas existentes. Chaves e banco da autenticação central permanecem no formato atual. A separação de dados nativos segue as identidades/grants já existentes: um perfil nativo compartilhado continua compartilhado.

## Backup e recuperação

O banco Jarvis e sua configuração entram no backup privado; modelos baixáveis e cache financeiro ficam fora. A verificação de restauração exige o SQLite Jarvis quando o overlay está presente.

Corrigida a preparação do backup Manyfold após reinício: uma consulta autenticada nativa inicializa os arquivos auxiliares WAL/SHM antes da leitura da origem montada somente para leitura. Não se ignora WAL nem se copia banco ativo sem snapshot.

Antes da ativação, backup completo, restauração isolada e cópia externa com SHA conferido. Depois da ativação, novo backup/restauração incluiu o Jarvis. Configuração anterior do gateway e seleção Compose preservadas para retorno sem apagar dados.

## Validação realizada

- 21 testes de autenticação central, em container sem rede e com dados fictícios.
- 21 testes Jarvis para propriedade de dados, CSRF, permissões, expiração, migrações, valores e confirmação atômica.
- 7 verificações DOM: identidade, HTML tratado como texto, proposta, revisão, cancelamento, confirmação e pesquisa desligada por padrão.
- 7 verificações financeiras com SDK fictício: autorização, totais, confirmação, centavos, prévia sem escrita, identificador de deduplicação e seleção de orçamento.
- Ensaio com modelo local real em rede de teste exclusiva, configurações fictícias e banco temporário: seleção de `note_save`, nenhuma gravação antes da confirmação, gravação sintética confirmada e isolamento de usuário. Sem segredos, redes ou bancos pessoais nesse ensaio.
- Inferência curta em aproximadamente 18 segundos; conversa sintética com ferramenta e confirmação em aproximadamente 99 segundos. Medidas do notebook, não garantia de latência.
- Piper gerou áudio sintético e Whisper transcreveu a frase em português; aproximadamente 9 e 7 segundos nesse teste.
- Consultas reais somente leitura aos cinco destinos nativos, sem criar dados de teste nos aplicativos.
- Compose e Nginx validados; acesso HTTPS/SSO e interface em tela estreita conferidos.

## Limitações práticas

Modelos pequenos podem interpretar pedidos incorretamente; revise dados antes de confirmar. Relatórios e consultas complexas podem demorar e precisam ser divididos. Aplicativos vazios precisam de contas, receitas ou modelos cadastrados para produzir resultados úteis. Não houve impressão física nem lançamento financeiro real como teste. Não existe integração de agenda externa, push no celular, ditado contínuo ou administração autônoma do servidor.

Documentação operacional completa: [JARVIS.md](JARVIS.md).
