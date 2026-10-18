import ipaddress,json,os,pathlib,shutil
root=pathlib.Path(__file__).resolve().parents[3]
source=pathlib.Path(__file__).parent
target=root/'data/homeassistant';target.mkdir(parents=True,exist_ok=True);target.chmod(0o750)
config=target/'configuration.yaml'
if not config.exists():
    shutil.copyfile(source/'configuration.yaml',config);config.chmod(0o640)
http=target/'.storage/http'
if not http.exists():
    env={}
    if (root/'.env').exists():
        for line in (root/'.env').read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key,value=line.split('=',1);env[key.strip()]=value.strip().strip('"').strip("'")
    server_ip=os.environ.get('SERVER_IP',env.get('SERVER_IP','127.0.0.1'))
    ipaddress.ip_address(server_ip)
    value=json.loads((source/'http.initial.json').read_text())
    value['data']['stable']['server_host']=list(dict.fromkeys(['127.0.0.1',server_ip]))
    http.parent.mkdir(exist_ok=True);http.write_text(json.dumps(value,indent=2));http.chmod(0o600)
print('Configuracao preservada/preparada; HTTP restrito ao loopback e IP LAN configurado.')
