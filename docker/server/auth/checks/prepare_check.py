"""Preparation regression checks: fixtures only; never a live deployment root."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare
from store import ADMIN_EMAIL, Store


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'secrets').mkdir()
        (self.root/'secrets/apps23-initial.json').write_text(json.dumps({'actual':{'password':'fixture_actual_password_000000000000000'}}))
        (self.root/'secrets/power-admin.key').write_text('fixture_power_secret_000000000000000')
        (self.root/'.env').write_text('COMPOSE_FILE=compose.server.yaml\nOPENGYM_ORIGIN=https://fixture.example.ts.net:8081\n')
        (self.root/'docker/server').mkdir(parents=True)
        (self.root/'docker/server/nginx.conf').write_text('server {\nlocation / { proxy_pass http://monitor; }\n}\n')
        identities = {'manyfold':'user@example.test','mealie':'user@example.test','actual':'shared',
                      'opengym':'existing','octoprint':'fixture','homeassistant':'1'*32,'homeboard':'editor','cockpit':'fixture'}
        self.inventory = {'apps':{a:{'identities':{i:'198.18.0.10' if a=='homeassistant' else i}} for a,i in identities.items()},
                          'admin_grants':identities}
        self.mapping = self.root/'mapping.json'
        self.mapping.write_text(json.dumps(self.inventory))
        self.original_env = (self.root/'.env').read_bytes()
        self.patch = patch.object(prepare.os,'chown',create=True)
        self.chown = self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_preparation_is_idempotent_and_does_not_activate_or_change_original_env(self):
        result = prepare.prepare(self.root, self.mapping)
        self.assertFalse(result['production_configuration_changed'])
        key_path = self.root/'secrets/sso/admin-initial.key'
        key = key_path.read_bytes()
        self.assertEqual(len(key.decode().splitlines()[1]),151)
        config = (self.root/'secrets/sso/apps.json').read_bytes()
        self.assertFalse(any(v.get('ready') for k,v in json.loads(config).items() if not k.startswith('_')))
        prepare.prepare(self.root,self.mapping)
        self.assertEqual(key,key_path.read_bytes())
        self.assertEqual(config,(self.root/'secrets/sso/apps.json').read_bytes())
        self.assertEqual(self.original_env,(self.root/'.env').read_bytes())
        store = Store(self.root/'data/auth/auth.sqlite3')
        token,_ = store.authenticate(ADMIN_EMAIL,key.decode().splitlines()[1],'fixture')
        self.assertEqual(set(store.session(token)['grants']),set(self.inventory['apps'])|{'portal'})
        self.chown.assert_any_call(self.root/'secrets/sso/monitor.key',65534,65534)

    def test_missing_or_root_identity_is_rejected_before_private_files(self):
        self.inventory['admin_grants']['cockpit']='root'
        self.inventory['apps']['cockpit']['identities']={'root':'root'}
        self.mapping.write_text(json.dumps(self.inventory))
        self.assertRaises(ValueError,prepare.prepare,self.root,self.mapping)
        self.assertFalse((self.root/'data/auth').exists())

    def test_existing_private_key_is_never_silently_overwritten_without_database(self):
        folder=self.root/'secrets/sso';folder.mkdir()
        key=folder/'admin-initial.key';key.write_text('existing-do-not-rotate')
        self.assertRaises(ValueError,prepare.prepare,self.root,self.mapping)
        self.assertEqual(key.read_text(),'existing-do-not-rotate')


if __name__=='__main__':
    unittest.main()
