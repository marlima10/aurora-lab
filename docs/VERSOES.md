# Versões do Aurora LAB

A partir da **5.4.0**, a versão técnica segue `X.Y.Z` e a tag usa `aurora-X.Y.Z`. O título no GitHub usa X.Y quando Z é zero, como **Aurora LAB 5.4**, e inclui o patch quando Z é diferente de zero.

| Identificador | Exemplo |
| --- | --- |
| VERSION e versão da documentação | 5.4.0 |
| Tag Git | aurora-5.4.0 |
| Imagem Docker | auroralab-opengym-web:5.4.0 |
| Cache PWA / APP_BUILD | auroralab-5.4.0 / auroralab-5.4 |

VERSION permanece em 53.0.0 nesta revisão. Na próxima release, ele passa diretamente para 5.4.0. Use a cronologia das releases ou a família de tags para ordenar o histórico, pois 5.4.0 é numericamente menor que 53.0.0.

O prefixo aurora- evita colisões com tags históricas como v5.0.0 a v9.0.0, que correspondem aos títulos 0.5 a 0.9. Antes de reutilizar números como 6.0.0 a 9.0.0 em imagens, confira o inventário do host com `docker image ls 'auroralab-*'`. Para rollback, use o ID ou digest da imagem registrada antes da implantação.

## Correspondência histórica

| Tag | Versão no título | Notas no repositório |
| --- | --- | --- |
| [v1.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v1.0.0) | 0.1 | — |
| [v2.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v2.0.0) | 0.2 | — |
| [v3.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v3.0.0) | 0.3 | — |
| [v4.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v4.0.0) | 0.4 | — |
| [v5.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v5.0.0) | 0.5 | — |
| [v6.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v6.0.0) | 0.6 | — |
| [v7.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v7.0.0) | 0.7 | — |
| [v8.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v8.0.0) | 0.8 | — |
| [v9.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v9.0.0) | 0.9 | — |
| [v10.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v10.0.0) | 1.0 | — |
| [v11.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v11.0.0) | 1.1 | — |
| [v12.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v12.0.0) | 1.2 | — |
| [v13.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v13.0.0) | 1.3 | — |
| [v14.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v14.0.0) | 1.4 | — |
| [v15.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v15.0.0) | 1.5 | — |
| [v16.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v16.0.0) | 1.6 | — |
| [v17.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v17.0.0) | 1.7 | — |
| [v18.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v18.0.0) | 1.8 | — |
| [v19.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v19.0.0) | 1.9 | — |
| [v20.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v20.0.0) | 2.0 | — |
| [v21.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v21.0.0) | 2.1 | — |
| [v22.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v22.0.0) | 2.2 | [RELEASE-22.md](RELEASE-22.md) |
| [v23.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v23.0.0) | 2.3 | [RELEASE-23.md](RELEASE-23.md) |
| [v24.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v24.0.0) | 2.4 | [RELEASE-24.md](RELEASE-24.md) |
| [v25.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v25.0.0) | 2.5 | [RELEASE-25.md](RELEASE-25.md) |
| [v26.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v26.0.0) | 2.6 | [RELEASE-26.md](RELEASE-26.md) |
| [v27.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v27.0.0) | 2.7 | [RELEASE-27.md](RELEASE-27.md) |
| [v28.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v28.0.0) | 2.8 | [RELEASE-28.md](RELEASE-28.md) |
| [v29.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v29.0.0) | 2.9 | [RELEASE-29.md](RELEASE-29.md) |
| [v30.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v30.0.0) | 3.0 | — |
| [v31.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v31.0.0) | 3.1 | [RELEASE-31.md](RELEASE-31.md) |
| [v32.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v32.0.0) | 3.2 | [RELEASE-32.md](RELEASE-32.md) |
| [v33.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v33.0.0) | 3.3 | [RELEASE-33.md](RELEASE-33.md) |
| [v34.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v34.0.0) | 3.4 | [RELEASE-34.md](RELEASE-34.md) |
| [v35.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v35.0.0) | 3.5 | [RELEASE-35.md](RELEASE-35.md) |
| [v36.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v36.0.0) | 3.6 | [RELEASE-36.md](RELEASE-36.md) |
| [v37.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v37.0.0) | 3.7 | [RELEASE-37.md](RELEASE-37.md) |
| [v38.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v38.0.0) | 3.8 | [RELEASE-38.md](RELEASE-38.md) |
| [v39.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v39.0.0) | 3.9 | [RELEASE-39.md](RELEASE-39.md) |
| [v40.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v40.0.0) | 4.0 | [RELEASE-40.md](RELEASE-40.md) |
| [v41.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v41.0.0) | 4.1 | [RELEASE-41.md](RELEASE-41.md) |
| [v42.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v42.0.0) | 4.2 | [RELEASE-42.md](RELEASE-42.md) |
| [v43.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v43.0.0) | 4.3 | [RELEASE-43.md](RELEASE-43.md) |
| [v44.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v44.0.0) | 4.4 | [RELEASE-44.md](RELEASE-44.md) |
| [v45.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v45.0.0) | 4.5 | [RELEASE-45.md](RELEASE-45.md) |
| [v46.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v46.0.0) | 4.6 | [RELEASE-46.md](RELEASE-46.md) |
| [v47.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v47.0.0) | 4.7 | [RELEASE-47.md](RELEASE-47.md) |
| [v48.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v48.0.0) | 4.8 | [RELEASE-48.md](RELEASE-48.md) |
| [v49.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v49.0.0) | 4.9 | [RELEASE-49.md](RELEASE-49.md) |
| [v50.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v50.0.0) | 5.0 | [RELEASE-50.md](RELEASE-50.md) |
| [v52.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v52.0.0) | 5.2 | [RELEASE-52.md](RELEASE-52.md) |
| [v53.0.0](https://github.com/marlima10/aurora-lab/releases/tag/v53.0.0) | 5.3 | [RELEASE-53.md](RELEASE-53.md) |
