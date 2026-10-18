# Garmin → openGym

Conector comunitário `garminconnect` 0.3.19 em container separado. Não é um plugin oficial do openGym ou da Garmin. Não requer criação de aplicativo Strava. Mudanças no login Garmin podem interromper o acesso.

## Uso

Conecte o Tailscale, entre no openGym e abra o botão **Garmin → openGym** no portal ou `/garmin/` no mesmo endereço HTTPS do openGym. Use o mesmo navegador da sessão openGym. Informe e-mail e senha Garmin apenas nessa página privada; se solicitado, informe o código de verificação dentro de três minutos.

Escolha até um ano por consulta, carregue a prévia e selecione as atividades. Só o botão **Importar selecionadas** grava no openGym. Até 1.000 atividades recentes são examinadas por consulta; a tela avisa se atingir esse limite. Não há sincronização automática ou envio para Garmin.

Importa resumos de data local, nome, duração e distância (metros convertidos para quilômetros e velocidade canônica em km/h). Não importa séries detalhadas de musculação, repetições, cargas, calorias, frequência cardíaca, mapas ou coordenadas. A duração aparece como resumo cardio neutro, inclusive para musculação; não representa uma série de resistência nem calcula músculos/carga.

IDs Garmin estáveis evitam duplicatas. Um registro persistente também impede recriar uma atividade que já foi importada e depois apagada no openGym. Planos, registros existentes e demais campos são preservados. Escrita usa a API autenticada do openGym com revisão e tentativa de mesclagem em conflitos. Não use restauração manual de um perfil antigo sem avaliar o registro de importações.

## Instalação

Defina `OPENGYM_ORIGIN` no `.env` com o endereço HTTPS privado do openGym. Prepare o volume antes de iniciar:

```sh
install -d -m 700 -o 65534 -g 65534 data/garmin
docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml config --quiet
docker compose -f compose.server.yaml -f compose.power.yaml -f compose.homeassistant.yaml -f compose.opengym.yaml up -d --build --no-deps opengym-garmin opengym-web
```

O template Nginx parte do openGym v1.4.1 e acrescenta `/garmin/`; revisar junto de futuras atualizações upstream. Não publica porta adicional. Container sem root, sistema de arquivos somente leitura e nenhuma capability. A página usa sessão openGym, sem nova chave administrativa; cada perfil possui diretório próprio identificado por hash. POST exige Origin HTTPS configurado para evitar solicitações de outros sites. A API interna não recebe credenciais Garmin.

A senha e código de verificação não são gravados nem registrados em logs; são usados em memória durante o login. Tokens de sessão persistem em `data/garmin/<hash>/tokens/garmin_tokens.json`, com diretórios 700 e arquivos 600. A prévia permanece em memória por 30 minutos, até reiniciar ou desconectar. O registro de IDs e uma cópia do perfil anterior à última importação também ficam no volume privado, incluído no backup. **Desconectar** apaga o token local; cópias anteriores de backup podem ainda contê-lo. Não remove atividades do Garmin nem as já importadas.

## Validação

```sh
python -m unittest discover -s docker/server/garmin -p 'test_*.py' -v
```

Testes usam dados sintéticos e API simulada. Login real e primeira importação dependem do titular da conta e devem ser confirmados separadamente. Nenhum dado pessoal é necessário para testar o código.
