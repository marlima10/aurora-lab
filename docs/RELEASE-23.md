# AuroraLAB 23.0.0 — Manyfold, Mealie e Actual Budget

Entrega conjunta de três aplicativos independentes, preservando openGym/Garmin, impressão 3D, automação e administração existentes.

## Manyfold 0.153.0

- Catálogo de modelos 3D, com biblioteca persistente própria em data/manyfold/library, montada como /models.
- Imagem padrão oficial, aplicação em container próprio e Redis dedicado em rede interna, sem porta Redis no host.
- SQLite local em data/manyfold/config/manyfold.sqlite3; plugins persistem separadamente. A instalação não move arquivos nem conecta automaticamente o catálogo à impressora.
- Autenticação multiusuário ativada; administração e conteúdo privado exigem login. Cadastro aberto e federação desativados. Biblioteca inicial AuroraLAB pronta para receber os modelos do titular.
- Um processo web, concorrência reduzida dos trabalhos e limites de CPU/memória para compartilhar o notebook com os serviços atuais.

## Mealie 3.29.0

- Aplicativo de receitas, planejamento de refeições e listas de compras em container próprio.
- SQLite e arquivos persistentes em data/mealie; grupo inicial AuroraLAB e casa Casa.
- Cadastro aberto desativado. Conta administrativa local rafael com senha exclusiva, substituindo as credenciais de fábrica antes da publicação.
- Importações de receitas, cardápios e demais conteúdo são escolhidos pelo titular. SMTP, IA e autenticação externa não são ativados nesta entrega.

## Actual Budget 26.10.0

- Aplicativo de orçamento e organização financeira em container próprio, com armazenamento em data/actual.
- Autenticação por senha do servidor, gerada de forma exclusiva na instalação; métodos por cabeçalho e OpenID ficam desativados.
- A instalação não vincula bancos nem importa extratos; o titular cria o orçamento e escolhe sua moeda ao começar.
- HTTPS privado permite usar os recursos do navegador necessários ao aplicativo.

## Acesso e isolamento

- Três overlays Compose: compose.manyfold.yaml, compose.mealie.yaml e compose.actual.yaml, acrescentados à combinação existente sem remover os demais arquivos ou perfis.
- Portas locais vinculadas apenas a 127.0.0.1: 3214 (Manyfold), 9925 (Mealie) e 5006 (Actual). Acesso remoto HTTPS pelo Tailscale Serve existente, sem Funnel ou abertura pública.
- Redes separadas por aplicativo; Redis fica somente na rede interna do Manyfold. Nenhum aplicativo recebe Docker socket, dispositivos da impressora ou volumes openGym.
- Imagens oficiais fixadas por versão e digest em images.lock.json. Reinicialização automática, healthchecks e logs limitados.
- Novos atalhos no portal e opções no menu; status e alertas aproveitam o monitor existente apenas para os módulos habilitados.
- Preparação idempotente preserva .env e as credenciais existentes, inclusive COMPOSE_FILE e o perfil da câmera. Acessos iniciais ficam em arquivos privados fora do Git, com senhas diferentes entre aplicativos.
- O nome de usuário local é rafael no Manyfold/Mealie; o formulário Manyfold pede login pelo e-mail local rafael@auroraserver.local; o endereço rafael@auroraserver.local é um identificador local de instalação, não uma caixa de e-mail configurada. Actual usa somente a senha do servidor. Alterar as senhas no aplicativo não atualiza automaticamente o registro inicial de acessos.

## Persistência, backup e retorno

- Os três overlays acrescentam seus volumes e configurações ao backup diário. Redis persiste snapshots RDB; sua fila não é o armazenamento principal dos modelos e pode exigir nova análise após interrupção.
- Backup usa snapshots SQLite, inclui bibliotecas/receitas/orçamentos/configurações e recusa execução sem o banco de um novo módulo montado.
- O teste de restauração passa a exigir bancos dos novos módulos declarados no arquivo, além de verificar os dados anteriores.
- Backup anterior e posterior, cópias externas com SHA-256, registros da implantação e acessos ficam privados no AuroraServer/Windows.
- Retorno consiste em parar somente os novos aplicativos e retirar seus overlays, atalhos e portas Serve adicionais, preservando os dados para recuperação. Não remover volumes como etapa de retorno.

## Documentação e validação

- VERSION, README, arquitetura, histórico e guia APPS.md atualizados para a entrega conjunta.
- Testes com dados sintéticos verificam idempotência, preservação de configurações/segredos existentes, rejeição de origens inseguras, redirects HTTPS e exigência dos bancos na restauração.
- A validação operacional registra configuração Compose, saúde dos containers, autenticação inicial, HTTPS privado, status dos serviços anteriores e backup com restauração isolada.
- Aplicativos iniciam sem dados pessoais de receitas, modelos ou finanças. Cada titular decide o conteúdo que deseja incluir.

## Resultados conferidos nesta implantação

- 25 testes operacionais passaram no Linux com dados sintéticos e rede desativada; 12 testes de preparação/restauração passaram também no Windows. Compose e Nginx validados.
- Manyfold, Redis, Mealie e Actual saudáveis. Contas administrativas verificadas por mecanismos nativos; telas de login dos três aplicativos abertas pelo HTTPS privado.
- Atalhos visíveis no portal e status dos 12 serviços monitorados online. Os aplicativos anteriores mantiveram seus containers; somente monitor e backup foram recriados para incorporar os módulos adicionais.
- Backup completo com SHA-256 verificado e restauração descartável: 532 arquivos, seis bancos SQLite, 42 JSON e os bancos dos três aplicativos presentes. Essa conferência valida arquivos e bancos, sem simular toda a operação de cada aplicativo.
