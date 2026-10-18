# Histórico de versões

## Não publicado

- Documentação centralizada em docs/, com README mantido na raiz e referências de backup atualizadas.
- Guias revisados contra o código da versão 12, distinguindo modos portátil/servidor, módulos opcionais e contas independentes.
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
