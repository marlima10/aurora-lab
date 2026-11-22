# wger — fontes do ambiente de avaliação

- Aplicativo oficial: https://github.com/wger-project/wger, release estável 2.7.
- Implantação oficial consultada: https://github.com/wger-project/docker.
- Base `wger/server:2.7@sha256:1c5789b93bfe5eed0b7287255782d9177027b255de2b22b59f511a693a48db04`.
- PostgreSQL 15 e Nginx fixados por digest no Compose.
- Licença wger: AGPL-3.0-or-later, conservada na imagem. Os adaptadores Python desta avaliação são disponibilizados sob a mesma licença.
- Dockerfile, adaptadores e procedimentos completos ficam neste diretório/repositório; nenhuma exportação de usuário, banco ou chave integra a compilação.
- O servidor web permanece sem saída externa. Não há Celery, Redis, PowerSync ou integração automática Garmin neste teste.
