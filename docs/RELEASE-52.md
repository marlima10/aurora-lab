# Aurora LAB 52.0.0 — Agenda, portal e energia

Publicada e implantada em 27/11/2026. A versão reúne as melhorias planejadas para as etapas 51 e 52 (AUR-013 a AUR-017). [Release no GitHub](https://github.com/marlima10/aurora-lab/releases/tag/v52.0.0).

## O que mudou

- **MagicMirror:** legenda e filtro por fonte, criação de compromisso pela data escolhida, agenda agrupada por dia, confirmação de exclusão no diálogo e destaque de hoje.
- **Configuração e login:** sequência numerada na galeria, prévia de aparência, aviso de alterações não salvas e contador e controle de visibilidade da chave de acesso.
- **Monitor:** resumo da saúde, indicadores de carregamento e indisponibilidade, painéis recolhíveis em telas pequenas e botão de instalação do PWA conforme a disponibilidade do navegador.
- **Energia:** resumo no Monitor e página própria em `/energia.html`, com histórico, estimativas e configuração de economia.
- **Navegação:** ícones SVG com rótulos e cores de interface baseadas nos tokens dos cinco temas.

## Implantação e validação

O Portal foi atualizado no Nginx. MagicMirror e autenticação usam as imagens 52.0.0. A API do Mirror permanece na imagem 50.0.0. Os quatro serviços passaram nas verificações de saúde.

Passaram os testes JavaScript de calendário, fundos, configurações, portal e PWA, dez testes de rotas e links, 37 testes de autenticação e fachada e os cenários sintéticos de energia disponível e indisponível. O servidor entregou as versões atualizadas do Monitor e da página Energia.

O backup posterior passou na restauração isolada de 991 arquivos, 27 bancos SQLite e 88 documentos JSON. O SHA-256 da cópia externa foi conferido.

A conferência visual em Chrome headless (1280 × 900), com dados sintéticos, cobriu o calendário com filtro e legenda, a página Energia com leituras, a prévia na configuração do MagicMirror e o contador e controle de visibilidade da chave no login.

O usuário confirmou a instalação e a abertura do PWA pelo ícone da tela inicial em aparelhos físicos Android e iOS. Consulte o [guia de atualização](ATUALIZACAO.md) e o [registro de implantação](HANDOFF.md#27112026--implantação-consolidada-da-release-52).
