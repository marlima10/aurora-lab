"""Adapt the pinned HomeBoard Auth class; source must match the reviewed checksum."""
from pathlib import Path
import hashlib
import sys

path = Path(sys.argv[1])
raw = path.read_bytes()
expected = Path(__file__).with_name('homeboard-auth.sha256').read_text().strip()
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit('HomeBoard auth source differs from reviewed revision')
text = raw.decode()
text = text.replace("import crypto from 'node:crypto';", "import crypto from 'node:crypto';\nimport { auroraEditor, ssoEnabled } from './aurora-auth.mjs';", 1)
text = text.replace('session(req){', 'session(req){if(ssoEnabled())return auroraEditor(req);', 1)
text = text.replace('configured:!!this.record', 'configured:ssoEnabled()||!!this.record')
text = text.replace('editable:!this.record||this.session(req)', 'editable:ssoEnabled()?this.session(req):!this.record||this.session(req)')
text = text.replace('if(this.record&&!this.session(req))', 'if((ssoEnabled()||this.record)&&!this.session(req))')
text = text.replace('async setup(req,password){', "async setup(req,password){if(ssoEnabled())throw Error('Use o administrador central AuroraLAB');", 1)
text = text.replace('async disable(req){', "async disable(req){if(ssoEnabled())throw Error('Use o administrador central AuroraLAB');", 1)
path.write_text(text)
