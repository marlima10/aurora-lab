# AuroraLAB 37.0.0 — Javis em português brasileiro, microfone e voz

O Javis agora abre em português brasileiro e utiliza o mesmo idioma para o reconhecimento de fala e a leitura das respostas. A integração Gemini da release 35, o login central, os dados e os limites de consulta permanecem preservados.

## Revisão do suporte oficial

O README principal anuncia documentação em doze idiomas. A própria seção de idiomas do README brasileiro distingue isso da interface: o dashboard e as mensagens do servidor são originalmente inglês/vietnamita; as respostas podem ser produzidas em português. A imagem oficial 0.623.0 contém somente `en.json` e `vi.json`.

A solução usa os mecanismos nativos de internacionalização, acrescentando o dicionário `pt.json` e a entrada brasileira no registro de idiomas, sem traduzir a tela por substituições improvisadas no DOM. A versão e a imagem upstream permanecem fixadas. Novos textos de versões futuras exigem revisão do dicionário; mensagens internas do servidor sem chave de tradução podem continuar em inglês.

## Alterações

- Tradução dos textos do dashboard para português brasileiro, preservando as chaves, os campos variáveis e os nomes dos produtos. Tradução gerada com o Gemini já autorizado usando somente os textos públicos do projeto; cobertura e campos variáveis conferidos automaticamente.
- Registro nativo `pt`, locale `pt-BR`, fuso `America/Sao_Paulo`, moeda BRL, dias da semana e orientação de resposta em português brasileiro.
- Preferência de idioma aplicada ao servidor e migração única dos navegadores existentes. Mudanças posteriores feitas pelo usuário no seletor nativo continuam respeitadas.
- Reconhecimento de fala e ditado configurados como `pt-BR`, corrigindo as escolhas anteriores restritas a inglês/vietnamita.
- Vozes brasileiras Francisca e Antônio disponíveis no seletor nativo; Francisca como padrão compartilhado entre os dispositivos.
- Leitura pelo Edge TTS gratuito já utilizado pelo Javis. Sem conta, chave ou API paga adicional. O texto lido é transmitido ao serviço de voz Microsoft; o áudio do microfone é processado pelo reconhecimento oferecido pelo navegador/sistema.
- Correção do processamento upstream que interpretava respostas não inglesas como vietnamitas e trocava a voz selecionada. Texto e voz brasileiros agora são preservados inclusive quando o cliente envia `en=0`.
- Fallback do sintetizador do navegador seleciona voz do idioma configurado, em vez de prender a seleção ao vietnamita.
- Saída de rede limitada aos dois destinos TLS exatos: API Gemini e `speech.platform.bing.com`, necessário à voz gratuita. Sem proxy genérico, Docker socket, nova porta pública, modelo Live pago ou shell para a IA.
- Cache dos arquivos alterados renovado. Cada ponto modificado no dashboard original é conferido durante a construção da imagem; divergências upstream interrompem o build.

## Validação e limites

Validação executada: 28 testes Python do módulo aprovados; sintaxe dos cinco arquivos JavaScript alterados aprovada; reconhecimento pt-BR/en/vi, ditado pt-BR e migração única das preferências conferidos em testes JavaScript. O teste real de Edge TTS pelo túnel restrito gerou 27.936 bytes de áudio MP3, decodificado com duração de 4,656 segundos. A cobertura conferiu as 7.744 chaves e seus placeholders. Dados do backup e da aplicação oficial são registrados na implantação privada. A conferência visual no Chrome não foi concluída porque o controle de janela não conseguiu confirmar com segurança o endereço ativo; nenhuma alteração foi feita nessa sessão. O teste real de áudio sintetiza somente uma frase sintética, sem dados pessoais. O teste automático não substitui ouvir a saída no aparelho nem falar ao microfone do iPhone: permissões de microfone, suporte ao Web Speech e disponibilidade de vozes dependem do navegador/sistema. Use o endereço HTTPS privado com Tailscale conectado; se o navegador não oferecer reconhecimento de fala, o teclado continua disponível.

Fontes: [README brasileiro oficial](https://github.com/blogminhquy/javis-os/blob/main/docs/i18n/pt-BR/README.md#-idiomas), [guia de idiomas](https://github.com/blogminhquy/javis-os/blob/main/docs/dev/adding-a-language.md).

## Compatibilidade do backup e histórico da publicação

A release 36 registrou a adaptação de português. Antes de implantá-la, o backup anterior à atualização detectou que a telemetria nativa do Claude é JSON por linha com extensão .json. A versão 37 reúne a adaptação de idioma/voz e a correção do verificador de restauração; a tag 36 foi preservada e não foi reescrita.

O verificador aceita JSONL apenas no caminho nativo `javis-claude-auth/telemetry/1p_failed_events.<id>.<id>.json`, validando todas as linhas como objetos JSON e registrando a contagem `jsonl_verified`. JSON de configurações, perfis e demais logs continua estrito. Não ignora arquivos, não altera bancos e mantém os controles de SHA-256, tipos/caminhos, tamanho, SQLite e restauração descartável. Dois testes adicionais cobrem os registros válidos, uma linha corrompida, tipos inválidos e a recusa de JSONL fora do caminho específico.
