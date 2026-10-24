# Revisão técnica — AuroraLAB 24.0.0

Data: 24/10/2026. Base: release 23.0.0, `9b39f6c8d300388fbec28ee31852e7a8f0ef0f6c`. Escopo: pacote recebido, segurança do portal, implementação opcional de autenticação central e preparação privada do administrador.

## Conclusão e estado de implantação

O pacote recebido foi incorporado após conferir origem, manifesto e aplicação do patch. A autenticação central foi implementada em serviços separados e adaptadores específicos; não depende apenas de proteger a página inicial. **A migração dos oito aplicativos em produção não foi executada.** Publicar esta versão não altera esse estado.

O novo administrador foi preparado em banco separado. A chave tem 151 caracteres e fica fora do Git; os oito vínculos administrativos usam as identidades já existentes. O `.env` e a seleção Compose ativa foram preservados. Todas as integrações privadas permanecem `ready: false`, impedindo sua liberação prematura. Essa chave é uma credencial preparada para a futura ativação, não uma credencial já aceita pelos aplicativos atuais.

## Problemas corrigidos durante a revisão

| Problema | Alteração |
| --- | --- |
| Nome de TAR sugeria distribuição oficial, mas trazia somente arquivos alterados | Publicação pelo Git e documentação da base e do conteúdo recebido; aplicador recebido não executado. |
| Os testes recebidos verificavam texto e não o comportamento do proxy | Ensaio HTTP com Nginx real, fontes delimitadas e serviços fictícios em rede isolada. |
| Login na página inicial não eliminaria nem controlaria identidades nativas | Adaptadores vinculam cada sessão à identidade existente do aplicativo. |
| Mealie reverse proxy faz login, mas pode manter tokens antigos em requisições seguintes | Middleware ASGI substitui a identidade e a sessão nativa em cada requisição. |
| Sessão anterior do OctoPrint poderia manter outro usuário | Plugin estabelece explicitamente o usuário mapeado, após verificar o segredo do proxy. |
| Token antigo do Home Assistant poderia pertencer a outra pessoa | Intermediário consulta o proprietário do token em HTTP/renovação/WebSocket antes de aceitá-lo. |
| Cockpit mantém autenticação do Debian mesmo atrás de um proxy genérico | Sessão local de conta não root por socket Unix privado; autorização administrativa no gateway. |
| Portas nativas e monitor poderiam contornar a autenticação do portal | Overlay remove publicações nativas; monitor exige segredo independente. A configuração nativa HA exige migração explícita. |
| Cookie central poderia chegar aos servidores dos aplicativos | Gateway remove apenas esse cookie, preservando cookies nativos; testadas posições inicial, intermediária e final. |
| Um aplicativo poderia tentar operar o gerador ou a energia com a sessão de outro | Verificação de origem exata, CSRF e papel administrativo; energia recebe credencial somente no servidor. |
| Fitness legado contém registros compartilhados | Rotas e arquivos Fitness ficam reservados ao administrador no gateway SSO. A credencial de energia não é enviada à API Fitness. |
| Importador Garmin dependia apenas da sessão nativa de navegador | Propagação controlada da identidade SSO ao openGym, condicionada ao modo habilitado; cliente de máquina permanece compatível. |
| Novo banco de autenticação poderia ficar fora do backup | Mount adicional e verificação de restauração exigem SQLite de autenticação quando o overlay estiver arquivado. |
| Risco de expor chaves em cache ou logs | `/auth/` fora do PWA, respostas sem cache, chaves fora do banco e sem logs de requisições na autenticação/gateway. |

## Evidências

| Verificação | Resultado e alcance |
| --- | --- |
| Garmin | 45 testes de importação, calorias, sincronização, API pessoal e propagação condicional de identidade, com API simulada. |
| Servidor | 32 testes em Linux: preparação, operação, restauração, aplicativos, links, cabeçalhos e versões do cache. |
| Autenticação e preparação | 18 testes: chave, hashes, sessões, permissões, CSRF, concorrência, idempotência e preservação da configuração ativa. |
| Gateway Nginx real | 49 verificações HTTP: nove destinos simulados, identidade, cookies, origem, papel, revogação, Fitness legado e bloqueio preventivo. |
| Home Assistant | 6 testes de protocolo com upstream simulado. Não é um ensaio do servidor HA completo com sua automação pessoal. |
| openGym | 3 testes do adaptador e construção da imagem sobre fonte com hash verificado. Não houve alteração de treinos pessoais. |
| HomeBoard | 3 testes do adaptador de edição e construção da imagem com hash da classe original verificado. |
| OctoPrint | 2 testes usando Flask e os pacotes nativos instalados, com usuários fictícios e sem hardware. |
| Manyfold | 4 verificações sintéticas do middleware no runtime instalado: usuário, papel, segredo forjado, inexistente e inativo. Não inicializam um banco Rails de produção. |
| Mealie | Imagem construída e aplicação nativa iniciada com banco descartável: usuário correto, cookie nativo, token antigo substituído, usuário desconhecido e segredo falso recusados. |
| Cockpit | Resposta de sessão via socket Unix temporário e processo no UID local esperado; serviço instalado preservado. Não é validação de todas as funções administrativas do painel. |
| Compose | Seleção de overlays em uso acrescida do novo overlay validada com `config --quiet`; nenhum serviço iniciado pela validação. |
| Interface | HTTPS temporário: entrada admin, saída e entrada comum. Gerador ausente para usuário comum. Prévia registrada sem chave real; rota temporária removida. |

O conjunto Garmin também é verificado com APIs simuladas para preservar os contratos de importação. Os relatórios locais guardam os resultados e o manifesto SHA-256 dos arquivos delimitados de ensaio. Não foram usados bancos pessoais nos testes.

## Condições para ativação

É necessário seguir [LOGIN-UNICO.md](LOGIN-UNICO.md), incluindo aceite por aplicativo, contas existentes, acesso compartilhado do Actual/HomeBoard, configuração HA, socket Cockpit, teste por outro aparelho das portas de desvio e backup restaurável do banco central. O estado `ready` não é uma certificação automática; o operador só o altera após concluir esses testes.

Os ensaios não substituem a homologação de todos os fluxos nativos em um navegador: funções administrativas, dispositivos, orçamento criptografado, automações HA e clientes móveis exigem verificação de aceitação na migração. Isso está separado da revisão e publicação de código solicitada.

## Limites de segurança e manutenção

A autenticação é própria do projeto e precisa de manutenção e revisão a cada atualização dos adaptadores. Não há verificação da caixa de e-mail: o e-mail é um identificador cadastrado pelo administrador. Quem obtiver a chave pode entrar até sua revogação; a distribuição é responsabilidade do administrador.

O ambiente confia nos aplicativos do mesmo hostname, no Docker e no administrador do host. O gateway não transforma um aplicativo comprometido em ambiente isolado. Dados offline e conexões já abertas não são apagados retroativamente. Contas nativas, SSH, SMB, tokens de máquina, sudo e polkit mantêm suas responsabilidades específicas.

Backups continuam privados e sem criptografia automática. A cópia privada da chave inicial e do banco central preparado não é publicada e deve acompanhar a política de proteção dos demais acessos do servidor.
