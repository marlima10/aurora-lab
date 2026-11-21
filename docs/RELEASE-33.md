# AuroraLAB 33.0.0 — retirada do módulo experimental de IA e voz

Removidos o assistente local, os modelos baixados, transcrição, síntese de voz, conectores e worker de lembretes. Excluídos seus 12 containers, imagens próprias, revisões órfãs identificadas, redes, dados, credenciais, fontes, preparadores, arquivos temporários e atalho do portal. Nenhuma porta adicional é mantida para esse módulo.

O login central e os aplicativos restantes permanecem inalterados. O serviço de backup volta ao escopo dos aplicativos mantidos; a correção de preparação de WAL/SHM do Manyfold permanece porque é necessária independentemente do módulo retirado. A verificação de restauração deixa de exigir o banco excluído.

Backups compartilhados recentes e suas cópias locais foram higienizados: removidos os arquivos exclusivos do módulo, atualizadas as configurações afetadas, preservados os demais arquivos com conferência individual por SHA-256 e recalculados os sidecars dos arquivos modificados. O procedimento não apaga o histórico dos dados dos outros aplicativos.

Cache PWA renovado, seis cenários PWA aprovados, rotas nativas preservadas e renderização do gateway sem o serviço removido. Compose e Nginx validados. Histórico Git anterior, tags e registros de pull requests não foram reescritos; essa operação está em avaliação separada por afetar o repositório compartilhado.
