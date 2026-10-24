"""Synthetic HA protocol tests, executed in the pinned HA runtime; no personal database."""
import json
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, TestServer
from ha_proxy import create_app

SECRET = 'fixture-private-proxy-secret-not-for-production'
OWNER = '1' * 32
OTHER = '2' * 32


class HomeAssistantIdentityTests(AioHTTPTestCase):
    async def get_application(self):
        self.native_calls = 0

        async def native_ws(request):
            self.assertNotIn('X-Aurora-Proxy-Secret', request.headers)
            self.assertNotIn('Cookie', request.headers)
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            await ws.send_json({'type':'auth_required','ha_version':'fixture'})
            auth = await ws.receive_json()
            user = {'owner-token':OWNER,'other-token':OTHER}.get(auth.get('access_token'))
            if not user:
                await ws.send_json({'type':'auth_invalid'})
                await ws.close()
                return ws
            await ws.send_json({'type':'auth_ok','ha_version':'fixture'})
            async for message in ws:
                data = json.loads(message.data)
                result = {'id':user} if data.get('type') == 'auth/current_user' else {'native_user':user}
                await ws.send_json({'id':data['id'],'type':'result','success':True,'result':result})
            return ws

        async def native_http(request):
            self.assertNotIn('X-Aurora-Proxy-Secret', request.headers)
            self.assertNotIn('Cookie', request.headers)
            self.native_calls += 1
            if request.path == '/auth/token':
                data = await request.post()
                return web.json_response({'access_token':data.get('refresh_token','owner-token'), 'refresh_token':'fixture-refresh'})
            return web.json_response({'ok':True,'alias':request.headers.get('X-Forwarded-For')})

        native = web.Application()
        native.router.add_get('/api/websocket', native_ws)
        native.router.add_route('*','/{path:.*}',native_http)
        self.native = TestServer(native)
        await self.native.start_server()
        return create_app(str(self.native.make_url('')).rstrip('/'), SECRET)

    async def tearDownAsync(self):
        await super().tearDownAsync()
        await self.native.close()

    def headers(self, user=OWNER):
        return {'X-Aurora-Proxy-Secret':SECRET,'X-Aurora-Identity':user,'X-Forwarded-For':'198.18.0.2',
                'Cookie':'__Host-aurora_session=fixture-only'}

    async def test_missing_secret_or_invalid_alias_denied_before_native_request(self):
        for headers in ({}, self.headers() | {'X-Aurora-Proxy-Secret':'forged'}, self.headers() | {'X-Forwarded-For':'192.168.0.1'}):
            response = await self.client.get('/api/test',headers=headers)
            self.assertEqual(response.status,403)
        self.assertEqual(self.native_calls,0)

    async def test_http_token_bound_to_native_identity_and_cache_is_not_shared_across_users(self):
        headers=self.headers()|{'Authorization':'Bearer owner-token'}
        response=await self.client.get('/api/test',headers=headers)
        self.assertEqual(response.status,200)
        self.assertEqual((await response.json())['alias'],'198.18.0.2')
        response=await self.client.get('/api/test',headers=headers|{'X-Aurora-Identity':OTHER})
        self.assertEqual(response.status,401)
        self.assertEqual(self.native_calls,1)

    async def test_wrong_refresh_token_never_reaches_browser(self):
        response=await self.client.post('/auth/token',headers=self.headers(),data={'refresh_token':'other-token'})
        self.assertEqual(response.status,400)
        self.assertEqual(await response.json(),{'error':'invalid_grant'})

    async def test_correct_refresh_flow_still_works(self):
        response=await self.client.post('/auth/token',headers=self.headers(),data={'refresh_token':'owner-token'})
        self.assertEqual(response.status,200)
        self.assertEqual((await response.json())['access_token'],'owner-token')

    async def test_websocket_rejects_a_different_native_user(self):
        async with self.client.ws_connect('/api/websocket',headers=self.headers()) as ws:
            self.assertEqual((await ws.receive_json())['type'],'auth_required')
            await ws.send_json({'type':'auth','access_token':'other-token'})
            self.assertEqual((await ws.receive_json())['type'],'auth_invalid')

    async def test_websocket_hides_identity_probe_and_forwards_normal_native_messages(self):
        async with self.client.ws_connect('/api/websocket',headers=self.headers()) as ws:
            await ws.receive_json()
            await ws.send_json({'type':'auth','access_token':'owner-token'})
            self.assertEqual((await ws.receive_json())['type'],'auth_ok')
            await ws.send_json({'id':1,'type':'get_states'})
            result=await ws.receive_json()
            self.assertEqual(result['id'],1)
            self.assertEqual(result['result']['native_user'],OWNER)


if __name__ == '__main__':
    import unittest
    unittest.main()
