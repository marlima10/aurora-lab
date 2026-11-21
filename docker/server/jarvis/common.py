"""Bounded private RPC shared by the isolated AuroraLAB Jarvis services."""
import json
import os
import secrets
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_BODY = 12 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


def config():
    return json.loads(Path(os.environ.get('CONFIG_FILE', '/run/secrets/config.json')).read_text())


def rpc(url, data=None, token=None, headers=None, timeout=120):
    h = {'Content-Type': 'application/json'} | (headers or {})
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=h)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read(MAX_BODY + 1)
        if len(raw) > MAX_BODY:
            raise Problem(502, 'Resposta excedeu o limite.')
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise Problem(503 if error.code >= 500 else error.code, 'O serviço solicitado recusou a operação (HTTP %s).' % error.code) from None
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        raise Problem(503, 'Serviço indisponível ou resposta inválida. Tente novamente.') from None


def text(value, maximum=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\x00' in value:
        raise Problem(400, 'Texto vazio ou acima do limite permitido.')
    return value.strip()


def authorize(headers, expected):
    supplied = headers.get('Authorization', '')
    if len(expected) < 32 or not secrets.compare_digest(supplied, 'Bearer ' + expected):
        raise Problem(403, 'Acesso interno não autorizado.')


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32


def serve(dispatch, health=lambda: {'status': 'ok'}, port=8000):
    import threading
    slots = threading.BoundedSemaphore(4)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Bodies, credentials and personal data must not be logged.

        def setup(self):
            super().setup()
            self.connection.settimeout(180)

        def handle_request(self):
            acquired = False
            try:
                if self.command == 'GET' and self.path == '/health':
                    return self.send(200, health())
                acquired = slots.acquire(blocking=False)
                if not acquired:
                    raise Problem(429, 'Serviço ocupado. Aguarde a operação atual.')
                if self.headers.get('Transfer-Encoding'):
                    raise Problem(400, 'Formato de envio não aceito.')
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    raise Problem(400, 'Tamanho inválido.')
                if size < 0 or size > MAX_BODY:
                    raise Problem(413, 'Envio acima do limite de 12 MiB.')
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise Problem(400, 'Envio incompleto.')
                data = json.loads(raw) if raw else {}
                if not isinstance(data, dict):
                    raise Problem(400, 'Objeto JSON necessário.')
                value = dispatch(self.command, self.path, self.headers, data)
                self.send(200, value)
            except Problem as error:
                self.send(error.status, {'error': error.message})
            except (ValueError, KeyError, TypeError):
                self.send(400, {'error': 'Campos inválidos. Confira os dados enviados.'})
            except Exception:
                self.send(503, {'error': 'Não foi possível concluir a operação. Nenhuma confirmação de sucesso foi recebida.'})
            finally:
                if acquired:
                    slots.release()

        def send(self, status, value):
            raw = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            for key, val in {'Content-Type': 'application/json; charset=utf-8', 'Content-Length': str(len(raw)),
                             'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}.items():
                self.send_header(key, val)
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        do_GET = handle_request
        do_POST = handle_request

    Server(('0.0.0.0', port), Handler).serve_forever()
