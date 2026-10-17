# Aurora Lab — Docker portátil

Este pacote permite executar o portal em outro computador com Docker Desktop, sem precisar do Armbian/RK322x.

## Conteúdo

- Site Aurora Lab e páginas Fitness, planos e exercícios.
- API Fitness em PHP e cópia do banco SQLite em `data/fitness.sqlite3`.
- Configuração Nginx isolada, sem encaminhar tráfego ao RK.

O banco é uma cópia de 16/10/2026. A instalação nova passa a gravar separadamente; registros criados depois no RK não serão sincronizados.

## Requisitos

- Windows 10/11 ou Linux/macOS com Docker Desktop ou Docker Engine e Docker Compose.
- Internet na primeira inicialização para baixar as imagens e montar PHP.

## Iniciar no Windows

1. Extraia a pasta `aurora-lab-docker-portatil-20261016` em um local permanente, por exemplo `C:\AuroraLab`.
2. Abra o PowerShell dentro dessa pasta.
3. Rode:

```powershell
docker compose up -d --build
docker compose ps
```

4. Acesse `http://localhost:8088`. Outro aparelho da mesma rede pode usar `http://IP-DO-COMPUTADOR:8088`.

## Iniciar no Linux ou macOS

Extraia a pasta, abra o terminal nela e rode:

```sh
docker compose up -d --build
docker compose ps
```

Acesse `http://localhost:8088`.

## Parar, iniciar e mover

```sh
docker compose stop
docker compose start
docker compose down
```

Para mover o portal, pare os containers e copie a pasta inteira para o outro computador. O arquivo `data/fitness.sqlite3` contém os registros; ele não sincroniza com o banco do RK.

**Não use `docker compose down -v`.** Faça cópias da pasta `data` antes de substituir ou atualizar o pacote.

## Limites deste pacote

O Fitness e o site funcionam sem o RK. Câmera, monitoramento de hardware, histórico de impressão e diagnósticos pertencem ao Armbian e não foram incluídos. Eles aparecerão como indisponíveis; o pacote não tenta conectar ao RK.

A aplicação não pede login. A porta 8088 fica aberta no computador e pode ser acessível na rede local. Use em rede confiável e não exponha diretamente à internet.

O ZIP inclui dados pessoais de peso e treino; guarde-o em local privado.
