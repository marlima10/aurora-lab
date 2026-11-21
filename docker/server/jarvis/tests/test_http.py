"""Real HTTP fixture: cookies, CSRF, per-user scope, and internal RPC authentication."""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))


class HTTPPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ['DB_PATH'] = str(Path(cls.tmp.name)/'fixture.sqlite3')
        import api
        cls.api = api
        cls.session = {'email': 'fixture@example.invalid', 'csrf': 'fixture-csrf', 'grants': {'portal': 'fixture'}}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_spoofed_identity_header_is_not_a_login(self):
        from common import Problem
        with patch.object(self.api, 'config', return_value={'origin': 'https://fixture.invalid'}):
            with self.assertRaises(Problem):
                self.api.current({'X-Aurora-Identity': 'admin@example.invalid'}, 'GET')

    def test_mutations_require_origin_and_csrf(self):
        from common import Problem
        with patch.object(self.api, 'config', return_value={'origin': 'https://fixture.invalid'}), patch.object(self.api, 'rpc', return_value=self.session):
            with self.assertRaises(Problem):
                self.api.current({'Cookie': 'fixture', 'Origin': 'https://attacker.invalid', 'X-Aurora-CSRF': 'fixture-csrf'}, 'POST')
            with self.assertRaises(Problem):
                self.api.current({'Cookie': 'fixture', 'Origin': 'https://fixture.invalid', 'X-Aurora-CSRF': 'wrong'}, 'POST')
            self.assertEqual(self.session, self.api.current({'Cookie': 'fixture', 'Origin': 'https://fixture.invalid', 'X-Aurora-CSRF': 'fixture-csrf'}, 'POST'))

    def test_model_write_only_creates_proposal(self):
        result = self.api.call_tool(self.session, 'note_save', {'content': 'fixture only'})
        self.assertTrue(result['confirmation_required'])
        self.assertEqual([], self.api.STORE.notes(self.session['email']))
        tool, args = self.api.STORE.claim(self.session['email'], result['proposal_id'])
        saved = self.api.call_tool(self.session, tool, args, confirmed=True)
        self.assertTrue(saved['saved'])

    def test_research_requires_explicit_opt_in(self):
        from common import Problem
        with self.assertRaises(Problem):
            self.api.call_tool(self.session, 'research_search', {'query': 'public query'})

    def test_removed_app_grant_blocks_confirmation(self):
        from common import Problem
        p = self.api.STORE.proposal(self.session['email'], 'finance_add_transaction', {'accountId': 'fixture', 'date': '2026-11-21', 'amount': -100, 'payee': 'fixture'})
        name, args = self.api.STORE.claim(self.session['email'], p['proposal_id'])
        with self.assertRaises(Problem):
            self.api.call_tool(self.session, name, args, confirmed=True, operation_id=p['proposal_id'])


if __name__ == '__main__':
    unittest.main()
