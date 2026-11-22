#!/bin/bash
set -euo pipefail
wger bootstrap --no-process-static
python3 manage.py shell -c "exec(open('/home/wger/src/init.py').read())"
exec /home/wger/entrypoint.sh
