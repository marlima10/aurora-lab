# AuroraLAB 31.0.0 — retirada de Home Assistant e HomeBoard

Home Assistant e HomeBoard foram desinstalados da instalação AuroraServer por solicitação do proprietário. O portal mantém Jarvis, openGym/Garmin, Actual Budget, Mealie, Manyfold, OctoPrint, Cockpit, Portainer e infraestrutura.

## Remoção realizada

- Quatro containers: Home Assistant atual, Home Assistant antigo do CasaOS, HomeBoard e proxy ha-sso.
- Sete imagens exclusivas, incluindo versões antigas e adaptadores SSO.
- Dados e configurações em data/homeassistant, data/homeboard, data/homeboard-photos e /DATA/AppData/homeassistant.
- Fonte temporária deploy-state/homeboard, preparadores e adaptadores exclusivos.
- Rede Docker ha-sso e publicações HTTPS Tailscale nas portas 8090 e 8123.
- Overlays compose.homeassistant.yaml e compose.homeboard.yaml; blocos SSO, portas e volumes de backup exclusivos.

## Portal e autenticação

Removidos atalhos, menus, linhas de status, nomes no painel de usuários, monitoramento e alertas. Endereços antigos retornam indisponibilidade definitiva (HTTP 410), sem redirecionar para um serviço inexistente. Cache PWA atualizado com URLs coerentes; endereços retirados não recebem fallback offline do portal.

Migration 2 do autenticador elimina somente os grants Home Assistant/HomeBoard. Usuários, hashes de chave, sessões e permissões dos aplicativos restantes continuam no esquema atual. Preparação de novas instalações usa o inventário dos seis aplicativos nativos restantes. Imagem do autenticador atualizada para 31.0.0; imagens Jarvis permanecem 30.0.0.

## Backups e histórico

Novos backups deixam de montar ou incluir os dados desses aplicativos. Os backups históricos compartilhados foram preservados, pois contêm também dados e credenciais dos aplicativos mantidos. Documentos e releases anteriores permanecem como histórico; guias dos aplicativos retirados estão marcados como históricos. A remoção de arquivos não é apagamento físico certificado do SSD.

## Validação

- 22 testes de autenticação em Linux, incluindo migração que preserva login e permissões restantes.
- 3 testes de preparação de SSO com dados fictícios.
- 3 testes de links, incluindo rejeição dos endereços retirados.
- 13 cenários DOM de administração de usuários, adaptados para os cinco apps comuns e Cockpit reservado ao administrador.
- 6 cenários PWA.
- Compose e Nginx validados, integridade do banco central aprovada e nenhum grant dos aplicativos retirados restante.
- Nenhum dado pessoal foi criado para testar. Remoção limitada a caminhos e imagens dos dois aplicativos, sem prune global de volumes ou imagens.
