# AuroraLAB 46.0.0 — encerramento da avaliação wger

O proprietário optou por permanecer com o openGym/Garmin. Esta release remove o ambiente de avaliação wger e retira o instalador anterior do estado atual do projeto.

## Remoção executada

- Projeto Compose independente auroralab-wger-test: aplicação, PostgreSQL, gateway e backup, com as duas redes próprias.
- Imagem nomeada da avaliação e referência da imagem oficial wger 2.7. Imagens compartilhadas por outros aplicativos não são alvo de limpeza global.
- Banco PostgreSQL, uploads, arquivos estáticos, cópia privada dos dados importados, dumps, credenciais e configurações do teste.
- Adaptadores, Compose, fontes implantadas, arquivos temporários específicos e cópias locais utilizadas para a avaliação.
- Rota HTTPS Tailscale :8444. As rotas do portal, openGym e demais serviços são preservadas; a configuração Serve inteira não é reinicializada.
- Pacote específico de recuperação do wger no servidor e na cópia externa. O backup geral misto que continha configurações do teste é higienizado seletivamente; cada arquivo preservado é comparado pelo hash de seu conteúdo, e o checksum do arquivo é atualizado.

## Ambiente mantido

O openGym e a integração Garmin permanecem como estavam, com seus dados e identidades existentes. A retirada não substitui o aplicativo de treinos, não importa ou apaga exercícios no banco ativo e não altera o COMPOSE_FILE de produção.

A documentação de avaliação vira um aviso de encerramento. Histórico Git, releases já publicadas e registros de auditoria são mantidos; não há reescrita do repositório compartilhado. Os backups dos outros aplicativos não são excluídos.

## Validação e recuperação

Conferida a ausência dos containers/redes/rota/pastas do wger e a saúde dos três serviços openGym/Garmin. Compose de produção válido. A higienização do backup preservou byte a byte os arquivos alheios ao teste, recebeu novo SHA-256 e passou na restauração isolada dos arquivos e bancos SQLite.

Gerar backup geral após a retirada, conferir restauração isolada e copiar para armazenamento privado externo. Os comprovantes operacionais ficam no relatório privado da implantação, sem dados pessoais ou credenciais publicados no Git.

Nenhum teste funcional do aplicativo removido é necessário. Não se afirma ter apagado o histórico Git ou conteúdos compartilhados de cache Docker por uma limpeza global.
