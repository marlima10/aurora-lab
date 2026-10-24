"""Prepare private SSO artifacts without changing Compose, native app data or systemd.

The root operator supplies an explicit native-identity mapping. This is a preparation
step, not an installer: native adapters must pass their probes before publication.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
from urllib.parse import urlsplit

from render_gateway import render
from store import ADMIN_EMAIL, APPS, Store


def write_private(path, value, uid=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.new')
    with temporary.open('x', encoding='utf-8') as output:
        output.write(value)
    temporary.chmod(0o600)
    if hasattr(os, 'chown'):
        os.chown(temporary, uid, uid)
    temporary.replace(path)


def prepare(root, mapping_file):
    root = Path(root).resolve()
    mapping = json.loads(Path(mapping_file).read_text())
    values = dict(line.split('=', 1) for line in (root / '.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
    parsed = urlsplit(values.get('OPENGYM_ORIGIN', '').strip('\"\''))
    if parsed.scheme != 'https' or parsed.port != 8081 or not parsed.hostname or not parsed.hostname.endswith('.ts.net') or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        raise ValueError('Configure a origem HTTPS privada existente do openGym.')
    origin = 'https://' + parsed.hostname
    native = mapping['apps']
    if set(native) != set(APPS) - {'portal'}:
        raise ValueError('Forneça o inventário explícito dos oito aplicativos.')
    grants = mapping['admin_grants']
    if set(grants) != set(native):
        raise ValueError('Confirme as oito identidades internas para o administrador inicial.')
    for app, identity in grants.items():
        if identity not in native[app]['identities']:
            raise ValueError('Identidade administrativa ausente do inventário: ' + app)
    local = grants['cockpit']
    if local == 'root' or not re.fullmatch('[a-z_][a-z0-9_-]{0,31}', local):
        raise ValueError('Use uma conta Debian existente sem mapear root.')
    private = root / 'secrets/sso'
    data = root / 'data/auth'
    if private.is_symlink() or data.is_symlink():
        raise ValueError('Diretórios privados não podem ser links simbólicos.')
    private.mkdir(parents=True, exist_ok=True)
    private.chmod(0o700)
    data.mkdir(parents=True, exist_ok=True)
    data.chmod(0o700)
    config_path = private / 'apps.json'
    existing = json.loads(config_path.read_text()) if config_path.exists() else {}
    result = {}
    initial = json.loads((root / 'secrets/apps23-initial.json').read_text())
    for app, inventory in native.items():
        prior = existing.get(app, {})
        config = {'ready': False, 'identities': dict(inventory['identities']), 'labels': inventory.get('labels', {})}
        if app == 'cockpit':
            config['local_user'] = local
        else:
            config['secret'] = prior.get('secret') or (initial['actual']['password'] if app == 'actual' else secrets.token_urlsafe(48))
            if len(config['secret']) < 32 or not re.fullmatch('[A-Za-z0-9_-]+', config['secret']):
                raise ValueError('Configure a credencial privada válida: ' + app)
            if app != 'actual':
                env = 'AURORA_SSO_SECRET=' + config['secret'] + '\n'
                if app == 'mealie':
                    env = 'REVERSE_PROXY_AUTH_SECRET=' + config['secret'] + '\n'
                write_private(private / (app + '.env'), env)
        # Re-preparing does not revoke a verified integration whose inventory and secret match.
        if prior and all(prior.get(k) == v for k, v in config.items() if k != 'ready'):
            config['ready'] = bool(prior.get('ready'))
        result[app] = config
    result['_power_secret'] = (root / 'secrets/power-admin.key').read_text().strip()
    write_private(config_path, json.dumps(result, indent=2), uid=65534)
    write_private(private / 'gateway.conf', render(origin))
    # Native monitor requests carry a separate private secret; a direct LAN request cannot bypass SSO.
    monitor_key_path = private / 'monitor.key'
    monitor_key = monitor_key_path.read_text().strip() if monitor_key_path.exists() else secrets.token_urlsafe(48)
    if not re.fullmatch('[A-Za-z0-9_-]{32,}', monitor_key):
        raise ValueError('Segredo do monitor inválido.')
    if not monitor_key_path.exists():
        write_private(monitor_key_path, monitor_key + '\n', uid=65534)
    elif hasattr(os, 'chown'):
        os.chown(monitor_key_path, 65534, 65534)
    nginx = (root / 'docker/server/nginx.conf').read_text()
    nginx = nginx.replace('server {\n', 'server {\n    proxy_set_header X-Aurora-Monitor-Secret "' + monitor_key + '";\n', 1)
    write_private(private / 'portal-nginx.conf', nginx)
    store = Store(data / 'auth.sqlite3')
    key_path = private / 'admin-initial.key'
    with store.db() as db:
        initialized = bool(db.execute('SELECT 1 FROM users LIMIT 1').fetchone())
    if not initialized:
        if key_path.exists():
            raise ValueError('Chave inicial existente sem banco; revise antes de recuperar.')
        key = store.initialize()
        with store.db() as db:
            for app, identity in grants.items():
                db.execute('INSERT INTO grants VALUES(?,?,?)', (ADMIN_EMAIL, app, identity))
            store.audit(db, 'local-bootstrap', 'map-native-identities', ADMIN_EMAIL)
        write_private(key_path, ADMIN_EMAIL + '\n' + key + '\n')
    elif not key_path.exists():
        raise ValueError('Banco já existe sem registro inicial; não rotacionar automaticamente.')
    if hasattr(os, 'chown'):
        os.chown(data, 65534, 65534)
        os.chown(data / 'auth.sqlite3', 65534, 65534)
    config = '[WebService]\nOrigins = ' + origin + ':9090 wss://' + parsed.hostname + ':9090\nProtocolHeader = X-Forwarded-Proto\nAllowUnencrypted = true\n'
    write_private(private / 'cockpit/cockpit.conf', config)
    for path in (Path(__file__).parent / 'host').iterdir():
        write_private(private / 'host' / path.name, path.read_text().replace('@LOCAL_USER@', local))
    return {'prepared': True, 'native_identities_mapped': 8, 'admin_email': ADMIN_EMAIL, 'key_file': str(key_path),
            'apps_validated': sorted(app for app in native if result[app]['ready']), 'production_configuration_changed': False,
            'notice': 'Não ativa SSO; valide adaptadores e siga o plano de migração/retorno.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--mappings', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Execute como root para preparar os arquivos privados.')
    os.umask(0o077)
    print(json.dumps(prepare(args.root, args.mappings)))
