# Atualização, implantação e publicação

Este guia parte da raiz do clone. Ele atualiza uma instalação preservando seus dados. Para zerar os serviços e dados deliberadamente, use [REINSTALACAO.md](REINSTALACAO.md). A versão em código é a de `VERSION`; uma release publicada não instala nada no servidor automaticamente.

## 1. Registrar o estado

```sh
pwd
git status --short --branch
git log -1 --oneline
cat VERSION
sudo docker compose ps -a
sudo docker compose images
```

No servidor, esses comandos Compose pressupõem COMPOSE_FILE correto no `.env`, incluindo todos os overlays ativos e o override VPN host quando usado. Confira [AURORASERVER.md](AURORASERVER.md). Registre versões, imagens, IP, identidade VPN, caminhos dos dados e origem HTTPS openGym antes da mudança. Não compartilhe `.env` nem tokens nos relatórios.

Os caminhos desta instalação podem ser `E:\aurora-lab` no Windows e `~/srv/docker/aurora-lab` no Debian. São exemplos: verifique o diretório real em vez de copiar o caminho de outra implantação. Se o servidor recebeu arquivos por cópia e não tem `.git`, não execute comandos Git nele até confirmar a origem.

## 2. Backup antes de atualizar

Se o serviço backup já está operacional:

```sh
sudo docker compose restart backup
sudo docker compose logs --tail=100 backup
sudo cat data/backup-status/fitness-backup.json
```

Espere uma execução nova com `status: ok` e `verified: true`. Esse serviço exige um banco Fitness válido e inclui apenas os caminhos montados no Compose; uma instalação incompleta pode não produzir backup válido.

No diretório `backups/`, verifique o arquivo real e seu sidecar:

```sh
cd backups
sudo sha256sum -c NOME-REAL-DO-BACKUP.tar.gz.sha256
cd ..
```

Copie o arquivo e o SHA-256 para outro disco/máquina e valide a cópia. Os backups locais contêm credenciais, não são criptografados e não têm retenção automática. `deploy-state`, Tailscale instalado no Debian e novos aplicativos em `/DATA/AppData` exigem planejamento adicional; não aparecem automaticamente no escopo do backup. Se nenhum backup está funcionando, faça cópia consistente dos dados antes de alterar os serviços.

## 3. Preservar configurações e atualizar Git

Não substitua `.env`, `secrets/`, `data/`, `backups/` ou `deploy-state/` por exemplos. Preserve as configurações nativas CasaOS/Cockpit e o estado VPN. Fitness portátil e servidor usam caminhos diferentes; openGym é independente.

Com o clone limpo, na branch que pretende atualizar:

```sh
git fetch origin
git pull --ff-only
git log -1 --oneline
```

Se houver alterações locais ou divergência, resolva-as antes de prosseguir; não use `reset --hard` ou `clean` como atualização. Para produção, escolha um commit/release da `main` conforme o processo de revisão. Para desenvolver na branch `marcelo`:

```sh
git switch marcelo
git fetch origin
git merge origin/main
```

Revise conflitos e o diff. `rafael` continua sendo outra branch de desenvolvimento, não um requisito universal. Não altere automaticamente a branch do servidor sem saber qual commit será implantado.

## 4. Preparar e validar

Consulte os [padrões de desenvolvimento](../skills/aurora-development/SKILL.md) e [visuais](../skills/aurora-visual/SKILL.md). Preserve contratos e dados; alterações de arquitetura devem atualizar [ESTRUTURA.md](ESTRUTURA.md).

```sh
sudo docker compose config --quiet
sudo docker compose build php
sudo docker compose run --rm --no-deps --entrypoint php php tests/run.php
python3 -m unittest discover -s docker/server/garmin -p 'test_*.py' -v
```

Execute os testes pertinentes à mudança, não necessariamente todos os comandos em toda atualização. A suíte PHP usa bancos temporários e não executa o entrypoint de produção. Testes Garmin usam dados sintéticos/API simulada. Login Garmin real e impressão física exigem validação separada do titular/operador.

## 5. Aplicar somente os serviços afetados

Para backend PHP:

```sh
sudo docker compose up -d --no-deps php
sudo docker compose logs --tail=100 php
```

Faça build/recriação dos outros serviços alterados quando necessário. `restart` não incorpora mudanças de ambiente/volumes; recrie o serviço para isso. Avalie dependências antes de usar `--no-deps`. Não execute o instalador de CasaOS como rotina de atualização: ele recusa instalação existente. Scripts com operações no host precisam de revisão própria antes da reexecução.

Mantenha a mesma seleção de arquivos Compose para não criar órfãos nem reintroduzir o Tailscale concorrente. Não remova volumes ou dados como etapa de atualização. Não interrompa impressão, SSH/VPN ou backup sem planejar o efeito.

## 6. Conferir e registrar

Verifique status/logs, portal, redirects `/opengym` e `/garmin`, acesso HTTPS e autenticação de cada módulo. Confirme que os registros antigos permanecem acessíveis no armazenamento correto. Confira backup, OctoPrint/Samba, monitoramento e os dispositivos presentes. Atualize cache PWA quando arquivos públicos versionados mudarem.

Registre data, commit anterior/novo, serviços/imagens, backup e cópia externa, testes executados, limitações e eventual retorno. Não registre como validado algo apenas descrito por uma implantação anterior.

## 7. Retorno e restauração

Preserve código e imagens anteriores antes da atualização. Voltar a imagem não desfaz migrations nem gravações; avalie compatibilidade dos dados. O [guia OctoPrint](UPGRADE-PYTHON-OCTOPRINT.md) traz exemplo de imagem de retorno.

Para restaurar, pare os escritores afetados, preserve o estado atual e extraia o backup para uma área temporária privada. Recoloque arquivos comuns e snapshots `sqlite-snapshots/` nos caminhos esperados por cada volume. Não sobreponha banco ativo nem misture WAL/SHM antigos com snapshots. Confira integridade, permissões e credenciais antes de reiniciar. Para openGym/Garmin, restaure de forma coerente perfil e registro de importações, preservando domínio e segredo de sessão.

## 8. Commit, push, PR e release

Na branch de desenvolvimento escolhida:

```sh
git status --short
git diff
git diff --check
git add CAMINHOS-REVISADOS
git diff --cached
git diff --cached --check
git commit -m 'Descreva a alteração'
git push -u origin marcelo
```

Substitua os caminhos/mensagem e o nome da branch quando diferente. Revise também arquivos novos e remoções; nunca adicione bancos/credenciais. Abra ou atualize o PR da branch de trabalho para `main`, com alteração, validação e implantação descritas.

Crie a release oficial após o merge e a revisão aplicável ao projeto. Confira a última versão do repositório oficial, `VERSION`, [CHANGELOG.md](CHANGELOG.md) e o commit de destino. A convenção histórica deste projeto incrementa o primeiro componente (`v12.0.0` → `v13.0.0`); isso é uma convenção local, não uma regra geral de versionamento semântico. Mudança documental em andamento fica em **Não publicado**, sem inventar uma release já lançada.

Não reutilize tags nem substitua releases publicadas para representar conteúdo novo. A release precisa registrar testes realmente realizados e limitações; depois, a implantação no servidor segue este guia.


## Verificação de restauração (22.0.0)

O backup executa restore_check.py após gerar e verificar o arquivo. O resultado independente aparece em data/backup-status/restore-check.json e no portal. O teste extrai em diretório privado descartável, confere bytes/SQLite/JSON e nunca restaura sobre data/. Limite descompactado de 20 GiB, sem links ou caminhos inseguros. Garanta espaço para a cópia temporária.

Para um ensaio manual, use uma imagem Python de confiança já instalada com `--network none`, monte somente o arquivo de backup e o verificador em leitura e forneça o SHA-256 do comprovante. Não monte volumes de produção como destino, dispositivos USB ou Docker socket. O resultado não substitui o ensaio completo de todos os aplicativos e hardware; preserve o domínio de passkeys em uma recuperação definitiva. Consulte RELEASE-22.md e o relatório privado da implantação para o ensaio adicional da API.
