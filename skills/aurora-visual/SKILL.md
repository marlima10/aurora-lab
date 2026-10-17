---
name: aurora-visual
description: Criar e alterar interfaces do Aurora Lab preservando seus componentes, temas, navegação responsiva e identidade visual. Usar em páginas e estilos deste projeto.
---

# Padrão visual do Aurora Lab

Leia ESTRUTURA.md na raiz para localizar os arquivos. Antes de alterar uma tela, examine a página e os estilos que ela carrega; estas orientações registram o visual existente, sem exigir um redesenho.

## Fontes do padrão

- `site/aurora.css`: tokens base, dashboard, painéis e componentes globais.
- `site/aurora-layout.css` e `.js`: navegação compacta, atalhos e temas. A barra lateral tem 68 px na versão compacta; telas estreitas usam navegação inferior.
- `site/fitness.css`: títulos, filtros, cards, formulários, gráficos e modais do Fitness.
- `site/fitness-planos.css` e `fitness-exercicios.css`: complementos das respectivas páginas.

## Identidade existente

O tema escuro usa fundo azul muito escuro, painéis azulados, bordas discretas e acentos ciano/azul. Consulte as variantes de tema do layout antes de aplicar cores novas.

| Token base | Valor atual | Uso |
| --- | --- | --- |
| --bg | #030914 | Fundo |
| --panel | #07182a | Superfícies |
| --panel2 | #0a2036 | Superfícies secundárias |
| --line | #173b5b | Separadores |
| --text | #eaf5ff | Texto principal |
| --muted | #86a5c3 | Texto secundário |
| --cyan | #16c8ff | Destaques |
| --blue | #1479ff | Ações |
| --green | #34e89e | Sucesso |
| --orange | #ff9d2e | Atenção |
| --red | #ff445d | Erro |

Use os tokens existentes quando adequados. Mantenha Inter com fallback system-ui/Segoe UI/Arial. Os painéis existentes têm cantos de aproximadamente 13 px, bordas de 1 px e espaçamentos compactos; reutilize as classes antes de criar variantes.

## Componentes e interação

- Reutilize `.panel`, `.panel-title`, `.fitness-btn`, `.fitness-section-title` e os componentes da página.
- Preserve os IDs e data-attributes usados pelo JavaScript. Textos da interface são em português brasileiro.
- Mostre carregamento, vazio, erro, indisponibilidade e sucesso conforme a operação; não declare que dados foram salvos antes da confirmação ou do fluxo offline existente.
- Use botões para ações e links para navegação, labels nos campos e nomes acessíveis nos controles de ícone. Estados precisam de texto ou ícone além da cor.
- Preserve foco visível, navegação por teclado, atributos dos modais e suporte a prefers-reduced-motion.
- Verifique telas estreitas, conteúdo longo, temas disponíveis, sobreposição da navegação inferior e ausência de rolagem horizontal. Os breakpoints existentes no CSS orientam os ajustes.

## Assets e cache

Preserve favicon, ícones e manifest quando a tarefa não pedir mudança de marca. Se arquivos públicos versionados forem alterados, mantenha coerência entre URLs das páginas e APP_SHELL em service-worker.js; atualize CACHE_NAME para que clientes recebam a nova versão.

Registre aqui decisões visuais novas somente quando adotadas no projeto.
