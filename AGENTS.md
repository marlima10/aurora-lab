# Regras compartilhadas do Aurora-LAB

A memória compartilhada tem cinco arquivos. Os quatro arquivos centrais da rotina são AGENTS.md, CONTEXT.md, HANDOFF.md e TASKS.md. [CLAUDE.md](CLAUDE.md) é o quinto arquivo e importa AGENTS.md para o Claude Code.

## Início e coordenação

1. Abra a raiz autorizada, `D:\AuroraServer\aurora-lab`, e leia este arquivo, [CONTEXT.md](docs/CONTEXT.md), [HANDOFF.md](docs/HANDOFF.md) e [TASKS.md](docs/TASKS.md) antes de iniciar cada tarefa. No Google Antigravity, solicite explicitamente a leitura desses quatro arquivos ao abrir uma sessão. No Claude Code, leia AGENTS.md explicitamente se o conteúdo da importação não estiver disponível.
2. Consulte `git status --short --branch --untracked-files=all` antes de trabalhar. Confirme a branch e identifique alterações existentes, inclusive arquivos não rastreados. Registre divergências entre o contexto e o Git.
3. Em trabalhos subsequentes, registre o responsável, o status e os arquivos previstos em TASKS.md e HANDOFF.md antes de editar. Combine a passagem de responsabilidade quando houver sobreposição. Trabalhe em arquivos distintos dos que outro agente estiver editando, inclusive nos registros compartilhados. Preserve integralmente as alterações de outros agentes.
4. Ao finalizar, consulte novamente `git status`, registre arquivos alterados, testes e resultados, riscos, pendências e próximos passos em HANDOFF.md e atualize TASKS.md. Atualize CONTEXT.md quando houver mudança relevante de arquitetura ou estado.

## Desenvolvimento e documentação

- Use a skill [aurora-development](skills/aurora-development/SKILL.md) para código e configuração e a skill [aurora-visual](skills/aurora-visual/SKILL.md) para interface. Preserve a identidade do Aurora-LAB e o tema próprio do MagicMirror.
- Escreva documentação em português brasileiro, salve Markdown em UTF-8 e use nomes descritivos em inglês no código.
- Valide as mudanças no DEV com os testes pertinentes descritos nas skills e na [estrutura do projeto](docs/ESTRUTURA.md). Use fixtures sintéticas ou descartáveis. Registre os testes omitidos e o motivo.

## Segurança e operações

- O PC Windows é DEV. O Aurora Server é PROD. Restrinja o trabalho ao diretório autorizado.
- Não acesse credenciais, chaves SSH, dados pessoais ou diretórios privados externos ao repositório. Não use dados reais de produção nos testes.
- Commit, push, reset, checkout, pull, deploy e alterações em produção exigem autorização explícita.
- Na configuração inicial deste contexto, crie somente os cinco arquivos solicitados que estiverem ausentes. Preserve os arquivos existentes. Não instale dependências, execute scripts de implantação ou publique alterações.
