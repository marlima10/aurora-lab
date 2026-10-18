# Reinstalação do AuroraLAB com exclusão dos dados

Este procedimento é destrutivo: destina-se a quem decidiu remover os dados da instalação AuroraLAB/CasaOS e começar novamente. Para atualizar preservando dados, use [ATUALIZACAO.md](ATUALIZACAO.md). Ele mantém Debian, usuários Linux, SSH e Docker; não formata o servidor nem faz limpeza global de outros projetos Docker.

O exemplo abaixo corresponde ao clone `/home/marcelo/srv/docker/aurora-lab`. Verifique o caminho real antes de qualquer remoção. Não execute a partir de uma sessão SSH pelo IP Tailscale. Use IP LAN ou console; mantenha essa sessão e teste uma segunda conexão LAN antes de remover a VPN.

## 1. Inventário e cópia opcional antes de zerar

```sh
cd /home/marcelo/srv/docker/aurora-lab
pwd -P
git status --short --branch
sudo docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}'
sudo systemctl is-active tailscaled casaos-gateway cockpit.socket
```

A exclusão abaixo inclui configurações, contas internas dos aplicativos, passkeys openGym, treinos, impressões, identidades VPN e backups locais. Se quiser recuperar qualquer informação, guarde uma cópia consistente **fora dos caminhos apagados** antes de seguir. Não precisa apagar o clone nem a branch para iniciar um conjunto novo de dados.

## 2. Remover o Tailscale do Debian

O acesso já deve estar pela LAN/console. Para a instalação pelo pacote Debian:

```sh
sudo systemctl disable --now tailscaled
sudo apt remove tailscale
```

Isso interrompe/remove o daemon do host; a remoção dos dados de identidade é tratada no passo 5. Se o programa foi instalado manualmente e o apt não conhece o pacote, pare aqui e localize sua origem com `command -v tailscale` e `systemctl cat tailscaled`; não apague executáveis de caminhos presumidos.

No painel administrativo Tailscale, remova o dispositivo antigo se não pretende mais usar sua identidade. Isso é uma operação distinta da remoção do pacote e evita confundi-lo com o novo nó. O contêiner será autorizado como uma identidade nova; IP e domínio podem mudar. Não copie o estado antigo para a instalação nova.

## 3. Parar serviços nativos e remover os contêineres Aurora

Confira quais serviços são desta instalação. Os nomes abaixo são os geridos pelos preparadores do projeto; rclone pode ter outros consumidores, então verifique antes de desativá-lo.

```sh
for unit in casaos-gateway casaos-message-bus casaos-user-service \
  casaos casaos-local-storage casaos-app-management rclone; do
  if systemctl cat "$unit.service" >/dev/null 2>&1; then
    sudo systemctl disable --now "$unit.service"
  fi
done
sudo systemctl disable --now cockpit.socket
sudo systemctl stop cockpit.service
```

Se um serviço estiver ausente, verifique a mensagem e continue apenas após confirmar que não existe escritor ativo. O encerramento do Cockpit não deve encerrar o SSH LAN, que é um serviço separado.

Liste os contêineres dos dois modos Aurora. Os filtros usam os nomes de projeto conhecidos; se sua instalação usou `-p`/outro nome, substitua pelos nomes confirmados no inventário.

```sh
sudo docker ps -a --filter label=com.docker.compose.project=auroralab
sudo docker ps -a --filter label=com.docker.compose.project=aurora-lab
```

Para removê-los, execute este bloco em **Bash**:

```bash
for project in auroralab aurora-lab; do
  mapfile -t ids < <(sudo docker ps -aq --filter "label=com.docker.compose.project=$project")
  if ((${#ids[@]})); then
    sudo docker rm -f --volumes "${ids[@]}"
  fi
done
```

Isso não remove automaticamente contêineres de outros projetos instalados pela loja CasaOS. Identifique os que ainda usam `/DATA/AppData` e remova somente os aplicativos que também decidiu descartar. Não apague essa pasta enquanto houver contêineres gravando nela. Não use `docker system prune` ou remoção global de volumes para substituir esse inventário.

## 4. Verificar ausência de escritores

```sh
sudo docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}'
sudo systemctl is-active tailscaled casaos-gateway casaos rclone cockpit.socket
```

Confira os volumes de qualquer contêiner remanescente com `sudo docker inspect ID-REAL`. Se ele usar um caminho que será apagado, resolva isso antes. Serviços inativos podem retornar código diferente de zero; isso não é, por si só, falha de limpeza.

## 5. Apagar os dados e configurações selecionados

Este bloco **apaga** os dados locais do projeto, inclusive seus backups e segredos, a identidade Tailscale do host, configuração/estado CasaOS e os dados de aplicativos em `/DATA/AppData`. Não execute se esses caminhos ainda atendem outro serviço que pretende manter.

O comando verifica o caminho do clone e recusa links simbólicos nos alvos de topo. Os alvos são explícitos; não amplie a lista para `/home`, `/var/lib`, `/etc`, `/DATA` ou `/var/lib/docker` inteiros.

```bash
(
  set -eu
  repo_dir=$(realpath -e /home/marcelo/srv/docker/aurora-lab)
  [ "$repo_dir" = /home/marcelo/srv/docker/aurora-lab ] || exit 1
  [ -f "$repo_dir/compose.server.yaml" ] || exit 1
  for name in data secrets backups deploy-state; do
    target="$repo_dir/$name"
    [ "$(realpath -m -- "$target")" = "$target" ] || exit 1
    sudo rm -rf -- "$target"
  done
  [ ! -L "$repo_dir/.env" ] || exit 1
  sudo rm -f -- "$repo_dir/.env"
  for target in /etc/casaos /var/lib/casaos /DATA/AppData /var/lib/tailscale; do
    [ "$(realpath -m -- "$target")" = "$target" ] || exit 1
    sudo rm -rf -- "$target"
  done
)
```

Se alguma guarda falhar, pare e revise o alvo; não retire a guarda para forçar a exclusão. Os pacotes/dependências do Debian e as imagens Docker não foram removidos por esse reset.

Para permitir uma nova execução do instalador CasaOS, após parar seus serviços e descartar seus dados como acima, remova apenas a guarda binária da instalação antiga:

```sh
sudo rm -f -- /usr/bin/casaos
sudo systemctl daemon-reload
```

Os outros arquivos de programa/unidades oficiais podem permanecer desativados e serão reaplicados pelo instalador fixado. Isso é uma reinstalação de componentes com dados novos, não um desinstalador genérico CasaOS. Se desejar remoção completa de seus arquivos de programa em vez de reinstalação, revise o manifesto de instalação **antes** de apagar `/var/lib/casaos`; não execute listas de remoção arbitrárias.

## 6. Instalar novamente pelo roteiro

Continue em [AURORASERVER.md](AURORASERVER.md), a partir da preparação do projeto existente. O novo `.env` começa sem overrides antigos. Escolha o Tailscale **no contêiner**, autorize-o e descubra seu domínio novo antes de preparar Cockpit/openGym. Crie contas novas no CasaOS, Home Assistant, OctoPrint e openGym. A conta Samba permanece rafael conforme a configuração atual, com a nova senha definida na preparação.

O estado antigo apagado não será recuperado por Git, imagem Docker ou reinstalação do aplicativo. Não registre essa operação como atualização com preservação de dados.
