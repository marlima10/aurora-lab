"""Exercise the real Nginx gateway in a private container network namespace.

All identities, keys and upstreams are fixtures. No production app is contacted.
The runner replaces only upstream addresses in a rendered gateway configuration.
"""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time

from server import COOKIE, handler, APP_PORTS
from store import ADMIN_EMAIL, Store

ORIGIN = 'https://portal.example.test'
SECRET = 'fixture-only-private-native-secret-000000'


def run():
    checks = 0

    def expect(value, message):
        nonlocal checks
        assert value, message
        checks += 1

    class Echo(BaseHTTPRequestHandler):
        def do_GET(self):
            payload = json.dumps(dict(self.headers)).encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        do_POST = do_GET
        def log_message(self, *args):
            pass

    with tempfile.TemporaryDirectory() as temporary:
        store = Store(Path(temporary) / 'auth.sqlite3')
        store.initialize()
        grants = {app: ('rafael' if app == 'cockpit' else 'fixture') for app in APP_PORTS}
        config = {app: {'ready': True, 'identities': {identity: '198.18.0.10'}, 'secret': SECRET,
                        'local_user': 'rafael'} for app, identity in grants.items()}
        config['_power_secret'] = SECRET
        key = store.issue(ADMIN_EMAIL, ADMIN_EMAIL, grants)
        token, _ = store.authenticate(ADMIN_EMAIL, key, 'fixture')
        cookie = COOKIE + '=' + token
        person_key = store.issue(ADMIN_EMAIL, 'person@example.test', {})
        person_token, _ = store.authenticate('person@example.test', person_key, 'fixture')
        auth = ThreadingHTTPServer(('127.0.0.1', 7777), handler(store, ORIGIN, apps_config=config))
        echo = ThreadingHTTPServer(('127.0.0.1', 18081), Echo)
        for service in (auth, echo):
            threading.Thread(target=service.serve_forever, daemon=True).start()

        def request(port=8080, path='/', session=None, method='GET', extra=None):
            headers = {'Host': 'portal.example.test'}
            if session:
                headers['Cookie'] = session
            headers.update(extra or {})
            client = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            client.request(method, path, headers=headers)
            response = client.getresponse()
            result = response.status, dict(response.getheaders()), response.read()
            client.close()
            return result

        try:
            for _ in range(40):
                try:
                    request()
                    break
                except OSError:
                    time.sleep(.1)
            for app, port in {'portal':8080, **APP_PORTS}.items():
                status, headers, _ = request(port)
                expect(status == 302 and headers['Location'] == ORIGIN + '/auth/', app + ' anonymous access')
                status, _, data = request(port, session=cookie, extra={'X-Aurora-Identity':'forged', 'X-Aurora-Proxy-Secret':'forged'})
                native = json.loads(data)
                expect(status == 200 and native['X-Aurora-Identity'] == grants.get(app, ADMIN_EMAIL), app + ' native identity')
                expect(COOKIE not in native.get('Cookie', ''), app + ' session cookie not leaked')
                if app not in ('portal', 'cockpit'):
                    expect(native['X-Aurora-Proxy-Secret'] == SECRET, app + ' trusted proxy secret')
            for original, expected in [(cookie+'; native=one', 'native=one'),
                                       ('native=one; '+cookie, 'native=one'),
                                       ('native=one; '+cookie+'; next=two', 'native=one; next=two')]:
                _, _, data = request(session=original)
                expect(json.loads(data)['Cookie'] == expected, 'native cookies preserved')
            expect(request(path='/auth/check', session=cookie)[0] == 404, 'private check endpoint')
            expect(request(path='/_aurora_verify', session=cookie)[0] == 404, 'private subrequest endpoint')
            expect(request(session=cookie, extra={'Host':'attacker.example.test'})[0] == 421, 'fixed host')
            expect(request(8088)[1]['Location'] == ORIGIN + '/', 'HTTP redirects to HTTPS')
            expect(request(3214, session=COOKIE+'='+person_token)[0] == 403, 'app grant required')
            expect(request(path='/fitness-api',session=COOKIE+'='+person_token)[0] == 403, 'legacy shared Fitness restricted to admin')
            expect('Authorization' not in json.loads(request(path='/fitness-api',session=cookie)[2]), 'power secret not sent to Fitness')
            expect(request(path='/api/power/set', method='POST', session=COOKIE+'='+person_token,
                           extra={'Origin':ORIGIN})[0] == 403, 'power requires admin')
            expect(request(path='/api/power/set', method='POST', session=cookie,
                           extra={'Origin':'https://portal.example.test:9925'})[0] == 403, 'sibling app CSRF denied')
            status, _, data = request(path='/api/power/set', method='POST', session=cookie, extra={'Origin':ORIGIN})
            expect(status == 200 and json.loads(data)['Authorization'] == 'Bearer '+SECRET, 'power credential stays behind gateway')
            config['manyfold']['ready'] = False
            expect(request(3214, session=cookie)[0] == 500, 'unverified native integration fails closed')
            store.issue(ADMIN_EMAIL, ADMIN_EMAIL, grants)
            expect(request(session=cookie)[0] == 302, 'key rotation invalidates next gateway request')
        finally:
            auth.shutdown(); echo.shutdown()
            auth.server_close(); echo.server_close()
    print(json.dumps({'gateway_assertions': checks, 'personal_data_used': False}))


if __name__ == '__main__':
    run()
