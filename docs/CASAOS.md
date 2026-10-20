> A partir da v15 o CasaOS foi removido do AuroraServer por escolha do titular. Este guia e historico; nao reinstalar como parte de atualizacao. Novo painel: [HomeBoard](HOMEBOARD.md).

# CasaOS (historico) no AuroraServer

O instalador deste repositório prepara CasaOS 0.4.15 e componentes oficiais fixados em `docker/server/casaos/packages.lock.json`. CasaOS roda no **Debian via systemd**, enquanto seus aplicativos continuam em Docker. O procedimento é específico de amd64; não é uma instalação de CasaOS dentro de um contêiner.

Os comandos partem da raiz do clone. No exemplo desta instalação:

```sh
cd ~/srv/docker/aurora-lab
```

## Antes de instalar

Confira Docker, arquitetura, espaço em disco e os serviços existentes. Prepare backup externo. Resolva contêineres que reiniciam antes de iniciar o instalador, especialmente uma segunda instância Tailscale. Consulte [rede](REDE-E-TAILSCALE.md).

```sh
uname -m
sudo docker info
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}'
test -e /usr/bin/casaos && echo 'CasaOS já existe; revisar instalação em vez de reinstalar'
```

O script aceita apenas instalação nova e recusa `/usr/bin/casaos` existente. Ele foi escrito para a implantação Debian do projeto; não deve ser tratado como instalador genérico de qualquer distribuição.

## Instalação nova

Para manter materiais e backup de configuração dentro da área local do projeto:

```sh
sudo python3 docker/server/casaos/install.py \
  --stage "$PWD/deploy-state/casaos-stage" --install
```

O argumento `--stage` é opcional. Sem ele, o script usa **`/srv/auroralab/deploy-state/casaos-stage`**, mesmo que o clone esteja em outra pasta. Esse caminho é o local dos pacotes extraídos, do backup `host-before-*.tar.gz` e do registro `installed.json` quando a execução conclui essa etapa.

O instalador verifica nove pacotes por SHA-256, confere acesso à API Docker 1.43, salva configurações selecionadas do host, instala dependências e serviços, configura o gateway na porta **81** e inclui rclone 1.75.2 em `/usr/local/bin`. Os pacotes têm versões próprias; consulte os arquivos lock para detalhes. O Docker existente não é substituído pelo script.

O Samba do host fica mascarado/parado para preservar o Samba Docker na porta 445. O script configura USBAutoMount=false e não adiciona a loja BigBear. Não ative outro Samba nem crie cópias de Home Assistant/openGym pela loja CasaOS quando essas aplicações já forem geridas pelo AuroraLAB.

## Verificação e primeiro acesso

```sh
sudo systemctl is-active casaos-gateway casaos-message-bus casaos-user-service \
  casaos casaos-local-storage casaos-app-management rclone
curl -I --connect-timeout 5 http://127.0.0.1:81/
sudo ss -ltnp 'sport = :81'
```

Na rede local, abra `http://IP-LAN-DO-SERVIDOR:81/` e crie sua conta administrativa. Ela não é a conta Linux nem a conta Samba. HTTPS privado requer uma rota Serve configurada separadamente; veja [REDE-E-TAILSCALE.md](REDE-E-TAILSCALE.md).

Se o UFW está ativo, o gateway CasaOS é um serviço do host: ele depende das permissões de entrada do Debian. Confira escuta local e IP antes de liberar a rede desejada. Não abra a porta para a internet como tentativa de reparo.

## Instalação interrompida no final

O erro `Um container existente reiniciou; revisar` ocorre **depois** da cópia de arquivos, instalação e habilitação dos serviços. A comparação usa nome e StartedAt dos contêineres ativos antes/depois; também falha se algum parou ou foi substituído. Isso não prova que o CasaOS falhou nem qual processo causou a alteração.

Não execute novamente `--install` e não apague `/usr/bin/casaos` para contornar a guarda. Confira primeiro os serviços e o gateway:

```sh
sudo systemctl --no-pager --full status casaos-gateway casaos rclone
sudo journalctl -u casaos-gateway -u casaos -u rclone -n 80 --no-pager
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}'
```

O arquivo `installed.json` não é escrito se a comparação dos contêineres falhar; sua ausência, sozinha, não significa que os componentes não foram instalados. Recupere o componente com erro após analisar logs. Preserve `/etc/casaos`, `/var/lib/casaos`, `/DATA` e o backup da etapa inicial.

## Atalhos por serviço

O script `docker/server/casaos/sync-shortcuts.py` existe a partir da evolução dos ícones da versão 10 e está presente na versão 12. Ele não é instalado pelo CasaOS: precisa existir no clone correto.

Crie sua conta no CasaOS antes de sincronizar. Descubra os diretórios de usuário existentes:

```sh
sudo find /var/lib/casaos -mindepth 2 -maxdepth 2 -name app_order.json
```

Use o ID real; `1` abaixo é um exemplo:

```sh
sudo install -d -m 700 deploy-state
sudo python3 docker/server/casaos/sync-shortcuts.py --user-id 1
sudo python3 docker/server/casaos/sync-shortcuts.py --user-id 1 --apply
```

A primeira chamada mostra a proposta sem gravar preferências. `--apply` cria backup `deploy-state/casaos-shortcuts-before-*`, escreve `link.json`/`app_order.json` e registra o resultado em `deploy-state/casaos-shortcuts.json`. Atualize a página do navegador após aplicar.

O script inventaria todos os contêineres do Docker acessado, preserva aplicativos nativos reconhecidos e cria LinkApps para serviços existentes; não implanta contêineres. Os ícones SVG são obtidos do repositório oficial. O campo de estado do atalho não é monitoramento ao vivo.

Limites atuais: os destinos são construídos com SERVER_IP/LAN, o Cockpit pode receber um link HTTP que redireciona para HTTPS, e os componentes sem interface apontam para Portainer em HTTP 9000. Portainer não é instalado pelo AuroraLAB e esse endereço pode não existir na sua máquina. A sincronização não descobre domínios privados HTTPS automaticamente. Revise os destinos e não confunda uma porta interna PHP 9000 com uma interface web Portainer.

Remover um LinkApp remove apenas o atalho. Excluir o aplicativo/stack nativo AuroraLAB pelo CasaOS pode remover seus contêineres. A identificação `x-casaos` nos dois Compose principais existe para representar o stack, não autoriza reaplicar o modo portátil sobre o servidor.

## Backup e retorno

O backup do servidor monta `/etc/casaos` e `/var/lib/casaos`, incluindo preferências e atalhos. Novos aplicativos em `/DATA/AppData` não são cobertos automaticamente. A área `deploy-state` também precisa de cópia separada se for necessária à recuperação.

Para reverter atalhos, preserve os JSON atuais e restaure os correspondentes do backup. Para desativar CasaOS, planeje parar/desabilitar apenas seus serviços e a rota Serve 81; mantenha os dados e o Samba do host mascarado enquanto o contêiner usa 445. O manifesto de arquivos fica em `/var/lib/casaos/aurora-install-manifest.json`. Não use desinstalação genérica para remover Docker ou dados de outros serviços.

Fontes dos componentes: [CasaOS](https://github.com/IceWhaleTech/CasaOS) e [rclone](https://rclone.org/rc/). Os locks do projeto, e não a versão mais recente desses sites, definem os artefatos usados nesta instalação.
