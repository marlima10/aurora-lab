# AuroraLAB 24.0.0 — revisão do portal e autenticação central

Esta versão incorpora a revisão do pacote enviado pelo Claude e acrescenta uma implementação **opcional** de login por e-mail e chave de 151 caracteres. Publicar esta release não instala nem ativa o login único no servidor.

## Revisão do pacote recebido

Os 25 arquivos recebidos foram conferidos com o manifesto e com a base oficial 23.0.0, commit `9b39f6c`. O arquivo recebido com nome de distribuição oficial continha somente os arquivos alterados; a publicação oficial é feita pelo fluxo Git, branch `rafael`, pull request, merge na `main` e tag.

Foram preservados os cinco cabeçalhos de segurança, ocultação da versão do Nginx, limites de POST de energia e Fitness, resposta 429 com indicação de espera, câmera sem cache, movimento reduzido, textos atualizados e renovação do cache PWA. Os testes recebidos são estáticos; os ensaios adicionais desta revisão estão descritos abaixo.

## Login central

- Administrador inicial: `aurora@server.local`. Somente esse administrador pode cadastrar e-mails, escolher os aplicativos e identidades permitidos, gerar/copiar uma nova chave e revogar acessos.
- Cada chave tem exatamente 151 caracteres aleatórios. O banco guarda seu resumo criptográfico, nunca a chave original. O administrador vê a chave nova para distribuição; recuperar uma chave antiga exige gerar outra.
- Trocar a chave invalida a anterior e todas as sessões daquele cadastro. Revogação bloqueia novas requisições. Sessões têm duração máxima de 12 horas, cookie Secure/HttpOnly e proteção contra operações de outra origem.
- Os aplicativos compartilham a sessão no mesmo navegador e hostname HTTPS. Outro aparelho, janela anônima ou armazenamento isolado precisa fazer sua própria entrada.
- As permissões centrais apontam para identidades **já existentes** em cada aplicativo. Cadastrar um e-mail não entrega automaticamente os dados pessoais de Rafael.
- O painel de energia usa a autorização administrativa central, sem pedir uma segunda chave ao navegador, quando o overlay SSO estiver ativo.

## Integração com os aplicativos

O gateway valida a sessão em cada requisição e substitui cabeçalhos de identidade enviados pelo cliente. O cookie central é retirado antes de encaminhar a requisição ao aplicativo. Portas nativas são retiradas da publicação ou vinculadas ao loopback; o monitor ganha um segredo independente para impedir acesso direto à porta 9101.

| Aplicativo | Integração implementada |
| --- | --- |
| Manyfold | Middleware Rack estabelece a identidade existente no Warden e preserva os papéis nativos. |
| Mealie | Middleware ASGI resolve o usuário existente, gera a sessão nativa e substitui tokens antigos em cada requisição. Cadastro automático desativado. |
| Actual Budget | Autenticação nativa por cabeçalho. A credencial fica no servidor. O acesso concede entrada à instância compartilhada, sem criar isolamento por orçamento. |
| openGym | Adaptador vincula a sessão ao perfil existente, sem migrar treinos. Tokens de clientes de máquina permanecem compatíveis. |
| Garmin | O intermediário repassa a identidade central ao openGym quando SSO está habilitado; a sincronização automática já pareada continua usando sua autorização nativa. |
| OctoPrint | Plugin valida o proxy e estabelece o usuário existente. Não cria usuários nem altera impressões. |
| Home Assistant | Proxy HTTP/WebSocket valida o dono do token nativo. O fluxo inicial usa aliases privados e autenticação nativa por rede confiável, restrita ao intermediário. |
| HomeBoard | Adaptação da classe de autenticação para papéis de visualização e edição, sem substituir configurações do painel. |
| Cockpit | Sessão local no usuário Debian existente, por socket Unix privado, acessível somente pelo gateway autorizado. Não entrega root nem modifica sudo/SSH. |

Os adaptadores que alteram fontes verificam o hash da revisão original e recusam versões não revisadas. São imagens próprias sobre versões fixadas; não são recursos oficiais dos respectivos projetos.

## Arquivos e operação

`compose.auth.yaml` é separado e não é acrescentado automaticamente ao `.env`. `docker/server/auth/prepare.py` prepara o novo banco, a chave inicial e os arquivos privados sem alterar dados dos aplicativos, serviços do host ou configuração ativa do Compose. Integrações começam com `ready: false` e ficam bloqueadas até a validação individual.

O banco central entra no backup e na verificação de restauração quando o overlay é selecionado. A rota `/auth/` fica fora do service worker. O menu do portal ganha “Minha conta” ou “Usuários e chaves” quando a sessão central está disponível; o ambiente anterior continua compatível.

Consulte [LOGIN-UNICO.md](LOGIN-UNICO.md) para requisitos, preparação, migração e retorno. Não ative apenas o gateway: a migração inclui identidades, portas, Home Assistant e o socket privado do Cockpit.

## Validação realizada em 24/10/2026

- 18 testes de autenticação e preparação: tamanho e armazenamento da chave, permissões, concorrência, expiração, rotação, revogação, cookies e proteção de operações administrativas.
- Nginx real: sintaxe válida e 49 verificações HTTP em rede isolada, com nove aplicativos simulados. Incluem redirecionamento anônimo, identidade forjada, cookies nativos, permissão por aplicativo, energia administrativa, origem e bloqueio de integração não validada.
- 32 testes do servidor e restauração, incluindo o novo banco central.
- 45 testes Garmin com APIs simuladas; 3 testes openGym, 3 HomeBoard, 2 OctoPrint e 4 verificações Manyfold com identidades fictícias.
- 6 testes de protocolo do Home Assistant com servidor simulado, incluindo token de outro usuário, renovação e WebSocket.
- Construção das imagens adaptadas de Mealie, openGym e HomeBoard sobre as revisões fixadas.
- Mealie real com banco novo descartável: identidade nativa correta, cookie nativo, token antigo substituído, segredo falso e usuário inexistente recusados.
- Cockpit instalado: ensaio em socket Unix temporário com UID do usuário local, resposta de sessão sem senha e sem alterar o serviço ativo.
- Tela HTTPS isolada: entrada administrativa, saída e entrada comum; gerador ausente para usuário comum. Nenhuma chave real foi usada nesse ensaio.

Resultados adicionais e limites estão em [REVISAO-24.md](REVISAO-24.md). Estes ensaios **não equivalem à migração dos aplicativos pessoais em produção**. A release deixa essa ativação separada, com bloqueio preventivo.

## Limites conhecidos

As aplicações no mesmo hostname são componentes confiáveis do ambiente. Um aplicativo comprometido não é isolado como um terceiro externo. Conteúdo já armazenado offline e conexões/streams já abertos não são apagados ou encerrados retroativamente ao revogar uma chave. A próxima requisição passa novamente pela autorização.

O login central cobre o acesso web aos aplicativos listados. SSH por chave, SMB e clientes de máquina mantêm suas credenciais próprias. Sudo/polkit pode pedir confirmação de elevação dentro do Cockpit. Os limites de tentativas podem ser compartilhados por aparelhos vistos pelo proxy com o mesmo IP.

Não foi alterado nenhum banco pessoal, configuração da impressora, política da tampa ou método de autenticação SSH durante a revisão. A implantação atual continua independente da publicação desta versão.
