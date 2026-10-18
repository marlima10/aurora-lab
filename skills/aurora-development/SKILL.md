---
name: aurora-development
description: Desenvolver e refatorar o Aurora Lab em PHP, SQLite e JavaScript conforme sua arquitetura em camadas, contrato Fitness e validações. Usar em código e configuração deste projeto.
---

# Padrão de desenvolvimento do Aurora Lab

Leia docs/ESTRUTURA.md a partir da raiz do projeto para a árvore, contrato HTTP e comandos. Em trabalho de interface, leia também skills/aurora-visual/SKILL.md. Estas skills ficam versionadas no projeto; não pressupõem instalação global.

## Organização

- Namespace PHP `Aurora`, autoload PSR-4 pelo Composer, uma classe por arquivo e declare(strict_types=1).
- `backend/public/index.php` lê o ambiente HTTP. Application roteia ações, converte exceções e produz JsonResponse.
- Controllers validam a entrada por Requests e chamam Services. Não inclua SQL nem regras de sincronização nos controllers.
- Requests validam tipos, formatos e limites. Services aplicam regras dependentes do estado e coordenam transações. Repositories concentram SQL e mapeamento dos registros.
- Injete dependências pelo construtor e componha-as em bootstrap.php. Introduza interfaces ou DTOs quando resolverem um problema concreto.
- Use nomes descritivos em inglês para código e português brasileiro para mensagens. Prefira métodos focados, condições legíveis e comentários sobre decisões ou invariantes.

## Compatibilidade e persistência

- Preserve /fitness-api, actions, campos JSON camelCase, status HTTP, formato de conflitos e comportamento offline em refatorações. Alterações de contrato precisam atualizar clientes e testes em conjunto.
- Preserve revisões independentes de estado e planos, expectedRevision, exclusões lógicas e desempate do merge a favor do servidor. Faça verificação de revisão e gravação dentro da mesma transação.
- Use statements preparados para entradas. Services dependem de Repositories, não de PDO. Transaction centraliza BEGIN IMMEDIATE, COMMIT e ROLLBACK, inclusive em exceções.
- Migrations são aplicadas na inicialização e registradas em schema_migrations; acrescente novas versões para evoluções futuras. Não edite migrations já aplicadas para introduzir mudanças novas.
- Seeds de referência rodam em migration, sem recriar registros apagados em cada requisição.
- Não use o banco pessoal para testes. data/, bancos, backups, segredos e vendor não entram no Git. O contexto Docker também exclui dados pessoais.
- Validação de peso e data em save e compatibilidade legada de import/merge são decisões existentes; não altere silenciosamente essas regras durante reorganizações.

## Erros e testes

Lance ValidationException para entrada inválida e ConflictException para conflitos de estado. Application centraliza as respostas; registre falhas inesperadas no log sem enviar stack trace ou SQL ao cliente. Services e Repositories não devem usar echo, exit, headers ou superglobais HTTP.

Para mudanças no backend, rode verificação de sintaxe PHP e `php tests/run.php`, ou o comando equivalente no Docker descrito em docs/ESTRUTURA.md. Cubra resultados observáveis: revisões, rollback, merge, planos, catálogo e migração de bases existentes. Acrescente testes quando a mudança trouxer nova regra ou risco de regressão; evite testes que apenas espelhem o código.

Valide Compose ao alterar volumes, build ou FastCGI. Rebuild é necessário para alterações em backend/, pois o código está na imagem. Scripts shell devem manter LF; .gitattributes registra essa regra.

Atualize docs/ESTRUTURA.md quando responsabilidades, caminhos ou execução mudarem. Registro de padrões não autoriza publicar, fazer push ou alterar dados externos sem relação com a solicitação em andamento.
