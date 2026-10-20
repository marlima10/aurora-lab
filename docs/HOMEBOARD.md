# HomeBoard no AuroraServer

O HomeBoard e um painel familiar independente (calendarios, fotos, tarefas e telas). Nao gerencia o Docker. Portainer e Cockpit continuam disponiveis para administracao; o portal AuroraLAB permanece na porta 80.

## Instalacao

O codigo oficial de https://github.com/MooreSi/HomeBoard foi fixado em `71da9914a809468b5183233ec0aedb0905550903`. URL e SHA-256 ficam em `docker/server/homeboard/source.lock.json`. Nenhum codigo upstream foi alterado ou incorporado ao Git deste projeto.

Na raiz do servidor:

```sh
sudo python3 docker/server/homeboard/prepare.py --build
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml -f compose.homeboard.yaml config --quiet
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml -f compose.homeboard.yaml up -d --no-deps homeboard
```

Inclua `compose.homeboard.yaml` na mesma selecao Compose persistida para operacoes futuras. Defina `HOMEBOARD_ORIGIN` no `.env`, usando seu dominio HTTPS Tailscale com porta 8090. Configure o encaminhamento no container Tailscale existente:

```sh
sudo docker exec auroralab-tailscale-1 tailscale serve --bg --https=8090 http://127.0.0.1:8090
```

A porta do container e publicada somente em 127.0.0.1:8090; acesso remoto pelo HTTPS privado do Tailscale. O portal encaminha `/homeboard` para essa origem. Nao existe publicacao por Funnel.

## Dados e uso

Dados em `data/homeboard/`; pasta opcional de fotos em `data/homeboard-photos/`, montada somente para leitura no aplicativo. Ambos entram no backup AuroraLAB. O container roda como UID 1000, sem capabilities, com filesystem somente leitura e reinicio automatico. Fontes e arquivo upstream para rebuild ficam em `deploy-state/homeboard/`, fora do Git; o lock permite baixar novamente o mesmo arquivo.

Configuracao inicial: nome AuroraLAB, tema Aurora e fuso America/Sao_Paulo. Clima, noticias e calendarios externos nao foram conectados. Abra `/settings` para personalizar e `/login` para definir sua senha administrativa (10 a 200 caracteres); ela nao e a senha Debian. Sem senha configurada, edicao fica disponivel a quem tem acesso a esse endereco privado. Nao compartilhe o endereco VPN com pessoas que nao devam configurar o painel. Integracoes externas e primeiro login administrativo sao etapas do titular.

Atualizacoes upstream devem ser revistas, ter o lock atualizado e a imagem reconstruida. Evite atualizar pelo painel se precisar manter o commit instalado sob controle desta release; o upstream possui seu proprio atualizador dentro do volume persistente.

## CasaOS e tampa

A remocao CasaOS usa `docker/server/casaos/remove.py`: primeiro sem argumentos para revisar; `--apply` para remover. Arquiva e retira somente servicos, arquivos e diretorios dedicados, comprovados pelo manifesto da instalacao anterior. Nao apaga `/DATA`, containers, volumes, Docker ou pacotes compartilhados. Material de retorno em `deploy-state/casaos-removed-*` e registro em `deploy-state/casaos-removed.json`. Nao use o desinstalador geral do CasaOS nesta instalacao.

A politica da tampa usa `sudo python3 docker/server/power/keep-awake.py --apply --user rafael`: ignora fechamento no systemd-logind e XFCE, tanto na tomada quanto na bateria, e desativa suspensao por inatividade. Nao muda a protecao de bateria critica. Copias anteriores e registro ficam em `deploy-state/lid-before-*` e `lid-policy.json`. Validar a tampa fisicamente exige fechar o notebook e conferir o acesso remoto; nao foi simulado por software.
