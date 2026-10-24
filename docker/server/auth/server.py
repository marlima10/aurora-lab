"""Private authentication service behind a validating reverse proxy; no public TCP listener."""
import argparse
import json
import os
import secrets
import threading
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from store import Store, AccessError, SESSION_SECONDS

COOKIE = '__Host-aurora_session'
APP_PORTS = {'manyfold':3214,'mealie':9925,'actual':5006,'opengym':8081,'octoprint':5000,'homeassistant':8123,'homeboard':8090,'cockpit':9090}


class BoundedHTTPServer(ThreadingHTTPServer):
    """Queue browser asset bursts while staying below the container PID limit."""
    daemon_threads = True
    request_queue_size = 128

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(24)
        super().__init__(*args, **kwargs)

    def process_request(self, request, address):
        if not self.slots.acquire(timeout=15):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


def handler(store, origin, assets=None, apps_config=None):
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Configure a origem HTTPS exata, sem caminho.')
    assets = assets or Path(__file__).parent / 'static'
    apps_config = apps_config or {}

    class Handler(BaseHTTPRequestHandler):
        server_version = 'AuroraAuth'

        def log_message(self, *args):
            pass  # Login bodies, cookies and generated keys must never reach access logs.

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def send(self, status, value=None, headers=None, content_type='application/json; charset=utf-8'):
            raw = value if isinstance(value, bytes) else json.dumps(value or {}, ensure_ascii=False).encode()
            self.send_response(status)
            for name, val in {'Content-Type': content_type, 'Content-Length': str(len(raw)), 'Cache-Control': 'no-store',
                              'Pragma': 'no-cache', 'X-Content-Type-Options': 'nosniff',
                              'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer',
                              'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}.items():
                self.send_header(name, val)
            for name, val in (headers or {}).items():
                self.send_header(name, val)
            self.end_headers()
            self.wfile.write(raw)

        def token(self):
            raw = self.headers.get('Cookie', '')
            # Reject shadow cookies rather than choose an attacker-controlled duplicate.
            if sum(part.strip().startswith(COOKIE + '=') for part in raw.split(';')) != 1:
                raise AccessError('Autenticação necessária.')
            cookie = SimpleCookie()
            try:
                cookie.load(raw)
                return cookie[COOKIE].value
            except (CookieError, KeyError):
                raise AccessError('Autenticação necessária.')

        def current(self, csrf=False, admin=False):
            session = store.session(self.token())
            if csrf and not secrets.compare_digest(session['csrf'].encode(), self.headers.get('X-Aurora-CSRF', '').encode()):
                raise AccessError('Confirmação de sessão inválida. Recarregue a página.')
            if admin and not session['admin']:
                raise AccessError('Somente o administrador pode gerenciar acessos.')
            return session

        def do_GET(self):
            path = urlsplit(self.path).path
            try:
                if path == '/health':
                    return self.send(200, {'status': 'ok'})
                if path in ('/auth/', '/auth/admin'):
                    if path == '/auth/admin':
                        self.current(admin=True)
                    return self.send(200, (assets / 'index.html').read_bytes(), content_type='text/html; charset=utf-8')
                for name, mime in (('app.js', 'text/javascript; charset=utf-8'), ('app.css', 'text/css; charset=utf-8')):
                    if path == '/auth/' + name:
                        return self.send(200, (assets / name).read_bytes(), content_type=mime)
                if path == '/auth/session':
                    return self.send(200, self.current())
                if path == '/auth/users':
                    return self.send(200, {'users': store.users(self.current(admin=True)['email'])})
                if path == '/auth/apps':
                    self.current(admin=True)
                    return self.send(200, {'apps': {app: [{'identity':key, 'label':config.get('labels', {}).get(key, key)} for key in config.get('identities', {})]
                                                  for app, config in apps_config.items() if app in APP_PORTS}})
                if path == '/auth/check':
                    session = self.current()
                    app = self.headers.get('X-Aurora-App', '')
                    if app not in session['grants']:
                        return self.send(403, {'error': 'Aplicativo não autorizado.'})
                    method = self.headers.get('X-Aurora-Method', 'GET')
                    expected_origin = origin if app == 'portal' else f'https://{parsed.hostname}:{APP_PORTS[app]}'
                    supplied_origin = self.headers.get('X-Aurora-Original-Origin')
                    if (supplied_origin and supplied_origin != expected_origin) or (method not in ('GET', 'HEAD', 'OPTIONS') and supplied_origin != expected_origin):
                        return self.send(403, {'error': 'Origem da operação não autorizada.'})
                    extra = {}
                    if self.headers.get('X-Aurora-Require-Admin') == '1':
                        if not session['admin']:
                            return self.send(403, {'error': 'Operação reservada ao administrador.'})
                    if self.headers.get('X-Aurora-Require-Power') == '1':
                        if not session['admin']:
                            return self.send(403, {'error': 'Somente o administrador pode alterar a energia.'})
                        power_key = apps_config.get('_power_secret', '')
                        if len(power_key) < 32 or '\r' in power_key or '\n' in power_key:
                            return self.send(503, {'error': 'Configure a integração privada de energia.'})
                        extra['X-Aurora-Power-Key'] = power_key
                    if app != 'portal':
                        config = apps_config.get(app, {})
                        identity = session['grants'][app]
                        if not config.get('ready') or identity not in config.get('identities', {}):
                            return self.send(503, {'error': 'Integração SSO ainda não validada para esta identidade.'})
                        if app == 'homeassistant':
                            extra['X-Aurora-HA-IP'] = config['identities'][identity]
                            if len(config.get('secret', '')) < 32:
                                return self.send(503, {'error': 'Configure o adaptador Home Assistant.'})
                            extra['X-Aurora-App-Secret'] = config['secret']
                        elif app == 'cockpit':
                            if not session['admin'] or identity != config.get('local_user'):
                                return self.send(403, {'error': 'Administração não autorizada.'})
                        else:
                            secret = config.get('secret', '')
                            if len(secret) < 32 or '\r' in secret or '\n' in secret:
                                return self.send(503, {'error': 'Configure o segredo privado do adaptador.'})
                            extra['X-Aurora-App-Secret'] = secret
                    return self.send(200, {}, extra | {'X-Aurora-Email': session['email'], 'X-Aurora-Identity': session['grants'][app],
                                              'X-Aurora-Admin': '1' if session['admin'] else '0'})
                return self.send(404, {'error': 'Página não encontrada.'})
            except AccessError as error:
                return self.send(401 if path in ('/auth/check', '/auth/session') else 403, {'error': str(error)})

        def do_POST(self):
            path = urlsplit(self.path).path
            try:
                # Auth API is same-origin, including the port; a sibling app cannot manage keys.
                if self.headers.get('Transfer-Encoding'):
                    return self.send(400, {'error': 'Formato de corpo não aceito.'})
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 8192:
                    return self.send(413, {'error': 'Conteúdo excede o limite.'})
                raw = self.rfile.read(size)
                if self.headers.get('Origin') != origin or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.send(403, {'error': 'Origem não autorizada.'})
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError('Corpo JSON inválido.')
                if path == '/auth/login':
                    # Trusted gateway replaces this header; the auth container is never published.
                    token, csrf = store.authenticate(data.get('email'), data.get('key'), self.headers.get('X-Aurora-Client-IP', self.client_address[0]))
                    return self.send(200, {'ok': True, 'csrf': csrf}, {'Set-Cookie': COOKIE + '=' + token + '; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=' + str(SESSION_SECONDS)})
                session = self.current(csrf=True)
                if path == '/auth/logout':
                    store.logout(self.token())
                    return self.send(200, {'ok': True}, {'Set-Cookie': COOKIE + '=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0'})
                if not session['admin']:
                    raise AccessError('Somente o administrador pode gerenciar acessos.')
                if path == '/auth/issue':
                    grants = data.get('grants')
                    if grants is not None:
                        if not isinstance(grants, dict):
                            raise ValueError('Permissões inválidas.')
                        for app, identity in grants.items():
                            if app != 'portal' and identity not in apps_config.get(app, {}).get('identities', {}):
                                raise ValueError('Escolha uma identidade nativa conhecida.')
                    key = store.issue(session['email'], data.get('email'), data.get('grants'))
                    return self.send(200, {'ok': True, 'key': key, 'length': len(key)})
                if path == '/auth/delete':
                    store.delete(session['email'], data.get('email'))
                    return self.send(200, {'ok': True})
                if path == '/auth/revoke':
                    store.revoke(session['email'], data.get('email'))
                    return self.send(200, {'ok': True})
                return self.send(404, {'error': 'Operação não encontrada.'})
            except AccessError as error:
                return self.send(403, {'error': str(error)})
            except (ValueError, UnicodeError, TypeError):
                return self.send(400, {'error': 'Confira os dados informados.'})

    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--initialize', action='store_true')
    parser.add_argument('--key-output', type=Path)
    parser.add_argument('--data', type=Path, default=Path(os.environ.get('AUTH_DATA', '/data')))
    args = parser.parse_args()
    os.umask(0o077)
    if args.initialize:
        if not args.key_output:
            raise SystemExit('--key-output privado é obrigatório; a chave não é impressa.')
        # Reserve the output first so an existing credential is never overwritten.
        with args.key_output.open('x', encoding='utf-8') as output:
            try:
                key = Store(args.data / 'auth.sqlite3').initialize()
            except BaseException:
                output.close()
                args.key_output.unlink()
                raise
            output.write('aurora@server.local\n' + key + '\n')
        args.key_output.chmod(0o600)
        print('Administrador inicial criado; chave gravada no arquivo privado indicado.')
    else:
        origin = os.environ['AUTH_ORIGIN'].rstrip('/')
        store = Store(args.data / 'auth.sqlite3')
        apps_config = json.loads(Path(os.environ['AUTH_APP_CONFIG']).read_text())
        BoundedHTTPServer(('0.0.0.0', 7777), handler(store, origin, apps_config=apps_config)).serve_forever()
