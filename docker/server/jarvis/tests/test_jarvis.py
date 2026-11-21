import concurrent.futures
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Problem, authorize
from store import Store
from tools import available, validate
from connector import fitness_summary


class JarvisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name)/'jarvis.sqlite3')
        self.a, self.b = 'a@example.invalid', 'b@example.invalid'

    def test_notes_are_owned(self):
        self.store.note(self.a, 'Privado')
        self.assertEqual([], self.store.notes(self.b))
        self.assertEqual('Privado', self.store.notes(self.a)[0]['content'])

    def test_history_is_owned(self):
        self.store.message(self.a, 'user', 'Teste')
        self.assertEqual([], self.store.messages(self.b))
        self.assertEqual('Teste', self.store.messages(self.a)[0]['content'])

    def test_duplicate_pending_proposal_reuses_confirmation(self):
        one = self.store.proposal(self.a, 'note_save', {'content': 'A'})
        two = self.store.proposal(self.a, 'note_save', {'content': 'A'})
        self.assertEqual(one['proposal_id'], two['proposal_id'])
        self.assertEqual(1, len(self.store.proposals(self.a)))

    def test_proposal_cannot_be_claimed_by_another_user(self):
        p = self.store.proposal(self.a, 'note_save', {'content': 'A'})
        with self.assertRaises(Problem):
            self.store.claim(self.b, p['proposal_id'])
        self.assertEqual('note_save', self.store.claim(self.a, p['proposal_id'])[0])

    def test_confirmation_is_atomic(self):
        p = self.store.proposal(self.a, 'note_save', {'content': 'A'})
        def claim(_):
            try:
                self.store.claim(self.a, p['proposal_id'])
                return True
            except Problem:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(1, sum(pool.map(claim, range(4))))

    def test_no_automatic_retry_after_uncertain_write(self):
        p = self.store.proposal(self.a, 'finance_add_transaction', {})
        self.store.claim(self.a, p['proposal_id'])
        self.store.finish(self.a, p['proposal_id'], 'uncertain', {})
        with self.assertRaises(Problem):
            self.store.claim(self.a, p['proposal_id'])

    def test_expired_proposal_is_rejected(self):
        p = self.store.proposal(self.a, 'note_save', {})
        with self.store.db() as db:
            db.execute('UPDATE proposals SET created=0')
        with self.assertRaises(Problem):
            self.store.claim(self.a, p['proposal_id'])

    def test_session_grants_limit_model_tools(self):
        session = {'grants': {'portal': self.a}}
        names = [t['function']['name'] for t in available(session)]
        self.assertNotIn('finance_summary', names)
        self.assertNotIn('fitness_summary', names)
        self.assertNotIn('research_search', names)
        self.assertIn('notes_list', names)
        with self.assertRaises(Problem):
            validate('finance_add_transaction', {}, session)

    def test_unknown_arguments_and_shell_are_rejected(self):
        s = {'grants': {'portal': self.a}}
        with self.assertRaises(Problem):
            validate('note_save', {'content': 'A', 'owner': self.b}, s)
        with self.assertRaises(Problem):
            validate('shell', {'command': 'id'}, s)

    def test_boolean_is_not_amount(self):
        s = {'grants': {'portal': self.a, 'actual': 'budget'}}
        with self.assertRaises(Problem):
            validate('finance_add_transaction', {'accountId': 'a', 'date': '2026-11-21', 'amount': True, 'payee': 'A'}, s)

    def test_rpc_requires_private_token(self):
        with self.assertRaises(Problem):
            authorize({'Authorization': 'Bearer attacker'}, 'x'*48)
        authorize({'Authorization': 'Bearer '+'x'*48}, 'x'*48)

    def test_calories_and_duration_are_not_invented(self):
        state = {'workouts': [
            {'d': '2026-11-21', 'name': 'Teste', 'start': 100000, 'end': 160000},
            {'d': '2026-11-20', 'name': 'Teste 2', 'garminActivity': {'calories': 0}},
        ]}
        result = fitness_summary(state, {'start': '2026-11-01', 'end': '2026-11-21'})
        self.assertEqual(1, result['totalMinutes'])
        self.assertEqual(1, result['missingCalories'])
        self.assertIsNone(result['workouts'][0]['calories'])
        self.assertEqual(0, result['workouts'][1]['calories'])
        self.assertIsNone(result['workouts'][1]['minutes'])

    def test_last_five_are_sorted_and_dedicated(self):
        rows = [{'d': '2026-11-%02d'%i, 'start': i, 'name': 'Teste'} for i in range(1, 10)]
        r = fitness_summary({'workouts': rows}, {'start': '2026-11-01', 'end': '2026-11-21', 'limit': 5})
        self.assertEqual(5, r['count'])
        self.assertEqual('2026-11-09', r['workouts'][0]['date'])

    def test_reminder_inbox_is_owned(self):
        with self.store.db() as db:
            db.execute('INSERT INTO reminders VALUES(?,?,?,?,0)', ('test', self.a, 'Lembrete', 1))
        self.store.tick()
        self.assertEqual(1, self.store.reminders(self.a)[0]['delivered'])
        self.assertEqual([], self.store.reminders(self.b))

    def test_migration_two_preserves_old_pending_proposal(self):
        import sqlite3
        old = Path(self.tmp.name)/'old.sqlite3'
        with sqlite3.connect(old) as db:
            db.execute('CREATE TABLE proposals(id TEXT PRIMARY KEY,owner TEXT NOT NULL,tool TEXT NOT NULL,args TEXT NOT NULL,created INTEGER NOT NULL,status TEXT NOT NULL,result TEXT)')
            db.execute('INSERT INTO proposals VALUES(?,?,?,?,?,?,NULL)', ('fixture-old', self.a, 'note_save', '{"content":"preservada"}', 1, 'pending'))
        db.close()
        upgraded = Store(old)
        name, args = None, None
        with upgraded.db() as db:
            row = db.execute('SELECT * FROM proposals WHERE id="fixture-old"').fetchone()
            self.assertEqual('{}', row['preview'])
            self.assertEqual('pending', row['status'])
            self.assertIn('preservada', row['args'])
            self.assertIsNotNone(db.execute('SELECT 1 FROM schema_migrations WHERE version=2').fetchone())

    def test_migration_preserves_notes(self):
        self.store.note(self.a, 'Preservada')
        again = Store(self.store.path)
        self.assertEqual('Preservada', again.notes(self.a)[0]['content'])


if __name__ == '__main__':
    unittest.main()
