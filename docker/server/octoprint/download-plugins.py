"""Download upstream plugin sources pinned by commit and SHA-256."""
import hashlib
import json
import pathlib
import urllib.request

root = pathlib.Path(__file__).resolve().parent
sources = pathlib.Path('/tmp/aurora-plugins')
sources.mkdir(parents=True, exist_ok=True)
for item in json.loads((root / 'plugins.lock.json').read_text()):
    target = sources / (item['plugin'] + '.zip')
    url = 'https://codeload.github.com/' + item['repo'] + '/zip/' + item['commit']
    request = urllib.request.Request(url, headers={'User-Agent': 'AuroraLAB-build'})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != item['sha256']:
        raise RuntimeError('SHA-256 divergente: ' + item['plugin'])
    target.write_bytes(payload)
    print('Fonte verificada:', item['plugin'], flush=True)
