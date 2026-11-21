"""Real native Javis session behind the central AuroraLAB administrator SSO."""
import hmac
import json
from pathlib import Path
import config
import main

SESSION = ''
ASSETS = Path('/opt/aurora')


async def reply(send, status, value, mime='application/json'):
    raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
    await send({'type': 'http.response.start', 'status': status, 'headers': [(b'content-type', mime.encode()), (b'content-length', str(len(raw)).encode()), (b'cache-control', b'no-store')]})
    await send({'type': 'http.response.body', 'body': raw})


class AuroraSSO:
    async def __call__(self, scope, receive, send):
        global SESSION
        if scope['type'] not in ('http', 'websocket'):
            return await main.app(scope, receive, send)
        path = scope.get('path', '')
        headers = {k.decode().lower(): v.decode() for k, v in scope.get('headers', [])}
        local = (scope.get('client') or ('',))[0] in ('127.0.0.1', '::1')
        if scope['type'] == 'http' and (path == '/health' or (local and path == '/hub/mcp')):
            return await main.app(scope, receive, send)
        cfg = json.loads(Path('/run/secrets/aurora.json').read_text())
        valid = (len(cfg['secret']) >= 32 and hmac.compare_digest(headers.get('x-aurora-proxy-secret', ''), cfg['secret'])
                 and hmac.compare_digest(headers.get('x-aurora-identity', ''), cfg['owner']))
        if not valid:
            if scope['type'] == 'websocket':
                return await send({'type': 'websocket.close', 'code': 1008})
            return await reply(send, 403, {'error': 'Entre pelo login do AuroraLAB.'})
        if scope['type'] == 'http':
            if path in ('/aurora-mode.js', '/aurora-mode.css'):
                mime = 'text/javascript' if path.endswith('.js') else 'text/css'
                return await reply(send, 200, (ASSETS/path.lstrip('/')).read_bytes(), mime)
            if path.startswith('/auth/') and scope.get('method') not in ('GET', 'HEAD'):
                return await reply(send, 403, {'error': 'O acesso é gerenciado pelo AuroraLAB.'})
        if scope['type'] == 'websocket' and path.startswith('/ws'):
            await receive()
            await send({'type': 'websocket.accept'})
            await send({'type': 'websocket.send', 'text': json.dumps({'type': 'error', 'message': 'Converse no Claude Desktop. O plano gratuito não ativa o chat interno.', 'text': 'Use o Claude Desktop conectado ao AuroraLAB.'})})
            return await send({'type': 'websocket.close', 'code': 1000})
        if not SESSION or not config.valid_session(SESSION):
            SESSION = config.new_session(ua='AuroraLAB SSO')
        # Client cookies never choose the native owner session.
        clean = [(k, v) for k, v in scope.get('headers', []) if k.lower() != b'cookie']
        scope = dict(scope, headers=clean + [(b'cookie', ('javis_session=' + SESSION).encode())])
        await main.app(scope, receive, send)


app = AuroraSSO()
