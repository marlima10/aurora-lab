# aurora-lab

Portal pessoal para Home Lab e acompanhamento de treinos e peso.

## Estrutura

- `site/`: interface em HTML, CSS e JavaScript, com suporte a PWA.
- `site/fitness-api/`: API PHP para perfis, registros, planos e exercícios.
- `docker/`: configuração do Nginx e ambiente PHP com SQLite.
- `compose.yaml`: serviços Docker Compose.

Consulte `LEIA-ME-DOCKER-PORTATIL.md` para detalhes do pacote portátil.

## Dados locais

O banco SQLite e os backups pessoais não são versionados. A aplicação usa `data/fitness.sqlite3` para armazenar os dados locais.

## Pendência conhecida

O `compose.yaml` referencia `docker/Dockerfile.php`, mas o arquivo presente é `docker/Dockerfile`. Ajuste essa referência antes de executar o build.
