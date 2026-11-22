# AuroraLAB 43.0.0 — página administrativa de configuração do MagicMirror

Adiciona **Configurar tela** no rodapé da página inicial, visível ao administrador. Endereço: `/auth/mirror/configurar`. Usa o login único existente, sem nova senha/chave ou porta pública. A página é própria do AuroraLAB e controla o módulo personalizado MMM-Aurora, executado no MagicMirror oficial.

## Ajustes disponíveis

- Mostrar ou ocultar individualmente relógio, clima, lembretes, calendário, metas, histórico de exercícios e notícias; pelo menos um bloco precisa permanecer visível.
- Ordenar os blocos por botões de subir/descer, também por teclado e celular. A ordem no documento acompanha a ordem visual.
- Escurecimento da paisagem (15–85%), opacidade dos painéis (20–85%), desfoque (0–16 px) e escala dos textos (80–125%). A imagem de pôr do sol existente é preservada. Layouts personalizados deixam o modo de altura fixa para manter o conteúdo acessível com rolagem.
- Relógio de 12/24 horas; temperatura em Celsius/Fahrenheit, sem mudar a fonte nem gravar localização; quantidade de notícias (1–8); consulta de dados a cada 5–60 minutos. Os caches e limites existentes dos provedores continuam valendo.
- Mostrar ou ocultar atalhos de aplicativos, sempre combinando a preferência com as permissões reais do usuário. Ocultar um atalho não remove dados nem serviços. Javis continua reservado ao administrador.
- Restaurar os valores padrão no formulário e salvar explicitamente; a restauração de aparência não apaga treinos, metas, eventos ou lembretes.

## Persistência e autorização

Os ajustes de apresentação são globais para a tela do portal e ficam na nova tabela `display_settings` do banco `data/mirror/mirror.sqlite3`, já incluído no backup consistente. Valores padrão são retornados quando não há ajuste salvo, sem criar registros fictícios ou alterar entradas pessoais. Metas, calendário e lembretes continuam separados por usuário.

HTML, CSS, JavaScript e GET/POST `/auth/mirror/settings` exigem uma sessão administrativa válida. Escritas também exigem origem HTTPS exata e CSRF. A fachada injeta a condição administrativa obtida da sessão; o navegador não escolhe sua identidade ou privilégio. O conector interno revalida o sinal de administrador para as operações de configuração. O endpoint comum de lembretes não permite gravar configurações globais.

O esquema aceita apenas chaves conhecidas, booleanos, inteiros limitados, unidade C/F e uma permutação completa dos blocos. Não aceita JavaScript, comandos, caminhos, HTML, URLs ou edição arbitrária de arquivos. Respostas e página administrativas usam `no-store` e ficam fora do service worker. Nenhum segredo é enviado ao formulário ou adicionado ao GitHub.

A tela inicial recebe as preferências na leitura autenticada de seu estado. A gravação sinaliza outras abas da mesma origem por um evento local contendo apenas um carimbo de atualização; outros aparelhos recebem as opções na próxima consulta. Abrir/recarregar a página inicial aplica os ajustes imediatamente. Indicadores pessoais continuam dependentes dos grants nativos e da fonte de dados existente.

## Escolha de implementação

O MMM-Remote-Control foi consultado, mas não instalado: os blocos visuais do AuroraLAB estão dentro de um único módulo próprio. Esta página oferece controles individuais desse painel, sem adicionar controles do host ou instalação de módulos. Configurações técnicas do núcleo MagicMirror e implantação de novos módulos continuam versionadas no repositório. O painel do Monitor de processos permanece sem os atalhos removidos na release 42.

## Validação e implantação

Testes de persistência/reabertura do SQLite, preservação de lembretes pessoais, rejeição de campos desconhecidos e valores inválidos, impossibilidade de ocultar tudo, ordem única/completa e padrões independentes. Testes HTTP exercitam bloqueio de usuários comuns mesmo com cabeçalhos forjados, origem exata e CSRF administrativo. Teste do módulo verifica ordem, ocultação, aplicação numérica e preservação das permissões de atalhos. Conferência visual em notebook/celular e salvamento, recarga, efeito na tela e restauração de padrões usam dados descartáveis.

No Linux passaram 12 testes do painel e 30 de autenticação. O teste de rajada de 64 conexões falhou por timeout na execução Windows e passou no Linux de destino; o relatório não considera o teste Windows aprovado. Verificações de PWA, monitor e sintaxe JS também foram executadas. Corrigida a codificação de mensagens de erro do conector do painel.

Aplicar somente `magicmirror`, `mirror-api` e `auth` após o backup. Nenhuma preparação de novas credenciais é necessária. Preserve `.env`, segredos e dados. O cache da PWA avança para 43; o relatório privado registra a tag aplicada, saúde, autorização, backup/restauração e cópia externa. Reverter código/imagens não deve apagar o novo registro de aparência.
