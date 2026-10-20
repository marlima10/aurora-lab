"""Remove only CasaOS-managed host files. Keep Docker, application containers and /DATA."""
import argparse,datetime as dt,json,os,pathlib,subprocess,tarfile
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[3]
services=['casaos-app-management','casaos-local-storage','casaos','casaos-user-service','casaos-message-bus','casaos-gateway','rclone']
manifest=pathlib.Path('/var/lib/casaos/aurora-install-manifest.json')
if not manifest.exists():raise SystemExit('Manifesto CasaOS ausente. Nenhuma remocao automatica foi feita.')
items=json.loads(manifest.read_text())
files=[]
for name in items:
 q=pathlib.PurePosixPath(name)
 allowed=(q.parent==pathlib.PurePosixPath('/usr/bin') and (q.name.startswith('casaos') or q.name=='appfile2compose')) or (q.parent==pathlib.PurePosixPath('/usr/lib/systemd/system') and (q.name.startswith('casaos') or q.name=='rclone.service')) or name=='/etc/bash_completion.d/casaos-cli-completion'
 if allowed and pathlib.Path(name).is_file():files.append(name)
folders=['/etc/casaos','/var/lib/casaos','/usr/share/casaos','/etc/systemd/system/rclone.service.d']
print(json.dumps({'services':services,'files':files,'folders':folders,'application_data_preserved':'/DATA and all Docker containers/volumes'}))
if not args.apply:raise SystemExit(0)
assert os.geteuid()==0,'Execute como root.'
mounts=subprocess.run(['findmnt','-rn','-t','fuse.rclone'],capture_output=True,text=True)
assert not mounts.stdout.strip(),'Montagens rclone ativas: revisar antes de remover.'
ids=subprocess.check_output(['docker','ps','-q'],text=True).split()
def starts():return {v['Name']:v['State']['StartedAt'] for v in json.loads(subprocess.check_output(['docker','inspect']+ids,text=True))}
before=starts()
stage=r/'deploy-state'/('casaos-removed-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'));stage.mkdir(mode=0o700)
archive=stage/'host-files.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for name in files+folders:
  path=pathlib.Path(name)
  if path.exists():t.add(path,arcname=name.lstrip('/'))
archive.chmod(0o600)
subprocess.run(['systemctl','disable','--now']+[s+'.service' for s in services],check=True)
# Move the proven, dedicated CasaOS paths to a private rollback folder. Never recurse through /DATA.
for name in files+folders:
 source=pathlib.Path(name)
 if source.exists():
  target=stage/'removed'/source.relative_to('/');target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);source.rename(target)
subprocess.run(['systemctl','daemon-reload'],check=True)
assert before==starts(),'Container existente mudou durante a remocao.'
for service in services:
 assert subprocess.run(['systemctl','is-active','--quiet',service]).returncode!=0,service
record={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'rollback':str(stage),'containers_unchanged':True,'preserved':['/DATA','Docker containers','Docker volumes','shared apt packages','rclone CLI binaries']}
(r/'deploy-state/casaos-removed.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))