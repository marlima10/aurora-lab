"""Optional real local-model rehearsal; only an ephemeral fictitious user/store.

Run in an isolated temporary container with the Jarvis network/config, not the
production app volume. This script never calls a native application connector.
"""
import json
import os
from pathlib import Path
import tempfile
import time

with tempfile.TemporaryDirectory() as directory:
    os.environ['DB_PATH'] = str(Path(directory)/'fixture.sqlite3')
    import api
    session = {'email': 'fixture@example.invalid', 'csrf': 'fixture-csrf', 'grants': {'portal': 'fixture'}}
    original_rpc = api.rpc

    def request(url, *args, **kwargs):
        if url == 'http://auth:7777/auth/session':
            return dict(session)
        if url != 'http://jarvis-engine:8000/generate':
            raise AssertionError('Unexpected external call in fixture')
        return original_rpc(url, *args, **kwargs)

    api.rpc = request
    job = {'owner': session['email'], 'cookie': 'fixture-only', 'status': 'running', 'created': time.time()}
    api.BUSY.acquire()
    started = time.monotonic()
    api.chat(session, 'Use a ferramenta note_save para propor uma nota com este texto exato: Comprar filamento PLA amanhã. Aguarde minha confirmação.', job)
    assert job['status'] == 'done', job.get('error')
    proposals = api.STORE.proposals(session['email'])
    assert len(proposals) == 1, job.get('answer')
    assert proposals[0]['tool'] == 'note_save'
    assert api.STORE.notes(session['email']) == []
    name, args = api.STORE.claim(session['email'], proposals[0]['id'])
    result = api.call_tool(session, name, args, confirmed=True)
    assert result['saved'] is True
    assert len(api.STORE.notes(session['email'])) == 1
    assert api.STORE.notes('other@example.invalid') == []
    print(json.dumps({'realLocalModel': True, 'seconds': round(time.monotonic()-started, 2),
                      'nativeToolSelected': True, 'noWriteBeforeConfirmation': True,
                      'confirmedSyntheticNoteSaved': True, 'userIsolation': True,
                      'personalDatabaseUsed': False}))
