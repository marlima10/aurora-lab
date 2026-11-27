import concurrent.futures
import hashlib
import http.client
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from server import COOKIE, handler, BoundedHTTPServer
from store import ADMIN_EMAIL, SESSION_SECONDS, AccessError, Store


class Fixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = 10000
        self.store = Store(Path(self.temp.name) / 'auth.sqlite3', clock=lambda: self.now)
        self.key = self.store.initialize()

    def tearDown(self):
        self.temp.cleanup()

    def login(self, email=ADMIN_EMAIL, key=None):
        return self.store.authenticate(email, key or self.key, 'fixture-client')


class AuthenticationTests(Fixture, unittest.TestCase):
    def test_key_exact_length_unique_and_only_digest_persisted(self):
        other = self.store.issue(ADMIN_EMAIL, 'person@example.test')
        self.assertEqual(len(self.key), 151)
        self.assertRegex(other, r'^[A-Za-z0-9_-]{151}$')
        self.assertNotEqual(self.key, other)
        raw = self.store.path.read_bytes()
        self.assertNotIn(self.key.encode(), raw)
        self.assertNotIn(other.encode(), raw)
        self.assertIn(hashlib.sha256(self.key.encode()).hexdigest().encode(), raw)

    def test_initialize_never_overwrites_existing_identity(self):
        self.assertRaises(AccessError, self.store.initialize)
        self.login()

    def test_admin_initially_has_no_implicit_access_to_private_apps(self):
        token, csrf = self.login()
        session = self.store.session(token)
        self.assertTrue(session['admin'])
        self.assertEqual(session['grants'], {'portal': ADMIN_EMAIL})
        self.assertEqual(session['csrf'], csrf)

    def test_key_tied_to_email_and_not_a_master_key(self):
        other = self.store.issue(ADMIN_EMAIL, 'person@example.test')
        self.assertRaises(AccessError, self.login, 'person@example.test', self.key)
        self.assertRaises(AccessError, self.login, ADMIN_EMAIL, other)
        token, _ = self.login('person@example.test', other)
        self.assertFalse(self.store.session(token)['admin'])

    def test_normal_user_cannot_issue_revoke_list_or_promote(self):
        self.store.issue(ADMIN_EMAIL, 'person@example.test')
        for method, args in ((self.store.issue, ('person@example.test', 'attacker@example.test')), (self.store.revoke, ('person@example.test', ADMIN_EMAIL)), (self.store.users, ('person@example.test',))):
            self.assertRaises(AccessError, method, *args)
        self.assertRaises(AccessError, self.store.issue, ADMIN_EMAIL, 'person@example.test', {'cockpit':'root'})

    def test_rotation_invalidates_old_key_and_existing_sessions(self):
        key = self.store.issue(ADMIN_EMAIL, 'person@example.test')
        token, _ = self.login('person@example.test', key)
        replacement = self.store.issue(ADMIN_EMAIL, 'person@example.test')
        self.assertRaises(AccessError, self.store.session, token)
        self.assertRaises(AccessError, self.login, 'person@example.test', key)
        self.login('person@example.test', replacement)

    def test_revoke_invalidates_key_and_sessions_and_admin_is_protected(self):
        key = self.store.issue(ADMIN_EMAIL, 'person@example.test')
        token, _ = self.login('person@example.test', key)
        self.store.revoke(ADMIN_EMAIL, 'person@example.test')
        self.assertRaises(AccessError, self.store.session, token)
        self.assertRaises(AccessError, self.login, 'person@example.test', key)
        self.assertRaises(AccessError, self.store.revoke, ADMIN_EMAIL, ADMIN_EMAIL)

    def test_delete_hides_user_invalidates_access_and_preserves_grants_for_recovery(self):
        target='person@example.test'
        key=self.store.issue(ADMIN_EMAIL,target,{'mealie':target})
        token,_=self.login(target,key)
        self.store.delete(ADMIN_EMAIL,target)
        self.assertNotIn(target,[u['email'] for u in self.store.users(ADMIN_EMAIL)])
        self.assertRaises(AccessError,self.store.session,token)
        self.assertRaises(AccessError,self.login,target,key)
        replacement=self.store.issue(ADMIN_EMAIL,target)
        restored,_=self.login(target,replacement)
        self.assertEqual(self.store.session(restored)['grants']['mealie'],target)
        self.assertIn(target,[u['email'] for u in self.store.users(ADMIN_EMAIL)])
        self.assertRaises(AccessError,self.login,target,key)

    def test_delete_is_admin_only_and_protects_initial_admin(self):
        target='person@example.test'
        self.store.issue(ADMIN_EMAIL,target)
        self.assertRaises(AccessError,self.store.delete,target,target)
        self.assertRaises(AccessError,self.store.delete,ADMIN_EMAIL,ADMIN_EMAIL.upper())
        self.assertRaises(ValueError,self.store.delete,ADMIN_EMAIL,'missing@example.test')
        self.store.revoke(ADMIN_EMAIL,target)
        self.store.delete(ADMIN_EMAIL,target)
        self.assertRaises(ValueError,self.store.delete,ADMIN_EMAIL,target)
        self.login()

    def test_version26_migration_preserves_existing_key_session_and_is_idempotent(self):
        path=Path(self.temp.name)/'legacy.sqlite3'
        key='A'*151;token='B'*64
        with sqlite3.connect(path) as db:
            db.executescript('CREATE TABLE users(email TEXT PRIMARY KEY,key_hash TEXT NOT NULL,enabled INTEGER NOT NULL,generation INTEGER NOT NULL DEFAULT 1,created INTEGER NOT NULL); CREATE TABLE sessions(hash TEXT PRIMARY KEY,email TEXT NOT NULL REFERENCES users(email),csrf TEXT NOT NULL,expires INTEGER NOT NULL,generation INTEGER NOT NULL); CREATE TABLE grants(email TEXT NOT NULL REFERENCES users(email),app TEXT NOT NULL,identity TEXT NOT NULL,PRIMARY KEY(email,app));')
            db.execute('INSERT INTO users VALUES(?,?,1,4,1)',(ADMIN_EMAIL,hashlib.sha256(key.encode()).hexdigest()))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,4)',(hashlib.sha256(token.encode()).hexdigest(),ADMIN_EMAIL,'fixture-csrf',20000))
            db.execute('INSERT INTO grants VALUES(?,?,?)',(ADMIN_EMAIL,'portal',ADMIN_EMAIL))
        db.close()
        for _ in range(2):
            migrated=Store(path,clock=lambda:10000)
            self.assertTrue(migrated.session(token)['admin'])
            migrated.authenticate(ADMIN_EMAIL,key,'fixture-migration')
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM schema_migrations WHERE version=1').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT generation,deleted FROM users').fetchone(),(4,0))
        db.close()

    def test_expiration_logout_and_session_tokens_are_hashed(self):
        token, _ = self.login()
        self.assertNotIn(token.encode(), self.store.path.read_bytes())
        self.now += SESSION_SECONDS
        self.assertRaises(AccessError, self.store.session, token)
        token, _ = self.login()
        self.store.logout(token)
        self.assertRaises(AccessError, self.store.session, token)

    def test_failed_attempts_persist_and_limit_expires(self):
        for _ in range(8):
            self.assertRaises(AccessError, self.login, ADMIN_EMAIL, 'x' * 151)
        fresh = Store(self.store.path, clock=lambda: self.now)
        with self.assertRaisesRegex(AccessError, '15 minutos'):
            fresh.authenticate(ADMIN_EMAIL, self.key, 'fixture-client')
        self.now += 901
        self.login()

    def test_grants_reject_unknown_app_and_header_injection(self):
        for grants in ({'bad':'identity'}, {'mealie':'person\r\nX-Evil:true'}, {'mealie':''}):
            self.assertRaises(ValueError, self.store.issue, ADMIN_EMAIL, 'person@example.test', grants)

    def test_concurrent_rotation_only_latest_key_works(self):
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            keys = list(pool.map(lambda _: self.store.issue(ADMIN_EMAIL, 'person@example.test'), range(4)))
        successes = 0
        for key in keys:
            try:
                self.login('person@example.test', key)
                successes += 1
            except AccessError:
                pass
        self.assertEqual(successes, 1)


class HttpAuthenticationTests(Fixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.http = BoundedHTTPServer(('127.0.0.1', 0), handler(self.store, 'https://portal.example.test',apps_config={'mealie':{'identities':{'person@example.test':'person@example.test'}},'cockpit':{'identities':{'fixture-system':'fixture-system'}}}))
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        super().tearDown()

    def request(self, path, body=None, headers=None):
        connection = http.client.HTTPConnection(*self.http.server_address, timeout=5)
        defaults = {'Origin':'https://portal.example.test', 'Content-Type':'application/json'}
        defaults.update(headers or {})
        connection.request('POST' if body is not None else 'GET', path, json.dumps(body).encode() if body is not None else None, defaults)
        response = connection.getresponse()
        raw = response.read()
        record = (response.status, dict(response.getheaders()), json.loads(raw))
        connection.close()
        return record

    def test_mirror_configuration_sends_anonymous_visitors_to_login(self):
        connection=http.client.HTTPConnection(*self.http.server_address,timeout=5)
        connection.request('GET','/auth/mirror/configurar')
        response=connection.getresponse()
        self.assertEqual(response.status,302);self.assertEqual(response.getheader('Location'),'/auth/')
        response.read();connection.close()

    def test_mirror_settings_are_admin_only_even_with_forged_headers(self):
        key=self.store.issue(ADMIN_EMAIL,'person@example.test')
        token,csrf=self.login('person@example.test',key)
        headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf,'X-Aurora-Admin':'1'}
        for path in ('/auth/mirror/configurar','/auth/mirror/settings','/auth/mirror/mirror-config.js','/auth/mirror/mirror-config.css'):
            self.assertEqual(self.request(path,headers=headers)[0],403)
        self.assertEqual(self.request('/auth/mirror/settings',{'admin':True},headers)[0],403)

    def test_mirror_settings_require_admin_csrf_and_exact_origin(self):
        from unittest.mock import patch
        token,csrf=self.login();headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        with patch('server.mirror_query',return_value=(200,{'settings':{},'defaults':{}})) as query:
            self.assertEqual(self.request('/auth/mirror/settings',headers=headers)[0],200)
            self.assertEqual(query.call_args.args[2],'settings-get')
            self.assertTrue(query.call_args.args[0]['admin'])
            self.assertEqual(self.request('/auth/mirror/settings',{},headers|{'X-Aurora-CSRF':'wrong'})[0],403)
            self.assertEqual(self.request('/auth/mirror/settings',{},headers|{'Origin':'https://attacker.example.test'})[0],403)
            self.assertEqual(self.request('/auth/mirror/settings',{},headers)[0],200)
            self.assertEqual(query.call_args.args[2],'settings-save')

    def test_mirror_city_search_requires_admin_csrf_and_exact_origin(self):
        from unittest.mock import patch
        token,csrf=self.login();headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        with patch('server.mirror_query',return_value=(200,{'locations':[]})) as query:
            self.assertEqual(self.request('/auth/mirror/locations',{'query':'Jacareí, SP'},headers)[0],200)
            self.assertEqual(query.call_args.args[2],'locations')
            self.assertTrue(query.call_args.args[0]['admin'])
            self.assertEqual(self.request('/auth/mirror/locations',{'query':'x'},headers|{'X-Aurora-CSRF':'wrong'})[0],403)
            self.assertEqual(self.request('/auth/mirror/locations',{'query':'x'},headers|{'Origin':'https://other.test'})[0],403)
        key=self.store.issue(ADMIN_EMAIL,'person@example.test');token,csrf=self.login('person@example.test',key)
        self.assertEqual(self.request('/auth/mirror/locations',{'query':'Jacareí, SP'},{'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf,'X-Aurora-Admin':'1'})[0],403)

    def test_background_upload_requires_admin_csrf_origin_and_raster_type(self):
        from unittest.mock import patch
        token,csrf=self.login();headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf,'Content-Type':'image/png','Origin':'https://portal.example.test'}
        def upload(extra=None):
            connection=http.client.HTTPConnection(*self.http.server_address,timeout=5)
            connection.request('POST','/auth/mirror/backgrounds/upload',b'fixture-image',headers|(extra or {}))
            response=connection.getresponse();status=response.status;response.read();connection.close();return status
        with patch('server.mirror_upload',return_value=(200,{'uploadedId':'a'*64})) as forwarded:
            self.assertEqual(upload(),200);self.assertEqual(forwarded.call_args.args[2],b'fixture-image')
            forwarded.reset_mock()
            for extra in [{'X-Aurora-CSRF':'wrong'},{'Origin':'https://other.test'},{'Content-Type':'image/svg+xml'},{'Content-Length':str(12*1024*1024+1)}]:
                self.assertIn(upload(extra),(400,403,413))
            forwarded.assert_not_called()
            key=self.store.issue(ADMIN_EMAIL,'person@example.test');normal,othercsrf=self.login('person@example.test',key)
            self.assertEqual(upload({'Cookie':COOKIE+'='+normal,'X-Aurora-CSRF':othercsrf,'X-Aurora-Admin':'1'}),403)

    def test_background_list_is_admin_only_and_image_requires_session(self):
        from unittest.mock import patch
        key=self.store.issue(ADMIN_EMAIL,'person@example.test');token,csrf=self.login('person@example.test',key)
        headers={'Cookie':COOKIE+'='+token}
        self.assertEqual(self.request('/auth/mirror/backgrounds',headers=headers)[0],403)
        connection=http.client.HTTPConnection(*self.http.server_address,timeout=5)
        connection.request('GET','/auth/mirror/backgrounds/'+'a'*64)
        response=connection.getresponse();self.assertEqual(response.status,403);response.read();connection.close()
        admin,_=self.login()
        with patch('server.mirror_query',return_value=(200,{'images':[]})) as query:
            self.assertEqual(self.request('/auth/mirror/backgrounds',headers={'Cookie':COOKIE+'='+admin})[0],200)
            self.assertEqual(query.call_args.args[2],'backgrounds')

    def test_agenda_requires_session_csrf_and_origin(self):
        from unittest.mock import patch
        token,csrf=self.login();headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        with patch('server.mirror_query',return_value=(200,{'items':[]})) as query:
            self.assertEqual(self.request('/auth/mirror/agenda',{'start':'2026-11-23','end':'2026-11-29'},headers)[0],200)
            self.assertEqual(query.call_args.args[2],'agenda')
            query.reset_mock()
            for extra in [{'X-Aurora-CSRF':'wrong'},{'Origin':'https://attacker.example.test'},{'Cookie':''}]:
                self.assertEqual(self.request('/auth/mirror/agenda',{},headers|extra)[0],403)
            query.assert_not_called()

    def test_agenda_facade_uses_session_native_identities(self):
        from unittest.mock import patch,MagicMock
        from mirror import query
        response=MagicMock();response.__enter__.return_value=response;response.status=200;response.read.return_value=b'{"items":[]}'
        session={'email':'a@example.test','admin':False,'grants':{'portal':'a','opengym':'native-a','mealie':'meal-a'}}
        with patch('mirror.urllib.request.urlopen',return_value=response) as opened:
            query(session,{'_mirror_secret':'s'*48},'agenda',{'start':'2026-11-23','end':'2026-11-29','identity':'victim','mealieIdentity':'victim'})
            sent=json.loads(opened.call_args.args[0].data)
            self.assertEqual(sent['identity'],'native-a');self.assertEqual(sent['mealieIdentity'],'meal-a');self.assertEqual(sent['owner'],'a@example.test')
        with self.assertRaises(ValueError):query(session|{'grants':{}},{'_mirror_secret':'s'*48},'agenda',{})

    def test_cookie_is_host_only_secure_httponly_and_no_store(self):
        status, headers, body = self.request('/auth/login', {'email':ADMIN_EMAIL, 'key':self.key})
        self.assertEqual(status, 200)
        self.assertIn('__Host-aurora_session=', headers['Set-Cookie'])
        for flag in ('HttpOnly', 'Secure', 'SameSite=Lax', 'Path=/'):
            self.assertIn(flag, headers['Set-Cookie'])
        self.assertNotIn('Domain=', headers['Set-Cookie'])
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertNotIn(self.key, json.dumps(body))

    def test_csrf_cross_origin_and_sibling_app_rejected(self):
        token, csrf = self.login()
        cookie = COOKIE + '=' + token
        for origin in ('https://attacker.example.test','http://portal.example.test','https://portal.example.test:5006'):
            self.assertEqual(self.request('/auth/issue', {'email':'person@example.test'}, {'Origin':origin, 'Cookie':cookie, 'X-Aurora-CSRF':csrf})[0], 403)
        self.assertEqual(self.request('/auth/issue', {'email':'person@example.test'}, {'Cookie':cookie})[0], 403)
        self.assertEqual(self.request('/auth/issue', {'email':'person@example.test'}, {'Cookie':cookie, 'X-Aurora-CSRF':csrf})[0], 200)

    def test_forward_auth_requires_session_and_per_app_grant(self):
        self.assertEqual(self.request('/auth/check', headers={'X-Aurora-App':'portal'})[0], 401)
        token, _ = self.login()
        headers={'Cookie':COOKIE+'='+token, 'X-Aurora-App':'portal'}
        self.assertEqual(self.request('/auth/check', headers=headers)[0], 200)
        headers['X-Aurora-App']='actual'
        self.assertEqual(self.request('/auth/check', headers=headers)[0], 403)
        headers['Cookie']+='; '+COOKIE+'=shadow'
        self.assertEqual(self.request('/auth/check', headers=headers)[0], 401)

    def test_registration_policy_blocks_cockpit_without_partial_user_and_accepts_allowed_grants(self):
        token,csrf=self.login();headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        status,_,registry=self.request('/auth/apps',headers=headers)
        self.assertEqual(status,200);self.assertEqual(registry['adminOnly'],['cockpit'])
        address='person@example.test'
        status,_,result=self.request('/auth/issue',{'email':address,'grants':{'mealie':address,'cockpit':'fixture-system'}},headers)
        self.assertEqual(status,403);self.assertNotIn('key',result)
        self.assertNotIn(address,[u['email'] for u in self.store.users(ADMIN_EMAIL)])
        status,_,result=self.request('/auth/issue',{'email':address,'grants':{'mealie':address}},headers)
        self.assertEqual(status,200);self.assertEqual(len(result['key']),151)
        native,_=self.login(address,result['key'])
        self.assertEqual(self.store.session(native)['grants']['mealie'],address)
        self.assertNotIn('cockpit',self.store.session(native)['grants'])

    def test_issue_returns_key_to_admin_and_delete_requires_admin_csrf(self):
        token,csrf=self.login()
        headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        target='person@example.test'
        status,_,body=self.request('/auth/issue',{'email':target},headers)
        self.assertEqual(status,200)
        self.assertRegex(body['key'],r'^[A-Za-z0-9_-]{151}$')
        user_token,_=self.login(target,body['key'])
        self.assertEqual(self.request('/auth/delete',{'email':target},{'Cookie':COOKIE+'='+token})[0],403)
        self.assertEqual(self.request('/auth/delete',{'email':target},headers|{'Origin':'https://attacker.example.test'})[0],403)
        self.assertEqual(self.request('/auth/delete',{'email':ADMIN_EMAIL},headers)[0],403)
        self.assertEqual(self.request('/auth/delete',{'email':target},headers)[0],200)
        self.assertEqual(self.request('/auth/session',headers={'Cookie':COOKIE+'='+user_token})[0],401)
        self.assertNotIn(body['key'],json.dumps(self.request('/auth/users',headers=headers)[2]))

    def test_non_admin_cannot_read_generator_api_or_issue_keys(self):
        key = self.store.issue(ADMIN_EMAIL,'person@example.test')
        token, csrf = self.login('person@example.test',key)
        headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        self.assertEqual(self.request('/auth/users', headers=headers)[0],403)
        self.assertEqual(self.request('/auth/apps', headers=headers)[0],403)
        self.assertEqual(self.request('/auth/delete', {'email':'person@example.test'},headers)[0],403)
        self.assertEqual(self.request('/auth/admin', headers=headers)[0],403)
        self.assertEqual(self.request('/auth/issue', {'email':'new@example.test'},headers)[0],403)


class BurstAuthenticationTests(unittest.TestCase):
    def test_browser_asset_burst_is_queued_without_exceeding_worker_limit(self):
        from http.server import BaseHTTPRequestHandler
        barrier = threading.Barrier(64)
        lock = threading.Lock()
        active = peak = 0
        class SlowHandler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_GET(self):
                nonlocal active, peak
                with lock:
                    active += 1
                    peak = max(peak,active)
                try:
                    time.sleep(0.08)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'ok')
                finally:
                    with lock:
                        active -= 1
        server=BoundedHTTPServer(('127.0.0.1',0),SlowHandler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        def fetch(_):
            barrier.wait(timeout=10)
            connection=http.client.HTTPConnection(*server.server_address,timeout=10)
            try:
                connection.request('GET','/synthetic-asset')
                response=connection.getresponse()
                return response.status,response.read()
            finally:
                connection.close()
        try:
            with concurrent.futures.ThreadPoolExecutor(64) as pool:
                responses=list(pool.map(fetch,range(64)))
            self.assertEqual(responses,[(200,b'ok')]*64)
            self.assertLessEqual(peak,24)
            self.assertGreater(peak,1)
        finally:
            server.shutdown();server.server_close();thread.join()


class RetiredApplicationsTests(unittest.TestCase):
    def test_migration_retires_only_removed_grants_and_preserves_login(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder)/'auth.sqlite3')
            key = store.initialize()
            token, _ = store.authenticate(ADMIN_EMAIL, key, 'fixture')
            with store.db() as db:
                db.execute('DELETE FROM schema_migrations WHERE version=2')
                for app in ('homeassistant','homeboard','opengym'):
                    db.execute('INSERT INTO grants VALUES(?,?,?)',(ADMIN_EMAIL,app,'fixture'))
                before = [tuple(row) for row in db.execute('SELECT * FROM users')]
            restored = Store(store.path)
            with restored.db() as db:
                self.assertEqual(before,[tuple(row) for row in db.execute('SELECT * FROM users')])
            grants = restored.session(token)['grants']
            self.assertNotIn('homeassistant',grants)
            self.assertNotIn('homeboard',grants)
            self.assertEqual(grants['opengym'],'fixture')
            self.assertEqual(restored.authenticate(ADMIN_EMAIL,key,'fixture')[0] is not None,True)


class JavisIntegrationTests(Fixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.secret='fixture_javis_private_key_000000000000000000'
        self.http=BoundedHTTPServer(('127.0.0.1',0),handler(self.store,'https://portal.example.test',apps_config={'_javis_proxy_secret':self.secret,'_javis_connector_secret':self.secret}))
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();super().tearDown()

    def request(self,path,headers):
        conn=http.client.HTTPConnection(*self.http.server_address,timeout=5);conn.request('GET',path,headers=headers);r=conn.getresponse();value=(r.status,dict(r.getheaders()),json.loads(r.read()));conn.close();return value

    def test_javis_origin_and_admin_session_are_required(self):
        token,_=self.login();headers={'Cookie':COOKIE+'='+token,'X-Aurora-App':'portal','X-Aurora-Require-Javis':'1','X-Aurora-Method':'GET','X-Aurora-Original-Origin':'https://portal.example.test:7777'}
        status,h,_=self.request('/auth/check',headers);self.assertEqual(status,200);self.assertEqual(h['X-Aurora-App-Secret'],self.secret)
        self.assertEqual(self.request('/auth/check',dict(headers,**{'X-Aurora-Original-Origin':'https://attacker.invalid'}))[0],403)
        key=self.store.issue(ADMIN_EMAIL,'person@example.invalid',{});person,_=self.store.authenticate('person@example.invalid',key,'fixture');self.assertEqual(self.request('/auth/check',dict(headers,Cookie=COOKIE+'='+person))[0],403)

    def test_connector_grants_need_private_key_and_follow_revocation(self):
        self.assertEqual(self.request('/auth/internal/javis',{})[0],403)
        status,_,value=self.request('/auth/internal/javis',{'Authorization':'Bearer '+self.secret});self.assertEqual(status,200);self.assertIn('portal',value['grants']);self.assertNotIn('key_hash',json.dumps(value))
        self.store.issue(ADMIN_EMAIL,ADMIN_EMAIL,{'mealie':'fixture'});self.assertEqual(self.request('/auth/internal/javis',{'Authorization':'Bearer '+self.secret})[2]['grants']['mealie'],'fixture')
        self.store.issue(ADMIN_EMAIL,ADMIN_EMAIL,{});self.assertNotIn('mealie',self.request('/auth/internal/javis',{'Authorization':'Bearer '+self.secret})[2]['grants'])



class RetiredPrintAppTests(unittest.TestCase):
    def test_retirement_keeps_keys_and_unrelated_grants(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'auth.sqlite3';store=Store(path);key=store.initialize()
            with store.db() as db:
                before=db.execute('SELECT key_hash FROM users WHERE email=?',(ADMIN_EMAIL,)).fetchone()[0]
                db.execute('INSERT INTO grants VALUES(?,?,?)',(ADMIN_EMAIL,'octoprint','retired-fixture'))
                db.execute('INSERT INTO grants VALUES(?,?,?)',(ADMIN_EMAIL,'manyfold','kept-fixture'))
                db.execute('DELETE FROM schema_migrations WHERE version=3')
            reopened=Store(path)
            with reopened.db() as db:
                self.assertEqual(db.execute('SELECT key_hash FROM users WHERE email=?',(ADMIN_EMAIL,)).fetchone()[0],before)
                self.assertEqual({row[0] for row in db.execute('SELECT app FROM grants WHERE email=?',(ADMIN_EMAIL,))},{'portal','manyfold'})
            self.assertTrue(reopened.authenticate(ADMIN_EMAIL,key,'fixture-retirement'))

if __name__ == '__main__':
    unittest.main()
