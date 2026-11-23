# AuroraLAB 49.0.0 — galeria e sequência de fundos

## Resultado

O MagicMirror agora permite enviar imagens pelo painel administrativo, selecionar as fotos do fundo e alterná-las automaticamente com intervalo configurável. O pôr do sol atual permanece disponível e é o padrão inicial; nenhuma foto de teste é instalada na galeria pessoal.

## Interface e uso

Nova seção **Imagens de fundo** em Configurar tela, com miniaturas, seleção, envio de vários arquivos e atualização da galeria. Modos: pôr do sol original, imagem fixa e sequência. Intervalo de 15 a 3.600 segundos, com padrão de 60. As fotos seguem a ordem da seleção, e as preferências ficam salvas no servidor.

As imagens enviadas ficam em data/mirror/backgrounds e podem também ser copiadas diretamente a essa pasta com permissão no servidor. A galeria reconhece JPG/PNG/WebP válidos; não duplica conteúdo repetido. Desmarcar exclui a foto da sequência, sem apagar o arquivo. A pasta integra o backup existente. [Instruções](MAGICMIRROR.md#imagens-de-fundo).

## Comportamento e consumo

A próxima imagem carrega antes da troca. Respostas antigas são ignoradas quando a seleção muda. O temporizador pausa quando o documento está oculto e retoma ao voltar. Imagens removidas ou indisponíveis não limpam a tela; há tentativa das demais e reserva no fundo original. Escurecimento e transparência existentes continuam valendo.

Originais preservados no disco privado. Derivados para exibição são JPEG sem EXIF, com dimensão reduzida para tela e miniaturas leves. A decodificação JPEG usa redução antecipada para lidar com fotos de celular de alta resolução. Pillow 13.0.0 fixado na imagem; limite da API Mirror passa de 128 para 512 MiB, com processamento de imagem serializado pela galeria. Nenhum serviço de IA ou nova porta pública é utilizado.

## Limites e revisão de acesso

Até 50 imagens, 12 MiB e 50 megapixels por arquivo; somente JPG, PNG ou WebP não animados. A extensão não substitui a validação do conteúdo. Caminhos arbitrários, links simbólicos, SVG, conteúdo inválido e imagens acima dos limites não são servidos. Os identificadores de imagem são hashes SHA-256.

Listar e enviar exige administrador. Upload binário exige sessão, CSRF e origem exata antes da leitura do corpo; aceita um envio por vez na fachada. JSON comum conserva o limite de 8 KiB. Consultar uma imagem exige sessão com grant do portal; fotos não são publicadas anonimamente ou em cache de service worker. Nenhuma permissão nativa do Jarvis, Cockpit ou outros aplicativos é ampliada.

## Validação

26 testes Mirror aprovados em Linux, incluindo upload, deduplicação, permanência após reabrir, pasta manual, JPEG normalizado/miniatura, foto JPEG de 48 MP, rejeição de formatos/animação/tamanho excessivo, links simbólicos, seleção e migração de preferências. 31 testes de autenticação aprovados em Linux, incluindo os limites e a proteção do upload/lista.

Quatro verificações Node: preferências/permissões, calendário, PWA e sequência de fundos. A sequência verifica ordem, pré-carregamento, intervalo, pausa em segundo plano, cancelamento de cargas antigas, falha e retorno ao fundo original.

Ensaio pelo navegador com duas imagens sintéticas: envio múltiplo pelo seletor de arquivos, miniaturas carregadas, seleção e intervalo salvos, reabertura preservada e troca observada entre os dois fundos. Um problema de vínculo dos temporizadores nativos encontrado nesse ensaio foi corrigido antes da publicação. Conferência da galeria em 820 px sem rolagem horizontal. Não se afirma teste em aparelho físico. Nenhuma foto pessoal foi usada como massa de testes.

## Publicação, implantação e recuperação

Branch rafael → PR oficial → merge em main → release v49.0.0 e implantação dos arquivos dessa tag. Atualizar somente magicmirror, mirror-api e auth, mantendo COMPOSE_FILE, domínio, segredos, agenda, clima, metas, perfis e aplicativos.

Backup novo com restauração isolada e cópia privada externa antes e depois. Snapshot consistente anterior do SQLite Mirror para retorno, porque o esquema anterior não reconhece as novas preferências. Os originais/derivados da galeria acompanham o backup da pasta Mirror; não entram no Git nem no contexto de construção. Retirar containers, dados sintéticos e túnel da prévia ao concluir. Comprovantes de implantação e hashes ficam no relatório privado.
