# Workout Cool: origem do ambiente de avaliação

- Projeto oficial: https://github.com/Snouzy/workout-cool
- Commit fixado: `d52f9f62d2a5fcbb78d67a95dc8763f9a34dbf9e` (package.json 1.3.2).
- Licença upstream: MIT, mantida na imagem; os adaptadores AuroraLAB ficam neste diretório.
- Node 22 Bookworm, PostgreSQL 15 Bookworm e Nginx Alpine fixados por digest nos arquivos de implantação.
- Nenhum dado, chave ou banco pessoal integra o contexto de compilação.
- `patch.mjs` recusa trechos upstream inesperados; atualizar o commit exige revisar os adaptadores e reconstruir.
