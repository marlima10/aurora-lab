from pathlib import Path
import os,secrets,json,shutil
R=Path('/srv/auroralab');private=R/'secrets/wger-test';data=R/'data/wger-test'
os.umask(0o077);private.mkdir(exist_ok=True,mode=0o700);data.mkdir(exist_ok=True,mode=0o700)
p=private/'config.json'
cfg=json.loads(p.read_text()) if p.exists() else {'databasePassword':secrets.token_hex(24),'proxySecret':secrets.token_urlsafe(48),'djangoSecret':secrets.token_urlsafe(64)}
p.write_text(json.dumps(cfg));p.chmod(0o600)
origin='https://auroraserver.tail7d26f7.ts.net:8444'
db={'POSTGRES_USER':'wger','POSTGRES_PASSWORD':cfg['databasePassword'],'POSTGRES_DB':'wger_test','PGPASSWORD':cfg['databasePassword']}
app={'DJANGO_SETTINGS_MODULE':'aurora_settings','SECRET_KEY':cfg['djangoSecret'],'DJANGO_DB_ENGINE':'django.db.backends.postgresql','DJANGO_DB_DATABASE':'wger_test','DJANGO_DB_USER':'wger','DJANGO_DB_PASSWORD':cfg['databasePassword'],'DJANGO_DB_HOST':'db','DJANGO_DB_PORT':'5432','SITE_URL':origin,'TIME_ZONE':'America/Sao_Paulo','TZ':'America/Sao_Paulo','DJANGO_DEBUG':'False','DJANGO_CLEAR_STATIC_FIRST':'False','WGER_USE_GUNICORN':'True','USE_CELERY':'False','ALLOW_REGISTRATION':'False','ALLOW_GUEST_USERS':'False','ENABLE_EMAIL':'False','SYNC_EXERCISES_ON_STARTUP':'False','SYNC_EXERCISES_CELERY':'False','DOWNLOAD_EXERCISE_IMAGES_ON_STARTUP':'False','LOAD_ONLINE_FIXTURES_ON_STARTUP':'False','DOWNLOAD_INGREDIENTS_FROM':'None','AURORA_PROXY_SECRET':cfg['proxySecret'],'GUNICORN_CMD_ARGS':'--workers 2 --threads 2 --timeout 120 --access-logfile /dev/null --control-socket /tmp/gunicorn-control.sock'}
for name,values in [('database.env',db),('app.env',app)]:
 f=private/name;f.write_text(''.join(k+'='+v+'\n' for k,v in values.items()));f.chmod(0o600)
for name in ('postgres','import','backups','static','media'):
 d=data/name;d.mkdir(exist_ok=True,mode=0o700)
 if name in ('import','static','media'):os.chown(d,1000,1000);d.chmod(0o755 if name!='import' else 0o700)
for name in ('source-opengym.json','catalogue.json'):
 source=R/'deploy-state/wger-test/import-source'/name;dest=data/'import'/name
 if not dest.exists():shutil.copyfile(source,dest)
 os.chown(dest,1000,1000);dest.chmod(0o600)
gateway=(R/'docker/server/wger-test/gateway.template').read_text().replace('__HOST__','auroraserver.tail7d26f7.ts.net').replace('__SECRET__',cfg['proxySecret'])
f=private/'gateway.conf';f.write_text(gateway);f.chmod(0o600);os.chown(f,101,101)
print('wger de avaliação preparado; credenciais existentes preservadas.')
