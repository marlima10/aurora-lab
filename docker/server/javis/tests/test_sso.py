import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class NativeSSOTests(unittest.TestCase):
    def setUp(self):
        self.captured = None

        async def native(scope, receive, send):
            self.captured = scope
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'ok'})

        config = types.SimpleNamespace(valid_session=lambda token: token == 'fixture-native', new_session=lambda **kwargs: 'fixture-native')
        self.modules = patch.dict(sys.modules, {'config': config, 'main': types.SimpleNamespace(app=native)})
        self.modules.start()
        path = Path(__file__).resolve().parents[1]/'aurora_entry.py'
        spec = importlib.util.spec_from_file_location('aurora_test_entry', path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.secret = patch.object(self.module.Path, 'read_text', return_value=json.dumps({'owner': 'fixture@example.invalid', 'secret': 'x'*48}))
        self.secret.start()

    def tearDown(self):
        self.secret.stop()
        self.modules.stop()

    def request(self, path, headers=(), method='GET', websocket=False, client='198.18.0.1'):
        events = []
        async def receive():
            return {'type': 'websocket.connect' if websocket else 'http.request', 'body': b''}
        async def send(event):
            events.append(event)
        scope = {'type': 'websocket' if websocket else 'http', 'path': path, 'method': method, 'headers': list(headers), 'client': (client, 1234)}
        asyncio.run(self.module.AuroraSSO()(scope, receive, send))
        return events

    def trusted(self):
        return [(b'x-aurora-identity', b'fixture@example.invalid'), (b'x-aurora-proxy-secret', b'x'*48)]

    def test_native_credentials_cannot_bypass_proxy_identity(self):
        result = self.request('/settings', [(b'cookie', b'javis_session=fixture-native')])
        self.assertEqual(result[0]['status'], 403)

    def test_owner_gets_real_native_session(self):
        result = self.request('/settings', self.trusted()+[(b'cookie', b'javis_session=forged')])
        self.assertEqual(result[0]['status'], 200)
        self.assertEqual(dict(self.captured['headers'])[b'cookie'], b'javis_session=fixture-native')

    def test_native_account_changes_are_not_an_alternate_login(self):
        self.assertEqual(self.request('/auth/setup', self.trusted(), method='POST')[0]['status'], 403)

    def test_health_is_public_but_mcp_requires_local_transport(self):
        self.assertEqual(self.request('/health')[0]['status'], 200)
        self.assertEqual(self.request('/hub/mcp')[0]['status'], 403)
        self.assertEqual(self.request('/hub/mcp', client='127.0.0.1')[0]['status'], 200)

    def test_paid_chat_socket_is_disabled_in_desktop_mode(self):
        events = self.request('/ws', self.trusted(), websocket=True)
        self.assertEqual(events[-1]['type'], 'websocket.close')
        self.assertIn('Claude Desktop', events[1]['text'])


if __name__ == '__main__':
    unittest.main()
