# Configurar o MagicMirror

Entre como administrador e abra **Configurar tela** no rodapé, ou `/auth/mirror/configurar`. As preferências ficam no banco do servidor e são compartilhadas com os aparelhos.

## Cidade do clima

1. Em **Relógio, clima e notícias**, digite a cidade e o estado, por exemplo `Jacareí, SP`.
2. Clique em **Buscar cidade** e selecione o resultado correto.
3. Clique em **Salvar configurações**.

A previsão usa o centro da cidade escolhida; não solicita GPS nem depende de permissão de localização. No AuroraServer, Jacareí–SP foi a cidade solicitada pelo proprietário. Outras instalações começam sem cidade e devem selecioná-la. Dados públicos de Open-Meteo / GeoNames; consultas e cache permanecem no conector separado. Desabilitar o bloco não apaga a cidade.

## Mês, semana e feriados

Escolha **Mês** ou **Semana** no calendário para mudar a visualização durante o uso. As setas avançam ou recuam o período selecionado. Para definir o padrão compartilhado que será usado ao abrir a página, salve **Visualização inicial** nas configurações.

**Agenda de feriados** permite Brasil + São Paulo + Jacareí, Brasil + São Paulo, somente nacionais, ou ocultar. A seleção regional é independente da cidade meteorológica: escolher outra cidade do clima não cadastra automaticamente seus feriados municipais.

O catálogo de 2026 a 2030 é gravado em holiday_events de forma idempotente. Os eventos pessoais e treinos aparecem juntos na agenda; os feriados possuem cor própria e link para sua fonte. Não é necessário importar arquivos em cada aparelho. O calendário não adiciona esses feriados aos treinos openGym nem aos seus lembretes.

Datas futuras são projeções das regras permanentes verificadas em novembro de 2026, e não decretos anuais ainda não publicados. Não são incluídos Carnaval, emendas ou outros pontos facultativos. Em 03/04/2026, aniversário da cidade e Sexta-feira Santa são dois feriados no mesmo dia, exibidos juntos.

Fontes: [feriados nacionais — Lei 662](https://www.planalto.gov.br/ccivil_03/leis/l0662.htm), [Nossa Senhora Aparecida — Lei 6.802](https://www.planalto.gov.br/ccivil_03/leis/l6802.htm), [Consciência Negra — Lei 14.759](https://www2.camara.leg.br/legin/fed/lei/2023/lei-14759-21-dezembro-2023-795091-publicacaooriginal-170522-pl.html), [data magna de SP — Lei 9.497](https://www.al.sp.gov.br/repositorio/legislacao/lei/1997/original-lei-9497-05.03.1997.html) e [Lei Orgânica de Jacareí, art. 222](https://www.jacarei.sp.leg.br/geral/lei-organica-do-municipio-de-jacarei-teste/).

## Jarvis no tablet

A barra de aplicativos ajusta suas linhas ao espaço disponível. O Jarvis tem ícone de robô e texto **JARVIS**. Em **Atalhos de aplicativos**, mantenha Jarvis selecionado. O serviço continua reservado ao administrador; uma conta sem essa permissão não passa a ter acesso por causa da mudança visual. Reabra a tela para carregar a versão nova.

## Validação e recuperação

Testes sintéticos Python em docker/server/mirror/test_*.py, autenticação em docker/server/auth/test_auth.py e verificações Node check_settings.mjs, check_calendar.mjs e check_pwa.mjs. Executar os scripts Node passando a raiz do repositório. As imagens alteradas são magicmirror, mirror-api e auth; openGym/Garmin e suas imagens não precisam ser reconstruídos.

O backup inclui mirror.sqlite3, preferências, catálogo e dados pessoais. Ao voltar para código anterior à release 48, restaurar coerentemente o snapshot anterior do Mirror: seu esquema antigo de configurações não reconhece as novas chaves. Não sobrepor um banco em uso. Seguir ATUALIZACAO.md.
