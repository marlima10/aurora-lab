# Aurora Lab — Docker portátil

Este pacote permite executar o portal em outro computador com Docker Desktop, sem precisar do Armbian/RK322x.

## Conteúdo

- Site Aurora Lab e páginas Fitness, planos e exercícios.
- API Fitness em PHP organizada em `backend/`. O banco local fica em `data/fitness.sqlite3`; ele não está incluído no GitHub.
- Configuração Nginx isolada, sem encaminhar tráfego ao RK.

O pacote portátil original continha uma cópia do banco de 16/10/2026. Ao baixar do GitHub, a instalação cria um banco novo; para preservar os registros existentes, copie sua pasta `data/` separadamente. Não há sincronização automática com o RK.

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

Faça cópias da pasta `data` antes de substituir ou atualizar o pacote. As migrations são aplicadas na inicialização do serviço PHP; o seed inicial roda uma vez. Consulte `ESTRUTURA.md` para arquitetura e testes.

## Limites deste pacote

O Fitness e o site funcionam sem o RK. Câmera, monitoramento de hardware, histórico de impressão e diagnósticos pertencem ao Armbian e não foram incluídos. Eles aparecerão como indisponíveis; o pacote não tenta conectar ao RK.

A aplicação não pede login. A porta 8088 fica aberta no computador e pode ser acessível na rede local. Use em rede confiável e não exponha diretamente à internet.

Se copiar ou compactar a pasta `data`, o pacote resultante conterá dados pessoais de peso e treino; guarde-o em local privado.
