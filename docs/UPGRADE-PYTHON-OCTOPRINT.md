# OctoPrint — imagem Python, atualização e retorno

A imagem do ambiente completo usa Python 3.12 com OctoPrint 1.11.8, substituindo a base Python 3.10. Os 12 plugins permanecem nas versões de `plugins.lock.json`; as fontes são baixadas por commit e verificadas por SHA-256 no build.

A receita deriva do repositório oficial OctoPrint/octoprint-docker, commit `32fdd6eae2a9a2c1f97f26cf4c7d3802cb0559db`. Os arquivos necessários estão em `docker/server/octoprint/root`, com licença original em `UPSTREAM-LICENSE`.

O supervisor s6-overlay 3.2.3.2 tem downloads amd64 verificados por SHA-256, registrados em `s6-provenance.json`. Caminhos `/command`, permissões executáveis e finais de linha dos scripts são ajustados no build. A receita antiga s6 v2 não é compatível com o layout usrmerge desta base.

Power Failure Recovery usa `sysconfig` para localizar os módulos Python. HomeAssistant permanece desativado até configurar MQTT e compatibilidade. O monitor e os demais serviços usam suas próprias imagens; a atualização não modifica o Python do host.

Os comandos partem da raiz e usam COMPOSE_FILE com os arquivos ativos da instalação, inclusive compose.printer.yaml quando necessário. Veja [AURORASERVER.md](AURORASERVER.md).

## Atualização de uma instalação existente

Antes de substituir a imagem, confirme que não há impressão em andamento e faça um backup consistente de `data/octoprint/`, mantendo uma cópia externa. Registre também a imagem anterior para permitir retorno. Exemplo, se o serviço já tiver a imagem atual definida:

```sh
old_image=$(sudo docker compose images -q octoprint)
sudo docker tag "$old_image" auroralab-octoprint:rollback
sudo docker compose build octoprint
sudo docker compose up -d --no-deps octoprint
sudo docker compose logs --tail=100 octoprint
sudo docker compose exec octoprint python --version
```

Valide login, plugins, histórico e conexão com a impressora. Para retorno, crie um arquivo local `compose.rollback.yaml`:

```yaml
services:
  octoprint:
    image: auroralab-octoprint:rollback
```

Acrescente compose.rollback.yaml ao final da lista COMPOSE_FILE no `.env`, mantendo os demais arquivos ativos. Então:

```sh
sudo docker compose up -d --no-deps --no-build octoprint
```

Isso usa a imagem preservada sem substituir os dados atuais. A restauração dos dados é uma operação separada e deve ser realizada com os serviços parados quando necessária.

Ao concluir o retorno ou adotar uma imagem nova, revise a seleção local do overlay rollback para que futuras operações não usem a imagem antiga por engano.

## Registro histórico de validação

O guia anterior registrou que, em uma implantação Debian 13 amd64, o OctoPrint detectou Python 3.12.15. Foram validados imports e versões dos 12 plugins, inicialização com cópia isolada dos dados, API e proxy HTTP, integridade e hashes do banco de histórico e acesso pela rede local e VPN. Não foi iniciada impressão física. A tag Python 3.12 recebe atualizações de correção; builds futuros podem apresentar outra versão 3.12.x.

Esse registro histórico não comprova o estado de outro servidor nem valida um build novo. Registre as versões e resultados obtidos na sua máquina; não inicie impressão física como teste automático de instalação.
