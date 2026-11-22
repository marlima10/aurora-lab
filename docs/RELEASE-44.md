# AuroraLAB 44.0.0 — avaliação isolada do Workout Cool

## Comportamento entregue

Workout Cool oficial, fixado por commit, em um projeto Docker de avaliação separado: aplicação, PostgreSQL, gateway de autenticação e backup. A interface nativa abre em português no endereço privado HTTPS com porta 8444. Uma faixa identifica o teste e oferece acesso ao relatório da cópia.

A cópia pontual do perfil openGym/Garmin inclui sessões, exercícios, séries e rotinas. Datas e horários originais são preservados; minutos passam para segundos, pesos e repetições inteiros mantêm seus valores. IDs determinísticos e checksum impedem duplicação e a substituição acidental de uma avaliação já modificada. O importador exige o banco de teste e as migrações concluídas; erros abortam a transação.

Rotinas viram programas não premium. A estrutura exigida pelo Workout Cool recebe uma semana/sessão por rotina; o nível obrigatório Iniciante é identificado como padrão técnico, não uma avaliação física. Não há recomendação de treino criada nesta importação.

Peso corporal e campos Garmin sem equivalente permanecem no snapshot JSON privado. Peso e detalhes originais aparecem no relatório da importação. Calorias não passam a ser uma estatística nativa do Workout Cool. A cópia não habilita sincronização contínua, não grava no Garmin e não devolve alterações ao openGym.

## Segurança e isolamento

- Banco e aplicação somente na rede interna do teste, sem portas de banco publicadas e sem saída de internet no aplicativo.
- HTTPS pelo Tailscale, gateway ligado apenas a 127.0.0.1:18444 e endereço privado :8444; sem Funnel.
- Gateway valida sessão administrativa central, origem e identidade. Cookies e Authorization originais não chegam ao Workout Cool.
- Identidade local de avaliação associada ao administrador AuroraLAB; login e cadastro nativos desabilitados. O teste não libera os dados pessoais a todos os usuários do portal.
- Cabeçalhos enviados pelo cliente são sobrescritos; segredo de delegação exclusivo em arquivo privado.
- Limites de memória/CPU, aplicação sem root, sistema de arquivos somente leitura e diretórios temporários limitados.
- Analytics, anúncios e cobrança desabilitados; serviços de pagamento recebem apenas marcadores inertes necessários à inicialização upstream, nunca credenciais reais. Nenhum recurso premium foi liberado artificialmente.
- Imagens base fixadas por digest e fonte oficial por commit; correção explícita da coluna onboardingPreferences ausente na migração 0_init upstream.

## Backup e validação

Compilação Next.js/TypeScript concluída. Conversão de séries conferida com dados sintéticos, incluindo recusa de arredondamento destrutivo. Importação real conferida por totais privados e segunda execução idempotente. Sessão delegada e páginas de perfil/relatório responderam; acesso anônimo e cabeçalhos falsos redirecionaram ao login, origem externa foi recusada.

Backup PostgreSQL em formato customizado, checksum SHA-256 e restauração completa em PostgreSQL temporário sem rede. Dados e comprovantes pessoais permanecem fora do Git. Backup diário próprio do teste; o backup geral do portal não deve ser confundido com uma cópia consistente desse PostgreSQL.

## Implantação e limites

O COMPOSE_FILE de produção não recebe este overlay. Os serviços e dados do openGym/Garmin permanecem ativos e independentes. Não há promoção ou substituição do aplicativo atual. O guia explica configuração, importação, recuperação e interrupção reversível do teste.

A conferência visual autenticada depende da sessão do titular no navegador; o resultado efetivamente observado deve constar no relatório privado da implantação. Campos que não possuem equivalente não são apresentados como dados nativos migrados.
