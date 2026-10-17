# Aurora Lab 4.0

Desenvolvimento do ambiente AuroraServer na branch `rafael` do repositório oficial, preservando o portal e a API Fitness originais. [Alterações da versão 2.0](CHANGELOG.md).

Portal pessoal que reúne um dashboard de Home Lab e ferramentas para acompanhar treinos e evolução de peso. A interface usa HTML, CSS e JavaScript; a API Fitness usa PHP e SQLite, com execução pelo Docker Compose.

## Funcionalidades

### Fitness

- Perfis para organizar registros por pessoa.
- Registros de peso e treino, gráficos de evolução e relatórios.
- Planos de treino A/B/C/D e agenda semanal.
- Catálogo de exercícios de força e cardio, com links de vídeos do YouTube.
- Treino guiado com acompanhamento de séries, tempo e descanso.
- Exportação de relatórios e recursos de importação e mesclagem de registros.
- Controle de revisão para detectar alterações feitas em outro aparelho.

### Portal Home Lab

O dashboard reúne atalhos e painéis para impressora 3D, câmera, recursos do sistema, rede, armazenamento e backups.

**Dois modos de execução:** o pacote portátil (`compose.yaml`) oferece portal e Fitness. O ambiente completo Linux (`compose.server.yaml`) acrescenta OctoPrint, câmera USB opcional, Samba, monitoramento, backups, Tailscale e Cockpit em contêineres separados. Consulte [instalação AuroraServer](AURORASERVER.md).

## Tecnologias e arquitetura

| Área | Implementação |
| --- | --- |
| Frontend | HTML, CSS e JavaScript, sem etapa de build |
| Interface | Layout responsivo, temas e recursos de PWA |
| API | PHP 8.2, respostas JSON e endpoint `/fitness-api` |
| Persistência | SQLite por PDO, migrations e seed inicial |
| Organização | Controllers, Requests, Services e Repositories |
| Autoload | Composer com PSR-4, namespace `Aurora` |
| Execução | Nginx e PHP-FPM em contêineres Docker |

Controllers recebem as requisições, Requests validam os dados, Services aplicam as regras e Repositories executam o SQL. A interface fica no frontend; não são usados templates PHP de Views.

## Requisitos

- Docker Desktop no Windows/macOS, ou Docker Engine com o plugin Compose no Linux.
- Docker iniciado e configurado para executar contêineres Linux.
- Internet no primeiro build para baixar as imagens e preparar o ambiente PHP.
- Porta `8088` disponível no computador.

PHP, Composer, Nginx e SQLite são preparados na imagem. Não é necessário instalá-los separadamente para executar pelo Docker.

## Início rápido

Baixe o código pelo GitHub ou clone o repositório, se tiver Git instalado:

```sh
git clone https://github.com/marlima10/aurora-lab.git
cd aurora-lab
git checkout rafael
```

Se o projeto já estiver no computador, abra o terminal na pasta que contém `compose.yaml`. Em seguida:

```sh
docker compose up -d --build
docker compose ps
```

Acesse:

- [Dashboard](http://localhost:8088/)
- [Treinos e peso](http://localhost:8088/fitness.html)
- [Planos de treino](http://localhost:8088/fitness-planos.html)
- [Catálogo de exercícios](http://localhost:8088/fitness-exercicios.html)

Na inicialização, o serviço PHP aplica as migrations pendentes e prepara o catálogo inicial de exercícios. Uma instalação obtida do GitHub começa sem os registros pessoais; eles são criados conforme o uso.

## Comandos úteis

| Ação | Comando |
| --- | --- |
| Ver o estado dos serviços | `docker compose ps` |
| Ver os logs do PHP | `docker compose logs --tail=100 php` |
| Ver os logs do Nginx | `docker compose logs --tail=100 web` |
| Parar os serviços | `docker compose stop` |
| Iniciar os serviços existentes | `docker compose start` |
| Recriar os serviços após alterações | `docker compose up -d --build` |
| Remover os contêineres e a rede do projeto | `docker compose down` |
| Validar a configuração Compose | `docker compose config --quiet` |

O frontend é montado diretamente de `site/`. Alterações no backend e no Dockerfile exigem um novo build. Ao alterar arquivos públicos usados pela PWA, mantenha as versões e o cache do service worker coerentes, conforme o padrão visual.

## Estrutura do projeto

```text
aurora-lab/
├── backend/
│   ├── public/           # Entrada HTTP da API
│   ├── config/           # Configuração do banco
│   ├── routes/           # Mapeamento das ações da API
│   ├── src/
│   │   ├── Http/         # Controllers, Requests e respostas JSON
│   │   ├── Services/     # Regras de negócio e sincronização
│   │   ├── Repositories/ # Acesso ao SQLite
│   │   ├── Database/     # Conexão, transações e migrations
│   │   └── Exceptions/   # Validação e conflitos
│   ├── database/         # Migrations e seeds
│   ├── bin/              # Comandos de manutenção
│   ├── tests/            # Testes de integração
│   ├── bootstrap.php     # Composição das dependências
│   └── composer.json
├── site/                 # Interface, estilos, scripts e PWA
├── docker/               # Nginx, imagem PHP e inicialização
├── data/                 # Banco local; não versionado
├── skills/               # Padrões visuais e de desenvolvimento
├── compose.yaml
└── ESTRUTURA.md
```

Somente `site/` é servido como conteúdo estático. O Nginx encaminha `/fitness-api` para o ponto de entrada do backend, cujo código permanece fora da raiz pública.

## Dados locais e backup

Os registros ficam em `data/fitness.sqlite3`, montado no contêiner como `/var/lib/fitness/fitness.sqlite3`. O caminho interno pode ser configurado pela variável de ambiente `FITNESS_DB_PATH` do serviço PHP.

A pasta `data/`, os bancos e os backups pessoais ficam fora do Git e do contexto de build. Eles não são enviados ao GitHub. O cache da PWA não substitui um backup do banco.

Para fazer uma cópia consistente, pare os serviços com `docker compose stop`, copie a pasta `data/` inteira para um local seguro e reinicie com `docker compose start`. Antes de atualizar o projeto ou mover a instalação, preserve essa pasta. Para restaurar uma cópia, mantenha os serviços parados durante a substituição de `data/`.

As migrations são registradas em `schema_migrations` e executadas na inicialização do serviço PHP. O seed inicial roda uma vez; exercícios excluídos não são recriados em cada acesso à API. O banco local não sincroniza automaticamente com o servidor RK.

## Testes

Após construir a imagem PHP, execute na raiz:

```sh
docker compose run --rm --no-deps --entrypoint php php tests/run.php
```

A suíte usa bancos SQLite temporários próprios e cobre gravação, importação, merge, conflitos de revisão, planos, catálogo, rollback e migração de uma base legada. O banco pessoal não é usado pelos testes.

Para desenvolvimento sem Docker, com PHP 8.2+, PDO SQLite e Composer disponíveis:

```sh
cd backend
composer dump-autoload --optimize
php tests/run.php
```

## Acesso pela rede local

Outro aparelho pode acessar `http://IP-DO-COMPUTADOR:8088`, desde que esteja na mesma rede e o firewall permita a conexão. O computador precisa permanecer ligado, com o Docker e os serviços em execução.

A versão atual não possui login. Use em uma rede confiável; a publicação na internet exige definir autenticação e proteção de acesso.

## Documentação e padrões

- [Estrutura e arquitetura detalhada](ESTRUTURA.md): responsabilidades, contrato da API, persistência e migrations.
- [Padrão visual](skills/aurora-visual/SKILL.md): identidade, componentes, temas, acessibilidade e cache.
- [Padrão de desenvolvimento](skills/aurora-development/SKILL.md): camadas, convenções, compatibilidade e validação.
- [Pacote Docker portátil](LEIA-ME-DOCKER-PORTATIL.md): transferência da instalação e limites das integrações.

As skills são documentos versionados neste repositório para orientar a evolução do projeto; não dependem de instalação global no Codex.

## Implantacao AuroraServer

O ambiente completo separado por servico usa compose.server.yaml; consulte AURORASERVER.md para volumes, restauracao, VPN, plugins e dispositivos USB. O compose.yaml continua disponivel para o pacote portatil original.


## Versão 2.0.0

Consulte o [histórico de alterações](CHANGELOG.md) e a [instalação completa no Linux](AURORASERVER.md). A identidade visual e o contrato da API Fitness foram preservados. Dados, senhas e backups são mantidos fora do repositório.

## Energia e autonomia

A versão 3.0 acrescenta bateria clicável, histórico de potência, GPUs, simulador de custo com tarifa configurável e pop-up de economia. Controles autenticados em serviço Docker opcional; consulte AURORASERVER.md. Sensores indisponíveis são identificados; consumo na tomada exige medidor externo.

## CasaOS

Gerenciamento no host e aplicativos Docker separados. Consulte [CasaOS](CASAOS.md).
