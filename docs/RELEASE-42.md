# AuroraLAB 42.0.0 — Monitor de processos sem atalhos de aplicativos

Remove a grade de ícones/atalhos de aplicativos do Monitor de processos. Os aplicativos continuam na página inicial do MagicMirror; nenhum serviço, volume, usuário ou dado é removido. O botão de instalação do app permanece disponível, em formato compacto e sem ícone. Indicadores, bateria/energia, gráficos, rede, armazenamento, backup e navegação continuam disponíveis.

O index estático portátil recebe a mesma limpeza. Cache da PWA avança para 42 para entregar o monitor atualizado aos aparelhos que já têm o aplicativo instalado. Não há alteração nas imagens Docker ou configuração dos serviços.

Validação: renderização do monitor com status sintético pelo teste existente, teste de navegação PWA e verificação de versões/segurança HTTP. Implantação somente dos arquivos públicos da tag; backup/restauração/cópia externa e hashes registrados no relatório privado.

A instalação atual do MagicMirror não inclui painel geral de configuração web. Metas, lembretes e calendário já possuem controles na página inicial; o restante está em docker/server/mirror/config.js e no módulo MMM-Aurora. O módulo comunitário MMM-Remote-Control pode oferecer controles web, mas não foi instalado por esta solicitação: https://github.com/Jopyth/MMM-Remote-Control .
