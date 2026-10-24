"""Bind every native Mealie request to the gateway's existing user identity.

No users are created and no database records are migrated. Native JWTs remain
native; client-supplied JWTs cannot choose a different profile behind the gateway.
"""
import asyncio
import hmac
import os


class AuroraIdentityMiddleware:
    def __init__(self, app):
        self.app = app

    @staticmethod
    def native_session(identity):
        from mealie.db.db_setup import session_context
        from mealie.core.security.providers.reverse_proxy_provider import ReverseProxyProvider
        from mealie.core.config import get_app_settings
        if get_app_settings().REVERSE_PROXY_AUTH_SIGNUP_ENABLED:
            raise RuntimeError('SSO requires native automatic signup disabled')
        with session_context() as session:
            return ReverseProxyProvider(session, identity).authenticate()

    async def __call__(self, scope, receive, send):
        if scope['type'] not in ('http', 'websocket'):
            return await self.app(scope, receive, send)
        # Only the native health response is public inside the private Docker network.
        if scope.get('path') == '/api/app/about':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        expected = os.environ.get('REVERSE_PROXY_AUTH_SECRET', '').encode()
        supplied = headers.get(b'x-mealie-reverse-proxy-secret', b'')
        identity = headers.get(b'x-aurora-identity', b'').decode('utf-8', errors='replace')
        valid = len(expected) >= 32 and hmac.compare_digest(expected, supplied) and identity and len(identity) <= 254
        auth = await asyncio.to_thread(self.native_session, identity) if valid else None
        if not auth:
            if scope['type'] == 'websocket':
                return await send({'type': 'websocket.close', 'code': 1008})
            await send({'type': 'http.response.start', 'status': 403, 'headers': [(b'cache-control', b'no-store')]})
            return await send({'type': 'http.response.body', 'body': b'Central identity required'})
        token, duration = auth
        scope = dict(scope)
        scope['headers'] = [(k, v) for k, v in scope['headers'] if k.lower() != b'authorization']
        scope['headers'].append((b'authorization', ('Bearer ' + token).encode()))
        cookies = []
        if scope['type'] == 'http':
            from starlette.requests import Request
            from starlette.responses import Response
            from mealie.routes.auth.auth import set_session_cookie
            response = Response()
            set_session_cookie(response, Request(scope), token, duration, remember_me=False)
            cookies = [(k, v) for k, v in response.raw_headers if k == b'set-cookie']
            # A fresh browser visits the application, without a second login form.
            if scope.get('path', '').rstrip('/') in ('/login', '/login/reverse-proxy'):
                await send({'type': 'http.response.start', 'status': 303,
                            'headers': cookies + [(b'location', b'/'), (b'cache-control', b'no-store')]})
                return await send({'type': 'http.response.body', 'body': b''})

        async def authenticated_send(message):
            if message['type'] == 'http.response.start':
                message = dict(message)
                message['headers'] = list(message.get('headers', [])) + cookies
            await send(message)
        await self.app(scope, receive, authenticated_send)
