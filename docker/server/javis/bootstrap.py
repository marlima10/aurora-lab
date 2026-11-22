"""One-time native Javis configuration. This program runs as its own container user."""
import json
from pathlib import Path
import config
import mcp_hub
import mcp_store

cfg = config.read_settings()
cfg['workspace_name'] = 'AuroraLAB'
cfg['setup_done'] = True
cfg.setdefault('locale', {}).update(ui_lang='pt', ui_lang_nguon='chon', tz='America/Sao_Paulo', currency='BRL')
cfg.setdefault('model', {})['claude_auto_update'] = False
cfg.setdefault('backup', {})['enabled'] = False
import os
if os.getenv('JAVIS_AI_PROVIDER') == 'gemini':
    cfg.setdefault('chat', {}).update(suggest_next=False, plan_tool=False)
    cfg.setdefault('model', {}).setdefault('auxiliary', {})['auto'] = False
cfg.setdefault('voice', {}).update(mode='standard', call_engine='basic', ear='off', stt_provider='browser', tts_provider='edge', edge_voice='pt-BR-FranciscaNeural')
config.write_settings(cfg)
brain = Path('/brains/auroralab')
for name in ('notes', 'reports'):
    (brain/name).mkdir(parents=True, exist_ok=True)
instructions = brain/'README.md'
if not instructions.exists():
    instructions.write_text('# AuroraLAB\n\nNotas e relatórios pessoais. Consulte os aplicativos pelas ferramentas aurora_. Não invente dados ausentes. Confirme o conteúdo antes de criar notas. Não envie credenciais ao modelo.\n')
# Use the same native vault in the browser and in the restricted Desktop bridge.
import default_brain
if not default_brain.pointer_path('/brains').exists():
    ok, reason = default_brain.set_folder('/brains', 'auroralab')
    if not ok: raise RuntimeError('Não foi possível selecionar o espaço de notas.')
secret = json.loads(Path('/run/secrets/mcp-bootstrap.json').read_text())['token']
if not any(c.get('label') == 'AuroraLAB' for c in mcp_store.list_connections()):
    cid, error = mcp_store.add_connection('custom', {'label': 'AuroraLAB', 'url': 'http://javis-mcp:8000/mcp',
        'transport': 'http', 'perm': 'readonly', 'auth': 'header', 'headers': {'Authorization': 'Bearer '+secret}})
    if error:
        raise RuntimeError('Não foi possível registrar o conector nativo.')
mcp_hub.hub_token()
print('Javis OS: conexão nativa AuroraLAB registrada, somente leitura.')
