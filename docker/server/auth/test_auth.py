import concurrent.futures
import hashlib
import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from server import COOKIE, handler
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
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), handler(self.store, 'https://portal.example.test'))
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

    def test_non_admin_cannot_read_generator_api_or_issue_keys(self):
        key = self.store.issue(ADMIN_EMAIL,'person@example.test')
        token, csrf = self.login('person@example.test',key)
        headers={'Cookie':COOKIE+'='+token,'X-Aurora-CSRF':csrf}
        self.assertEqual(self.request('/auth/users', headers=headers)[0],403)
        self.assertEqual(self.request('/auth/apps', headers=headers)[0],403)
        self.assertEqual(self.request('/auth/admin', headers=headers)[0],403)
        self.assertEqual(self.request('/auth/issue', {'email':'new@example.test'},headers)[0],403)


if __name__ == '__main__':
    unittest.main()
