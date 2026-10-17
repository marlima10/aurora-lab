# Atualização do AuroraLAB

Este documento orienta as atualizações do AuroraLAB, desde a preparação até a publicação da release oficial.

## 1. Origem do código

Usar o repositório oficial: https://github.com/marlima10/aurora-lab.

Desenvolver e publicar as alterações na branch `rafael`. A branch `main` recebe as alterações por Pull Request.

## 2. Diretórios de trabalho

- Windows: `D:\AuroraServer\aurora-lab`.
- Servidor Debian: `/srv/auroralab`.
- Relatório do sistema: `D:\AuroraServer\relatorio AuroraServer.MD`.
- Arquivos de acesso, cópias externas e demais materiais deste trabalho: `D:\AuroraServer`.

O diretório do servidor foi implantado por cópia de arquivos e não deve ser considerado um clone Git sem verificar antes.

## 3. Verificações antes da atualização

Conferir os serviços ativos, os logs relevantes, o espaço disponível e a versão instalada. Registrar o commit e as imagens atuais para permitir retorno.

No Debian:

```sh
cd /srv/auroralab
sudo docker compose -f compose.server.yaml ps
sudo docker compose -f compose.server.yaml images
sudo docker compose -f compose.server.yaml logs --tail=100
```

Confirmar que nenhuma impressão está em andamento antes de interromper ou recriar o OctoPrint. Evitar alterações concorrentes nos serviços durante a implantação.

## 4. Backup antes de atualizar

Gerar uma cópia consistente dos bancos SQLite, arquivos e configurações antes de alterar o ambiente. O serviço de backup executa ao iniciar e a cada 24 horas; para solicitar uma nova execução, reiniciar somente esse serviço:

```sh
cd /srv/auroralab
sudo docker compose -f compose.server.yaml restart backup
sudo docker compose -f compose.server.yaml logs --tail=100 backup
```

Aguardar a conclusão e conferir o status:

```sh
sudo cat data/backup-status/fitness-backup.json
```

Confirmar que o arquivo indicado corresponde à nova execução, apresenta `status: ok` e `verified: true`. Conferir também o arquivo de integridade correspondente:

```sh
cd /srv/auroralab/backups
sudo sha256sum -c NOME-DO-BACKUP.tar.gz.sha256
```

Substituir `NOME-DO-BACKUP` pelo nome real. Guardar uma cópia do arquivo e do SHA-256 fora do servidor, em `D:\AuroraServer\backups`. Verificar o hash dessa cópia. Os backups contêm credenciais e devem permanecer com acesso restrito.

## 5. Preservar dados e configurações locais

Preservar `.env`, `secrets/`, `data/` e `backups/` durante a atualização. Preservar também `deploy-state/`, que guarda registros e materiais de implantação.

Esses diretórios e arquivos não devem ser enviados ao GitHub nem incluídos no contexto de build. Não substituir configurações locais por exemplos sem revisar as diferenças.

O ambiente completo usa `data/fitness/fitness.sqlite3`; o pacote portátil usa `data/fitness.sqlite3`. Não confundir os caminhos durante cópias e restaurações.

## 6. Atualizar e preparar o código

No PowerShell do Windows:

```powershell
Set-Location 'D:\AuroraServer\aurora-lab'
git status
git switch rafael
git fetch origin
git pull --ff-only origin rafael
```

Resolver alterações locais antes de atualizar a branch. Revisar as diferenças em relação à `main` oficial:

```powershell
git diff origin/main...HEAD
git log --oneline origin/main..HEAD
```

Antes de modificar o projeto, seguir os padrões de `skills/aurora-development/SKILL.md` e, em mudanças visuais, `skills/aurora-visual/SKILL.md`. Preservar a identidade visual, os recursos existentes, o contrato `/fitness-api` e a compatibilidade dos dados. Documentar mudanças de arquitetura em `ESTRUTURA.md`.

Registrar o commit exato que será implantado:

```powershell
git rev-parse HEAD
```

Transferir somente código e configurações versionadas para o servidor. Conferir se o commit aprovado para implantação coincide com o pacote transferido. Não executar `git pull` em `/srv/auroralab` sem antes confirmar que existe um clone configurado nesse diretório.

## 7. Validar e aplicar as alterações

Para alterações no backend, executar a verificação de sintaxe PHP e a suíte de integração conforme `ESTRUTURA.md`. Usar bancos temporários, nunca os bancos pessoais.

No Debian, após transferir os arquivos e antes de recriar serviços:

```sh
cd /srv/auroralab
sudo docker compose -f compose.server.yaml config --quiet
```

Quando houver alterações no PHP ou no backend:

```sh
sudo docker compose -f compose.server.yaml build php
sudo docker compose -f compose.server.yaml run --rm --no-deps --entrypoint php php tests/run.php
```

Construir e recriar apenas os serviços afetados. Exemplo para PHP:

```sh
sudo docker compose -f compose.server.yaml up -d --no-deps php
```

Para alterações em outros serviços, substituir `php` pelo nome correspondente e executar o build quando necessário. Ao alterar dependências entre serviços, avaliar também os serviços relacionados antes de usar `--no-deps`.

Manter os arquivos adicionais de câmera ou impressora usados na instalação. Scripts shell devem manter finais de linha LF. Não usar remoção de volumes como procedimento de atualização.

## 8. Conferir o funcionamento

Após a implantação, verificar os serviços e seus logs:

```sh
cd /srv/auroralab
sudo docker compose -f compose.server.yaml ps
sudo docker compose -f compose.server.yaml logs --tail=100
```

Conferir:

- Portal, navegação e interface.
- Fitness: leitura, registros, planos e catálogo, preservando os dados existentes.
- OctoPrint: login, plugins, histórico e comunicação com a impressora quando conectada.
- Compartilhamento Samba.
- Monitoramento e descoberta de rede.
- Acesso Tailscale.
- Administração pelo Cockpit.
- Status e integridade dos backups.
- Câmera USB e impressora, quando conectadas e configuradas.

Não iniciar uma impressão real apenas para verificar uma atualização sem combinar essa operação. Atualizar o cache da interface quando necessário, conforme os padrões da PWA.

## 9. Retorno em caso de falha

Preservar o código, as imagens anteriores e um backup validado antes da atualização. Se a verificação falhar, interromper a implantação, consultar os logs e retornar os serviços afetados para a versão anterior.

A troca de imagem não restaura os dados. Antes de retornar código que depende de uma versão anterior do banco, verificar a compatibilidade das migrations e decidir se uma restauração é necessária.

Para restaurar dados, parar os serviços escritores, extrair o backup em uma pasta temporária, conferir os arquivos e restaurar os snapshots SQLite nos caminhos corretos. Não sobrepor bancos ativos nem restaurar journals antigos junto aos snapshots. Validar integridade e funcionamento após o retorno.

Consultar `UPGRADE-PYTHON-OCTOPRINT.md` para o procedimento específico de imagem do OctoPrint.

## 10. Registrar o resultado

Atualizar o relatório e a documentação com:

- Data da atualização.
- Commits anterior e novo.
- Serviços e imagens alterados.
- Backup utilizado e localização da cópia externa.
- Testes executados e seus resultados.
- Falhas, retorno realizado e pendências, quando houver.
- Links do Pull Request e da release, assim que disponíveis.

## 11. Commit, push e Pull Request no repositório oficial

Antes do commit, revisar os arquivos e garantir que não há dados pessoais, bancos, backups ou credenciais entre as alterações:

```powershell
Set-Location 'D:\AuroraServer\aurora-lab'
git status
git diff
git diff --check
```

Adicionar explicitamente os arquivos desejados, revisar o conteúdo preparado e criar o commit:

```powershell
git add CAMINHOS-DOS-ARQUIVOS
git diff --cached
git diff --cached --check
git commit -m 'Descreva a alteração realizada'
git push -u origin rafael
```

Substituir os exemplos pelos arquivos e pela mensagem reais.

Após o commit e o push, criar um Pull Request no repositório oficial `marlima10/aurora-lab`, com origem `rafael` e destino `main`. Se já existir um Pull Request aberto para essa atualização, atualizar o existente.

No GitHub, Pull Request é o nome equivalente a merge request. Informar o problema resolvido, as alterações, os testes e os cuidados de implantação. Acompanhar a revisão e corrigir os pontos necessários antes do merge.

## 12. Release a partir da main após o merge

Criar a release somente depois que o Pull Request estiver aprovado conforme as regras do projeto e mesclado na `main` oficial.

Antes de publicar:

1. Atualizar as referências do repositório oficial.
2. Confirmar que a `main` contém as alterações do Pull Request.
3. Conferir a versão em `VERSION`, no histórico e nas notas da release.
4. Criar a tag no commit da `main` que será lançado.
5. Publicar a release no repositório oficial, apontando para essa tag.
6. Informar alterações, validações, requisitos de atualização e limitações conhecidas.

A criação do Pull Request não equivale à aprovação ou ao merge. Não publicar a release enquanto as alterações estiverem apenas na branch `rafael`.

Depois da publicação, registrar o link e o commit lançado. Uma release no GitHub não atualiza automaticamente o servidor: a implantação deve seguir as etapas deste documento.

## 13. Incremento obrigatório de versão

Consultar a última release do repositório oficial `marlima10/aurora-lab` antes de definir a próxima versão. Não usar como referência uma release existente apenas no fork pessoal.

Cada nova release deve incrementar o primeiro número em uma unidade:

- `1.0` → `2.0` → `3.0`.
- Com três componentes: `v1.0.0` → `v2.0.0` → `v3.0.0`.

Manter o formato adotado pelo projeto. Atualizar `VERSION`, `CHANGELOG.md` e as referências de versão relevantes na branch `rafael` antes do merge, para que a `main` contenha os metadados corretos da release.

Se outra release oficial for publicada antes do merge, recalcular a próxima versão e ajustar o Pull Request. Não reutilizar tags já publicadas nem substituir uma release existente para representar uma versão nova.
