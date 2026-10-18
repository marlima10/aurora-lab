#!/bin/sh
# Preparar somente diretorios/arquivos ausentes; preservar dados existentes.
set -eu
cd "$(dirname "$0")/../.."

fail() {
    printf '%s\n' "$1" >&2
    exit 1
}

# Bind mounts ausentes podem ser criados como diretorios pelo Docker.
# rmdir nunca apaga conteudo: diretorios ocupados/com dados exigem revisao.
prepare_file_path() {
    file_path=$1
    [ ! -L "$file_path" ] || fail "Caminho de arquivo e um link simbolico; revise: $file_path"
    if [ -d "$file_path" ]; then
        if ! rmdir -- "$file_path" 2>/dev/null; then
            fail "Esperado arquivo em $file_path, mas existe um diretorio com conteudo ou em uso. Pare o servico que o monta e revise o caminho; nenhum conteudo foi removido."
        fi
        printf 'Diretorio vazio removido para preparar arquivo: %s\n' "$file_path"
    elif [ -e "$file_path" ] && [ ! -f "$file_path" ]; then
        fail "Esperado arquivo regular; revise: $file_path"
    fi
}

[ "$(id -u)" -eq 0 ] || fail 'Execute com sudo sh docker/server/prepare.sh'
umask 077
[ ! -L secrets ] || fail 'O diretorio secrets e um link simbolico; revise antes de preparar.'
mkdir -p data/fitness data/octoprint data/prints data/samba data/monitor data/backup-status data/tailscale secrets backups

# Validar antes de alterar permissoes ou solicitar a senha.
prepare_file_path .env
prepare_file_path secrets/octoprint-api.key
prepare_file_path secrets/samba-users.txt

chmod 700 secrets backups data/tailscale
chmod 755 data/monitor data/backup-status
chown 65534:65534 data/monitor
[ -f .env ] || cp .env.example .env
chmod 600 .env
[ -f secrets/octoprint-api.key ] || touch secrets/octoprint-api.key
# Monitor e executado como nobody; a pasta secrets permanece restrita no host.
chmod 644 secrets/octoprint-api.key

if [ ! -s secrets/samba-users.txt ] && [ ! -s data/samba/private/passdb.tdb ]; then
    [ -t 0 ] || fail 'Senha Samba ausente. Execute a preparacao em um terminal interativo; a senha nao sera exibida.'
    terminal_state=$(stty -g)
    trap 'stty "$terminal_state" 2>/dev/null || true' EXIT
    trap 'exit 1' HUP INT TERM
    stty -echo
    printf 'Defina a senha Samba para o usuario: '
    if ! IFS= read -r samba_password; then
        printf '\n'
        fail 'Nao foi possivel ler a senha; preparacao interrompida.'
    fi
    stty "$terminal_state"
    printf '\n'
    [ -n "$samba_password" ] || fail 'Senha vazia; preparacao interrompida.'
    printf '%s\n' "$samba_password" > secrets/samba-users.txt
    unset samba_password
    trap - EXIT HUP INT TERM
elif [ ! -f secrets/samba-users.txt ]; then
    # A base Samba existente ja guarda a senha; manter o bind como arquivo.
    touch secrets/samba-users.txt
fi
chmod 600 secrets/samba-users.txt

echo 'Preparacao concluida. Revise SERVER_IP em .env antes de iniciar.'
