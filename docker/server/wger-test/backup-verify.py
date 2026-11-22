"""Dump the evaluation DB and verify it in a disposable offline PostgreSQL."""
import subprocess,os,time,json,hashlib,secrets
from pathlib import Path
os.umask(0o077)
root=Path('/srv/auroralab');os.chdir(root)
c=['docker','compose','-p','auroralab-wger-test','-f','compose.wger-test.yaml']
out=root/'data/wger-test/backups';out.mkdir(parents=True,exist_ok=True)
stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime());dump=out/('wger-test-'+stamp+'.dump')
sql="SELECT json_build_object('workouts',(SELECT count(*) FROM manager_workoutsession),'sets',(SELECT count(*) FROM manager_workoutlog),'routines',(SELECT count(*) FROM manager_routine),'weights',(SELECT count(*) FROM measurements_measurement),'snapshots',(SELECT count(*) FROM aurora_import_snapshot));"
live=json.loads(subprocess.run(c+['exec','-T','db','psql','-U','wger','-d','wger_test','-Atc',sql],capture_output=True,text=True,check=True).stdout)
with dump.open('wb') as f:subprocess.run(c+['exec','-T','db','pg_dump','-U','wger','-d','wger_test','-Fc'],stdout=f,stderr=subprocess.PIPE,check=True)
hash=hashlib.sha256(dump.read_bytes()).hexdigest();dump.with_suffix('.dump.sha256').write_text(hash+'  '+dump.name+'\n')
image='postgres:15-bookworm@sha256:8180c3e1b9b603d2988f937dfbe51008bad5c4b07c77f35119695c027a7315ab'
name='auroralab-wger-restore-'+secrets.token_hex(5)
env=dict(os.environ,POSTGRES_PASSWORD=secrets.token_urlsafe(32))
def run(args,**kw):return subprocess.run(args,capture_output=True,check=True,**kw)
try:
 run(['docker','run','-d','--name',name,'--network','none','--memory','512m','--tmpfs','/var/lib/postgresql/data:size=512m','-e','POSTGRES_PASSWORD',image],env=env)
 for _ in range(40):
  if subprocess.run(['docker','exec',name,'pg_isready','-U','postgres'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
  time.sleep(1)
 else:raise RuntimeError('Offline restore database did not start')
 with dump.open('rb') as f:subprocess.run(['docker','exec','-i',name,'pg_restore','-U','postgres','-d','postgres','--no-owner','--no-privileges','--exit-on-error'],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 counts=json.loads(run(['docker','exec',name,'psql','-U','postgres','-d','postgres','-Atc',sql],text=True).stdout)
 assert counts==live, 'Restored counts differ from the pre-dump database; retry without concurrent changes.'
 result={'verified':True,'archive':dump.name,'sha256':hash,'restored':counts,'network':'none','timestamp':stamp}
 dump.with_suffix('.restore.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
