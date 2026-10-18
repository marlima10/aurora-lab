"""Add native CasaOS LinkApp shortcuts for existing Docker services; never deploy containers."""
import argparse,datetime as dt,ipaddress,json,os,pathlib,stat,subprocess,urllib.request
parser=argparse.ArgumentParser()
parser.add_argument('--user-id',required=True,type=int)
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()
if os.geteuid()!=0:raise SystemExit('Execute como root.')
if args.user_id<1:raise SystemExit('Usuario CasaOS invalido.')
root=pathlib.Path(__file__).resolve().parents[3]
user=pathlib.Path('/var/lib/casaos')/str(args.user_id)
if not (user/'app_order.json').is_file():raise SystemExit('Preferencias do usuario CasaOS nao encontradas.')
env={}
for line in (root/'.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1);env[k.strip()]=v.strip().strip('"').strip("'")
ip=str(ipaddress.IPv4Address(env.get('SERVER_IP','192.168.0.71')))
portal='http://'+ip
portainer=portal+':9000/#!/home'
icon_base='https://raw.githubusercontent.com/marlima10/aurora-lab/main/site/icons/services/'
def inspect():
    ids=subprocess.check_output(['docker','ps','-aq'],text=True).split()
    return json.loads(subprocess.check_output(['docker','inspect']+ids,text=True)) if ids else []
containers=inspect()
before={c['Name']:c['State']['StartedAt'] for c in containers}
with urllib.request.urlopen('http://127.0.0.1:81/v2/app_management/web/appgrid',timeout=20) as response:
    native={item['name'] for item in json.load(response)['data']}
paths=[user/'link.json',user/'app_order.json']
original={path:path.read_bytes() if path.exists() else None for path in paths}
links=json.loads(original[paths[0]]) if original[paths[0]] else []
order=json.loads(original[paths[1]])
if not isinstance(links,list) or not isinstance(order,dict) or not isinstance(order.get('data'),list):
    raise SystemExit('Formato de preferencias desconhecido; nada foi modificado.')
manifest_path=root/'deploy-state/casaos-shortcuts.json'
previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
previous_names={row['container']:row['name'] for row in previous.get('shortcuts',[])}
known={
    'octoprint':('OctoPrint',portal+':5000/','octoprint'),
    'samba':('Samba - arquivos',portainer,'samba'),
    'php':('PHP AuroraLAB',portainer,'php'),
    'homeassistant':('Home Assistant Aurora',portal+':8123/','homeassistant'),
    'opengym-web':('openGym',portal+'/opengym','opengym'),
    'opengym-api':('openGym - API',portainer,'api'),
    'backup':('Backup AuroraLAB',portainer,'backup'),
    'cockpit':('Cockpit',portal+':9090/','cockpit'),
    'power':('Energia AuroraLAB',portal+'/#energy-card','power'),
    'monitor':('Monitoramento AuroraLAB',portal+'/#system-card','monitor'),
    'tailscale':('Tailscale',portainer,'tailscale'),
}
shortcuts=[];existing=[]
for container in containers:
    name=container['Name'].lstrip('/')
    labels=container['Config'].get('Labels') or {}
    project=labels.get('com.docker.compose.project','')
    service=labels.get('com.docker.compose.service','')
    if (project=='auroralab' and service=='web' and 'auroralab' in native) or (project!='auroralab' and project in native):
        existing.append({'container':name,'native_app':project});continue
    title,url,icon=known.get(service if project=='auroralab' else '',(name,portainer,'containers'))
    managed=previous_names.get(name)
    if managed: title=managed
    conflict=next((item for item in links if item.get('name')==title),None)
    if conflict and not managed and conflict.get('hostname')!=url:
        title=title+' ('+name+')'
    item={'hostname':url,'name':title,'icon':icon_base+icon+'.svg','app_type':'LinkApp','status':'running'}
    match=next((i for i,v in enumerate(links) if v.get('name')==title),None)
    if match is None:links.append(item)
    elif managed:links[match]=item
    if title not in order['data']:order['data'].append(title)
    shortcuts.append({'container':name,'name':title,'url':url,'icon':icon,'state':container['State']['Status']})
record={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'user_id':args.user_id,'containers':len(containers),'native':existing,'shortcuts':shortcuts}
print(json.dumps({'containers':len(containers),'native_icons':len(existing),'service_shortcuts':len(shortcuts),'names':[row['name'] for row in shortcuts]},ensure_ascii=False),flush=True)
if not args.apply:
    print('Simulacao concluida. Use --apply para gravar.');raise SystemExit(0)
stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup=root/'deploy-state'/('casaos-shortcuts-before-'+stamp);backup.mkdir(mode=0o700)
for path,value in original.items():
    if value is not None:
        saved=backup/path.name;saved.write_bytes(value);saved.chmod(0o600)
for path in paths:
    if (path.read_bytes() if path.exists() else None)!=original[path]:
        raise SystemExit('Preferencias mudaram durante a preparacao; repita a sincronizacao.')
for path,value in ((paths[0],links),(paths[1],order)):
    mode=stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    temp=path.with_name(path.name+'.aurora.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.chmod(mode);temp.replace(path)
    assert json.loads(path.read_text())==value
record['backup']=str(backup)
record['container_start_times_unchanged']=before=={c['Name']:c['State']['StartedAt'] for c in inspect()}
assert record['container_start_times_unchanged'],'Estado Docker mudou durante a sincronizacao.'
manifest_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');manifest_path.chmod(0o600)
print('Icones sincronizados. Containers preservados; backup: '+str(backup),flush=True)