# Histórico de versões

## 27.0.0 — chave visível e exclusão de usuários

Janela automática com a chave de 151 caracteres e botão de cópia, visualização das chaves recém-geradas durante a mesma sessão da página e renovação mantendo permissões. Exclusão administrativa recuperável, encerramento das sessões, proteção do administrador inicial e migração preservando cadastros anteriores. [Descrição completa](RELEASE-27.md).

## 26.0.0 — fila limitada para picos do login único

O autenticador mantém 24 trabalhadores e coloca conexões excedentes em espera, evitando resets e erros 500 nos arquivos carregados em paralelo pelo OctoPrint. Fila TCP de 128 conexões e prazo limitado de espera; sem mudanças em chaves, permissões ou bancos. Teste sintético e ensaio real com 64 requisições simultâneas aprovados. [Descrição completa](RELEASE-26.md).

## 25.0.0 — migração do login único e gestão no Início

Ativação validada do SSO no AuroraServer com as identidades existentes dos oito aplicativos e atalho administrativo 👥 Gestão de usuários na página principal. Correções de WebSocket/formulários do Home Assistant, socket Unix do Cockpit, cache PWA por papel e monitoramento privado da API OctoPrint. Chave administrativa, dados e SSH somente por chave preservados. Backup com autenticação central e restauração isolada; configuração anterior preservada para retorno. [Descrição completa](RELEASE-25.md).

## 24.0.0 — revisão do portal e login único opcional

Cabeçalhos de segurança em todas as rotas do Nginx, limite de tentativas em POST (energia e API Fitness), aviso na chave de energia quando o portal está em HTTP, movimento reduzido em todas as páginas e textos do Fitness atualizados de Armbian para servidor. Autenticação central opcional por e-mail e chave de 151 caracteres, gerador administrativo, permissões e adaptadores para os oito aplicativos; preparação privada e backup do novo banco. Ativação separada, sem migração automática de produção. [Descrição completa](RELEASE-24.md) · [Revisão técnica](REVISAO-24.md).

## 23.0.0 — novos aplicativos independentes

Manyfold 0.153.0, Mealie 3.29.0 e Actual Budget 26.10.0: containers, redes e dados separados, HTTPS privado, contas protegidas, atalhos e backup/restore. [Descrição detalhada](RELEASE-23.md).

## 22.0.0 — metas, sincronização e operação

Metas semanais por perfil, resumo Garmin no Início, alertas persistentes do servidor, verificação de restauração após backup e histórico diário/mensal de energia. [Descrição completa](RELEASE-22.md).

## [18.0.0] - 2026-10-21

- Atualização opcional a cada hora do treino Garmin mais recente, com primeira consulta imediata após ativação.
- Pareamento nativo openGym por perfil e renovação da sessão; autorização privada sem segredo global do backend.
- Agenda e resultados persistentes, controles de pausa/execução imediata e retomada após reiniciar o container.
- Mesma proteção de revisão/duplicatas nas importações manuais e automáticas, inclusive recuperação após resposta de gravação perdida.
- Automação começa desativada e depende da ativação no painel autenticado. Treinos anteriores continuam na importação manual.
- 32 testes cobrem autenticação, isolamento, conflitos, renovação, reinício, falhas e preservação do histórico.


## [17.0.0] - 2026-10-21

- Integração com a API oficial Garmin Connect Personal, chave privada por perfil e validação de leitura antes de salvar.
- Troca da chave por token com POST sem corpo, aceitando token em texto/JSON; consultas de atividades continuam em JSON.
- Diagnóstico de código HTTP/etapa sem credenciais; redirects bloqueados e erros não expõem o corpo remoto.
- Migração preserva o conector comunitário anterior, os IDs já importados e o fluxo manual de prévia/importação.
- Testes cobrem autenticação, proteção da chave, negociação do token, isolamento e duplicatas.


## [16.0.0] - 2026-10-20

- Atalhos Cockpit, OctoPrint e Home Assistant redirecionam para o nome HTTPS privado configurado, inclusive quando o portal é aberto por IP/HTTP.
- Cache PWA atualizado; redirects e transmissão da câmera não entram no cache offline.
- Guia de ativação da câmera USB por identificador persistente e diagnóstico do stream.
- Testes HTTP dos redirects, recusa de origens inválidas e indisponibilidade de configuração.


## [15.0.0] - 2026-10-20

- HomeBoard em container independente, fonte upstream fixada, dados incluidos no backup e HTTPS privado.
- CasaOS removido preservando containers, volumes e /DATA; atalhos e monitoramento passam para HomeBoard.
- Politica de tampa/inatividade no systemd-logind e XFCE para manter o notebook ligado; bateria critica preservada.
- Scripts de preparacao/retorno e documentacao da mudanca.


## [14.0.0] - 2026-10-18

- Preparação valida os caminhos de configuração e segredos, substitui apenas diretórios vazios por arquivos e preserva conteúdo existente.
- Arquivo Samba vazio sem banco inicializado solicita senha em terminal interativo; erros de caminho são informados antes da solicitação.
- Testes de regressão cobrem instalação nova, reexecução, diretórios incorretos, preservação e entrada de senha.

## [13.0.0] - 2026-10-18

- Documentação centralizada em docs/, com README mantido na raiz e referências de backup atualizadas.
- Guias revisados contra a base funcional da versão 12, distinguindo modos portátil/servidor, módulos opcionais e contas independentes.
- Instalação passo a passo, seleção Compose persistente, diagnóstico, migração VPN e reinstalação destrutiva com escopo explícito.
- Limitações de preparadores com nome fixo do contêiner Tailscale e recuperação de instalação parcial do CasaOS documentadas.

## [12.0.0] - 2026-10-18

- Importação Garmin → openGym em serviço separado, integrado pelo proxy e origem privada HTTPS.
- Prévia de atividades, seleção e proteção persistente contra duplicatas.
- Resumos de data, duração e distância; sem inferir séries, cargas, músculos ou trajetos.
- Volume Garmin privado e incluído no escopo do backup do servidor.
- Validação sintética separada de login e importação reais do titular.

## [11.0.0] - 2026-10-18

- Cockpit autentica pelo PAM do Debian, sem exigir senha no SSH.
- Acesso HTTPS 9090 mantido em container proxy, com certificado do backend verificado.
- Configuração nativa e certificados locais incluídos no backup.

## [10.0.0] - 2026-10-18

- Ícones individuais dos serviços no CasaOS, sem criar containers duplicados.
- Interfaces abrem o serviço; componentes internos abrem o Portainer.
- Sincronizador preserva atalhos existentes, cria backup e permite reexecução.

## [9.0.0] - 2026-10-18

- Ícone AuroraLAB no CasaOS configurado com serviço web, portas 80/8088 e página inicial.
- Nome e ícone próprios do portal, sem criar outro stack ou reiniciar aplicativos.

## [8.0.0] - 2026-10-18

- Removida a tela intermediária openGym; o botão abre diretamente o serviço.
- Redirecionamento pelo servidor, incluindo compatibilidade com o endereço antigo.
- Cache PWA não armazena o redirecionamento externo.

## [7.0.0] - 2026-10-18

- Removidos os atalhos Fitness, planos e exercícios da navegação.
- openGym usa botão com o mesmo estilo dos demais atalhos principais.
- Preferências antigas de atalhos recebem opções válidas; registros preservados.

## [6.0.0] - 2026-10-17

- openGym 1.4.1, interface e API em containers próprios e rede dedicada.
- Passkeys pelo domínio HTTPS da VPN; atalhos em português, monitoramento e backup dos dados.
- Fitness original preservado, sem migração automática nem envio de dados a IA.

## [5.0.0] - 2026-10-17

- Home Assistant Container 2026.10.2, imagem fixada por digest, porta 8123.
- Dados persistentes e backup consistente do SQLite, atalhos e monitoramento.
- Proxy HTTPS privado confiável somente pelo loopback.

## [4.0.0] - 2026-10-17

- CasaOS 0.4.15 na porta 81, com componentes oficiais fixados por SHA-256.
- Atalhos no portal, monitoramento e backup do estado/configuração CasaOS.
- Gerenciamento autorizado no Debian; Docker e Samba existentes preservados.

## 3.0.0 — 2026-10-17

- Bateria clicável, autonomia, saúde e ciclos no dashboard.
- Potência CPU/GPU, origem das leituras e indisponibilidade explícita.
- Histórico e energia observada, sem duplicar RAPL ou inventar medições da tomada.
- Simulador mensal com tarifa configurável e comparação de suspensão.
- Pop-up acessível de perfis e brilho, autenticado em container separado.
- Configurações persistidas, limites validados e retorno em falha.
- Suspensão bloqueada até teste físico do RTC; rede, USB e drivers preservados.
- Cache da PWA atualizado e nove testes Linux de sensores e controles.

## 2.0.0 — 2026-10-17

### Processo de atualização

- Guia ATUALIZACAO.md com backup, validação, implantação, retorno, Pull Request para main e incremento de versão da release oficial.

### Ambiente completo AuroraServer

- Novo `compose.server.yaml` com Nginx, PHP-FPM, OctoPrint, Samba, monitoramento, backups, Tailscale e Cockpit em serviços separados.
- Câmera USB opcional em contêiner próprio e arquivo adicional para impressora USB.
- OctoPrint 1.11.8 com Python 3.12, supervisor s6-overlay 3.2.3.2 e 12 plugins fixados por commit e SHA-256.
- Correção de temporizador no Power Failure Recovery e identificação de versão do Cost Estimation. HomeAssistant permanece desativado até configurar MQTT e compatibilidade.
- Monitoramento do host, histórico e descoberta da rede, integrados ao dashboard existente.
- Backups locais a cada 24 horas, snapshots SQLite consistentes, verificação de integridade e SHA-256.
- Preparação de diretórios, exemplo de ambiente e instruções de instalação, migração e operação.

### Compatibilidade

- Preservados interface, identidade visual, PWA, funcionalidades Fitness, contrato `/fitness-api`, migrations e modelo SQLite.
- `compose.yaml` continua oferecendo o pacote portátil original de dois serviços.
- Dados pessoais, bancos, credenciais, identidade VPN e backups não integram a release.
- O ambiente completo é destinado a Linux amd64; câmera e impressora exigem dispositivos conectados. O pacote portátil mantém os requisitos anteriores.

### Validação e limites

- Implantação validada em Debian 13 amd64, incluindo API Fitness, OctoPrint e proxies HTTP.
- Suíte Fitness usa bancos temporários; restauração da instalação existente foi conferida separadamente.
- Backups automáticos permanecem no mesmo disco; cópia externa deve ser configurada pelo administrador.
- Não há autenticação no portal/Fitness. Use rede confiável ou VPN; não exponha essas portas diretamente à internet.

## 1.0.0

Distribuição portátil original do portal e Fitness, com Nginx, PHP-FPM e SQLite.


## 19.0.0 — Gráficos de progresso, tempo e calorias no openGym

- Gráfico de progresso existente também na página inicial; tempo de exercício e calorias Garmin nas duas páginas, com filtros de período, totais por dia, cobertura e tabela acessível.
- Frontend reconstruído de fonte upstream fixada, com patch reproduzível, tema e cache PWA preservados.
- Calorias válidas nos novos resumos Garmin; enriquecimento das calorias ausentes no histórico com controle de revisão, preservando edições e exclusões. Dados ausentes não são estimados nem tratados como zero.


## 20.0.0 — Fundo e organização do openGym

- Imagem fornecida pelo titular como fundo, com tratamento de contraste por tema e cache offline.
- Painéis independentes no Início, reorganizados por arraste, toque, teclado ou botões. Preferência sincronizada por perfil e restauração da ordem padrão.
- Controles de treino preservados; organização somente no modo dedicado. Nenhuma alteração nos treinos, calorias ou agenda Garmin.


## 21.0.0 — Sincronização dos últimos 5 treinos Garmin

- Janela automática ampliada para os 5 treinos mais recentes, mantendo consulta a cada hora, autorização existente, calorias e proteção contra duplicatas/exclusões.
- Validação integral do lote antes da gravação e envio das novas atividades em ordem cronológica.
