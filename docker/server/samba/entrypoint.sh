#!/bin/sh
set -eu
id rafael >/dev/null 2>&1 || useradd -M -u 1000 -s /usr/sbin/nologin rafael
mkdir -p /shares/prints /run/samba
chmod 755 /var/lib/samba
chown rafael:rafael /shares/prints
if [ ! -s /var/lib/samba/private/passdb.tdb ]; then
    password=$(cat /run/secrets/samba-users.txt)
    [ -n "$password" ] || { echo 'Senha Samba ausente'; exit 1; }
    printf '%s\n%s\n' "$password" "$password" | smbpasswd -s -a rafael >/dev/null
    unset password
fi
exec smbd --foreground --no-process-group --debug-stdout
