"""Disposable UI rehearsal only; never run with production data or a published port."""
import os
from pathlib import Path
import tempfile
from server import BoundedHTTPServer, handler
from store import Store, ADMIN_EMAIL

if __name__ == '__main__':
    if os.environ.get('AURORA_DISPOSABLE_FIXTURE') != '1':
        raise SystemExit('Explicit disposable fixture flag required')
    with tempfile.TemporaryDirectory() as temporary:
        store = Store(Path(temporary) / 'fixture.sqlite3')
        store.initialize()
        # Known fixture keys are restricted to this disposable database.
        from store import digest
        user_key = store.issue(ADMIN_EMAIL, 'person@example.test', {})
        with store.db() as db:
            db.execute('UPDATE users SET key_hash=? WHERE email=?', (digest('A'*151), ADMIN_EMAIL))
            db.execute('UPDATE users SET key_hash=? WHERE email=?', (digest('B'*151), 'person@example.test'))
        apps = {'homeboard':{'ready':False,'identities':{'viewer':'viewer','editor':'editor'},
                             'labels':{'viewer':'Somente visualizar','editor':'Editar painel'}}}
        BoundedHTTPServer(('0.0.0.0',7777), handler(store, os.environ['AUTH_ORIGIN'], apps_config=apps)).serve_forever()
