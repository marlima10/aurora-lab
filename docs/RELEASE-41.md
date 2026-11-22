# AuroraLAB 41.0.0 — nova página inicial com MagicMirror

A página inicial passa a ser um painel pessoal baseado no MagicMirror² oficial 2.38.0. O dashboard anterior continua em **Monitor de processos**, com todos os indicadores de sistema e energia. Login único, identidades nativas e dados dos aplicativos são preservados.

## Página inicial

- Fundo de pôr do sol original, painéis translúcidos, organização baseada na referência fornecida, versão para notebook, tablet e celular, foco de teclado e diálogos acessíveis.
- Relógio e data em português, usando o horário do aparelho.
- Clima atual e previsão de três dias por Open-Meteo. O usuário autorizou substituir o Google Weather por uma fonte gratuita, pois a API de produção do Google exige faturamento habilitado. A localização depende da permissão do navegador; coordenadas são arredondadas a duas casas antes de consultar o provedor, usadas somente em memória no AuroraLAB e não gravadas no banco ou no backup. O provedor recebe a localização aproximada e pode registrar consultas conforme sua própria política. Fonte e atribuição visíveis.
- Notícias em português pelo RSS do Google Notícias, com título, link de origem, horário e estado de erro. Atualização do painel a cada cinco minutos; cache de notícias de dez minutos e clima de quinze minutos. O RSS público não tem garantia de disponibilidade nem contrato de API; erros são exibidos sem dados inventados.
- Lembretes com inclusão, conclusão e exclusão. Calendário mensal com eventos pessoais e treinos recentes do openGym. Entradas isoladas pelo e-mail da sessão central; não há integração automática com calendários Google/Outlook nesta versão.
- Metas semanais configuráveis de quantidade de treinos, minutos e calorias. Nenhuma meta fictícia é criada. Histórico de minutos dos últimos sete dias, soma das calorias conhecidas e indicação de registros sem calorias. A leitura usa o perfil openGym autorizado na sessão e não modifica os treinos nem o importador Garmin.
- Atalhos para openGym, Mealie, Javis, lembretes, calendário, Manyfold, Actual Budget e Monitor. Gestão de usuários e Javis aparecem apenas para o administrador; cada aplicativo respeita os grants existentes. Home Assistant permanece desinstalado.
- Botão **Instalar app** na página inicial e no monitor. Manifest e registro do service worker ajustados para carregamento tardio no MagicMirror. Android/desktop usam o convite do navegador; iOS recebe orientação para Compartilhar → Adicionar à Tela de Início. A confirmação de instalação continua pertencendo ao usuário.

## Containers e integração

Acrescente `compose.mirror.yaml` ao COMPOSE_FILE, mantendo todos os overlays existentes e `compose.auth.yaml` por último. Execute `docker/server/mirror/prepare.py` no servidor antes da primeira ativação. A preparação preserva a configuração privada existente e cria somente o segredo do novo conector. Nenhum segredo é distribuído no código público.

- **magicmirror**: fonte oficial fixada no commit `f138f5b690ceab6450f55c852ac81d268363f563`, Node fixado por digest, modo server-only, sem Electron. Módulo próprio `MMM-Aurora`; alteração guardada do import Socket.IO para funcionar em `/mirror/`, identidade/PWA no HTML e arquivos de inicialização gerados somente em `/tmp`. Sem porta pública, Docker socket ou volume de dados pessoais.
- **mirror-api**: serviço separado, sem porta publicada. Fornece dados do openGym, clima, notícias, calendário e lembretes. Comunicação interna autenticada; origens externas fixas, limites de resposta/tempo, armazenamento SQLite em `data/mirror`, incluído no backup com snapshot consistente.
- Fachada `/auth/mirror/*`: valida sessão e permissão de portal. Escritas e localização usam a verificação de origem e CSRF existente; e-mail/perfil nativo vêm da sessão, nunca de parâmetros do navegador. Respostas pessoais não são armazenadas em cache.
- `/` e `/index.html` redirecionam a `/mirror/`; `/monitor-processos` abre `/monitor-processos.html`. O proxy remove o prefixo somente ao encaminhar ao MagicMirror. Rotas de proxy genérico `/mirror/cors`, ambiente e recarga são bloqueadas. Permissão de geolocalização limitada à própria origem; câmera, microfone, USB e pagamentos continuam bloqueados no portal.
- O monitor portátil continua disponível mesmo sem o overlay MagicMirror. O healthcheck do web usa o manifest estático para não depender do novo serviço.

## Javis e consultas na internet

Novo container **javis-web**, separado do motor Gemini e dos conectores de dados. Duas ferramentas de leitura são acrescentadas à lista permitida:

1. `aurora_web_search`: pesquisa notícias no Google Notícias RSS. É uma busca de notícias, não uma API de busca geral do Google.
2. `aurora_web_read`: lê texto de uma página HTTPS pública indicada por URL, limitado a 512 KiB de resposta e 16 mil caracteres de texto retornado.

Não requer nova chave ou API paga. Mantém o projeto Gemini Free Tier atual; não ativa Google Search Grounding pago. URLs com credenciais, portas alternativas, redes privadas, loopback, link-local, Tailscale e metadados são recusadas. Todos os endereços DNS devem ser públicos; a conexão TLS usa o IP já validado e verifica o certificado do hostname, evitando uma segunda resolução vulnerável a DNS rebinding. Cada redirecionamento é revalidado. Sem cookies, envio de dados de aplicativos, scripts, shell, escrita ou acesso ao Docker. Limite de 120 consultas por hora. Consultas devem conter somente termos públicos; conteúdo externo é marcado como dado não confiável e os links retornam ao modelo para citação. O envio eventual de dados a Gemini mantém as regras e consentimentos da integração existente.

## Validação e operação

Testes de isolamento de usuários/identidades, CSRF e login, SQLite, notícias/links, dados ausentes, coordenadas inválidas, SSRF e redirecionamentos. Validação das imagens, Compose, configuração Nginx, PWA e interface em larguras de notebook e celular, com dados sintéticos. Verificações reais de RSS, Open-Meteo com coordenadas de exemplo e páginas públicas. O relatório privado registra resultados finais da implantação, containers, backup/restauração/cópia externa e revisão exata implantada.

Antes de aplicar, execute o procedimento de backup em ATUALIZACAO.md. Preserve `.env`, `secrets`, `data`, `backups` e `deploy-state`. Recrie somente serviços afetados; o novo estado é incluído pelo overlay no backup. Para retornar o visual, restaure a configuração anterior do proxy e o código da release anterior, preservando os novos dados de calendário para uso futuro.

## Fontes e imagem

- MagicMirror oficial: https://github.com/MagicMirrorOrg/MagicMirror — licença MIT.
- Open-Meteo: https://open-meteo.com/en/terms — uso pessoal não comercial, atribuição CC-BY 4.0.
- Google Weather: https://developers.google.com/maps/documentation/weather/usage-and-billing.
- RSS Google Notícias: https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419.
- Fundo `docker/server/mirror/MMM-Aurora/sunset.png`: imagem original gerada pela ferramenta de imagens integrada. Prompt: “Generate a clean photorealistic widescreen 16:9 landscape background asset for the AuroraLAB personal smart mirror dashboard. Sunset over a quiet lake, soft low golden sun near the center-right horizon, subtle distant trees and hills, deep warm charcoal and amber brown tones, tranquil realistic reflections, slightly soft focus. Darker lower and upper edges so white dashboard text will read clearly. Only the landscape photograph. Absolutely no text, logos, UI, panels, borders, icons, people or watermark. This is the background behind translucent glass cards, not a screenshot of an interface.”

## Compatibilidade adicional com aplicativos já instalados

A release 40 permanece imutável. A 41 mantém todas as funcionalidades acima e corrige a navegação quando um service worker anterior segue o redirecionamento da raiz e entrega o HTML mantendo o endereço antigo. O HTML do MagicMirror declara base explícita `/mirror/`, a raiz e o index deixam de ser interceptados pelo service worker e novas instalações iniciam diretamente em `/mirror/`. Isso preserva os recursos relativos também antes da troca do worker antigo. Cache avança para 41; login, treinos, calendário, lembretes e chaves não são migrados nem recriados. Teste de regressão executa o handler real do worker com navegações sintéticas e valida a base dos recursos e o início do manifest.
