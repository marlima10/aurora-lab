# Estrutura e arquitetura — AuroraLAB 13.0.0

Este documento descreve o código atual, não o estado de uma máquina específica. Os caminhos de código são relativos à raiz do repositório; os links entre guias são relativos a `docs/`.

## Mapa do projeto

```text
aurora-lab/
├── backend/
│   ├── public/index.php       # Entrada HTTP da API Fitness
│   ├── bootstrap.php          # Composição de dependências
│   ├── config/database.php    # Caminho SQLite
│   ├── routes/api.php         # Método/action → controller
│   ├── src/
│   │   ├── Http/              # Controllers, Requests, Application e JsonResponse
│   │   ├── Services/          # Regras e sincronização
│   │   ├── Repositories/      # SQL e mapeamento
│   │   ├── Database/          # Conexão, transações, Migrator
│   │   └── Exceptions/        # Validação e conflitos
│   ├── database/              # Migrations e seed
│   ├── bin/migrate.php
│   ├── tests/run.php
│   └── composer.json
├── site/                      # Interface, PWA e ícones
├── docker/
│   ├── Dockerfile             # PHP portátil e servidor
│   ├── nginx.conf             # Proxy portátil
│   └── server/                # Monitor, backup, preparação e imagens dos módulos
├── docs/                      # Guias, histórico e diagnóstico
├── skills/                    # Padrões reutilizáveis
├── compose.yaml               # Portátil: web e php
├── compose.server.yaml        # Servidor Linux: projeto auroralab
├── compose.homeassistant.yaml
├── compose.opengym.yaml       # API/web openGym e importador Garmin
├── compose.power.yaml
├── compose.printer.yaml
├── VERSION
└── README.md
```

## Interface e módulos

O frontend usa HTML/CSS/JavaScript sem build obrigatório. Layout compacto, temas e atalhos são compartilhados. A PWA versiona o cache; endpoints dinâmicos e redirects externos não devem ser tratados como dados offline permanentes.

Desde a versão 7, Fitness/planos/exercícios saíram da navegação; os arquivos e a API continuam no repositório. O módulo atual openGym usa imagens externas fixadas por digest e dados próprios. O servidor redireciona `/opengym`, o legado `/opengym.html` e `/garmin` pelo monitor para a origem HTTPS configurada. O portátil não possui esse monitor nem instala esses serviços.

## API Fitness em camadas

`/fitness-api → public/index.php → Application → Controller → Request → Service → Repository → SQLite`

Controllers adaptam entrada/chamada; Requests validam tipos e limites; Services aplicam regras e coordenam transações; Repositories concentram SQL. JsonResponse produz cabeçalhos/status/JSON, e Application converte erros conhecidos ou registra falhas internas. Não há Views PHP: a apresentação está no frontend. Autoload PSR-4 usa namespace Aurora.

| Método | action | Operação |
| --- | --- | --- |
| GET | ausente ou desconhecida | Estado de perfis/registros, por compatibilidade |
| GET | catalog | Catálogo de exercícios |
| GET | plans | Planos; exige query person |
| POST | save ou ausente | Salvar estado com expectedRevision |
| POST | import | Inicializar apenas se ainda não houver estado |
| POST | merge | Mesclar por id/updatedAt, servidor vence empate |
| POST | save_plans | Fichas A/B/C/D e agenda |
| POST | save_catalog_exercise | Criar/editar exercício |
| POST | delete_catalog_exercise | Excluir quando não está em planos |

Validação retorna 400; conflito 409; corpo acima de 2 MB 413; método não suportado 405; falha interna 500. Nomes JSON camelCase e revisões independentes de estado/planos são preservados. `save` valida calendário, datas futuras, duplicidade pessoa/data e peso; import/merge mantêm compatibilidade legada. Exclusões lógicas são preservadas e a exclusão de perfil remove seus planos.

## SQLite e migrations

FITNESS_DB_PATH escolhe o banco, por padrão `/var/lib/fitness/fitness.sqlite3`. O portátil monta `data/`; o servidor monta `data/fitness/`. Transaction usa BEGIN IMMEDIATE e rollback em exceções. A inicialização aplica migrations como www-data antes de iniciar PHP-FPM. `schema_migrations` registra versões; o seed inicial roda uma vez. Não há seed executado em toda requisição nem migração automática para openGym.

O backend fica na imagem, fora da raiz pública Nginx. Rebuild é necessário para suas alterações; `site/` continua montado do host. Os contextos Docker têm regras próprias: o contexto PHP inclui apenas backend e arquivos necessários; imagens dos módulos usam seus diretórios como contextos. Não acrescente dados/segredos aos contextos de build.

## Serviços e limites

| Componente | Papel e implementação |
| --- | --- |
| web | Conteúdo estático, API FastCGI e proxies/redirects do ambiente |
| monitor | Python em rede host; /proc e /sys somente leitura, sem Docker socket |
| backup | Python, snapshots SQLite, validação e arquivo com SHA-256 |
| octoprint | Python 3.12, OctoPrint 1.11.8, s6-overlay e plugins fixados |
| samba | Prints autenticado; conta rafael fixada nos arquivos atuais |
| camera | Perfil opcional, uStreamer e dispositivo USB explícito |
| tailscale | Daemon em rede host; pode conflitar com a instalação Debian |
| cockpit | Nginx HTTPS 9090 para backend Cockpit/PAM nativo 9091 |
| CasaOS | Serviços systemd no Debian, não um serviço Compose Aurora |
| homeassistant | Container com rede host e configuração própria |
| opengym-api/web | Rede Docker dedicada, API interna e web loopback 8081 |
| opengym-garmin | Serviço Python sem porta extra no host, integrado pelo proxy web |
| power | Telemetria/controles locais, mounts específicos de CPU/brilho |

Os preparadores openGym/Cockpit ainda consultam o nome fixo do contêiner VPN. Os atalhos CasaOS são LinkApps, não monitoramento vivo. Monitor usa SERVER_IP e varredura ICMP /24; alguns diagnósticos são textos estáticos de referência e não comprovam hardware conectado. Sensores ausentes devem continuar indisponíveis, sem inventar zero.

## Persistência e backup

Os estados ficam separados em `data/fitness`, `octoprint`, `prints`, `samba`, `monitor`, `power`, `homeassistant`, `opengym`, `garmin` e `tailscale`. CasaOS e Cockpit também têm configuração nativa em `/etc` e `/var/lib`. `.env`, `secrets`, `backups` e `deploy-state` não entram no Git.

O backup monta explicitamente suas origens no Compose, incluindo `docs/`. Usa snapshots dos SQLite reconhecidos e valida JSON openGym individualmente. Não há transação global entre todos os aplicativos. Ele exige o banco Fitness e valida o histórico PrintHistory quando presente. Estado VPN do host, deploy-state e aplicativos CasaOS novos não são incluídos automaticamente. Restauração e cópia externa: [ATUALIZACAO.md](ATUALIZACAO.md).

## Validação e evolução

Testes PHP: `docker compose run --rm --no-deps --entrypoint php php tests/run.php`, com a seleção correta do ambiente e imagem construída. Alternativa local em backend: `composer dump-autoload` e `php tests/run.php`, com PHP/PDO SQLite. Energia: `python3 docker/server/power/test_power.py` em Linux. Garmin: `python3 -m unittest discover -s docker/server/garmin -p 'test_*.py' -v`, com dependências de teste disponíveis conforme [GARMIN.md](GARMIN.md).

Os testes sintéticos não substituem login real, restore real ou impressão física. Verifique Compose com config --quiet e use fixtures temporárias; não teste gravando dados pessoais.

Padrões: [desenvolvimento](../skills/aurora-development/SKILL.md) e [visual](../skills/aurora-visual/SKILL.md). Procedimentos operacionais: [servidor](AURORASERVER.md), [rede](REDE-E-TAILSCALE.md), [CasaOS](CASAOS.md), [Cockpit](COCKPIT.md), [Home Assistant](HOMEASSISTANT.md), [openGym](OPENGYM.md), [Garmin](GARMIN.md) e [OctoPrint](UPGRADE-PYTHON-OCTOPRINT.md).
