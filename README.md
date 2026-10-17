# aurora-lab

Portal pessoal para Home Lab e acompanhamento de treinos e peso.

## Executar

Com Docker Desktop/Engine e Compose disponíveis, execute na raiz:

```sh
docker compose up -d --build
docker compose ps
```

Acesse http://localhost:8088. O build prepara PHP, SQLite e autoload; a inicialização aplica as migrations. Alterações no backend exigem um novo build.

## Documentação

- [Estrutura e arquitetura](ESTRUTURA.md)
- [Padrão visual](skills/aurora-visual/SKILL.md)
- [Padrão de desenvolvimento](skills/aurora-development/SKILL.md)
- [Pacote Docker portátil](LEIA-ME-DOCKER-PORTATIL.md)

## Testes

```sh
docker compose run --rm --no-deps --entrypoint php php tests/run.php
```

Os testes usam bancos temporários. O banco SQLite em data/ e os backups pessoais não são versionados. Preserve essa pasta e faça backup antes de atualizar.
