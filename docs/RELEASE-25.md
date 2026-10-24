# AuroraLAB 25.0.0 — login único ativado e gestão de usuários no Início

## Resultado

A migração do AuroraServer foi executada para a autenticação central preparada na versão 24. Um login por e-mail e chave pessoal de 151 caracteres autoriza o portal e os oito aplicativos com suas identidades já existentes. A chave administrativa anterior foi preservada; nenhuma credencial é incluída nesta publicação.

A página principal ganhou o atalho **👥 Gestão de usuários**, com o mesmo padrão visual dos demais serviços. Ele abre `/auth/admin` e só aparece depois da confirmação da sessão administrativa. O backend continua recusando o gerenciamento para qualquer usuário comum, mesmo que tente abrir o endereço diretamente.

## Integrações migradas

| Aplicativo | Aceitação realizada |
| --- | --- |
| Manyfold | Usuário nativo existente reconhecido e página autenticada de conta acessível. |
| Mealie | Identidade existente confirmada pela API nativa; interface protegida acessível. |
| Actual Budget | Autenticação nativa por cabeçalho e acesso à instância compartilhada, sem redefinir sua senha ou dados. |
| openGym / Garmin | Perfil existente, treinos preservados e sincronização previamente pareada mantida. O navegador abriu o perfil Rafael sem solicitar passkey novamente. |
| OctoPrint | Leitura autenticada de configurações com o usuário existente, sem comandos físicos. |
| Home Assistant | Fluxo nativo sem senha, token pertencente ao perfil mapeado e comandos WebSocket válidos; navegador abriu a visão geral como Rafael. |
| HomeBoard | Sessão autenticada com papel existente confirmado. |
| Cockpit | Sessão real do usuário Debian Rafael por socket Unix privado; navegador abriu a visão geral sem outro login. Elevação sudo/polkit continua separada. |

## Correções encontradas durante a migração

- **Home Assistant:** a verificação interna da identidade foi movida para outro WebSocket. Isso evita consumir um ID alto no canal do navegador e quebrar os comandos subsequentes, que precisam de IDs crescentes. Os cabeçalhos `Sec-WebSocket-*` não são repassados entre handshakes independentes. Os formulários do navegador, inclusive multipart, continuam funcionando; a revogação aceita a resposta nativa vazia sem permitir que um token de outro perfil seja devolvido. A consulta do token força `Accept-Encoding: identity` sem duplicação por diferenças de maiúsculas/minúsculas.
- **HA 2026.10:** a configuração HTTP já migrada foi ajustada no armazenamento nativo conforme o esquema instalado. A porta 18123 fica apenas no loopback e na interface dedicada ao intermediário, confiando somente nesse proxy. O guia deixa explícito que acrescentar `http:` ao YAML pode não alterar essa versão.
- **Instância HA antiga:** foi identificada outra instalação ocupando a porta pública anterior. Sua configuração foi copiada, o contêiner foi desativado e seus dados foram preservados. A instância atual segue usando seu armazenamento original.
- **Cockpit:** a configuração foi instalada no subdiretório `cockpit/` dentro de `XDG_CONFIG_DIRS`. O tmpfs do gateway agora usa `/run`, preservando o socket filho; o caminho `/var/run` é um link na imagem. O proxy/socket TCP legado foi desativado depois do ensaio bem-sucedido.
- **Monitoramento:** no overlay SSO, o monitor consulta a API OctoPrint em uma publicação exclusiva no loopback 15000, com a chave interna existente, evitando receber uma página de login no lugar do JSON. A porta direta 9101 recusa requisições sem o segredo privado.
- **PWA:** cache renovado para a versão 25; a instalação verifica a sessão e não tenta armazenar arquivos Fitness administrativos para usuários comuns. Respostas redirecionadas de login não são guardadas como HTML ou JavaScript. `/auth/` permanece fora do cache e a instalação sem SSO continua compatível.

## Segurança e preservação

Somente `aurora@server.local` cadastra e-mails, escolhe permissões/identidades, gera ou renova chaves e revoga acessos. A chave nova pode ser copiada no momento da geração; o banco guarda hashes. A sessão central é limitada a 12 horas. As contas pessoais existentes não são atribuídas automaticamente a novos cadastros.

O gateway exige autorização em cada requisição, substitui cabeçalhos de identidade e não entrega o cookie central aos aplicativos. As portas nativas são retiradas da publicação ou limitadas às interfaces privadas necessárias. O HTTPS continua privado pelo Tailscale; não foi ativado Funnel. SSH segue somente por chave e o acesso Cockpit não entrega root nem adiciona NOPASSWD.

Foram preservados dados, perfis, chave administrativa, configurações e seleção anterior dos serviços. O backup anterior à migração e o posterior foram verificados. O posterior inclui o banco central de autenticação e passou por restauração descartável: **598 arquivos, sete SQLite e 44 JSON**, incluindo os bancos dos três aplicativos adicionais e do SSO. Nenhuma restauração foi feita sobre os dados ativos. Cópias externas ficam em diretório privado do operador, fora do Git.

## Validação desta versão

- 32 testes de servidor/operação/restore e 15 testes da autenticação central, todos com dados sintéticos.
- Dez testes isolados de protocolo HA, incluindo perfil incorreto, renovação, revogação, multipart, compressão WebSocket e sequência nativa de comandos.
- Seis cenários PWA: papéis administrativo/comum, compatibilidade sem SSO, redirects em navegação/arquivos e exclusão de `/auth/`.
- Compose completo e Nginx válidos; imagens adaptadas construídas com as bases fixadas.
- Os nove destinos reais recusaram acesso anônimo com redirecionamento ao login e responderam 200 com a sessão central; o monitor direto recusou acesso com 403.
- Identidades nativas conferidas nos aplicativos. Testes temporários de token foram revogados; tokens e senhas não fazem parte das evidências públicas.
- Portal real: atalho administrativo visível e navegação à gestão sem segundo login; leitura de bateria e monitoramento funcionando. Cockpit, openGym e HA conferidos também no navegador.

Os ensaios anteriores dos demais adaptadores permanecem documentados na [release 24](RELEASE-24.md). Esta release acrescenta a ativação e a aceitação de produção; não reescreve o estado histórico da versão anterior.

## Limites e retorno

A impressora e a câmera USB não foram detectadas durante a migração. Seus dados/configurações foram preservados; o overlay da impressora e o perfil da câmera ausentes não foram ativados. A câmera integrada não foi usada como substituta. A conexão física e uma impressão real permanecem dependentes dos dispositivos.

O SSO cobre o acesso web. SSH, SMB, clientes de máquina e elevação administrativa mantêm suas próprias autorizações. Actual autoriza a instância compartilhada; não cria isolamento por orçamento. Aplicativos no mesmo hostname são componentes confiáveis e conteúdo offline/conexões já abertas não são removidos retroativamente por uma revogação.

O overlay continua opcional para outras instalações. Publicar ou copiar esta release não substitui sua migração: preserve o inventário privado e valide cada aplicação antes de liberar `ready: true`. A configuração Compose, os destinos Serve, as configurações nativas e o código anteriores foram preservados para retorno sem remover volumes. Consulte [LOGIN-UNICO.md](LOGIN-UNICO.md) e [ATUALIZACAO.md](ATUALIZACAO.md).
