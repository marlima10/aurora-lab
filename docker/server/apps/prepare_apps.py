"""Idempotent local preparation. No downloads, application passwords or env contents on stdout."""
import argparse
import json
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit

OVERLAYS = ['compose.manyfold.yaml','compose.mealie.yaml','compose.actual.yaml']

def prepare(root):
    root=Path(root).resolve();env=root/'.env'
    lines=env.read_text(encoding='utf-8').splitlines()
    values={row.split('=',1)[0]:row.split('=',1)[1].strip('\"\'') for row in lines if '=' in row and not row.startswith('#')}
    origin=urlsplit(values.get('OPENGYM_ORIGIN',''))
    if origin.scheme!='https' or not origin.hostname or not origin.hostname.endswith('.ts.net') or origin.username or origin.password or origin.port!=8081 or origin.path not in ('','/') or origin.query or origin.fragment:raise ValueError('Origem HTTPS privada invalida')
    if not values.get('COMPOSE_FILE'):raise ValueError('COMPOSE_FILE existente obrigatorio')
    secret_dir=root/'secrets';secret_dir.mkdir(exist_ok=True)
    creds=secret_dir/'apps23-initial.json'
    if not creds.exists():
        for app in ('manyfold','mealie','actual'):
            folder=root/'data'/app
            if folder.exists() and any(folder.iterdir()):raise ValueError('Dados existentes sem credenciais de preparacao: nao sobrescrever')
        data={app:{'username':'rafael','email':'rafael@auroraserver.local','password':secrets.token_urlsafe(30)} for app in ('manyfold','mealie','actual')}
        creds.write_text(json.dumps(data,indent=2),encoding='utf-8');creds.chmod(0o600)
    manyfold=secret_dir/'manyfold.env'
    if not manyfold.exists():manyfold.write_text('SECRET_KEY_BASE='+secrets.token_hex(64)+'\n',encoding='utf-8');manyfold.chmod(0o600)
    for name in ('manyfold','manyfold/config','manyfold/library','manyfold/plugins','manyfold-redis','mealie','actual'):
        folder=root/'data'/name;folder.mkdir(parents=True,exist_ok=True);folder.chmod(0o700);os.chown(folder,1000,1000)
    compose=values['COMPOSE_FILE'].split(':')
    updates={'COMPOSE_FILE':':'.join(dict.fromkeys(compose+OVERLAYS)),'AURORA_PRIVATE_HOST':origin.hostname,'MEALIE_ORIGIN':f'https://{origin.hostname}:9925','ACTUAL_ORIGIN':f'https://{origin.hostname}:5006'}
    output=[]
    for row in lines:
        key=row.split('=',1)[0]
        if key in updates:output.append(key+'='+updates.pop(key))
        else:output.append(row)
    output.extend(key+'='+value for key,value in updates.items())
    temporary=env.with_suffix('.apps.tmp');temporary.write_text('\n'.join(output)+'\n',encoding='utf-8');temporary.chmod(0o600);temporary.replace(env)
    return {'prepared':True,'overlays':OVERLAYS,'private_host':origin.hostname,'credentials':'secrets/apps23-initial.json'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);args=parser.parse_args()
    if os.geteuid()!=0:raise SystemExit('Execute como root.')
    os.umask(0o077)
    print(json.dumps(prepare(args.root)))
