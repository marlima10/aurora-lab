import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONF = (ROOT / 'docker/server/nginx.conf').read_text(encoding='utf-8')
SNIPPET = (ROOT / 'docker/server/nginx-security-headers.conf').read_text(encoding='utf-8')
INCLUDE = 'include /etc/nginx/aurora-security-headers.conf;'


def location_blocks(text):
    """Retorna (cabecalho, corpo) de cada location, sem aninhamento."""
    return [(m.group(1).strip(), m.group(2)) for m in re.finditer(r'location\s+([^{]+)\{([^{}]*)\}', text)]


class NginxSecurityHeadersTest(unittest.TestCase):
    def test_snippet_has_all_headers(self):
        for name in ('X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy',
                     'Permissions-Policy', 'Content-Security-Policy'):
            self.assertRegex(SNIPPET, r'add_header\s+' + name + r'\s')
        directives = re.findall(r'^add_header\s.*$', SNIPPET, re.M)
        self.assertEqual(len(directives), 5)
        for line in directives:
            self.assertTrue(line.endswith('always;'), line)

    def test_server_and_every_location_with_add_header_include_snippet(self):
        self.assertIn(INCLUDE, CONF.split('location', 1)[0])
        blocks = location_blocks(CONF)
        self.assertGreater(len(blocks), 10)
        for head, body in blocks:
            if 'add_header' in body:
                self.assertIn(INCLUDE, body, f'location {head} perde os cabecalhos de seguranca')

    def test_server_tokens_off(self):
        self.assertIn('server_tokens off;', CONF)

    def test_post_limits_only_count_post(self):
        self.assertIn('map $request_method $aurora_post_key { default ""; POST $binary_remote_addr; }', CONF)
        power = dict(location_blocks(CONF))['^~ /api/power']
        api = dict(location_blocks(CONF))['= /fitness-api']
        self.assertIn('limit_req zone=aurora_power_post', power)
        self.assertIn('limit_req zone=aurora_api_post', api)
        for body in (power, api):
            self.assertIn('error_page 429 @aurora_rate_limited;', body)
        self.assertIn('location @aurora_rate_limited', CONF)

    def test_camera_stream_not_cached(self):
        self.assertIn('Cache-Control "no-store"', dict(location_blocks(CONF))['= /camera-stream'])

    def test_compose_mounts_snippet(self):
        compose = (ROOT / 'compose.server.yaml').read_text(encoding='utf-8')
        self.assertIn('./docker/server/nginx-security-headers.conf:/etc/nginx/aurora-security-headers.conf:ro', compose)


class ServiceWorkerVersionsTest(unittest.TestCase):
    CHANGED = ('aurora-layout.css', 'aurora-layout.js', 'power.css', 'power.js', 'fitness.js',
               'fitness-planos.js', 'fitness-guided.js', 'fitness-exercicios.js', 'fitness-plan-card.js')

    def test_pages_match_app_shell_versions(self):
        shell = (ROOT / 'site/service-worker.js').read_text(encoding='utf-8')
        for name in self.CHANGED:
            cached = re.search(r"'/" + re.escape(name) + r"\?v=([^']+)'", shell)
            self.assertIsNotNone(cached, name)
            for page in (ROOT / 'site').glob('*.html'):
                for version in re.findall(r'/' + re.escape(name) + r'\?v=([^"\']+)', page.read_text(encoding='utf-8')):
                    self.assertEqual(version, cached.group(1), f'{page.name} usa versao diferente de {name}')


if __name__ == '__main__':
    unittest.main()
