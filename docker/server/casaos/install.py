"""Install pinned official CasaOS packages without replacing/restarting Docker."""
import argparse,datetime,hashlib,json,os,pathlib,shutil,subprocess,tarfile,urllib.request

parser=argparse.ArgumentParser()
parser.add_argument('--stage',default='/srv/auroralab/deploy-state/casaos-stage')
parser.add_argument('--install',action='store_true')
args=parser.parse_args()
assert os.geteuid()==0,'Execute como root.'
assert os.uname().machine=='x86_64','Pacotes fixados para amd64.'
stage=pathlib.Path(args.stage).resolve();stage.mkdir(parents=True,exist_ok=True)
lock=pathlib.Path(__file__).with_name('packages.lock.json')
items=json.loads(lock.read_text())
build=stage/'build'
for item in items:
    archive=stage/item['file']
    if not archive.exists():
        with urllib.request.urlopen(item['url'],timeout=180) as response:archive.write_bytes(response.read())
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==item['sha256'],item['file']+' SHA-256 divergente'
    with tarfile.open(archive) as source:source.extractall(stage,filter='data')
print('Nove pacotes oficiais conferidos.',flush=True)
if not args.install:raise SystemExit(0)
assert not pathlib.Path('/usr/bin/casaos').exists(),'Instalacao existente: revisar atualizacao em separado.'
api=subprocess.check_output(['curl','--unix-socket','/var/run/docker.sock','-fsS','http://localhost/v1.43/containers/json'],text=True)
json.loads(api)
before=json.loads(subprocess.check_output(['docker','inspect']+subprocess.check_output(['docker','ps','-q'],text=True).split(),text=True))
before={c['Name']:c['State']['StartedAt'] for c in before}
backup=stage/('host-before-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.tar.gz')
with tarfile.open(backup,'w:gz') as target:
    for name in ('etc/samba','etc/udevil','etc/docker','etc/systemd/system/docker.service.d'):
        path=pathlib.Path('/')/name
        if path.exists():target.add(path,arcname=name)
backup.chmod(0o600)
subprocess.run(['systemctl','mask','smbd.service','nmbd.service','samba-ad-dc.service'],check=True)
env=os.environ.copy();env['DEBIAN_FRONTEND']='noninteractive'
subprocess.run(['apt-get','update'],check=True,env=env)
subprocess.run(['apt-get','install','-y','--no-install-recommends','curl','wget','smartmontools','parted','ntfs-3g','net-tools','udevil','samba','cifs-utils','mergerfs','unzip','rclone'],check=True,env=env)
# Samba stays in the existing Docker container, on port 445.
subprocess.run(['systemctl','stop','smbd.service','nmbd.service','samba-ad-dc.service'],check=False)
subprocess.run(['cp','-a',str(build/'sysroot')+'/.','/'],check=True)
manifest=[]
for path in (build/'sysroot').rglob('*'):
    if path.is_file():manifest.append('/'+str(path.relative_to(build/'sysroot')))
pathlib.Path('/var/lib/casaos').mkdir(exist_ok=True)
pathlib.Path('/var/lib/casaos/aurora-install-manifest.json').write_text(json.dumps(manifest,indent=2))
for service in ('gateway','user-service','casaos','local-storage','message-bus','app-management'):
    setup=build/'scripts/setup/service.d'/service/'debian'/('setup-'+service+'.sh')
    subprocess.run(['bash',str(setup)],check=True,env=env)
# Reserve port 81; preserve portal 80, camera 8080 and existing services.
gateway=pathlib.Path('/etc/casaos/gateway.ini')
gateway.write_text('[common]\nruntimepath=/var/run/casaos\n\n[gateway]\nport=81\n')
local=pathlib.Path('/etc/casaos/local-storage.conf')
text=local.read_text().replace('USBAutoMount=','USBAutoMount=false')
local.write_text(text)
# Only CasaOS vendor store. Extra catalogs can be added deliberately from its UI.
apps=pathlib.Path('/etc/casaos/app-management.conf')
text=apps.read_text();text='\n'.join(line for line in text.splitlines() if 'bigbeartechworld' not in line)+'\n';apps.write_text(text)
subprocess.run(['bash',str(build/'scripts/setup/script.d/99-setup-appstore.sh')],check=True,env=env)
pathlib.Path('/DATA/AppData').mkdir(parents=True,exist_ok=True)
from rclone import install_rclone
install_rclone(lock.with_name('rclone.lock.json'),stage)
services=['casaos-gateway','casaos-message-bus','casaos-user-service','rclone','casaos','casaos-local-storage','casaos-app-management']
subprocess.run(['systemctl','daemon-reload'],check=True)
for service in services:
    subprocess.run(['systemctl','enable','--now',service],check=True)
after=json.loads(subprocess.check_output(['docker','inspect']+subprocess.check_output(['docker','ps','-q'],text=True).split(),text=True))
after={c['Name']:c['State']['StartedAt'] for c in after}
assert all(after.get(k)==v for k,v in before.items()),'Um container existente reiniciou; revisar.'
record={'version':'0.4.15','port':81,'host_backup':str(backup),'docker_containers_unchanged':True,'docker_api':'1.43 supported without changes','samba_host_services':'masked; SMB retained in Docker','packages':items}
(stage/'installed.json').write_text(json.dumps(record,indent=2))
for service in services:
    assert subprocess.check_output(['systemctl','is-active',service],text=True).strip()=='active',service
print('CasaOS instalado; containers existentes preservados.',flush=True)
