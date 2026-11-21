# AuroraLAB 34.0.0 — Javis OS e Claude Desktop gratuito

O AuroraLAB passa a oferecer o **Javis OS original 0.623.0**, integrado aos aplicativos existentes por ferramentas MCP. A conversa usa a conta gratuita do Claude Desktop no Windows, sem chave de API paga e sem modelo local. O painel Javis tem atalho administrativo no portal e usa a sessão do login único.

## Origem e implementação

- Upstream: `blogminhquy/javis-os`, commit `38cc59499c7bb18b50324b1789a32a3a53a1a7dd`.
- Imagem oficial amd64 fixada por digest; build confere versão e SHA-256 de seis arquivos críticos. Interface, hub MCP, registro de conexões e ferramentas de notas são os originais.
- Overlay opcional `compose.javis.yaml`, sem executar o instalador completo do upstream, Watchtower, guard privilegiado ou atualização automática dos CLIs.
- Seis containers separados: `javis`, `javis-mcp`, `javis-fitness`, `javis-food`, `javis-print` e `javis-finance`.
- Usuários sem privilégios, limites de memória/processos, código em leitura, tokens diferentes por conector e redes correspondentes aos aplicativos. Javis fica em rede interna, sem saída para provedores de IA e sem Docker socket.

## Consultas disponíveis

| Aplicativo | Função |
| --- | --- |
| openGym / Garmin importado | Resumo dos últimos treinos, duração e calorias disponíveis, em período limitado |
| Actual Budget | Contas/categorias e totais de receitas, despesas e saldo do período |
| Mealie | Pesquisa de receitas e consulta de listas de compras |
| OctoPrint | Estado, progresso e trabalho atual da impressora |
| Manyfold | Consulta à biblioteca de modelos 3D |

São sete ferramentas AuroraLAB, publicadas pelo hub com o prefixo `auroralab__`. Consultam permissões vigentes no SSO a cada listagem/chamada. As entradas rejeitam parâmetros desconhecidos, URLs arbitrárias, datas inválidas e limites excessivos. Medições ausentes permanecem ausentes.

O conector financeiro utiliza o SDK oficial `@actual-app/api` 26.10.0 e cache próprio. Totais são expressos em centavos; transferências e linhas-pai não entram na soma; histórico de contas encerradas é preservado. Não há ferramentas de importação ou gravação de transações. Mais de um orçamento ou criptografia exige seleção privada explícita, sem criação automática de orçamento.

## Notas e relatórios

O Claude pode ler, pesquisar e listar somente o vault próprio do Javis. Pode criar uma nova nota Markdown em `notes/` ou `reports/`, até 20 mil caracteres, sem sobrescrever arquivos. A orientação entregue ao modelo exige confirmação do conteúdo antes de salvar. Caminhos absolutos, ocultos e fora desse espaço são bloqueados; gravações da ponte são coordenadas por bloqueio.

Isso não autoriza gravar nos aplicativos nativos, executar shell, comandar o Docker ou iniciar impressões. A lista exata de ferramentas também é validada nas chamadas, não apenas apresentada ao modelo.

## Login e conexão privada

- Painel reservado ao administrador protegido e à permissão portal. Adaptador cria uma sessão nativa após validar a identidade e o segredo do gateway; cookies do cliente não escolhem o perfil.
- Endpoint de permissões autenticado por token, disponível somente na rede interna e bloqueado no portal público.
- Claude Desktop usa uma chave SSH exclusiva com comando forçado e `restrict`, sem terminal nem encaminhamento de portas. A chave privada permanece no Windows.
- Ponte local em UTF-8 abre um transporte restrito por chamada ao hub stateless, permitindo recuperar as consultas após reinícios do Javis.
- Sem endpoint MCP público nem Tailscale Funnel. Preferências anteriores do Desktop foram preservadas. Aprovações de ferramentas no Claude continuam sendo respeitadas.

## Interface e backup

Novo atalho Javis OS visível ao administrador, redirect HTTPS privado, entrada no menu e renovação coerente do cache PWA. A interface original abre nas notas do AuroraLAB e mostra orientação em português e links para notas/conexões/portal sem cobrir a navegação.

Backup ampliado para estado, notas e configurações do Javis; cache financeiro fica fora. O backup confiável recebe acesso gravável ao estado Javis para permitir inicialização dos arquivos auxiliares SQLite/WAL, mediante autorização específica do proprietário. Os bancos de origem continuam abertos por `mode=ro`, com snapshots consistentes e sem ignorar WAL ativo. Notas e demais novos volumes são somente leitura no backup. O verificador de restauração exige o estado Javis quando o overlay está incluído.

## Validação realizada

- 24 testes de autenticação: sessão, origem, administrador, token interno e revogação de permissões.
- 16 testes do módulo Javis: consultas, isolamento, sessão nativa, bloqueio de chat pago, preparação idempotente e proteção das notas.
- 3 testes da ponte Desktop: uma mensagem por linha inclusive CRLF, notificações e falha de transporte sem exposição de diagnóstico privado.
- 7 verificações financeiras com dados sintéticos: centavos, transferências, histórico, identidade, datas e bloqueio de escrita.
- 16 testes de redirects, cabeçalhos, cache PWA, alertas e restauração.
- Compose e sintaxe JavaScript aprovados; configuração Nginx aprovada.
- Sete consultas reais responderam pelo hub original, registrando apenas metadados técnicos. Nenhum dado de teste foi gravado nos aplicativos pessoais.
- Navegador confirmou atalho, login único e página de notas. Claude Desktop gratuito listou `notes/` e `reports/` sem erro, sem ler conteúdo pessoal nem gravar arquivos.
- Backup com restauração descartável aprovado: 939 arquivos, 19 bancos SQLite e 78 JSON, incluindo estado e notas Javis. Não substitui um ensaio completo de todos os serviços/hardware.

## Limitações desta modalidade

O Claude gratuito não fornece Claude Code/API para o chat interno do Javis. A conversa acontece no **Claude Desktop**, sujeita aos limites gratuitos da Anthropic. Chat interno e terminais WebSocket permanecem desativados. O painel original oferece inglês/vietnamita, com orientação AuroraLAB em português.

Esta ponte local exige Windows e Tailscale ativos; não habilita conversa pelo iPhone ou pelo navegador nem execução de IA com o Desktop fechado. Os resultados autorizados nas consultas ao Claude são enviados à Anthropic para responder, sem envio integral dos bancos ou credenciais. Não há integração de voz Whisper/Piper nem automações autônomas com IA nesta release.

Guia completo e arquitetura: [docs/JAVIS.md](https://github.com/marlima10/aurora-lab/blob/main/docs/JAVIS.md). Os aplicativos anteriores e seus dados foram preservados; a remoção do módulo experimental da release 33 não foi revertida. Históricos Git compartilhados não foram reescritos.
