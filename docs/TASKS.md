# Controle de tarefas

Use os estados **Pendente**, **Em andamento**, **Bloqueada** e **Concluída**. Registre em [HANDOFF.md](HANDOFF.md) os arquivos sob responsabilidade de cada agente e o resultado ao concluir.

| ID | Descrição | Prioridade | Responsável | Dependências | Status |
| --- | --- | --- | --- | --- | --- |
| AUR-001 | Criar o contexto compartilhado e o fluxo de passagem de trabalho | Alta | OpenAI Codex | Nenhuma | Concluída |
| AUR-002 | Confirmar a branch de continuidade da Release 50 diante da divergência entre a branch informada e a ativa | Alta | Claude Code | Nenhuma | Concluída |
| AUR-003 | Concluir a conferência visual da agenda da Release 50 no DEV com dados sintéticos | Alta | Claude Code | AUR-002 (concluída) | Concluída |
| AUR-004 | Revisar a consistência dos cinco arquivos de memória compartilhada | Média | OpenAI Codex | AUR-002 (concluída) | Concluída |
| AUR-005 | Revisar a última tarefa executada pelo OpenAI Codex conforme critérios de aceitação registrados pelo Claude Code | Média | Google Antigravity | AUR-002 (concluída) e AUR-004 (concluída) | Concluída |
| AUR-006 | Corrigir o timeout indefinido em `image()` da fachada Mirror, que devolve 503 para toda imagem da galeria, e cobrir com teste | Alta | Claude Code | Nenhuma | Concluída |
| AUR-007 | Alinhar CHANGELOG.md, ESTRUTURA.md, MAGICMIRROR.md e RELEASE-50.md à versão 50.0.0 | Média | Claude Code | AUR-006 | Concluída |
| AUR-008 | Reexecutar os testes Python do Mirror com Pillow apesar da interceptação TLS do AVG no DEV | Alta | Claude Code | Nenhuma | Concluída |
| AUR-009 | Corrigir os itens do calendário cortados sem aviso no layout de altura fixa e tornar o segredo Mealie opcional na preparação | Alta | Claude Code | AUR-003 | Concluída |
| AUR-010 | Commit e push da 50.0.0 na branch `rafael` | Alta | Claude Code | Autorização do usuário (concedida em 27/11/2026) | Concluída |
| AUR-011 | Merge na `main`, release e implantação da 50.0.0 no Aurora Server | Alta | Claude Code | AUR-010 e autorização explícita do usuário (concedida em 27/11/2026) | Concluída |
| AUR-012 | Documentar a entrada pelo Claude no Aurora AI Manager | Alta | OpenAI Codex | Aurora AI Manager local | Concluída |

## AUR-004 — Requisitos e critérios de aceitação

**Escopo** — `AGENTS.md`, `CLAUDE.md`, `docs/CONTEXT.md`, `docs/HANDOFF.md` e `docs/TASKS.md`.

### Requisitos

1. Siga o fluxo de início do [AGENTS.md](../AGENTS.md). Antes de editar, registre neste arquivo e no [HANDOFF.md](HANDOFF.md) o status **Em andamento** e os arquivos previstos.
2. Compare os cinco arquivos entre si e com o estado real do Git: branch, versão, remoto, IDs, status e responsáveis das tarefas.
3. Verifique a coerência das referências:
   - quantidade de arquivos centrais citada, pois o AGENTS.md menciona quatro e a memória tem cinco;
   - links relativos válidos;
   - importação `@AGENTS.md` no CLAUDE.md;
   - menções a skills e documentos existentes.
4. Verifique se as regras de segurança e autorização estão descritas da mesma forma em todos os arquivos, sem contradições ou lacunas.
5. Corrija somente inconsistências de texto nesses cinco arquivos. Não altere código-fonte, skills, Compose, README, VERSION ou outros documentos. Proponha no HANDOFF.md as mudanças que forem necessárias fora do escopo.
6. Mantenha português brasileiro, UTF-8 e o formato atual das tabelas e seções. Preserve integralmente o histórico do HANDOFF.md e os registros de outros agentes.
7. Não troque de branch e não faça commit, push, pull, reset, checkout ou deploy sem autorização explícita.

### Critérios de aceitação

- Nenhuma contradição entre os cinco arquivos ou entre eles e `git status --short --branch --untracked-files=all`.
- Todos os links relativos dos cinco arquivos apontam para arquivos existentes.
- Os cinco arquivos continuam em UTF-8 e são os únicos alterados pela tarefa, o que deve ser confirmado pela comparação de `git status` antes e depois.
- O HANDOFF.md tem uma nova entrada da AUR-004 com as inconsistências encontradas, as correções feitas, os itens deixados fora do escopo, a validação, os riscos e os próximos passos.
- AUR-004 marcada como **Concluída** nesta tabela, ou **Bloqueada** com o motivo.

### Observações iniciais para a revisão

Registradas pelo Claude Code e ainda não verificadas pelo Codex:

- Os cinco arquivos de memória estão como não rastreados no Git.
- Em uma sessão do Claude Code em 27/11/2026, o conteúdo do AGENTS.md não apareceu carregado automaticamente pela importação do CLAUDE.md e precisou ser lido de forma explícita.
- O CHANGELOG.md e o ESTRUTURA.md ainda indicam 49.0.0, mas a correção deles está fora do escopo da AUR-004.
