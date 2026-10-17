#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
[ "$(id -u)" -eq 0 ] || { echo 'Execute com sudo.'; exit 1; }
mkdir -p data/power secrets
chmod 700 data/power secrets
if [ ! -s secrets/power-admin.key ]; then
    umask 077
    head -c 32 /dev/urandom | base64 > secrets/power-admin.key
fi
chmod 600 secrets/power-admin.key
echo 'Preparacao concluida. Chave administrativa em secrets/power-admin.key; nao publicar.'
