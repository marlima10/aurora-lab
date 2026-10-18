# openGym

O repositório indicado, https://github.com/arvids-unavailable/openGym, aponta para o projeto mantido https://github.com/DuarteSantos8/openGym. Esta implantação usa as imagens oficiais **1.4.1** desse projeto, fixadas por digest.

## Serviços

`compose.opengym.yaml` separa `opengym-api` (Node, sem porta publicada) e `opengym-web` (Nginx e interface), numa rede própria. O HTTP 8081 fica no loopback; Tailscale Serve publica HTTPS privado 8081. Os atalhos Aurora levam a `/opengym`, que redireciona imediatamente ao endereço HTTPS configurado no servidor, inclusive quando o portal é aberto pelo IP LAN. O endereço antigo `/opengym.html` também redireciona, sem tela intermediária.

```sh
cd /srv/auroralab
sudo python3 docker/server/opengym/prepare.py
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml config --quiet
sudo docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml up -d --no-deps opengym-api opengym-web
sudo docker exec auroralab-tailscale-1 tailscale serve --bg --https=8081 http://127.0.0.1:8081
```

A preparação usa o domínio real da máquina autenticada no Tailscale; grava `RP_ID`, `ORIGIN` e nome do serviço em `secrets/opengym.env` (600), preservando esse arquivo quando já existe. Também informa `OPENGYM_ORIGIN` ao monitor pelo `.env`. Não envie esses arquivos nem dados pessoais ao GitHub.

## Primeiro acesso

Conecte o Tailscale no celular/computador, abra o endereço HTTPS e crie seu perfil com uma passkey. O primeiro perfil torna-se administrador. Não há senha padrão. Convidados estão desativados; registro inicial está disponível na rede privada. Depois de criar o proprietário, pode-se ativar `INVITE_ONLY=1` no arquivo local `secrets/opengym.env` e recriar somente `opengym-api`. Guarde uma segunda passkey para recuperação e preserve o domínio usado: mudar ORIGIN/RP_ID pode impedir o uso de passkeys existentes.

O idioma inicial é português brasileiro. O recurso opcional de IA está desativado por `COACH_DISABLED=1`; a imagem padrão não instala runtimes opcionais de IA. Nenhuma credencial de provedor foi configurada.

## Dados e recuperação

O estado fica em `data/opengym/`: perfis, passkeys públicas, sessão, treinos, auditoria e uploads. O aplicativo usa arquivos JSON, não o SQLite do Fitness. O backup inclui esses arquivos; cópias JSON são lidas e verificadas antes da compactação para evitar arquivos parciais. As gravações do projeto usam substituição atômica; o backup não representa uma transação única entre todos os perfis. Para cópia estritamente simultânea, pare a API antes de solicitar um backup e reinicie depois.

Para restaurar, pare somente opengym-api/web, guarde o estado atual, restaure `opengym/` e o arquivo local de ambiente com permissões restritas e reinicie. Preserve domínio e segredo de sessão. Não restaure esse diretório dentro do Fitness.

O Fitness Aurora e seus registros continuam independentes. Não foi feita migração nem sincronização automática de treinos.

Para desativar, pare os dois serviços, desligue somente a rota Serve 8081 e mantenha os dados. Não use `down -v` no ambiente completo.
