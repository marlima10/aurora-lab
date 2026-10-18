# CasaOS no AuroraServer

O gerenciamento CasaOS 0.4.15 foi instalado no Debian por autorização do responsável. Os aplicativos continuam em Docker. O fabricante recomenda Debian 12; o AuroraServer usa Debian 13 e esta implantação foi validada localmente.

Acesso local: `http://IP-DO-SERVIDOR:81`. Na VPN, use o domínio HTTPS do servidor com porta 81. Crie a conta administrativa no primeiro acesso. Ela é independente do usuário Linux.

## Instalação reproduzível

Em uma máquina amd64 nova, após backup, copie `docker/server/casaos/` para uma área privada e execute como root:

```sh
python3 docker/server/casaos/install.py --install
```

O instalador aceita somente instalação nova. As nove versões dos componentes oficiais e seus hashes estão em `packages.lock.json`; a origem e o método de conferência estão registrados por pacote. O rclone oficial 1.75.2 fica em `/usr/local/bin`, separado do pacote Debian; seu hash está em `rclone.lock.json`. Ele oferece o socket Unix exigido pelo CasaOS, ausente no rclone Debian 1.60.1.

O gateway usa 81. A API Docker 1.43 é conferida antes da instalação; não se reduz a versão mínima da API nem se reinicia Docker. Montagem USB automática e mergerfs permanecem desativados. Apenas o catálogo oficial CasaOS é pré-configurado.

O Samba do host fica mascarado: o compartilhamento existente continua no container na porta 445. Não ative compartilhamento Samba pelo CasaOS enquanto esse serviço estiver em uso.

## Persistência e backup

`/etc/casaos` e `/var/lib/casaos` entram no backup automático; SQLite é copiado pela API de backup antes da compactação. Credenciais e bancos ficam fora do Git. Novos aplicativos instalados pela loja gravam normalmente em `/DATA/AppData`: antes de usá-los, acrescente seus volumes e procedimentos de consistência ao backup. O backup atual não promete cobrir aplicativos que ainda não foram instalados.

Home Assistant e openGym são geridos pelo Compose AuroraLAB, com volumes próprios. Não recrie esses serviços pela loja, pois isso duplicaria instâncias e portas.

## Reversão

Pare e desabilite os sete serviços CasaOS/rclone; desligue a rota Tailscale da porta 81. Preserve `/etc/casaos`, `/var/lib/casaos` e `/DATA` para recuperação. O manifesto de arquivos CasaOS está em `/var/lib/casaos/aurora-install-manifest.json`; revise-o antes de remover arquivos. O instalador salva as configurações anteriores em `deploy-state/casaos-stage/host-before-*.tar.gz`. Mantenha Samba do host mascarado enquanto o container ocupa 445. Não use o desinstalador genérico para apagar Docker ou dados dos outros serviços.

Fontes: https://github.com/IceWhaleTech/CasaOS e https://rclone.org/rc/.

## Ícone AuroraLAB

O bloco `x-casaos` em `compose.server.yaml` identifica `web` como serviço principal e define HTTP, porta 80 e `/` como destino. O hostname é o mesmo usado para abrir CasaOS. O ícone representa o stack existente, sem duplicar containers. Pela VPN também é possível abrir o portal pelo endereço HTTPS principal do servidor. Não exclua o aplicativo AuroraLAB pelo CasaOS para remover só seu ícone: isso pode remover o stack completo.

Compatibilidade com CasaOS AppManagement 0.4.10-alpha2: o carregador dessa versão escolhe o Compose padrão do diretório e pode ignorar a lista de overlays do stack. Por isso `compose.yaml` também define os metadados, com porta 8088, atendida tanto no modo portátil como no AuroraServer. Essa mudança afeta o ícone; não aplique a configuração portátil ao ambiente completo pelo CasaOS. Gerencie atualizações do stack pelo fluxo AuroraLAB/Compose.
