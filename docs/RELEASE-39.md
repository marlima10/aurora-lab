# AuroraLAB 39.0.0 — Remoção de OctoPrint e câmera
+
+Retirada completa das duas aplicações do ambiente ativo, conforme solicitação do proprietário, incluindo dados persistentes e os dados desses aplicativos dentro de backups antigos no servidor e em D:\AuroraServer.
+
+## Ambiente e portal
+
+- Removidos os serviços Compose, builds e arquivos exclusivos, perfil de câmera, overlay de dispositivo da impressora, portas e rotas HTTP/HTTPS específicas.
+- Removidos atalhos, painéis de impressão/câmera, reconexão do stream, sensores de hotend/mesa, métricas de armazenamento específicas e diagnóstico OctoPrint. Os demais painéis continuam recebendo dados; cache PWA e scripts alterados recebem nova versão.
+- Monitor deixa de consultar a API da impressora e de alertar indisponibilidade dos serviços retirados.
+- Retirados containers, imagens específicas, configuração de dispositivos, credenciais, gateway e publicação Tailscale da porta 5000. Nenhum comando físico de movimento ou aquecimento é enviado à impressora.
+- Migração 3 da autenticação remove somente grants OctoPrint, preservando usuários, chaves e demais acessos.
+- Javis deixa de oferecer a ferramenta de estado da impressora. O conector de biblioteca Manyfold continua; sua configuração privada não contém OctoPrint. Catálogo restrito: seis consultas de aplicativos e três leituras de notas.
+
+## Backups e preservação
+
+O proprietário autorizou explicitamente remover os dados também das cópias antigas. O utilitário operacional sanitize_print_backups.py retira diretórios e segredos específicos, limpa o registro privado de aplicativos e grants OctoPrint nos snapshots de autenticação, inclusive em arquivos aninhados. Regrava somente arquivos afetados, verifica cada membro mantido e atualiza sidecars SHA-256. Registros privados de higienização relacionam hashes anteriores/novos; hashes históricos dos relatórios anteriores ficam supersedidos pelo novo manifesto.
+
+Backups novos deixam de montar os dados removidos. O procedimento não reescreve tags, commits ou o histórico compartilhado do GitHub. As cópias de código antigas higienizadas são artefatos sanitizados e não devem ser tratadas como uma cópia exata da tag antiga; para reinstalar, use a release atual e seus dados preservados.
+
+Manyfold, Samba/arquivos compartilhados, openGym/Garmin, Mealie, Actual Budget, Cockpit, energia, autenticação e Gemini mantêm seus dados e identidades. A remoção de software não apaga firmware nem modifica o funcionamento da câmera USB como dispositivo do Debian.
+
+## Validação
+
+Testes de autenticação/migração, preparação, monitor/links, proteção HTTP, catálogo Javis, higienização de backups mistos/aninhados, SQLite e renderização sintética do dashboard. Resultados efetivamente executados, inventário final, quantidades higienizadas e restauração/cópia externa são registrados no relatório privado da implantação.
+