"""Patch the exact pinned upstream source, refusing an unreviewed server revision."""
import hashlib
from pathlib import Path
import sys

path = Path(sys.argv[1])
expected = Path(__file__).with_name('opengym-server.sha256').read_text().strip()
raw = path.read_bytes()
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit('openGym source differs from the reviewed pinned revision')
text = raw.decode()
needle = 'function sessionOf(req) {\n'
if text.count(needle) != 1:
    raise SystemExit('openGym session entry point changed')
addition = '''  if (process.env.AURORA_SSO_ENABLED === '1') {
    const central = auroraSession(req, db.users);
    if (central) return central;
    // Paired machine clients (Garmin) retain the native bearer verification below.
    // Browser cookies alone cannot bypass the central session.
    if (!(req.headers.authorization || '').startsWith('Bearer ')) return null;
  }
'''
path.write_text("import { auroraSession } from './aurora-sso.js';\n" + text.replace(needle, needle + addition))
