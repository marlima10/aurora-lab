from pathlib import Path
import json,os,secrets
root=Path('/srv/auroralab');p=root/'secrets/sso/apps.json';cfg=json.loads(p.read_text())
cfg['_mirror_secret']=cfg.get('_mirror_secret') or secrets.token_urlsafe(48)
p.write_text(json.dumps(cfg,indent=2));p.chmod(0o600);os.chown(p,65534,65534)
out=root/'secrets/mirror.json';out.write_text(json.dumps({'token':cfg['_mirror_secret'],'opengymSecret':cfg['opengym']['secret']}));out.chmod(0o600);os.chown(out,65534,65534)
d=root/'data/mirror';d.mkdir(exist_ok=True,mode=0o700);os.chown(d,65534,65534)
print('Configuração privada do painel preparada.')
