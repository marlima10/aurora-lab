"""Bind Home Assistant HTTP/WebSocket tokens to the identity authorized by central SSO.

Only the private gateway may call this adapter. Native authentication and refresh flows
remain in Home Assistant; an old token for a different person must not override SSO.
"""
import asyncio
import hashlib
import hmac
import ipaddress
import json
import os
import re
import time

from aiohttp import ClientSession, ClientTimeout, WSMsgType, web

HOP = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailer', 'transfer-encoding', 'upgrade', 'content-length'}


def identity(headers, secret):
    supplied = headers.get('X-Aurora-Proxy-Secret', '')
    if not hmac.compare_digest(supplied.encode(), secret.encode()):
        raise web.HTTPForbidden(text='SSO required')
    user = headers.get('X-Aurora-Identity', '')
    if not re.fullmatch('[a-f0-9]{32}', user):
        raise web.HTTPForbidden(text='Mapped identity required')
    try:
        address = ipaddress.ip_address(headers.get('X-Forwarded-For', ''))
    except ValueError:
        raise web.HTTPForbidden(text='Private identity alias required')
    if address not in ipaddress.ip_network('198.18.0.0/24'):
        raise web.HTTPForbidden(text='Private identity alias required')
    return user


def headers_for(headers):
    return {k.lower(): v for k, v in headers.items() if k.lower() not in HOP and not k.lower().startswith(('x-aurora-', 'sec-websocket-')) and k.lower() != 'cookie'}


async def authorize_socket(socket, auth, wanted):
    await socket.send_json(auth)
    result = await socket.receive_json(timeout=15)
    if result.get('type') != 'auth_ok':
        return False
    # Consume this internal response before handing the channel to the browser.
    probe = 9007199254740991
    await socket.send_json({'id': probe, 'type': 'auth/current_user'})
    result = await socket.receive_json(timeout=15)
    return result.get('id') == probe and result.get('success') is True and result.get('result', {}).get('id') == wanted


def create_app(upstream, secret):
    if len(secret) < 32 or not upstream.startswith('http://') or upstream.rstrip('/') != upstream:
        raise ValueError('Private fixed upstream and proxy secret required')
    app = web.Application(client_max_size=48 * 1024 * 1024)
    app['cache'] = {}

    async def clients(app):
        async with ClientSession(timeout=ClientTimeout(total=None, sock_connect=10, sock_read=300), auto_decompress=False) as client:
            app['client'] = client
            yield
    app.cleanup_ctx.append(clients)

    async def token_matches(token, wanted, headers):
        if not isinstance(token, str) or len(token) > 4096:
            return False
        cache = app['cache']
        key = (hashlib.sha256(token.encode()).hexdigest(), wanted)
        if cache.get(key, 0) > time.monotonic():
            return True
        async with app['client'].ws_connect(upstream + '/api/websocket', headers=headers) as ws:
            hello = await ws.receive_json(timeout=15)
            if hello.get('type') != 'auth_required':
                return False
            if not await authorize_socket(ws, {'type':'auth', 'access_token':token}, wanted):
                return False
        if len(cache) >= 512:
            cache.clear()
        cache[key] = time.monotonic() + 20
        return True

    async def proxy(request):
        if request.path == '/health':
            return web.json_response({'status': 'ok'})
        wanted = identity(request.headers, secret)
        headers = headers_for(request.headers)
        target = upstream + request.rel_url.raw_path_qs
        if request.headers.get('Upgrade', '').lower() == 'websocket':
            async with app['client'].ws_connect(target, headers=headers, autoping=True) as backend:
                hello = await backend.receive_json(timeout=15)
                if hello.get('type') != 'auth_required':
                    raise web.HTTPBadGateway(text='Unexpected native authentication')
                browser = web.WebSocketResponse(heartbeat=30, max_msg_size=5 * 1024 * 1024)
                await browser.prepare(request)
                await browser.send_json(hello)
                try:
                    message = await browser.receive_json(timeout=15)
                    # Validate ownership on a separate socket. HA requires increasing command
                    # IDs; an internal probe on the browser channel would consume its ID space.
                    if message.get('type') != 'auth' or not await token_matches(message.get('access_token'), wanted, headers):
                        await browser.send_json({'type':'auth_invalid', 'message':'Entre no perfil autorizado pelo AuroraLAB.'})
                        await browser.close()
                        return browser
                    await backend.send_json(message)
                    native_auth = await backend.receive_json(timeout=15)
                    if native_auth.get('type') != 'auth_ok':
                        await browser.send_json({'type':'auth_invalid', 'message':'A sessão nativa não está válida.'})
                        await browser.close()
                        return browser
                    await browser.send_json(native_auth)

                    async def pump(source, destination):
                        async for message in source:
                            if message.type == WSMsgType.TEXT:
                                await destination.send_str(message.data)
                            elif message.type == WSMsgType.BINARY:
                                await destination.send_bytes(message.data)
                            elif message.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                                break
                    tasks = [asyncio.create_task(pump(browser, backend)), asyncio.create_task(pump(backend, browser))]
                    try:
                        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    finally:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                finally:
                    await browser.close()
                return browser

        authorization = request.headers.get('Authorization', '')
        if authorization.startswith('Bearer ') and not await token_matches(authorization[7:], wanted, headers):
            raise web.HTTPUnauthorized(text='Token belongs to a different or invalid native profile')
        # Bounded request body; native limits still apply downstream.
        body = await request.read()
        if request.path == '/auth/token':
            headers['accept-encoding'] = 'identity'
        async with app['client'].request(request.method, target, headers=headers, data=body, allow_redirects=False) as response:
            response_headers = {k: v for k, v in response.headers.items() if k.lower() not in HOP}
            if request.path == '/auth/token' and response.status == 200:
                raw = await response.content.read(65537)
                if len(raw) > 65536:
                    raise web.HTTPBadGateway(text='Unexpected token response')
                if not raw:
                    # Native revocation returns an empty 200 for both URL-encoded
                    # and browser multipart forms. No access token is disclosed.
                    return web.Response(body=raw, status=response.status, headers=response_headers)
                payload = json.loads(raw)
                if not await token_matches(payload.get('access_token'), wanted, headers):
                    return web.json_response({'error':'invalid_grant'}, status=400, headers={'Cache-Control':'no-store'})
                return web.Response(body=raw, status=response.status, headers=response_headers)
            result = web.StreamResponse(status=response.status, headers=response_headers)
            await result.prepare(request)
            async for chunk in response.content.iter_chunked(65536):
                await result.write(chunk)
            await result.write_eof()
            return result

    app.router.add_route('*', '/{path:.*}', proxy)
    return app


if __name__ == '__main__':
    app = create_app(os.environ['HA_NATIVE_UPSTREAM'], os.environ['AURORA_SSO_SECRET'])
    web.run_app(app, host='0.0.0.0', port=8123, access_log=None, print=None)
