# AuroraLAB 22.0.0 — metas, sincronização e operação do servidor

## openGym: metas semanais por perfil

- Painel de metas no Início e na página Estatísticas: quantidade de treinos, minutos e calorias.
- Semana de segunda-feira até a data atual, conforme o calendário local do usuário. Datas futuras ou inválidas e IDs duplicados não entram nos totais.
- Metas editáveis, com barras de progresso e comparação entre realizado e planejado. Zero desativa uma meta; nenhuma meta de saúde é imposta ao usuário.
- Preferência `auroraWeeklyGoals` no estado nativo do perfil, com persistência e sincronização existentes. A gravação não altera treinos, planos ou pesos.
- Duração reutiliza o cálculo dos gráficos existentes; calorias usam os dados Garmin disponíveis, sem estimativas. O painel informa a cobertura dos registros.
- Painel de metas e resumo Garmin podem ser reorganizados pelos controles de arraste e teclado existentes. A ordem anterior dos demais painéis é preservada.

## openGym: resumo da sincronização Garmin

- Novo cartão no Início com conexão, atualização ativa/pausada, última consulta, quantidade importada, quantidade já existente, próxima consulta e mensagens de falha.
- Botão **Sincronizar agora** no próprio openGym e link para configurar a conexão Garmin.
- Usa a sessão existente e os endpoints privados do conector; não acrescenta chave administrativa global nem expõe credenciais no frontend.
- Atualiza o resumo a cada 30 segundos com a página visível. A importação continua no servidor, consultando os cinco últimos treinos a cada hora, mesmo com o navegador fechado.
- O service worker deixa as rotas Garmin fora do cache, evitando resultados privados ou antigos guardados como arquivos estáticos.

## Portal: alertas do servidor

- Novo painel com ocorrências ativas e histórico de recuperações.
- Monitora a disponibilidade de OctoPrint, câmera USB, portal, Samba, Cockpit, HomeBoard, Home Assistant e openGym.
- Avisa quando o disco chega a 80% de uso e eleva para crítico em 90%.
- Avisa sobre falha no backup, backup ausente/atrasado há mais de 36 horas e falha no teste de restauração.
- Confirma a condição por 30 segundos para filtrar interrupções breves. Ausência de registro de backup recebe tolerância inicial de cinco minutos.
- Histórico persistente limitado a 200 eventos, com os 30 mais recentes visíveis no painel; não repete notificações a cada coleta sem mudança de gravidade.
- Avisos entregues no portal enquanto aberto. Esta versão não envia mensagens por e-mail, Telegram ou outros canais externos e não instala acesso ao Docker socket no monitor.

## Backup: restauração isolada e verificável

- Novo verificador extrai o arquivo em diretório temporário privado, remapeia os snapshots SQLite para os caminhos originais e confere cada arquivo restaurado por SHA-256.
- Valida integridade dos bancos SQLite, leitura dos JSON e presença dos dados essenciais Fitness/openGym.
- Recusa caminhos absolutos, travessia de diretórios, links, duplicatas, arquivos especiais, limite acima de 20 GiB e espaço insuficiente.
- Dados temporários são removidos ao terminar, inclusive quando ocorre falha.
- O backup diário passa a executar essa verificação após concluir seu arquivo. O resultado da cópia e o resultado da restauração são separados, evitando tratar um backup válido como perdido caso apenas o teste falhe.
- O portal exibe data, quantidade de arquivos, bancos e JSON verificados.
- A validação cobre recuperação dos dados; não representa um teste de impressão física, VPN ou inicialização completa de todos os serviços. O ensaio desta implantação inclui uma verificação adicional da API openGym com os dados restaurados, sem portas públicas e sem rede.

## Energia: histórico diário e resumo mensal

- Registro persistente de até 90 dias com energia do pacote CPU, descarga da bateria e horas efetivamente observadas em cada fonte.
- Virada do dia em America/Sao_Paulo; preserva o acumulado existente do dia e inicia a série histórica nesta atualização.
- Não extrapola intervalos de suspensão, desligamento, reinicialização ou ausência de sensores. Não soma CPU com bateria, pois são escopos sobrepostos.
- Tabela diária, total do mês corrente e custo parcial da CPU pela tarifa R$/kWh já configurável no navegador. Alterar a tarifa recalcula os valores apresentados.
- CPU sem leitura permanece indisponível. Esta medição não equivale ao gasto total do notebook na tomada; a simulação de 30 dias permanece separada.

## Documentação, implantação e compatibilidade

- README, versão do projeto, arquitetura e guias atualizados para 22.0.0.
- Frontend openGym reconstruído a partir do mesmo commit upstream fixado; backend, passkeys e formato dos dados nativos preservados.
- Mantidos foto de fundo, painéis organizáveis, gráficos, importação Garmin e demais serviços independentes em Docker.
- Atualização do cache PWA para distribuir os novos recursos do portal e do openGym.
- Backup privado antes da implantação, cópia externa conferida, testes com dados sintéticos e registros de validação separados do Git. Credenciais e backups não acompanham esta release.
