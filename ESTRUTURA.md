# Estrutura do Aurora Lab

O Aurora Lab reúne um portal de Home Lab e uma aplicação de treinos e peso. O frontend é HTML, CSS e JavaScript; a API usa PHP 8.2+, PDO e SQLite. Nginx e PHP-FPM são executados pelo Docker Compose.

## Diretórios

```text
aurora-lab/
├── backend/
│   ├── public/index.php       # Entrada HTTP da API
│   ├── bootstrap.php          # Composição das dependências
│   ├── config/database.php    # Caminho do SQLite
│   ├── routes/api.php         # Método + action → controller
│   ├── src/
│   │   ├── Http/
│   │   │   ├── Controllers/  # Adaptação HTTP → serviço
│   │   │   ├── Requests/     # Validação dos dados recebidos
│   │   │   ├── Application.php
│   │   │   └── JsonResponse.php
│   │   ├── Services/         # Regras e coordenação de transações
│   │   ├── Repositories/     # Consultas e gravações SQL
│   │   ├── Database/         # Conexão, transações e migrations
│   │   └── Exceptions/       # Erros de validação e conflito
│   ├── database/
│   │   ├── migrations/       # Evolução versionada do esquema
│   │   └── seeds/            # Catálogo inicial de exercícios
│   ├── bin/migrate.php       # Comando de atualização do banco
│   ├── tests/run.php         # Integração com SQLite temporário
│   └── composer.json         # Autoload PSR-4: Aurora → src/
├── site/                     # Arquivos públicos e PWA
├── docker/                   # Nginx, Dockerfile e inicialização PHP
├── data/                     # Banco pessoal; fora do Git e da imagem
├── skills/
│   ├── aurora-visual/SKILL.md
│   └── aurora-development/SKILL.md
├── compose.yaml
└── ESTRUTURA.md
```

## Fluxo de uma requisição

`/fitness-api → public/index.php → Application → Controller → Request → Service → Repository → SQLite`

O controller recebe os dados e chama o serviço. Requests validam formato, tipos e limites. Services aplicam regras que dependem do estado, como impedir excluir exercícios usados por planos, e definem a fronteira das transações. Repositories concentram o SQL. JsonResponse escreve status, cabeçalhos e JSON; erros são tratados por Application.

Esta é uma organização em camadas para API. A apresentação já está no frontend; não há templates PHP de Views. Interfaces, entidades e DTOs adicionais devem surgir conforme uma necessidade real, evitando arquivos que apenas repassem chamadas.

## Contrato mantido

| Método | action | Operação |
| --- | --- | --- |
| GET | ausente | Ler perfis e registros |
| GET | catalog | Listar exercícios |
| GET | plans | Ler planos; query person obrigatória |
| POST | save ou ausente | Salvar estado com expectedRevision |
| POST | import | Inicializar estado somente se ainda não existir |
| POST | merge | Mesclar registros por id e updatedAt |
| POST | save_plans | Salvar fichas A/B/C/D e agenda |
| POST | save_catalog_exercise | Cadastrar ou editar exercício |
| POST | delete_catalog_exercise | Excluir exercício sem referências |

GET com action desconhecida continua retornando o estado, por compatibilidade. POST com ação desconhecida retorna 400; métodos não suportados retornam 405. Mantêm-se os nomes camelCase do JSON, revisões, campos de conflito e exclusões lógicas. Erros 400 representam entrada inválida, 409 conflito, 413 corpo acima de 2 MB e 500 falha interna. Erros internos são registrados no log e não expõem SQL ao cliente.

## Persistência e migrations

`FITNESS_DB_PATH` define o banco; o padrão é `/var/lib/fitness/fitness.sqlite3`, montado de `data/` pelo Compose. Os registros permanecem nas tabelas e nos campos JSON existentes. Não houve normalização ou transformação dos dados pessoais nesta reorganização.

A inicialização do contêiner aplica migrations como `www-data`, antes de iniciar PHP-FPM. `schema_migrations` registra as versões concluídas. A primeira migration aceita a base existente, acrescenta revision quando ausente e cria as tabelas que faltarem. O seed de exercícios roda apenas nessa migration; exercícios excluídos não reaparecem a cada requisição. Faça backup de `data/` antes de atualizar o contêiner.

Gravações coordenadas usam `BEGIN IMMEDIATE`, com commit ou rollback centralizado. Revisão do estado e revisão de planos são independentes. Na mesclagem, o updatedAt mais recente vence; em empate, o servidor vence. A exclusão de perfil remove seus planos e revisões. Validação estrita de data e peso é mantida em save; import e merge aceitam o formato legado.

## Execução e validação

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 php
```

Acesse http://localhost:8088. O Composer e o PHP são preparados na imagem; não é necessário instalá-los no computador. Mudanças no backend exigem rebuild; o frontend continua montado da pasta site.

```powershell
docker compose run --rm --no-deps --entrypoint php php tests/run.php
```

O teste substitui FITNESS_DB_PATH por bancos temporários próprios e não executa o entrypoint de produção. Com PHP e Composer disponíveis localmente, execute `composer dump-autoload` e `php tests/run.php` em backend. Para migrations manuais, configure FITNESS_DB_PATH e execute `php bin/migrate.php`.

## Docker e limites do pacote

Somente site/ é servido como conteúdo estático. Nginx encaminha apenas /fitness-api para /var/www/backend/public/index.php no PHP-FPM. O backend é copiado para a imagem; código, configuração e vendor ficam fora da raiz pública. O contexto de build usa uma lista de inclusão em .dockerignore, excluindo dados pessoais.

O dashboard mantém as integrações originais, mas monitoramento, câmera, rede e serviços do RK retornam indisponibilidade nesta distribuição portátil. A aplicação mantém o acesso sem login existente; mudanças de autenticação são uma evolução separada.

## Padrões do projeto

- [Padrão visual](skills/aurora-visual/SKILL.md): componentes, cores, temas e responsividade existentes.
- [Padrão de desenvolvimento](skills/aurora-development/SKILL.md): responsabilidades, compatibilidade, banco e testes.

Atualize estes documentos junto das mudanças de arquitetura e das decisões visuais adotadas.
