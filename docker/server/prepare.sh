#!/bin/sh
# Preparar somente diretorios/arquivos ausentes; preservar dados existentes.
set -eu
cd "$(dirname "$0")/../.."
[ "$(id -u)" -eq 0 ] || { echo 'Execute com sudo sh docker/server/prepare.sh'; exit 1; }
mkdir -p data/fitness data/octoprint data/prints data/samba data/monitor data/backup-status data/tailscale secrets backups
chmod 700 secrets backups data/tailscale
chmod 755 data/monitor data/backup-status
chown 65534:65534 data/monitor
[ -f .env ] || cp .env.example .env
chmod 600 .env
if [ ! -f secrets/octoprint-api.key ]; then
    touch secrets/octoprint-api.key
fi
# Monitor e executado como nobody; a pasta secrets permanece restrita no host.
chmod 644 secrets/octoprint-api.key
if [ ! -f secrets/samba-users.txt ]; then
    umask 077
    if [ -s data/samba/private/passdb.tdb ]; then
        touch secrets/samba-users.txt
    else
        printf 'Defina a senha Samba para o usuario rafael: '
        trap 'stty echo 2>/dev/null || true' EXIT HUP INT TERM
        stty -echo
        IFS= read -r samba_password
        stty echo
        printf '\n'
        [ -n "$samba_password" ] || { echo 'Senha vazia; preparacao interrompida.'; exit 1; }
        printf '%s\n' "$samba_password" > secrets/samba-users.txt
        unset samba_password
        trap - EXIT HUP INT TERM
    fi
fi
chmod 600 secrets/samba-users.txt
echo 'Preparacao concluida. Revise SERVER_IP em .env antes de iniciar.'
