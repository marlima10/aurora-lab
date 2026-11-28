# Aurora LAB 5.3 — openGym

Versão técnica 53.0.0. O openGym permanece na base 1.4.5, commit upstream 2d70e026.

- **Garmin:** um estado de conexão por vez, nova tentativa quando a consulta falha e motivo visível quando a sincronização manual está indisponível.
- **Início:** painel Tempo e calorias com abas, período compartilhado e visibilidade por perfil. As posições salvas das métricas antigas são convertidas para o painel novo.
- **Estatísticas:** o resumo nativo precede os cartões Aurora. A Visão geral oferece o link para o código-fonte da versão.
- **Interface:** cartões com ícones nativos e explicações recolhíveis. A tela Início passa a duas colunas a partir de 900 px e o fundo tem contraste reforçado.

A implantação recria somente o frontend do openGym. API, SSO, importador Garmin e dados continuam usando os componentes e volumes existentes. Para voltar, restaure a configuração e a imagem anteriores de opengym-web. Consulte [o guia de atualização](ATUALIZACAO.md) e [os testes do módulo](../docker/server/opengym/README.md).

## Validação

82 testes Vitest e cinco testes Node de métricas aprovados. O build de demonstração foi conferido em pt-BR nos temas claro e escuro a 390, 820, 1024 e 1280 px. A imagem de produção foi construída pelo Compose em staging. O ensaio usou dados sintéticos.
