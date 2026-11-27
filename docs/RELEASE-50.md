# AuroraLAB 50.0.0 — Agenda unificada

O calendário do MagicMirror reúne compromissos pessoais, lembretes com data e horário, treinos realizados e planejados do openGym/Garmin e refeições planejadas no Mealie. Os aplicativos continuam sendo os responsáveis pelos seus registros; a integração de treinos e refeições é somente de leitura.

## Uso

- Use **＋** no calendário para criar um compromisso, com data obrigatória e horário opcional.
- Lembretes aceitam data e horário opcionais. Sem data, permanecem na lista de lembretes; com data, aparecem também no calendário.
- Clique em um compromisso ou lembrete para editar ou excluir. O horário informado é o de Brasília.
- **Mês / Semana**, setas e **Hoje** permitem navegar. **Ver agenda do período** abre uma lista legível com data, horário, situação e origem.
- Cada dia mostra até três itens, com compromissos e lembretes antes de treinos e refeições, e um botão **＋N itens** para os demais. Em telas onde o dia tem menos espaço, o botão reúne também os itens que não couberem. Os feriados permanecem visíveis separadamente.
- Os treinos têm situação **Planejado** ou **Realizado**. Refeições mostram o tipo, como almoço ou jantar. Clique para abrir o aplicativo responsável e editar nele.

## Integração e preservação

- Mantém eventos, lembretes concluídos, metas, feriados até 2030, cidade fixa e galeria de fundos. A migração acrescenta o campo `time` à tabela existente, sem recriar registros.
- A agenda usa exclusivamente as identidades openGym/Mealie atribuídas à sessão AuroraLAB. Identidades enviadas pelo navegador não substituem essas permissões.
- Dados pessoais do calendário pertencem ao usuário; refeições seguem as permissões da residência no Mealie. Uma fonte indisponível é identificada e não apaga os compromissos das demais.
- A leitura usa os serviços internos existentes, sem novas portas públicas. `mirror-api` participa também da rede privada do Mealie e recebe o segredo SSO já existente em sua configuração privada. Nenhum segredo entra no repositório.
- Consulta limitada a 42 dias e cache de leitura de até 60 segundos, separado por fonte, identidade nativa e período. A tela segue o intervalo de atualização já configurado e oferece atualização manual.
- Planejamento respeita dias da semana, exceções por data, descanso, sessões fixadas e fila do openGym 1.4.5. Sequências sem data não são espalhadas artificialmente pelo calendário. No passado aparecem os treinos realizados, sem reconstruir planos históricos.

## Validação

- 35 testes Python do Mirror e 33 da autenticação em containers Linux isolados, sem bancos pessoais como fixture.
- Cobertura de migração idempotente, edição e isolamento de proprietário, horários inválidos, limite de período, paginação Mealie, autorização, CSRF, origem, separação de cache e falha parcial.
- Verificações Node de calendário, preferências, fundos, PWA e agenda: rótulos, itens excedentes, edição pessoal, deduplicação e descarte de respostas de navegação antigas.
- Prévia isolada com dados sintéticos e respostas HTTP verificadas das duas fontes. Leitura do endpoint Mealie instalado confirmada com HTTP 200.
- A conferência visual em navegador não foi concluída: o controle do navegador ficou indisponível. Não se afirma validação em aparelho físico, tablet ou iPhone.

### Revisão de fechamento (27/11/2026)

- **Correção** — `image()` em `docker/server/auth/mirror.py` usava a variável `action`, inexistente naquela função, ao calcular o tempo limite. O `NameError` era capturado como falha genérica e toda imagem ou miniatura da galeria retornava 503. O tempo limite voltou a 20 s. Um teste novo em `test_mirror_facade.py` cobre o encaminhamento da miniatura.
- **Teste desatualizado** — `test_weather_cannot_override_identity_action_or_admin` ainda esperava `lat`/`lon` no corpo, embora a release 48 tenha passado a usar só a cidade salva no servidor. Ele falhava desde a 48. Agora verifica que as coordenadas do cliente não são encaminhadas.
- **Mealie sem segredo** — `prepare.py` não termina mais com `KeyError` quando `apps.json` não tem a entrada `mealie`; grava `mealieSecret` vazio. A agenda trata fonte sem segredo como **sem acesso** e não faz a consulta. Coberto por teste novo em `test_agenda.py`.
- **Calendário no modo paisagem** — Na tela com altura fixa (largura ≥1000 px e altura ≥680 px), cada dia rolava sem barra visível. Itens e o botão **＋N** ficavam cortados sem aviso: a 1280×800, um dia com 7 itens mostrava só 2. Agora o módulo move para **＋N** os itens que não cabem, depois de desenhar e ao redimensionar a tela. Compromissos e lembretes têm prioridade sobre treinos e refeições importados, e um único item oculto aparece no lugar do botão. A ordenação é coberta por `check_calendar.mjs`. As verificações Node citadas na lista acima não cobriam a agenda antes desta revisão.
- **Testes executados no DEV** — Testes Python do Mirror: 36 aprovados. Autenticação: 33 aprovados. Fachada Mirror: 4 aprovados. Todos rodaram em container Linux `--network none`, sobre a base fixada `python:3.13-slim` e com Pillow 13.0.0. O `pip` não conseguiu baixar o Pillow, porque o antivírus AVG intercepta o HTTPS no DEV. O wheel foi baixado pelo Windows, conferido com o SHA-256 publicado no PyPI e instalado sem rede. A verificação de certificado não foi desativada. As verificações Node `check_calendar`, `check_settings`, `check_backgrounds` e `check_pwa` também foram aprovadas.
- **Conferência visual** — Feita no Chrome headless, com o `MMM-Aurora.js` e o CSS reais e respostas geradas pelo próprio `api.Data`/`agenda.collect` a partir de dados sintéticos. Telas verificadas: mês e semana a 1280×800, 1180×820 e 1920×1080; retrato a 820×1180; celular a 390×844, mês e semana. Também foram verificados a agenda do período, a lista de um dia com **＋N**, e a falha parcial com openGym indisponível e Mealie sem acesso. A prévia não usa o servidor MagicMirror nem dados reais. Não se afirma validação em aparelho físico.
- **Compose** — Sem `compose.mealie.yaml`, a seleção é rejeitada: `service "mirror-api" refers to undefined network mealie`. A seleção completa do servidor parou apenas no `secrets/sso/manyfold.env` ausente no DEV.

## Limites e recuperação

Esta agenda não adiciona notificações push, sincronização com Google/Outlook nem gravação de treinos ou refeições. Não cria refeições quando não há planejamento no Mealie.

Implantar conforme `ATUALIZACAO.md`, com backup e restauração isolada antes/depois. Atualizar somente `magicmirror`, `mirror-api` e `auth` para 50.0.0; imagens openGym/Garmin/Mealie são preservadas. Preparar a configuração privada atualizada com `docker/server/mirror/prepare.py` antes de iniciar a API.

Pré-requisitos: `COMPOSE_FILE` precisa incluir `compose.mealie.yaml` junto com `compose.opengym.yaml` e `compose.mirror.yaml`. `secrets/sso/apps.json` deve ter a entrada `mealie` com `secret`. Sem ela, a preparação conclui, mas as refeições aparecem como **sem acesso**.

Para retornar à 49, restaurar coerentemente o snapshot anterior do SQLite e a configuração privada com o código anterior. O INSERT da versão antiga não aceita a coluna adicional. Preservar alterações feitas após o snapshot antes de qualquer restauração; não substituir banco em uso.
