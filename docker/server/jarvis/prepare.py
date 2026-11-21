"""Prepare private connector configs without activating Compose or changing app data."""
import argparse
import json
import os
import secrets
from pathlib import Path


def private(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.new')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temp.chmod(0o600)
    if hasattr(os, 'chown'):
        os.chown(temp, 65534, 65534)
    temp.replace(path)


def prepare(root):
    root = Path(root).resolve()
    sso = json.loads((root / 'secrets/sso/apps.json').read_text())
    env = dict(line.split('=', 1) for line in (root / '.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
    origin = 'https://' + env['AURORA_PRIVATE_HOST'].strip('"\'')
    dest = root / 'secrets/jarvis'
    if dest.is_symlink():
        raise ValueError('Diretório privado não pode ser link.')
    dest.mkdir(parents=True, exist_ok=True)
    dest.chmod(0o700)
    old = json.loads((dest/'api.json').read_text()) if (dest/'api.json').exists() else {}
    roles = ('engine', 'whisper', 'piper', 'fitness', 'finance', 'food', 'print', 'research')
    services = {role: {'token': old.get('services', {}).get(role, {}).get('token') or secrets.token_urlsafe(48)} for role in roles}
    private(dest/'api.json', {'origin': origin, 'services': services})
    for role in roles:
        value = dict(services[role])
        app = {'fitness': 'opengym', 'finance': 'actual', 'food': 'mealie'}.get(role)
        if app:
            value |= sso[app]
        if role == 'print':
            value['apps'] = {app: sso[app] for app in ('manyfold', 'octoprint')}
        prior = json.loads((dest/(role+'.json')).read_text()) if (dest/(role+'.json')).exists() else {}
        # Never discard explicit budget or encryption mappings on re-prepare.
        for key in ('budgets', 'encryptionPasswords'):
            if key in prior:
                value[key] = prior[key]
        private(dest/(role+'.json'), value)
    for name in ('app', 'finance', 'models', 'ollama'):
        path = root/'data/jarvis'/name
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o700)
        if hasattr(os, 'chown'):
            os.chown(path, 65534, 65534)
    return {'prepared': True, 'services': len(roles), 'activated': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().root)))
