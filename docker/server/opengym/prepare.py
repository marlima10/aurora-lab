import json,os,pathlib,re,subprocess
from urllib.parse import urlparse
root=pathlib.Path(__file__).resolve().parents[3]
folder=root/'secrets';folder.mkdir(exist_ok=True);folder.chmod(0o700)
file=folder/'opengym.env'
if not file.exists():
    status=json.loads(subprocess.check_output(['docker','exec','auroralab-tailscale-1','tailscale','status','--json'],text=True))
    domain=status['Self']['DNSName'].rstrip('.')
    assert re.fullmatch(r'[a-zA-Z0-9.-]+',domain) and domain.endswith('.ts.net'),'Dominio Tailscale invalido'
    file.write_text('RP_ID='+domain+'\nORIGIN=https://'+domain+':8081\nRP_NAME=openGym AuroraLAB\n')
    file.chmod(0o600)
values=dict(line.split('=',1) for line in file.read_text().splitlines() if '=' in line and not line.startswith('#'))
origin=values['ORIGIN'];url=urlparse(origin)
assert url.scheme=='https' and url.hostname==values['RP_ID'] and url.port==8081 and not url.username and not url.password
config=root/'.env';text=config.read_text() if config.exists() else ''
lines=[line for line in text.splitlines() if not line.startswith('OPENGYM_ORIGIN=')]
config.write_text('\n'.join(lines)+'\nOPENGYM_ORIGIN='+origin+'\n')
data=root/'data/opengym';data.mkdir(parents=True,exist_ok=True);data.chmod(0o700)
print('Origem HTTPS e dados openGym preparados; configuracao existente preservada.')
