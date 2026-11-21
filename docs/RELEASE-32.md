# AuroraLAB 32.0.0 — limpeza final dos atalhos

Complementa a desinstalação de Home Assistant e HomeBoard entregue na release 31.0.0. A conferência visual encontrou dois atalhos legados do Home Assistant que ainda usavam openPort(8123); ambos foram removidos da página principal e o cache PWA foi renovado.

Os quatro containers, sete imagens exclusivas, dados, fotos/configurações HomeBoard, instalação antiga CasaOS do Home Assistant, rede SSO e rotas HTTPS 8090/8123 já foram excluídos na versão 31. Não existe reinstalação desses serviços na seleção Compose atual. Backups históricos compartilhados permanecem preservados.

Nesta revisão final, nenhum outro serviço ou banco foi modificado. Imagem do autenticador continua 31.0.0 e serviços Jarvis 30.0.0. Página real conferida com a sessão existente: portal e Jarvis acessíveis, Home Assistant e HomeBoard ausentes. Sintaxe JavaScript válida; nova versão de cache impede a permanência dos atalhos antigos. A versão 31 registrou 22 testes de autenticação Linux, três de preparação, três de links, 13 cenários DOM e seis cenários PWA aprovados.

Detalhes da desinstalação: docs/RELEASE-31.md. Não foram feitos testes de escrita nos dados pessoais.
