"""Prepare Debian Cockpit/PAM behind the existing Docker HTTPS entry point."""
import configparser,datetime as dt,ipaddress,json,os,pathlib,shutil,ssl,subprocess,tarfile,time,urllib.request
root=pathlib.Path(__file__).resolve().parents[3]
assert os.geteuid()==0,'Execute como root.'
state=root/'deploy-state';state.mkdir(exist_ok=True)
def run(args):return subprocess.check_output(args,text=True).strip()
policy_before=run(['/usr/sbin/sshd','-T'])
stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S')
backup=state/('cockpit-local-before-'+stamp+'.tar.gz')
with tarfile.open(backup,'w:gz') as archive:
 for name in ('/etc/cockpit','/etc/systemd/system/cockpit.socket.d'):
  if pathlib.Path(name).exists():archive.add(name,arcname=name.lstrip('/'))
backup.chmod(0o600)
subprocess.run(['systemctl','mask','cockpit.socket'],check=True)
env=os.environ.copy();env['DEBIAN_FRONTEND']='noninteractive'
subprocess.run(['apt-get','update'],check=True,env=env)
subprocess.run(['apt-get','install','-y','--no-install-recommends','cockpit-ws','openssl'],check=True,env=env)
bridge=json.loads(run(['docker','network','inspect','bridge']))[0]['IPAM']['Config'][0]['Gateway']
ipaddress.IPv4Address(bridge)
values={}
for line in (root/'.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"').strip("'")
server_ip=str(ipaddress.IPv4Address(values.get('SERVER_IP','192.168.0.71')))
ts=json.loads(run(['docker','exec','auroralab-tailscale-1','tailscale','status','--json']))
domain=ts['Self']['DNSName'].rstrip('.')
assert domain.endswith('.ts.net') and all(c.isalnum() or c in '.-' for c in domain)
secrets=root/'secrets';secrets.mkdir(exist_ok=True);secrets.chmod(0o700)
cert=secrets/'cockpit-tls.crt';key=secrets/'cockpit-tls.key'
if not cert.exists() and not key.exists():
 subprocess.run(['openssl','req','-x509','-newkey','rsa:3072','-sha256','-nodes','-days','825','-subj','/CN=auroraserver','-addext','subjectAltName=DNS:auroraserver,DNS:'+domain+',IP:127.0.0.1,IP:'+server_ip,'-keyout',str(key),'-out',str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
assert cert.is_file() and key.is_file(),'Par de certificado/chave incompleto.'
key.chmod(0o600);cert.chmod(0o644)
ws=pathlib.Path('/etc/cockpit/ws-certs.d');ws.mkdir(parents=True,exist_ok=True)
shutil.copyfile(cert,ws/'99-aurora.cert');shutil.copyfile(key,ws/'99-aurora.key');(ws/'99-aurora.key').chmod(0o600)
config=pathlib.Path('/etc/cockpit/cockpit.conf')
ini=configparser.ConfigParser();ini.optionxform=str
if config.exists():ini.read(config)
if not ini.has_section('WebService'):ini.add_section('WebService')
ini['WebService']['Origins']='https://'+domain+':9090 https://'+server_ip+':9090 https://auroraserver:9090'
ini['WebService']['LoginTo']='false'
with config.open('w') as target:ini.write(target)
config.chmod(0o644)
folder=pathlib.Path('/etc/systemd/system/cockpit.socket.d');folder.mkdir(parents=True,exist_ok=True)
(folder/'aurora.conf').write_text('[Socket]\nListenStream=\nListenStream=127.0.0.1:9091\nListenStream='+bridge+':9091\nFreeBind=yes\n')
subprocess.run(['systemctl','unmask','cockpit.socket'],check=True)
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','cockpit.socket'],check=True)
assert run(['/usr/sbin/sshd','-T'])==policy_before,'Politica SSH mudou durante a preparacao.'
context=ssl.create_default_context(cafile=str(cert))
for attempt in range(30):
 try:
  with urllib.request.urlopen('https://127.0.0.1:9091/',context=context,timeout=15) as response:assert response.status==200
  break
 except Exception:
  if attempt==29:raise
  time.sleep(1)
record={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'backup':str(backup),'backend_bind':['127.0.0.1:9091',bridge+':9091'],'authentication':'Debian PAM; no SSH password exception','ssh_policy_unchanged':True,'cockpit_ws_version':run(['dpkg-query','-W','-f=${Version}','cockpit-ws']),'https_domain':domain}
(state/'cockpit-local-prepared.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record),flush=True)