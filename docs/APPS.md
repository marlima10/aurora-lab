# Aplicativos adicionais — AuroraLAB

Manyfold, Mealie e Actual Budget são módulos opcionais, em overlays separados, introduzidos na release 23. Consulte RELEASE-23.md para escopo e versões e docker/server/apps/images.lock.json para digests.

## Instalação em servidor existente

1. Faça e valide um backup externo do ambiente existente. Preserve .env, secrets/, data/, backups/ e deploy-state/.
2. Execute como root `python3 docker/server/apps/prepare_apps.py`. O script valida OPENGYM_ORIGIN, acrescenta os três overlays ao COMPOSE_FILE existente, prepara diretórios e gera segredos apenas se ausentes. Se detectar dados anteriores sem o registro inicial, recusa sobrescrever.
3. Valide `docker compose config --quiet`; baixe as imagens fixadas com `docker compose pull manyfold manyfold-redis mealie actual`.
4. Inicie somente os novos serviços com `docker compose up -d manyfold-redis manyfold mealie actual`. Espere healthchecks saudáveis. As portas ficam somente no loopback do Debian.
5. Antes de publicar, execute `python3 docker/server/apps/bootstrap_apps.py`: inicializa somente a instalação nova preparada e grava o marcador privado de conclusão. Não imprime senhas. Senhas geradas ficam em secrets/apps23-initial.json; nunca copie para o Git ou para um chamado público.
6. Execute `python3 docker/server/apps/publish_apps.py` para publicar as portas 3214, 9925 e 5006 no Tailscale Serve existente. O script exige inicialização concluída e confere preservação dos encaminhamentos anteriores, sem redefinição global nem ativação de Funnel.
7. Recrie somente monitor e backup para incorporar os volumes/flags dos overlays; recarregue Nginx após validar a configuração. Confirme atalhos, HTTPS e autenticação.
8. Confira um backup novo e sua restauração isolada com os três bancos. Copie o backup para outro equipamento e compare SHA-256.

Os aplicativos ficam no mesmo hostname HTTPS privado dos demais serviços, nas suas próprias portas. Use /manyfold, /mealie e /actual no portal para abrir o destino correto mesmo quando o portal for acessado por IP.

## Dados e contas

Manyfold: data/manyfold/config, library e plugins; Redis em data/manyfold-redis. Mealie: data/mealie. Actual: data/actual. Todos ficam no SSD local, sem compartilhar bancos com serviços anteriores. As contas iniciais estão documentadas em RELEASE-23.md; configure e-mail real/SMTP somente se desejar recuperação por e-mail. O registro de senhas é inicial, não um sincronizador de credenciais.

Não há importação automática de arquivos de impressão, receitas ou extratos. A biblioteca Manyfold inicial /models está vazia. O orçamento Actual é criado pelo titular, que escolhe moeda e conteúdo. Consumo de recursos depende de análises 3D, importações e tamanho das bibliotecas; os limites dos overlays são revisáveis.

## Atualização e retorno

Siga ATUALIZACAO.md, selecione versões estáveis oficiais e atualize tag e digest em conjunto. Faça backup antes de migrations. Voltar a imagem não desfaz alterações do banco.

Para desativar a instalação nova, pare somente manyfold, manyfold-redis, mealie e actual; preserve data/ e segredos; retire somente os três overlays do COMPOSE_FILE, os três encaminhamentos Serve e a integração opcional do portal/monitor. Não use down -v ou remoção global do projeto Aurora.
