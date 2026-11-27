# Fluxo de trabalho com Claude, Codex e Antigravity

Ative este fluxo quando a pessoa pedir para **usar o fluxo de trabalho**, **orquestrar a tarefa** ou **chamar Codex e Antigravity**. Para outras solicitações, siga a rotina habitual de [AGENTS.md](AGENTS.md).

1. No Claude Code, leia a memória indicada em AGENTS.md, confira a branch `rafael` e prepare um plano com objetivo, escopo e critérios de aceite. Informe premissas e preserve o trabalho local já existente.
2. Envie a solicitação original e o plano ao Aurora AI Manager local. O gerenciador repassa o plano ao Codex para elaborar uma proposta em texto. Em seguida, o Antigravity revisa a proposta, se a implementação tiver respondido.
3. Confira o estado devolvido e apresente o resumo, os pontos da revisão e o ID da execução. Se chegar a `aguardando_aprovacao`, deixe a decisão final para a pessoa no painel. Se falhar ou for reprovado, apresente a etapa e o motivo registrado.

## Chamada local no Windows

Use o comando abaixo em PowerShell no DEV, trocando os dois textos de exemplo. O Aurora AI Manager precisa estar em execução na versão que aceita planos do Claude. Limite cada campo a 12.000 caracteres e inclua apenas o contexto necessário, sem credenciais ou dados de produção.

```powershell
$manager = 'http://127.0.0.1:8765'
$settings = Invoke-RestMethod "$manager/api/settings" -TimeoutSec 5
if (-not $settings.accepts_claude_plan -or $settings.workspace -ne (Get-Location).Path) {
    throw 'Confira a versão do Aurora AI Manager e a raiz Git configurada.'
}
$body = @{
    mode = 'claude-plano-real'
    request = 'Substitua pela solicitação original.'
    plan = 'Substitua pelo plano elaborado no Claude.'
} | ConvertTo-Json
$run = Invoke-RestMethod "$manager/api/runs" -Method Post `
    -Headers @{ Origin = $manager } -ContentType 'application/json; charset=utf-8' `
    -Body $body -TimeoutSec 380
$run | ConvertTo-Json -Depth 8
```

Acompanhe a execução no **Histórico** do painel local, em `http://127.0.0.1:8765/`. A aprovação registra a decisão humana no gerenciador. Edições no repositório, commits, push e deploy seguem o procedimento e as autorizações de AGENTS.md.
