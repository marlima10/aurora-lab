"""Build a fixed upstream HomeBoard revision without placing upstream sources in Git."""
import argparse,hashlib,json,os,pathlib,subprocess,tarfile,urllib.request
p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
assert os.geteuid()==0,'Execute como root.'
r=pathlib.Path(__file__).resolve().parents[3]
lock=json.loads(pathlib.Path(__file__).with_name('source.lock.json').read_text())
stage=r/'deploy-state/homeboard';stage.mkdir(parents=True,exist_ok=True,mode=0o700)
archive=stage/(lock['commit']+'.tar.gz')
if not archive.exists():
 with urllib.request.urlopen(lock['url'],timeout=180) as res:archive.write_bytes(res.read())
assert hashlib.sha256(archive.read_bytes()).hexdigest()==lock['sha256'],'HomeBoard SHA-256 divergente'
source=stage/('HomeBoard-'+lock['commit'])
if not source.exists():
 with tarfile.open(archive) as t:
  for m in t.getmembers():
   q=pathlib.PurePosixPath(m.name)
   assert not q.is_absolute() and '..' not in q.parts and q.parts[0]==source.name
  t.extractall(stage,filter='data')
for name in ('data/homeboard','data/homeboard-photos'):
 folder=r/name;folder.mkdir(parents=True,exist_ok=True,mode=0o700);os.chown(folder,1000,1000)
settings=r/'data/homeboard/settings.json'
if not settings.exists():
 settings.write_text(json.dumps({'name':'AuroraLAB','timezone':'America/Sao_Paulo','theme':'aurora','weatherEnabled':False,'newsEnabled':False}));settings.chmod(0o600);os.chown(settings,1000,1000)
if a.build:
 subprocess.run(['docker','build','--build-arg','HOMEBOARD_COMMIT='+lock['commit'],'-t',lock['image'],str(source)],check=True)
print('Fonte HomeBoard conferida: '+lock['commit'])
