import http.client
import os
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import monitor


class ServiceLinksTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'OPENGYM_ORIGIN': 'https://example.tail123.ts.net:8081', 'HOMEBOARD_ORIGIN': 'https://example.tail123.ts.net:8090'})
        self.env.start()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), monitor.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.env.stop()

    def request(self, path, host='100.80.213.50'):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        connection.request('GET', path, headers={'Host': host})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders())
        response.read()
        connection.close()
        return result

    def test_redirects_from_ip_domain_and_lan(self):
        destinations = {'/manyfold':':3214/','/mealie':':9925/','/actual':':5006/','/octoprint': ':5000/', '/cockpit': ':9090/', '/homeassistant': ':8123/', '/opengym': ':8081', '/garmin': ':8081/garmin/', '/homeboard': ':8090'}
        for host in ('100.80.213.50', '192.168.0.25', 'example.tail123.ts.net', 'attacker.invalid'):
            for path, suffix in destinations.items():
                with self.subTest(host=host, path=path):
                    status, headers = self.request(path, host)
                    self.assertEqual(status, 302)
                    self.assertEqual(headers['Location'], 'https://example.tail123.ts.net' + suffix)
                    self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_missing_or_unsafe_origin_is_unavailable(self):
        for value in ('', 'http://example.tail123.ts.net:8081', 'https://example.com:8081', 'https://example.ts.net:5000', 'https://user:secret@example.ts.net:8081', 'https://example.ts.net:8081/path', 'https://example.ts.net:8081?x=1', 'https://example.ts.net:8081#x', 'https://example.ts.net:invalid', 'https://example.ts.net:8081\r\nX-Test:yes'):
            with self.subTest(origin=value), patch.dict(os.environ, {'OPENGYM_ORIGIN': value}):
                status, headers = self.request('/cockpit')
                self.assertEqual(status, 503)
                self.assertNotIn('Location', headers)

    def test_homeboard_has_independent_origin(self):
        with patch.dict(os.environ, {'HOMEBOARD_ORIGIN': ''}):
            self.assertEqual(self.request('/homeboard')[0], 503)
            self.assertEqual(self.request('/octoprint')[0], 302)


if __name__ == '__main__':
    unittest.main()
