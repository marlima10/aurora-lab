# Rede, portas e Tailscale

Os comandos Linux partem da raiz do projeto. Este guia complementa [AURORASERVER.md](AURORASERVER.md); não configura automaticamente VPN, firewall ou rotas.

## Endereços

- `127.0.0.1`: acessível no próprio servidor.
- IP LAN, como `192.168.0.145`: acessível pela rede local quando serviço, rota e firewall permitirem.
- IP Tailscale `100.x`: exige conexão à tailnet e políticas que permitam o serviço.
- Domínio `maquina.rede.ts.net`: HTTPS depende de Serve configurado; o domínio privado não torna o serviço público.

O `SERVER_IP` do `.env` é o IP LAN. O dispositivo que abre o navegador também precisa estar conectado ao Tailscale para usar seus endereços privados. Acesso sem cliente VPN exige outra publicação/autenticação, fora da configuração padrão deste projeto.

## Uma instância Tailscale por interface

O contêiner usa `network_mode: host` e tenta criar `tailscale0`. Se o Debian já usa essa interface, o log mostra `TUN device tailscale0 is busy` e o contêiner reinicia. Confira:

```sh
systemctl is-active tailscaled
sudo tailscale status
sudo lsof -n /dev/net/tun
sudo docker compose -f compose.server.yaml logs --tail=60 tailscale
```

Não pare a VPN do host durante uma sessão SSH que depende dela. Migrar a identidade para o contêiner é uma operação separada, com acesso alternativo e backup; não copie estados entre máquinas.

### Manter a VPN do Debian

Pare apenas o contêiner conflitante:

```sh
sudo docker compose -f compose.server.yaml stop tailscale
mkdir -p deploy-state
cat > deploy-state/compose.host-tailscale.yaml <<'YAML'
services:
  tailscale:
    profiles: [vpn-container]
YAML
```

Esse override é uma configuração **local a criar**, não um arquivo distribuído no clone. Acrescente sua seleção ao `.env`, preservando as outras variáveis:

```dotenv
COMPOSE_FILE=compose.server.yaml:deploy-state/compose.host-tailscale.yaml
```

Acrescente os overlays dos módulos depois desse par, quando preparados. O perfil torna o contêiner opcional: não habilite `vpn-container` nem solicite `up tailscale` nesse modo. Um comando com `-f compose.server.yaml` sozinho ignora o override e pode iniciar o conflito novamente. Use a seleção persistida para as operações normais.

Essa receita resolve a seleção do serviço, mas não adapta os scripts: `docker/server/opengym/prepare.py` e `docker/server/cockpit/prepare.py` ainda procuram `auroralab-tailscale-1`. Veja as limitações nos guias dos módulos. O backup padrão inclui apenas o estado Tailscale do contêiner; planeje cópia separada do estado do host.

### Usar a VPN do contêiner

Somente quando não houver outra instância ocupando a interface:

```sh
sudo docker compose up -d tailscale
sudo docker compose exec tailscale tailscale up --hostname=auroraserver --accept-dns=false
sudo docker compose exec tailscale tailscale status
```

O arquivo principal define o nome do projeto `auroralab`. Usar outro `-p`/COMPOSE_PROJECT_NAME muda os nomes e pode quebrar scripts com nomes fixos. Prefira `compose exec tailscale` nas operações manuais.

## HTTPS privado com Serve

Primeiro confirme que o serviço local responde e consulte `tailscale serve status`. No modo contêiner, substitua `sudo tailscale` por `sudo docker compose exec tailscale tailscale` nos exemplos abaixo.

```sh
sudo tailscale serve --bg --https=443 http://127.0.0.1:8088
sudo tailscale serve --bg --https=81 http://127.0.0.1:81
sudo tailscale serve --bg --https=8123 http://127.0.0.1:8123
sudo tailscale serve --bg --https=8081 http://127.0.0.1:8081
sudo tailscale serve status
```

Configure apenas as portas dos serviços já funcionando e siga a autorização/ativação de HTTPS solicitada pelo Tailscale. Use o endereço informado por Serve, não um domínio de outra instalação. Para remover só uma rota, por exemplo openGym: `sudo tailscale serve --https=8081 off`. Evite `serve reset`, que apaga a configuração inteira. [Referência de Serve](https://tailscale.com/docs/reference/tailscale-cli/serve).

Cockpit usa backend local HTTPS autoassinado; encaminhar como HTTP não funciona. O guia [COCKPIT.md](COCKPIT.md) explica a terminação TLS. Não ative Funnel para publicar essas interfaces administrativas.

## Firewall

PHP 9000, API openGym 3000 e a porta interna do Garmin não precisam ser publicados no host. `8081` e `9110` são acessos locais nas configurações atuais. Os demais binds constam da tabela do [servidor](AURORASERVER.md).

Docker pode encaminhar portas publicadas antes das regras UFW. Portanto, `ufw deny` não é uma garantia de bloqueio para um contêiner publicado; analise também bind e encaminhamento Docker. CasaOS é um serviço do Debian, com regras do host. [Docker e UFW](https://docs.docker.com/engine/network/packet-filtering-firewalls/#docker-and-ufw).

Exemplo para permitir CasaOS somente de uma LAN `192.168.0.0/24`, após conferir que essa é sua rede:

```sh
sudo ufw allow from 192.168.0.0/24 to any port 81 proto tcp
sudo ufw status numbered
```

Não altere regras SSH sem preservar o acesso atual. Antes de abrir portas, teste localmente e confirme o erro; veja [diagnóstico](SOLUCAO-DE-PROBLEMAS.md).
