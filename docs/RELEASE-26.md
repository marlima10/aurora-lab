# AuroraLAB 26.0.0 — fila limitada para picos do login único

Esta correção complementa a [migração e o ícone de gestão publicados na release 25](RELEASE-25.md). A tag anterior foi preservada. Não há novas contas, permissões, chaves ou migrações de dados.

## Problema e correção

Ao abrir o OctoPrint, o navegador solicita muitos arquivos simultaneamente. O autenticador já limitava seus trabalhadores a 24 para respeitar o limite de processos do contêiner, mas encerrava imediatamente cada conexão que ultrapassasse esse teto. O Nginx recebia resets na consulta de autorização e devolvia erros 500 para parte das imagens/scripts, prejudicando o carregamento da interface.

`BoundedHTTPServer` continua limitado a 24 trabalhadores. Agora o atendimento espera uma vaga por até 15 segundos, com fila TCP de 128 conexões pendentes. O timeout de leitura existente permanece ativo e toda requisição continua passando pela mesma autorização; não foi adicionado cache de permissões nem liberado acesso anônimo.

A suíte HTTP passou a usar a mesma classe de servidor da produção. Um novo teste dispara 64 conexões simultâneas, confere que todas recebem resposta 200 e verifica que o pico de trabalhadores não ultrapassa 24.

## Validação e implantação

- 16 testes de autenticação aprovados, incluindo cookie, CSRF, permissões, rotação/revogação e o novo pico concorrente, sempre com dados sintéticos.
- Ensaio real pelo gateway: **64 requisições simultâneas autenticadas a um arquivo público do OctoPrint, 64 respostas 200, zero erros**, em 1,51 segundo no ambiente observado. Não foram enviados comandos à impressora.
- Bibliotecas JavaScript públicas do OctoPrint responderam 200, passaram na verificação de sintaxe e tiveram variantes normal/gzip equivalentes.
- Apenas a imagem `auth` foi reconstruída e seu contêiner recriado. Os demais aplicativos, as sessões persistidas e a chave administrativa existente foram preservados.
- O backup posterior à migração 25, já com o banco central, passou na restauração isolada de sete SQLite/44 JSON e sua cópia externa privada teve SHA-256 conferido. Esta correção altera código/limites de fila, sem transformar dados.

O navegador integrado do Codex apresentou `ERR_HTTP2_PING_FAILED` ao tentar concluir a interface OctoPrint. Isso limita a validação visual desse aplicativo; a API autenticada, as bibliotecas e o pico real foram verificados independentemente. Não foi alterada a VPN ou desabilitada a segurança HTTPS para contornar esse erro.

## Uso e recuperação

A entrada permanece no HTTPS privado do portal, com o e-mail e a chave já distribuídos. O atalho **👥 Gestão de usuários** segue visível apenas ao administrador e abre `/auth/admin`. SSH continua somente por chave. Impressora e câmera USB não estavam detectadas; suas configurações e dados foram preservados.

O retorno de código consiste em restaurar a imagem/configuração anterior do autenticador, sem remover volumes ou o banco central. O código oficial, os metadados de publicação e os backups privados foram preservados no diretório de trabalho do operador. O modo opcional de ativação em outras instalações permanece descrito em [LOGIN-UNICO.md](LOGIN-UNICO.md).
