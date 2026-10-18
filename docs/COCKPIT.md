# Cockpit com autenticação local Debian

Desde a versão 11, o login é feito pelo Cockpit/PAM do **Debian**, e um contêiner Nginx publica o proxy HTTPS na porta 9090. Não é mais o container cockpit/ws autenticando por SSH. Senhas no SSH não precisam ser habilitadas para esse login.

## Limitação da preparação atual

`docker/server/cockpit/prepare.py` consulta diretamente `auroralab-tailscale-1` para descobrir o domínio. Ele **não suporta automaticamente Tailscale no host ou outro nome de projeto**. Nesse cenário, não execute o script esperando fallback: ele já instala pacotes e altera o host antes dessa consulta. Mantenha a VPN existente e adapte/revise essa etapa antes de prosseguir. Veja [rede](REDE-E-TAILSCALE.md).

Para a instalação que usa o contêiner Tailscale autenticado e o nome de projeto padrão, execute na raiz:

```sh
sudo python3 docker/server/cockpit/prepare.py
sudo docker compose config --quiet
sudo docker compose up -d --no-deps cockpit
sudo docker compose logs --tail=60 cockpit
```

Use COMPOSE_FILE da instalação conforme [AURORASERVER.md](AURORASERVER.md). O script salva configurações anteriores em `deploy-state/cockpit-local-before-*.tar.gz`, instala cockpit-ws/openssl pelo Debian e verifica que a política obtida por `sshd -T` não mudou.

## Portas e TLS

- Backend nativo: HTTPS 9091 no loopback e gateway da bridge Docker, via override de cockpit.socket.
- Entrada Nginx: HTTPS 9090 em 127.0.0.1 e SERVER_IP.
- Certificado e chave: `secrets/cockpit-tls.crt`/`.key`, também copiados para `/etc/cockpit/ws-certs.d/`.

O proxy verifica o certificado do backend com nome `auroraserver` e encaminha WebSocket. Não publique 9091 na internet. Se SERVER_IP ou o gateway Docker mudar, revise binds e configuração; o preparador não renova automaticamente um par de certificados existente.

Na LAN, use `https://IP-LAN:9090`; o certificado é autoassinado e precisa de confiança apropriada. HTTP nessa porta redireciona para HTTPS. HTTPS privado no domínio Tailscale requer Serve configurado separadamente. Para um backend autoassinado, a opção `https+insecure://127.0.0.1:9090` de Serve ignora a validação apenas nesse trecho local; isso não é equivalente à verificação feita pelo Nginx até 9091. Avalie essa confiança antes de configurá-la. [Referência de Serve](https://tailscale.com/docs/reference/tailscale-cli/serve#ignore-invalid-and-self-signed-certificate-checks).

## Entrar e diagnosticar

Use seu usuário Debian e sua senha local. O usuário `rafael` de outra implantação não é uma conta automática na sua máquina. A administração depende das permissões reais desse usuário, como sudo/polkit. Não existe senha padrão do AuroraLAB.

```sh
sudo systemctl --no-pager --full status cockpit.socket
sudo journalctl -u cockpit.socket -u cockpit.service -n 80 --no-pager
sudo docker compose exec cockpit nginx -t
```

Preserve SSH por chave e sessões administrativas existentes durante mudanças. Caso o preparador falhe no meio, consulte logs e os arquivos gerados antes de repetir: ele altera pacotes, socket e configuração local.

## Backup e retorno

O backup monta `/etc/cockpit`, `/etc/systemd/system/cockpit.socket.d` e `secrets/`. Copie separadamente o registro de `deploy-state` quando necessário. A geração inicial do certificado usa validade de 825 dias; planeje renovação e sincronização do par nas duas localizações, com validação/reload dos componentes.

Para desativar, pare o proxy e planeje parar cockpit.socket/cockpit.service, mantendo arquivos para recuperação; remova só a rota Serve 9090. Voltar ao modelo antigo cockpit/ws é uma troca de arquitetura, e não resolve login por senha com SSH configurado somente por chave. Não reative senhas SSH como tentativa de reparo.

Referência de autenticação: [Cockpit](https://cockpit-project.org/guide/latest/authentication.html).
