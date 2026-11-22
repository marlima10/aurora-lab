# AuroraLAB 35.0.0 — Gemini no Javis do servidor

O Javis passa a conversar com o Gemini diretamente no AuroraServer. O navegador ou celular com Tailscale acessa o próprio chat do Javis, com login único. O Claude Desktop e a ponte SSH do Windows deixam de participar da arquitetura ativa.

## Motor e configuração

- Mantido o Javis OS original 0.623.0, commit upstream `38cc59499c7bb18b50324b1789a32a3a53a1a7dd`, imagem oficial fixada por digest e seis fontes críticas verificadas no build.
- Gemini API usa o motor, streaming e ciclo de ferramentas nativos do Javis.
- Modelo validado: **gemini-3.5-flash-lite**, presente no catálogo real da chave e na faixa gratuita documentada pelo Google na data da migração. O proprietário confirmou o projeto Free Tier.
- Formulário privado em `/aurora-ai/setup`, protegido pelo administrador do SSO. A chave é salva no cofre nativo criptografado e retirada do campo do navegador após o envio; não passa pelo chat, URL, Git ou localStorage.
- Estado técnico em `/aurora-ai/status` informa somente presença da chave, provedor e modelo. Uma chave salva não é apresentada como prova de autenticação válida: catálogo real e resposta de IA são verificações separadas.
- Diagnóstico de chave recusada pelo Google (HTTP 400), catálogo indisponível e permissão de projeto (HTTP 403). A chave inválida inicialmente salva foi corrigida pelo proprietário na página privada, sem exposição da credencial.
- Consulta do catálogo Google envia a chave em cabeçalho, substituindo o envio por query string do upstream.

## Conectividade e containers

Novo container **javis-ai-egress** fornece um túnel TLS que aceita somente `generativelanguage.googleapis.com:443`. Não descriptografa tráfego nem registra chave, cabeçalhos ou conteúdo. Outros destinos são recusados.

O Javis continua em rede interna, sem acesso geral à internet ou Docker socket. Somente o túnel participa também de uma rede de saída. `NO_PROXY` mantém a comunicação com o MCP interno. Código em leitura, usuário sem privilégios, limites de memória/CPU/processos e ausência de portas públicas são preservados.

São sete serviços do módulo: Javis, MCP, quatro conectores de domínio e túnel Gemini. Somente Javis/túnel usam novas imagens 35.0.0; os conectores sem mudanças permanecem nas imagens 34.0.0. Os aplicativos existentes foram preservados.

## Conversa, dados e ferramentas

- WebSocket de conversa e grafo liberado com identidade do gateway e sessão nativa do Javis, sem segundo login.
- Terminal e voz ao vivo permanecem desativados nesta implantação.
- Sete consultas aos aplicativos: treinos openGym/Garmin, contas/categorias Actual, resumo financeiro Actual, receitas Mealie, listas de compras Mealie, estado OctoPrint e biblioteca Manyfold.
- Três ferramentas nativas de leitura, pesquisa e listagem do vault `/brains/auroralab`.
- Descoberta, inventário e rotas recebem a mesma lista de permissões. O filtro respeita o identificador nativo `fn`, incluindo o namespace `auroralab__`, e mantém solicitações de escopo mais estreito.
- Plugins, staging, diretórios externos, shell e ferramentas de escrita não ampliam o catálogo. Os aplicativos mantêm a verificação das identidades/permissões vigentes a cada chamada.
- Escritas financeiras, alterações em treinos/receitas, exclusões e comandos de impressão continuam pelas interfaces dos próprios aplicativos. Esta release não oferece escrita irrestrita ou administração do Debian pela IA.
- Sugestões automáticas de próximo prompt, ferramenta de planejamento adicional e seleção automática de modelo de fundo desativadas. Pausas de tarefas autônomas já existentes foram mantidas para reservar a cota às solicitações do usuário.

## Retirada da dependência do PC

Removida somente a entrada MCP AuroraLAB gerenciada no Claude Desktop. Demais preferências, conectores e o aplicativo pessoal foram preservados, com cópia privada da configuração anterior. Revogada a chave SSH exclusiva da ponte e retirado o lançador de comando forçado. A chave administrativa principal e o acesso SSH ao servidor foram preservados. Não houve reescrita de histórico Git.

## Validação realizada

- **25 testes do módulo** com fixtures: identidade SSO, sessão nativa, WebSocket, estado sem chave exposta, preservação de segredos, consultas limitadas, namespace de ferramentas, filtro de inventário, transporte e destino TLS.
- **16 testes operacionais**: redirects, cabeçalhos de segurança, versões do cache PWA, alertas e restauração.
- Compose validado; imagens construídas a partir do código revisado. Identificador de cache do portal e URLs do banner do Javis renovados.
- Túnel alcançou a API Google sem credencial e recusou um destino externo fora da lista.
- Catálogo da chave corrigida confirmado com `live: true`.
- Gemini 3.5 Flash-Lite respondeu a uma mensagem curta a partir do container do servidor.
- Ciclo nativo do motor chamou `auroralab__aurora_fitness_summary` e produziu resposta, sem erro. Registro técnico guarda somente provedor, modelo, ferramenta, tipos de eventos e tamanho da resposta; conteúdo pessoal não foi publicado.
- Catálogo nativo conferido com dez ferramentas autorizadas, sem shell/escrita.
- WebSocket autenticado retornou `hello` e `pong`, sem depender do Windows ou criar dados de teste nos aplicativos pessoais.
- Backup anterior à migração e restauração isolada aprovados. O backup privado inclui estado do Javis e chave criptografada; cópia externa e conferência final são registradas no relatório de implantação.

## Uso, privacidade e limites

Abra o Javis pelo portal ou por `https://SEU-HOST-PRIVADO:7777/#p=chat`, com Tailscale conectado, e recarregue a página após a atualização. Exemplo: “Resuma meus últimos cinco treinos”.

O modelo roda na nuvem Google. Dados incluídos nas consultas e mensagens são enviados ao provedor. O Free Tier tem limites e condições próprias: o Google informa uso de entradas/saídas para melhorar produtos e orienta não enviar informações pessoais, confidenciais ou sensíveis. O proprietário deve considerar esses termos ao escolher quais fontes disponibilizar. Credenciais dos aplicativos não são retornadas ao modelo.

A instalação não ativa faturamento nem muda o plano do projeto Google. Limites/elegibilidade podem impedir chamadas; uma chave de projeto pago configurada futuramente pode gerar cobrança de acordo com esse projeto. Não foi habilitado fallback pago. Testes não representam garantia de disponibilidade contínua ou de quota futura.

Guia de arquitetura, configuração e retorno: [docs/JAVIS.md](https://github.com/marlima10/aurora-lab/blob/main/docs/JAVIS.md). Fontes do provedor: [preços](https://ai.google.dev/gemini-api/docs/pricing), [chaves](https://ai.google.dev/gemini-api/docs/api-key), [termos](https://ai.google.dev/gemini-api/terms).
