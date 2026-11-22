"""Prepare only the isolated evaluation credentials; never rotates an existing lab."""
from pathlib import Path
import os,secrets,json,re,shutil
R=Path('/srv/auroralab');private=R/'secrets/workoutcool-test';data=R/'data/workoutcool-test'
os.umask(0o077);private.mkdir(exist_ok=True,mode=0o700);data.mkdir(exist_ok=True,mode=0o700)
p=private/'config.json'
cfg=json.loads(p.read_text()) if p.exists() else {'databasePassword':secrets.token_hex(24),'proxySecret':secrets.token_urlsafe(48),'authSecret':secrets.token_urlsafe(48)}
p.write_text(json.dumps(cfg));p.chmod(0o600)
host='auroraserver.tail7d26f7.ts.net';origin='https://'+host+':8444'
db={'POSTGRES_USER':'workoutcool','POSTGRES_PASSWORD':cfg['databasePassword'],'POSTGRES_DB':'workoutcool_test','PGPASSWORD':cfg['databasePassword']}
app={'DATABASE_URL':'postgresql://workoutcool:'+cfg['databasePassword']+'@db:5432/workoutcool_test','BETTER_AUTH_URL':origin,'NEXT_PUBLIC_APP_URL':origin,'BETTER_AUTH_SECRET':cfg['authSecret'],'GOOGLE_CLIENT_ID':'disabled','GOOGLE_CLIENT_SECRET':'disabled','REVENUECAT_SECRET_KEY':'disabled-local-evaluation','STRIPE_SECRET_KEY':'sk_test_disabled_local_evaluation','DEFAULT_BILLING_MODE':'DISABLED','NEXT_PUBLIC_SHOW_ADS':'false','NODE_ENV':'production','NEXT_TELEMETRY_DISABLED':'1','PRISMA_HIDE_UPDATE_MESSAGE':'1','CHECKPOINT_DISABLE':'1','AURORA_LAB_SSO':'1','AURORA_LAB_PROXY_SECRET':cfg['proxySecret'],'AURORA_LAB_USER_ID':'aurora-rafael-lab','TZ':'America/Sao_Paulo'}
for name,values in [('database.env',db),('app.env',app)]:
 f=private/name;f.write_text(''.join(k+'='+v+'\n' for k,v in values.items()));f.chmod(0o600)
for name in ('postgres','import','backups'):(data/name).mkdir(exist_ok=True,mode=0o700)
os.chown(data/'import',10001,10001)
source=R/'deploy-state/workoutcool-test/source-opengym.json';target=data/'import/source-opengym.json'
if not target.exists():shutil.copyfile(source,target)
target.chmod(0o600);os.chown(target,10001,10001)
gateway=(R/'docker/server/workoutcool-test/gateway.template').read_text().replace('__HOST__',host).replace('__SECRET__',cfg['proxySecret'])
f=private/'gateway.conf';f.write_text(gateway);f.chmod(0o600);os.chown(f,101,101)
print('Projeto de avaliação preparado; credenciais existentes preservadas.')
