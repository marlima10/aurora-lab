"""Per-user Jarvis data; migrations and atomic confirmation claims."""
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from common import Problem, text


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, owner TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS notes(id TEXT PRIMARY KEY, owner TEXT NOT NULL, content TEXT NOT NULL, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS reminders(id TEXT PRIMARY KEY, owner TEXT NOT NULL, content TEXT NOT NULL, due INTEGER NOT NULL, delivered INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, owner TEXT NOT NULL, tool TEXT NOT NULL, args TEXT NOT NULL, created INTEGER NOT NULL, status TEXT NOT NULL, result TEXT);
                CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, owner TEXT NOT NULL, action TEXT NOT NULL, target TEXT, created INTEGER NOT NULL);
                INSERT OR IGNORE INTO schema_migrations VALUES(1);
            ''')
            db.execute('BEGIN IMMEDIATE')
            columns = {row['name'] for row in db.execute('PRAGMA table_info(proposals)')}
            if 'preview' not in columns:
                db.execute("ALTER TABLE proposals ADD COLUMN preview TEXT NOT NULL DEFAULT '{}'")
            db.execute('INSERT OR IGNORE INTO schema_migrations VALUES(2)')
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def messages(self, owner):
        with self.db() as db:
            rows = list(db.execute('SELECT role,content FROM messages WHERE owner=? ORDER BY id DESC LIMIT 12', (owner,)))
        return [dict(r) for r in reversed(rows)]

    def message(self, owner, role, content):
        with self.db() as db:
            db.execute('INSERT INTO messages(owner,role,content,created) VALUES(?,?,?,?)', (owner, role, content[:24000], int(time.time())))

    def note(self, owner, content):
        nid = secrets.token_urlsafe(18)
        with self.db() as db:
            db.execute('INSERT INTO notes VALUES(?,?,?,?)', (nid, owner, text(content, 16000), int(time.time())))
        return {'saved': True, 'id': nid}

    def notes(self, owner):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT id,content,created FROM notes WHERE owner=? ORDER BY created DESC LIMIT 100', (owner,))]

    def reminder(self, owner, content, due):
        due = int(due)
        if not time.time() < due < time.time() + 366 * 86400:
            raise Problem(400, 'Escolha um horário futuro de até um ano.')
        rid = secrets.token_urlsafe(18)
        with self.db() as db:
            db.execute('INSERT INTO reminders(id,owner,content,due) VALUES(?,?,?,?)', (rid, owner, text(content), due))
        return {'saved': True, 'id': rid, 'delivery': 'Caixa de lembretes do Jarvis; não envia push com o navegador fechado.'}

    def reminders(self, owner):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT id,content,due,delivered FROM reminders WHERE owner=? ORDER BY due DESC LIMIT 100', (owner,))]

    def tick(self):
        with self.db() as db:
            # Inbox delivery is durable; this is not a phone push notification.
            db.execute('UPDATE reminders SET delivered=1 WHERE delivered=0 AND due<=?', (int(time.time()),))

    def proposal(self, owner, tool, args, preview=None):
        pid = secrets.token_urlsafe(24)
        encoded = json.dumps(args, sort_keys=True, ensure_ascii=False)
        with self.db() as db:
            prior = db.execute('SELECT id FROM proposals WHERE owner=? AND tool=? AND args=? AND status="pending" AND created>?', (owner, tool, encoded, int(time.time())-900)).fetchone()
            if prior:
                pid = prior['id']
            else:
                db.execute('INSERT INTO proposals(id,owner,tool,args,created,status,result,preview) VALUES(?,?,?,?,?,?,NULL,?)', (pid, owner, tool, encoded, int(time.time()), 'pending', json.dumps(preview or {})))
        return {'confirmation_required': True, 'proposal_id': pid, 'tool': tool, 'details': args}

    def proposals(self, owner):
        with self.db() as db:
            return [dict(r) | {'args': json.loads(r['args']), 'preview': json.loads(r['preview'])} for r in db.execute('SELECT * FROM proposals WHERE owner=? AND status="pending" AND created>? ORDER BY created DESC', (owner, int(time.time())-900))]

    def claim(self, owner, pid):
        with self.db() as db:
            row = db.execute('SELECT * FROM proposals WHERE id=? AND owner=?', (pid, owner)).fetchone()
            if not row or row['status'] != 'pending' or row['created'] < time.time()-900:
                raise Problem(409, 'Confirmação indisponível, expirada ou já executada.')
            db.execute('UPDATE proposals SET status="running" WHERE id=?', (pid,))
            return row['tool'], json.loads(row['args'])

    def finish(self, owner, pid, status, result):
        with self.db() as db:
            db.execute('UPDATE proposals SET status=?,result=? WHERE id=? AND owner=?', (status, json.dumps(result), pid, owner))
            db.execute('INSERT INTO audit(owner,action,target,created) VALUES(?,?,?,?)', (owner, status, pid, int(time.time())))
