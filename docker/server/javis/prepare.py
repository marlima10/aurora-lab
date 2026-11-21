"""Create private connector configuration; never prints or rotates existing secrets."""
import json
import os
from pathlib import Path
import secrets
import sqlite3

OWNER = 'aurora@server.local'


def write(path, data, uid=65534):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(raw)
    path.chmod(0o600)
    os.chown(path, uid, uid)


def prepare(root):
    os.umask(0o077)
    root = Path(root).resolve()
    private = root/'secrets/javis'
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    apps_path = root/'secrets/sso/apps.json'
    apps = json.loads(apps_path.read_text())
    for key in ('_javis_proxy_secret', '_javis_connector_secret'):
        apps[key] = apps.get(key) or secrets.token_urlsafe(48)
    write(apps_path, apps)
    existing = json.loads((private/'mcp.json').read_text()) if (private/'mcp.json').exists() else {}
    tokens = {role: existing.get('connectors', {}).get(role) or secrets.token_urlsafe(48) for role in ('fitness', 'finance', 'food', 'print')}
    cfg = {'token': existing.get('token') or secrets.token_urlsafe(48), 'authToken': apps['_javis_connector_secret'], 'connectors': tokens}
    write(private/'mcp.json', cfg)
    write(private/'bootstrap.json', {'token': cfg['token']}, 10001)
    write(private/'proxy.json', {'owner': OWNER, 'secret': apps['_javis_proxy_secret']}, 10001)
    for role, app in [('fitness', 'opengym'), ('food', 'mealie'), ('finance', 'actual')]:
        native = dict(apps[app])
        if role == 'finance' and (private/'finance.json').exists():
            previous = json.loads((private/'finance.json').read_text())
            for key in ('budgets', 'encryptionPasswords'):
                if key in previous:
                    native[key] = previous[key]
        write(private/(role+'.json'), dict(native, token=tokens[role]))
    write(private/'print.json', {'token': tokens['print'], 'apps': {app: apps[app] for app in ('manyfold', 'octoprint')}})
    control = private/'admin.env'
    if not control.exists():
        write(control, 'JAVIS_ADMIN_USER='+OWNER+'\nJAVIS_ADMIN_PASSWORD='+secrets.token_urlsafe(64)+'\n', 10001)
    for name in ('app', 'brains', 'claude-auth', 'codex-auth'):
        path = root/'data/javis'/name
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chown(path, 10001, 10001)
    cache = root/'data/javis/finance-cache'
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chown(cache, 65534, 65534)
    print('Configurações privadas preparadas; segredos existentes preservados.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='/srv/auroralab')
    prepare(parser.parse_args().root)
