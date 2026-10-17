# Histórico de versões

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
