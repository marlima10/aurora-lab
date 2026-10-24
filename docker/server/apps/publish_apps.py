"""Publish only initialized apps through the existing private Tailscale Serve instance."""
import json
import os
from pathlib import Path
import subprocess

PORTS=(3214,9925,5006)

def publish(root):
    root=Path(root).resolve()
    initialized=json.loads((root/'deploy-state/apps23-initialized.json').read_text())
    if not all(initialized.get(app) for app in ('manyfold','mealie','actual')):raise ValueError('Inicialize as contas antes de publicar')
    prefix=['docker','compose','exec','-T','tailscale','tailscale']
    before=json.loads(subprocess.check_output(prefix+['serve','status','--json'],cwd=root))
    snapshot=root/'deploy-state/apps23-serve-before.json'
    if not snapshot.exists():snapshot.write_text(json.dumps(before,indent=2));snapshot.chmod(0o600)
    for port in PORTS:
        if str(port) in before.get('TCP',{}):
            configured=[v.get('Handlers',{}).get('/',{}).get('Proxy') for k,v in before.get('Web',{}).items() if k.endswith(':'+str(port))]
            if configured!=['http://127.0.0.1:'+str(port)]:raise ValueError('Porta Serve existente pertence a outro destino')
        result=subprocess.run(prefix+['serve','--bg','--https='+str(port),'http://127.0.0.1:'+str(port)],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if result.returncode:raise RuntimeError('Tailscale Serve recusou aplicativo; nenhuma redefinicao global foi solicitada')
    after=json.loads(subprocess.check_output(prefix+['serve','status','--json'],cwd=root))
    for key in ('TCP','Web'):
        for name,value in before.get(key,{}).items():
            if after.get(key,{}).get(name)!=value:raise RuntimeError('Encaminhamento anterior divergiu')
    return {'private_https_ports':list(PORTS),'previous_routes_preserved':True,'funnel_enabled':any(after.get('AllowFunnel',{}).values())}

if __name__=='__main__':
    if os.geteuid()!=0:raise SystemExit('Execute como root.')
    print(json.dumps(publish(Path(__file__).resolve().parents[3])))
