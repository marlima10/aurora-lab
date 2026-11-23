# AuroraLAB 47.0.0 — evolução do openGym

## Resultado

Atualização de openGym 1.4.1 personalizado para 1.4.5, preservando o aplicativo de treinos e sua integração Garmin. O frontend e a API partem da mesma versão upstream; não há reinstalação dos aplicativos de avaliação encerrados.

## Interface

- Cartões Aurora com os cabeçalhos nativos, espaçamento consistente, fontes relativas e superfícies mais legíveis sobre a imagem de fundo existente. Preferência de maior contraste recebe superfícies opacas.
- Nova navegação fixa das Estatísticas: Visão geral, Corpo, Exercícios e Esforço quando há dados/módulo correspondente. Metas, tempo e calorias na Visão geral; progresso por exercício em Exercícios e no Início.
- Melhorias nativas de zoom/leitura e ajustes de tamanho do texto, mantendo modos Cartões/Lista/Compacto/Foco e temas já existentes. Esses modos não são apresentados como criação desta release.
- Agenda e pequenos mapas musculares da versão upstream preservados. Configurações → Módulos permite ocultar recursos nativos sem excluir dados.
- Organização pessoal do Início mantém os IDs e posições existentes. Resumo, retrospectiva, recuperação, deload e desafios entram como painéis adicionais quando aplicáveis. Componentes sem conteúdo não deixam espaços ou controles de movimento vazios.
- Arraste, movimento por teclado/botões, cancelamento e restauração da ordem padrão preservados. Fundo fornecido pelo titular mantido.

## Dados, login e Garmin

- Mesmos perfis, histórico, rotinas, pesagens, unidades, metas e preferência auroraHomePanels. Não há importação para outro aplicativo nem teste sobre banco pessoal.
- Conector AuroraLAB Garmin separado do suporte nativo a relógios; atualização horária dos últimos cinco treinos e proteção contra duplicatas preservadas. Nenhuma chamada adicional paga de IA é ativada.
- API 1.4.5 introduz confirmação em operações de conta. O adaptador reconhece a sessão central verificada somente no pareamento usado pelo Garmin. Senha, e-mail, passkeys e exclusão de conta mantêm a confirmação nativa.
- Atualizado o hash obrigatório do server.js para f9cbb9a5ca7aa48c1be26741baae41991186a2d5e1274ecab727e4c6e92e6ebe. Builds falham se a fonte não for a esperada.
- Gradientes de múltiplos gráficos continuam com IDs React distintos. Vite renova o cache da PWA pelo conteúdo; /garmin/ permanece fora do cache.

## Fontes e imagens

Frontend upstream 1.4.5: commit 2d70e026effc6602f513555166a97443520f0572. Web oficial fixada por digest e621677554302a0e1745e3b8c90acddc7d7149e118c4d683d51c13aa88f47d27; API por 397c83e9ac33a413bc8f21e66b2e55038100fc7f9da900d80be28b30fbb12ea8. Imagens locais auroralab-opengym-web:47.0.0 e auroralab-opengym-api-sso:47.0.0. Patch e componentes legíveis publicados neste repositório; licenças upstream preservadas.

## Revisão e validação

- Construção Vite e ambas as imagens concluídas.
- 171 testes Vitest passaram para Home, Stats, cartões Aurora, gráficos, módulos e service worker.
- Quatro testes SSO passaram, incluindo tentativa de usar o pareamento para alterar a conta e cabeçalhos forjados.
- 45 testes Garmin passaram com API simulada e dados descartáveis.
- Migração isolada de API 1.4.1 para 1.4.5 comprovou token legado Garmin, SSO, preservação dos campos pessoais sintéticos, novo pareamento e conflito de revisão HTTP 409.
- Escrita real do conector sobre API 1.4.5 sintética adicionou uma atividade e ignorou sua repetição, conservando as preferências.
- Navegador conferido em 390 e 820 px, temas claro/escuro, índice das Estatísticas, ausência de rolagem horizontal, organização persistida após recarregar e ocultação de módulos sem lacunas.

Não se afirma cobertura de toda a suíte upstream, ensaio em aparelhos físicos ou nova consulta autenticada aos serviços Garmin. Durante os testes, chamadas de rede de componentes nativos sem backend foram bloqueadas; os resultados funcionais passaram. Avisos de importação dinâmica do empacotador não impediram a compilação.

## Implantação e recuperação

Seguir docs/ATUALIZACAO.md: backup novo verificado, restauração isolada e cópia privada externa antes da troca. Guardar imagens anteriores e checkpoint coerente de openGym/Garmin; preservar ORIGIN/RP_ID e o segredo de sessão. Publicar PR da branch rafael para main, criar v47.0.0 a partir do merge e implantar o arquivo dessa tag. Recriar somente opengym-api e opengym-web com a seleção Compose de produção existente.

Após implantar, conferir saúde, acesso protegido, versão do bundle, campos/identidades existentes e autorização do agendador sem imprimir credenciais. Fazer novo backup e cópia privada externa. Os comprovantes operacionais ficam no relatório privado do servidor. A prévia usa somente dados fictícios e deve ser removida ao terminar, incluindo sua rota temporária.
