# Docker portátil — portal e Fitness

Modo reduzido de dois serviços, definido em `compose.yaml`: Nginx e PHP-FPM/SQLite. Pode rodar sem o servidor RK/Armbian ou o ambiente Linux completo. O backend é organizado em camadas; Composer e PHP são preparados na imagem.

## Requisitos e execução

Use Docker Desktop com contêineres Linux no Windows/macOS ou Docker Engine e plugin Compose no Linux. O motor precisa estar rodando, com internet para o primeiro build e a porta 8088 disponível. Clone/extraia o repositório numa pasta onde seu usuário possa gravar e execute na raiz:

```sh
docker compose -f compose.yaml up -d --build
docker compose -f compose.yaml ps
```

No Linux, use sudo para Docker quando seu usuário não tiver acesso ao socket. Não use o modo portátil para atualizar um servidor completo, que tem volumes e proxies diferentes. O `-f` explícito também evita selecionar COMPOSE_FILE de uma configuração servidor existente.

Abra `http://localhost:8088`. As páginas legadas `/fitness.html`, `/fitness-planos.html` e `/fitness-exercicios.html` continuam acessíveis por URL, mas saíram do menu principal na evolução para openGym. O módulo openGym e os atalhos Garmin dependem dos serviços do servidor e não são instalados nesse modo.

## Dados

Uma cópia baixada do GitHub não inclui registros pessoais. A aplicação cria `data/fitness.sqlite3`, aplica migrations na inicialização e cadastra os exercícios iniciais uma vez. Não há sincronização com RK, outro clone ou openGym.

O pacote ZIP histórico de 16/10/2026 podia incluir uma cópia pessoal; isso não descreve o conteúdo de um clone atual. Qualquer cópia da pasta data contém dados privados.

## Operação, backup e mudança de computador

```sh
docker compose -f compose.yaml logs --tail=100
docker compose -f compose.yaml stop
docker compose -f compose.yaml start
```

Pare os serviços antes de copiar a pasta data inteira. Preserve o banco e eventuais arquivos auxiliares, mantenha uma cópia externa e recoloque os dados na mesma estrutura no destino antes de iniciar. Não copie um banco ativo como se fosse snapshot consistente. Alterações no backend exigem novo build.

O backup automático descrito para AuroraServer não é um serviço desse Compose. `down` remove contêineres/rede do projeto, mas não substitui uma estratégia de backup nem deve ser acompanhado de limpeza de dados durante atualizações.

## Teste e limites

```sh
docker compose -f compose.yaml run --rm --no-deps --entrypoint php php tests/run.php
```

A suíte usa SQLite temporário. Monitoramento, câmera, diagnósticos e recursos externos aparecem indisponíveis no portátil. PWA cacheia interface, não substitui backup ou todos os serviços externos. Portal/Fitness não possuem login; use rede confiável e controle de acesso apropriado antes de publicar fora dela.

Veja [arquitetura](ESTRUTURA.md), [instalação servidor](AURORASERVER.md) e [solução de problemas](SOLUCAO-DE-PROBLEMAS.md).
