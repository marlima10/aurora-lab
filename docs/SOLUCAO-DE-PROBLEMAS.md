# Solução de problemas

Use os comandos na pasta do projeto, sem compartilhar `.env`, tokens ou arquivos de `secrets/`. No servidor, confira a seleção `COMPOSE_FILE` definida conforme [AURORASERVER.md](AURORASERVER.md).

## Git: permissão negada ao clonar

O Git precisa criar o diretório do clone. Use uma pasta do seu usuário:

```sh
mkdir -p ~/srv/docker
cd ~/srv/docker
git clone https://github.com/marlima10/aurora-lab.git
```

Confira `pwd` e `ls -ld .` antes de alterar permissões. Não use permissões 777 ou mudanças recursivas em diretórios do sistema para resolver esse erro. Se o clone já existe, use o [fluxo de atualização](ATUALIZACAO.md).

## Docker: comando ou plugin ausente

Confira `docker --version` e `docker compose version`. No Windows, abra Docker Desktop, habilite contêineres Linux e reabra o terminal após ajustar a instalação/PATH. Instalar apenas o cliente não inicia o motor. Em Linux, instale o plugin Compose compatível com a instalação Docker; os guias usam `docker compose`, não o comando legado `docker-compose`.

## Docker: sem arquivo de configuração

`no configuration file provided` significa que o terminal está em outra pasta ou a seleção de arquivos está errada:

```sh
pwd
ls compose.yaml compose.server.yaml
```

Portátil: `docker compose -f compose.yaml ...`. Servidor: selecione `COMPOSE_FILE` e mantenha a combinação de overlays nos comandos. Não entre em `docs/` para executar os comandos de implantação.

## Docker: permission denied no socket

Confira `sudo docker info`. Se funcionar, o usuário não tem acesso a `/var/run/docker.sock`; use `sudo docker compose ...` ou configure o grupo Docker conforme a política da máquina. Não aplique `chmod 666` ao socket. O grupo Docker permite operações com privilégios equivalentes a root. [Orientação oficial](https://docs.docker.com/engine/install/linux-postinstall/).

## Docker: motor indisponível

No Debian com systemd:

```sh
sudo systemctl --no-pager --full status docker
sudo journalctl -u docker -n 60 --no-pager
sudo docker info
```

No Windows, confira se o Docker Desktop terminou de iniciar e use `docker context ls`. Uma conexão `npipe` inexistente indica que o motor/contexto esperado não está disponível, não comprova falta de privilégios.

## Contêiner reiniciando

```sh
sudo docker compose ps -a
sudo docker compose logs --tail=80 NOME-DO-SERVICO
```

Substitua o serviço. Não tente `exec` antes de ele permanecer ativo. Para Tailscale com `tailscale0 is busy`, siga [REDE-E-TAILSCALE.md](REDE-E-TAILSCALE.md): mantenha uma única instância e não interrompa a VPN do seu SSH.

## Contêiner inexistente ou órfão

`No such container` pode significar nome fixo incorreto, projeto diferente ou serviço não criado. Liste `sudo docker ps -a` e confira a combinação Compose. O projeto de servidor chama-se `auroralab`; o portátil usa outro nome por padrão.

Avisos de órfãos aparecem quando um serviço existente não está na configuração usada. Inclua seus overlays em COMPOSE_FILE. Não use `--remove-orphans` para eliminar o aviso se pretende manter Home Assistant, openGym ou outro serviço.

## Script exige root ou não existe

Para `Execute como root`, os instaladores exigem `sudo python3 ...`; isso não autoriza repetir uma instalação parcialmente aplicada. Para `No such file or directory`, confira o caminho e a branch:

```sh
git status --short --branch
git log -1 --oneline
ls docker/server/casaos/
```

`sync-shortcuts.py` está presente no código da versão 12; não é uma dependência instalada pelo pip. Atualize o clone correto conforme [ATUALIZACAO.md](ATUALIZACAO.md), sem sobrescrever alterações locais.

## CasaOS: verificação de contêiner falhou

`Um container existente reiniciou; revisar` ocorre ao comparar os contêineres ativos antes/depois. O código já pode ter instalado os serviços. A verificação também falha se um contêiner parou ou foi recriado; ela não identifica automaticamente a causa. Não repita o instalador: use os comandos de [CASAOS.md](CASAOS.md).

## Site não abre na LAN ou VPN

No servidor, substitua a porta pelo serviço:

```sh
curl -I --connect-timeout 5 http://127.0.0.1:81/
sudo ss -ltnp 'sport = :81'
ip -br -4 addr
```

Conexão recusada sugere ausência de escuta; timeout pode indicar rota ou filtro; uma resposta HTTP aponta para o serviço. Local funcionando e remoto falhando exige conferir bind, IP, firewall e políticas VPN. Para CasaOS, consulte também `sudo journalctl -u casaos-gateway -n 60 --no-pager`.

No dispositivo de origem, confirme Tailscale conectado e use `tailscale ping IP-TAILSCALE`. Esse ping testa conectividade Tailscale, não garante permissão TCP/HTTP. O HTTPS privado requer domínio e rota Serve corretos; passkeys openGym dependem da origem configurada.
