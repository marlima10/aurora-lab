"""Private, bounded JSON transport for the AuroraLAB data connectors."""
import hmac
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LIMIT = 2 * 1024 * 1024


def configuration():
    return json.loads(Path(os.getenv('CONFIG_FILE', '/run/secrets/config.json')).read_text())


class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'} | (headers or {}))
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('oversized')
        return json.loads(raw) if raw else {}
    except Exception:
        raise Problem(503, 'A fonte de dados não respondeu. Confira o aplicativo e tente novamente.') from None


def authorize(headers, secret):
    if len(secret) < 32 or not hmac.compare_digest(headers.get('Authorization', ''), 'Bearer ' + secret):
        raise Problem(403, 'Acesso não autorizado.')


def serve(dispatch):
    import threading
    slots = threading.BoundedSemaphore(6)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(90)

        def send(self, status, body):
            raw = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            for key, value in {'Content-Type': 'application/json', 'Content-Length': str(len(raw)), 'Cache-Control': 'no-store'}.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(raw)

        def run_request(self):
            if self.command == 'GET' and self.path == '/health':
                return self.send(200, {'status': 'ok'})
            if not slots.acquire(False):
                return self.send(429, {'error': 'Serviço ocupado.'})
            try:
                if self.headers.get('Transfer-Encoding'):
                    raise Problem(400, 'Formato não permitido.')
                size = int(self.headers.get('Content-Length', 0))
                if not 0 <= size <= LIMIT:
                    raise Problem(413, 'Pedido acima do limite.')
                data = json.loads(self.rfile.read(size)) if size else {}
                if not isinstance(data, dict):
                    raise Problem(400, 'Objeto JSON necessário.')
                result = dispatch(self.command, self.path, self.headers, data)
                self.send(202 if result is None else 200, result or {})
            except Problem as error:
                self.send(error.status, {'error': error.message})
            except (ValueError, KeyError, TypeError):
                self.send(400, {'error': 'Campos inválidos.'})
            except Exception:
                self.send(503, {'error': 'Não foi possível concluir a consulta.'})
            finally:
                slots.release()

        do_GET = run_request
        do_POST = run_request

    ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
