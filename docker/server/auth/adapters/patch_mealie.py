"""Fail closed when the reviewed native Mealie entry point changes."""
from pathlib import Path
import hashlib
import sys

path = Path(sys.argv[1])
raw = path.read_bytes()
expected = '6480cfcf42008d4b1195e11e02931ce7e2f2700900a8417294e4a4c759dfdcc2'
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit('Mealie entry point differs from reviewed revision')
insertion = '\nfrom aurora_mealie import AuroraIdentityMiddleware\napp.add_middleware(AuroraIdentityMiddleware)\n\n'
text = raw.decode()
anchor = '\nif __name__ == "__main__":'
if text.count(anchor) != 1:
    raise SystemExit('Mealie entry point anchor is ambiguous')
path.write_text(text.replace(anchor, insertion + anchor))
