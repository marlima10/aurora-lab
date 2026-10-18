# openGym

A versão 12 usa as imagens `opengym-api` e `opengym-web` 1.4.1 do projeto DuarteSantos8/openGym, fixadas por digest em `compose.opengym.yaml`. O overlay também define o importador Garmin separado. Não é o mesmo armazenamento do Fitness Aurora.

## Pré-requisitos

Use o [ambiente servidor](AURORASERVER.md), uma identidade Tailscale autenticada e seu domínio real `.ts.net`. HTTPS é necessário para as passkeys. Não altere ORIGIN/RP_ID depois de cadastrar usuários sem planejar recuperação das credenciais.

O preparador tem uma dependência concreta: quando `secrets/opengym.env` não existe, ele executa `docker exec auroralab-tailscale-1 ...`. Com Tailscale no Debian ou projeto Docker com outro nome, essa chamada falha; siga a alternativa abaixo antes de rodar o script.

### Tailscale no contêiner

Com o contêiner autenticado e estável:

```sh
sudo python3 docker/server/opengym/prepare.py
```

### Tailscale no host

Consulte seu domínio sem publicar tokens:

```sh
sudo tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))'
sudo install -d -m 700 secrets
sudo test -e secrets/opengym.env && echo 'Arquivo existente: preservar e revisar'
```

Se o arquivo não existir, crie-o com `sudo nano secrets/opengym.env`, substituindo o domínio de exemplo pelo resultado real:

```dotenv
RP_ID=SEU-SERVIDOR.SUA-REDE.ts.net
ORIGIN=https://SEU-SERVIDOR.SUA-REDE.ts.net:8081
RP_NAME=openGym AuroraLAB
```

Depois:

```sh
sudo chmod 600 secrets/opengym.env
sudo python3 docker/server/opengym/prepare.py
```

Quando esse arquivo já existe, o script valida sua origem HTTPS e usa seus valores, sem consultar o contêiner para criá-lo. Não sobrescreva a configuração de usuários existentes com um domínio novo. O preparador atualiza OPENGYM_ORIGIN no `.env` e cria `data/opengym/`.

## Subir os serviços

Antes de selecionar o overlay, prepare também o volume Garmin: ele faz parte do mesmo arquivo de configuração, mesmo se a importação não for usada inicialmente.

```sh
sudo install -d -m 700 -o 65534 -g 65534 data/garmin
```

Acrescente `compose.opengym.yaml` a COMPOSE_FILE no `.env`, mantendo o arquivo base e os outros overlays ativos. Confirme que OPENGYM_ORIGIN foi preenchido pelo preparador; o overlay exige essa variável e o arquivo `secrets/opengym.env`.

```sh
sudo docker compose config --quiet
sudo docker compose up -d --build opengym-api opengym-garmin opengym-web
sudo docker compose up -d --no-deps --force-recreate monitor
sudo docker compose ps
curl -I --connect-timeout 5 http://127.0.0.1:8081/
```

A API escuta internamente em 3000; a web publica apenas 127.0.0.1:8081. Atualizar `.env` não muda o ambiente de um monitor já criado; por isso ele precisa ser recriado para receber a origem. A rota `/opengym` e o endereço legado `/opengym.html` redirecionam para essa origem. `/garmin` redireciona para `/garmin/` na mesma origem HTTPS.

Configure Serve na instância VPN escolhida. No host:

```sh
sudo tailscale serve --bg --https=8081 http://127.0.0.1:8081
```

No contêiner, use `sudo docker compose exec tailscale tailscale serve --bg --https=8081 http://127.0.0.1:8081`. O overlay e o preparador não criam essa rota automaticamente.

## Primeiro acesso e dados

No dispositivo com Tailscale conectado, abra a origem HTTPS e crie seu perfil com passkey. FIRST_USER_ADMIN=1 torna o primeiro perfil administrador; ALLOW_GUEST=0 desativa convidados. Cadastre uma segunda passkey para recuperação. Se usar INVITE_ONLY=1 no ambiente local, recrie a API para aplicar e confirme a política na aplicação. Não há senha padrão. COACH_DISABLED=1 mantém o recurso de IA desativado.

`data/opengym/` guarda perfis, sessões, treinos, auditoria e uploads em arquivos próprios. Não há migração nem sincronização automática com Fitness ou outro servidor. O backup verifica os JSON individualmente, mas não cria uma transação global entre todos os arquivos. Para uma cópia simultânea, interrompa os escritores necessários durante o backup.

Ao restaurar, pare API, web e importador Garmin, preserve o estado atual, recoloque `opengym/` e o ambiente local correto e mantenha domínio/RP_ID. Depois reinicie os três serviços e verifique login. Consulte [GARMIN.md](GARMIN.md) antes de restaurar perfis com histórico de importação.

Para desativar, pare os serviços do overlay e remova apenas a rota Serve 8081 na instância usada; preserve dados. Não use `down -v` nem remova um overlay de COMPOSE_FILE enquanto pretende continuar gerenciando seus contêineres.
