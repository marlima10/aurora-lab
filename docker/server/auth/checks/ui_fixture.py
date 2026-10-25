"""Real auth HTTP/SQLite with dummy identities, strictly loopback and temporary data.
HTTP adapter models trusted TLS termination only for this local browser test.
Never forwards to production or permits choosing a data directory/listen address.
Fixture administrator key: the letter F repeated 151 times; not a real credential.
"""
import json
import shutil
import sqlite3
import sys
import tempfile
from http.cookies import SimpleCookie
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from store import Store, ADMIN_EMAIL, digest
from server import handler, BoundedHTTPServer

HTTP_ORIGIN='http://127.0.0.1:8489'
TLS_ORIGIN='https://fixture.invalid'
with tempfile.TemporaryDirectory(prefix='aurora-real-auth-fixture-') as directory:
    data=Path(directory)
    store=Store(data/'auth.sqlite3')
    store.initialize()
    with store.db() as db:
        db.execute('UPDATE users SET key_hash=? WHERE email=?',(digest('F'*151),ADMIN_EMAIL))
    assets=data/'static';shutil.copytree(ROOT/'static',assets)
    page=assets/'index.html'
    page.write_text(page.read_text(encoding='utf-8').replace('<header>','<header><b>TESTE · DADOS FICTÍCIOS</b>'),encoding='utf-8')
    identities={'manyfold':'person@example.invalid','mealie':'person@example.invalid','actual':'fixture-instance','opengym':'fixture-profile','octoprint':'fixture-operator','homeassistant':'f'*32,'homeboard':'viewer','cockpit':'fixture-system'}
    registry={name:{'identities':{identity:identity},'labels':{identity:'Perfil fictício'}} for name,identity in identities.items()}
    Base=handler(store,TLS_ORIGIN,assets=assets,apps_config=registry)
    class LocalTLSAdapter(Base):
        def send_header(self,name,value):
            if name.lower()=='set-cookie':value=value.replace('__Host-aurora_session','aurora_fixture_session').replace('; Secure','')
            super().send_header(name,value)
        def token(self):
            cookie=SimpleCookie(self.headers.get('Cookie',''))
            return cookie['aurora_fixture_session'].value if 'aurora_fixture_session' in cookie else ''
        def do_POST(self):
            if self.headers.get('Origin')!=HTTP_ORIGIN:
                return self.send(403,{'error':'Fixture loopback origin required'})
            self.headers.replace_header('Origin',TLS_ORIGIN)
            return super().do_POST()
    print('Real API fixture: '+HTTP_ORIGIN+'/auth/; dummy data only.',flush=True)
    BoundedHTTPServer(('127.0.0.1',8489),LocalTLSAdapter).serve_forever()
