# Contexto do Aurora-LAB

## Ambientes e estado do repositório

| Item | Estado em 27/11/2026 |
| --- | --- |
| DEV | PC Windows, com workspace em `D:\AuroraServer\aurora-lab` |
| PROD | Aurora Server, instalação Linux/Debian |
| GitHub oficial | `marlima10/aurora-lab`, remoto local `origin` |
| Branch oficial de desenvolvimento | `rafael`, rastreando `origin/rafael`. Decisão confirmada pelo usuário em 27/11/2026 e verificada por `git branch --show-current` (AUR-002) |
| Branch `terminal` | Existe localmente, sem remoto, parada em `51ced03` (49.0.0). Não recebeu o trabalho da Release 50 |
| Versão do workspace | `50.0.0`, conforme [VERSION](../VERSION) |
| Release 50 | Publicada em 27/11/2026: merge na `main` (`ebeb06d`), tag e release `v50.0.0` no GitHub e implantação no Aurora Server concluídas (AUR-011) |

## Arquitetura

- Portal estático e PWA em `site/`, servidos por Nginx. O modo portátil usa `compose.yaml` com Nginx e PHP-FPM. O ambiente completo usa `compose.server.yaml` e arquivos Compose adicionais por módulo.
- A API Fitness legada em `backend/` usa PHP e SQLite, com Controllers, Requests, Services e Repositories. openGym é o aplicativo atual de treinos, com persistência própria e importação opcional Garmin.
- `docker/server/` contém serviços e configurações do servidor, incluindo autenticação central, monitoramento, backup e MagicMirror. Mealie, Manyfold e Actual Budget são módulos independentes. O MagicMirror tem módulo e tema próprios em `docker/server/mirror/MMM-Aurora`.

## Release 50

A agenda mensal e semanal do MagicMirror reúne compromissos, lembretes com data e horário, treinos openGym/Garmin e refeições Mealie. As integrações de treinos e refeições são somente leitura e usam as identidades atribuídas à sessão AuroraLAB. A migração acrescenta o campo `time` aos registros existentes. A documentação da release registra validações isoladas e a conferência visual feita em Chrome headless com dados sintéticos, sem aparelho físico. No DEV, o antivírus AVG intercepta HTTPS, e o `pip` dentro de containers falha na verificação TLS. Para testes, os wheels são baixados pelo Windows, conferidos com o SHA-256 do PyPI e instalados sem rede.

O [changelog](CHANGELOG.md) registra a 50.0.0 como publicada em 27/11/2026 e o [guia de arquitetura](ESTRUTURA.md) já descreve a agenda. A partir desta release, `compose.mirror.yaml` depende de `compose.mealie.yaml`. Para o estado de desenvolvimento e as validações pendentes, consulte [RELEASE-50.md](RELEASE-50.md) e o [README](../README.md).
