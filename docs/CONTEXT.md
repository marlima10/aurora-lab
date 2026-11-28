# Contexto do Aurora-LAB

## Ambientes e estado do repositório

| Item | Estado em 27/11/2026 |
| --- | --- |
| DEV | PC Windows, com workspace em `D:\AuroraServer\aurora-lab` |
| PROD | Aurora Server, instalação Linux/Debian |
| GitHub oficial | `marlima10/aurora-lab`, remoto local `origin` |
| Branch oficial de desenvolvimento | `rafael`, rastreando `origin/rafael`. Decisão confirmada pelo usuário em 27/11/2026 e verificada por `git branch --show-current` (AUR-002) |
| Branches oficiais | `main` e `rafael`. As branches `terminal` (local) e `marcelo` (remota) foram removidas após conferir a integração de seus históricos. |
| Versão do workspace | `5.4.0`, conforme [VERSION](../VERSION) |
| Release 50 | Publicada em 27/11/2026: merge na `main` (`ebeb06d`), tag e release `v50.0.0` no GitHub e implantação no Aurora Server concluídas (AUR-011) |
| Release 52 | AUR-013 a AUR-017 implantadas em produção em 27/11/2026. A [release 52.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v52.0.0) foi publicada a partir do merge ef97f83. |
| Numeração de versões | Decisão do usuário em 28/11/2026: títulos das releases em X.Y (53 → 5.3). A partir da 5.4, `VERSION` X.Y.Z e tags `aurora-X.Y.Z`; as tags `vNN.0.0`, inclusive `v53.0.0`, ficam como histórico. Implementação na AUR-025, ver [TASKS.md](TASKS.md#aur-025--nova-numeração-de-versões) |
| Release 53 | Publicada como [5.3](https://github.com/marlima10/aurora-lab/releases/tag/v53.0.0) e implantada no Aurora Server em 28/11/2026. Merge 34ffb1d. |

A [convenção de versões](VERSOES.md) passa a usar tags com prefixo aurora- a partir da 5.4.0.

## Arquitetura

- Portal estático e PWA em `site/`, servidos por Nginx. O modo portátil usa `compose.yaml` com Nginx e PHP-FPM. O ambiente completo usa `compose.server.yaml` e arquivos Compose adicionais por módulo.
- A API Fitness legada em `backend/` usa PHP e SQLite, com Controllers, Requests, Services e Repositories. openGym é o aplicativo atual de treinos, com persistência própria e importação opcional Garmin.
- `docker/server/` contém serviços e configurações do servidor, incluindo autenticação central, monitoramento, backup e MagicMirror. Mealie, Manyfold e Actual Budget são módulos independentes. O MagicMirror tem módulo e tema próprios em `docker/server/mirror/MMM-Aurora`.

## Release 50

A agenda mensal e semanal do MagicMirror reúne compromissos, lembretes com data e horário, treinos openGym/Garmin e refeições Mealie. As integrações de treinos e refeições são somente leitura e usam as identidades atribuídas à sessão AuroraLAB. A migração acrescenta o campo `time` aos registros existentes. A documentação da release registra validações isoladas e a conferência no Chrome headless com dados sintéticos. O usuário também confirmou os modos Mês e Semana e a lista de itens excedentes no tablet físico. No DEV, o antivírus AVG intercepta HTTPS, e o `pip` dentro de containers falha na verificação TLS. Para testes, os wheels são baixados pelo Windows, conferidos com o SHA-256 do PyPI e instalados sem rede.

O [changelog](CHANGELOG.md) registra a 50.0.0 como publicada em 27/11/2026 e o [guia de arquitetura](ESTRUTURA.md) já descreve a agenda. A partir desta release, `compose.mirror.yaml` depende de `compose.mealie.yaml`. Para o estado de desenvolvimento e as validações pendentes, consulte [RELEASE-50.md](RELEASE-50.md) e o [README](../README.md).
