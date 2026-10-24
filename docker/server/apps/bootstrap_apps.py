"""Initialize only newly prepared apps before private publication; never prints credentials."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request

MANYFOLD = r'''require 'json'
c = JSON.parse(STDIN.read)
raise 'Unexpected existing accounts' if User.count > 1
u = User.first || User.new
u.assign_attributes(username: c.fetch('username'), email: c.fetch('email'), password: c.fetch('password'), password_confirmation: c.fetch('password'))
u.save!
u.add_role :administrator
SiteSettings.registration_enabled = false
SiteSettings.default_viewer_role = 'private'
Library.find_by(path: '/models') || Library.create!(name: 'AuroraLAB', path: '/models', path_template: '{modelName}', storage_service: 'filesystem')
raise 'Administrator validation failed' unless u.is_administrator? && u.valid_password?(c.fetch('password'))
puts 'Initialized'
'''
MEALIE = r'''import json,sys
from mealie.core.config import get_app_settings
from mealie.core.security.security import hash_password
from mealie.db.db_setup import session_context
from mealie.repos.repository_factory import AllRepositories
c=json.load(sys.stdin)
with session_context() as session:
    repos=AllRepositories(session,group_id=None,household_id=None)
    u=repos.users.get_one(get_app_settings()._DEFAULT_EMAIL,'email') or repos.users.get_one(c['email'],'email')
    if not u:raise RuntimeError('Initial user missing')
    repos.users.update_password(u.id,hash_password(c['password']))
    u.email=c['email'];u.username=c['username'];u.full_name='Rafael'
    repos.users.update(u.id,u)
print('Initialized')
'''

def post(url, value):
    request=urllib.request.Request(url,data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=45) as response:return json.load(response)

def initialize(root):
    root=Path(root).resolve();state=root/'deploy-state/apps23-initialized.json'
    credentials=json.loads((root/'secrets/apps23-initial.json').read_text())
    done=json.loads(state.read_text()) if state.exists() else {}
    def save():state.write_text(json.dumps(done,indent=2));state.chmod(0o600)
    for name,program in [('manyfold',MANYFOLD),('mealie',MEALIE)]:
        if done.get(name):continue
        args=['docker','compose','exec','-T','--user','1000:1000',name]
        args += ['bundle','exec','rails','runner',program] if name=='manyfold' else ['python','-c',program]
        result=subprocess.run(args,cwd=root,input=json.dumps(credentials[name]).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if result.returncode:
            log=root/'deploy-state'/('apps23-'+name+'-bootstrap.log');log.write_bytes(result.stdout+result.stderr);log.chmod(0o600)
            raise RuntimeError('Falha ao inicializar '+name+'; consulte diagnostico privado')
        done[name]=True;save()
    if not done.get('actual'):
        with urllib.request.urlopen('http://127.0.0.1:5006/account/needs-bootstrap',timeout=15) as response:settings=json.load(response)
        if settings.get('data',{}).get('bootstrapped'):raise RuntimeError('Actual ja inicializado sem marcador; revisar antes de alterar acesso')
        result=post('http://127.0.0.1:5006/account/bootstrap',{'password':credentials['actual']['password']})
        if result.get('status')!='ok':raise RuntimeError('Actual nao confirmou inicializacao')
        done['actual']=True;save()
    return {'initialized':sorted(done),'credentials_file':'secrets/apps23-initial.json','passwords_printed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);args=parser.parse_args()
    if os.geteuid()!=0:raise SystemExit('Execute como root.')
    os.umask(0o077)
    print(json.dumps(initialize(args.root)))
