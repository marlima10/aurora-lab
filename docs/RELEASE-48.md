# AuroraLAB 48.0.0 — MagicMirror mais limpo e configurável

## Alterações solicitadas

- Data/hora, clima e lembretes sem borda, superfície de vidro ou sombra. Títulos redundantes ocultos visualmente e mantidos para leitores de tela. Relógio, data, temperatura e lembretes com fontes menores. Os demais painéis mantêm o tema aprovado.
- Cidade meteorológica selecionável e salva no servidor. Busca por nome/estado, escolha do resultado e confirmação em Salvar configurações. Sem GPS, consulta de permissões ou localização automática por aparelho. Previsão baseada no local salvo, com cache e atribuição Open-Meteo. Jacareí–SP é o local inicial solicitado para esta implantação; não vira localização padrão de outros servidores.
- Calendário mensal ou semanal com navegação do período correspondente. Configuração administrativa grava o padrão compartilhado; o seletor da tela permite trocar temporariamente durante o uso.
- Feriados nacionais, estaduais de SP e municipais de Jacareí gravados até 2030 em catálogo separado. Cadastro idempotente, sem duplicar eventos pessoais nem consumir sua cota. Datas móveis calculadas pelo calendário gregoriano. Os dois feriados de 03/04/2026 convivem no mesmo dia.
- Seleção regional Brasil/SP/Jacareí, Brasil/SP, Brasil ou feriados ocultos. Cidade do clima e calendário regional são escolhas independentes. Datas futuras seguem legislação permanente atual; pontos facultativos não são classificados como feriados. Fontes legais em [MAGICMIRROR.md](MAGICMIRROR.md).
- Jarvis ganha ícone SVG local de robô, texto explícito e nome acessível. A barra pode quebrar linhas no tablet, sem recortar os atalhos. O acesso administrativo e os grants existentes continuam obrigatórios.

## Implementação e revisão

settings.py valida os novos campos e migra somente registros antigos armazenados. Atualizações HTTP mantêm esquema completo e limites de tipos/intervalos. holiday_events guarda data, escopo e fonte; entries e goals pessoais são preservados. O catálogo pode ser disponibilizado sem internet depois da inicialização.

POST /auth/mirror/locations requer sessão administrativa, CSRF e origem exata. O conector consulta uma origem HTTPS fixa, com tamanho, quantidade, tempo e cache limitados. O navegador não escolhe URLs de destino. A previsão ignora coordenadas recebidas de clientes e utiliza a cidade persistida. Nenhuma chave externa é exigida.

Imagens alteradas: auroralab-magicmirror:48.0.0, auroralab-mirror-api:48.0.0 e auroralab-auth:48.0.0. A base MagicMirror oficial fixada no Dockerfile permanece a mesma. Recursos do openGym e sua atualização 1.4.5 não são substituídos.

## Verificações

19 testes Python do Mirror aprovados: preferências antigas, persistência após reabrir, calendário regional, reinicialização idempotente, anos/datas móveis, colisão de feriados, preservação/isolamento pessoal, limites, fontes de notícias e clima. 29 testes de autenticação aprovados em Linux, incluindo rajada de requisições e proteção administrativa/CSRF/origem da busca de cidades.

Verificações Node aprovadas para aplicação de preferências/permissões, reativação imediata do clima, intervalos mês/semana, fevereiro bissexto, virada de ano, ausência de GPS, ícone Jarvis e navegação/manifest da PWA.

Prévia privada com containers MagicMirror e API novos e dados fictícios: consulta de clima real de Jacareí, busca/seleção/salvamento da cidade pelo formulário, padrão semanal persistido após recarregar, feriado municipal e evento pessoal no mesmo dia e presença do Jarvis. Conferidos layouts de 390, 820 e 1024 px, sem rolagem horizontal. As bordas dos três blocos superiores foram verificadas como zero e o fundo transparente. Não se afirma ensaio em tablet físico ou login pessoal em navegador de teste.

## Publicação, implantação e retorno

PR da branch rafael para main, release v48.0.0 a partir do merge e implantação dos arquivos dessa tag. Antes da alteração: backup verificado, restauração isolada e cópia privada externa; snapshot coerente do SQLite Mirror para retorno. Depois: conferir serviços, acesso protegido, cidade/feriados/preferências existentes, novo backup restaurado e cópia externa.

Atualizar somente magicmirror, mirror-api e auth com o mesmo COMPOSE_FILE. Não alterar domínio, segredos, usuários ou dados dos demais aplicativos. Preferências anteriores ganham novas chaves; a escolha inicial de Jacareí e da região de feriados é feita somente no servidor autorizado. Remover a prévia e o túnel ao concluir.

Para retornar à versão anterior, parar o escritor e usar o snapshot Mirror anterior junto do código/imagens anteriores; o esquema estrito da versão antiga não aceita as novas preferências. Os comprovantes e hashes ficam no relatório privado da implantação.
