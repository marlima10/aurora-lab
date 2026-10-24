"""Central identities. High-entropy access keys are never stored in clear text."""
import hashlib
import hmac
import re
import secrets
import sqlite3
import string
import time
from contextlib import contextmanager
from pathlib import Path

APPS = ('portal', 'manyfold', 'mealie', 'actual', 'opengym', 'octoprint', 'homeassistant', 'homeboard', 'cockpit')
ADMIN_EMAIL = 'aurora@server.local'
SESSION_SECONDS = 12 * 3600


class AccessError(ValueError):
    pass


def email(value):
    if not isinstance(value, str) or len(value) > 254 or not re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+', value):
        raise ValueError('Informe um e-mail válido.')
    return value.lower()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def generate_key():
    return ''.join(secrets.choice(string.ascii_letters + string.digits + '-_') for _ in range(151))


class Store:
    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, key_hash TEXT NOT NULL, enabled INTEGER NOT NULL,
                    generation INTEGER NOT NULL DEFAULT 1, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS grants (
                    email TEXT NOT NULL REFERENCES users(email), app TEXT NOT NULL,
                    identity TEXT NOT NULL, PRIMARY KEY(email, app));
                CREATE TABLE IF NOT EXISTS sessions (
                    hash TEXT PRIMARY KEY, email TEXT NOT NULL REFERENCES users(email),
                    csrf TEXT NOT NULL, expires INTEGER NOT NULL, generation INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, stamp INTEGER NOT NULL, actor TEXT NOT NULL,
                    action TEXT NOT NULL, target TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts (
                    hash TEXT PRIMARY KEY, count INTEGER NOT NULL, until INTEGER NOT NULL);
            ''')
            # Migration 1 preserves existing hashes, sessions and native mappings.
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied INTEGER NOT NULL)')
            if not db.execute('SELECT 1 FROM schema_migrations WHERE version=1').fetchone():
                columns = {row['name'] for row in db.execute('PRAGMA table_info(users)')}
                if 'deleted' not in columns:
                    db.execute('ALTER TABLE users ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0')
                db.execute('INSERT INTO schema_migrations VALUES(1,?)', (int(self.clock()),))
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def audit(self, db, actor, action, target):
        db.execute('INSERT INTO audit(stamp,actor,action,target) VALUES(?,?,?,?)', (int(self.clock()), actor, action, target))

    def initialize(self):
        key = generate_key()
        with self.db() as db:
            if db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                raise AccessError('Instalação já inicializada; não alterada.')
            db.execute('INSERT INTO users(email,key_hash,enabled,generation,created) VALUES(?,?,1,1,?)', (ADMIN_EMAIL, digest(key), int(self.clock())))
            db.execute('INSERT INTO grants VALUES(?,?,?)', (ADMIN_EMAIL, 'portal', ADMIN_EMAIL))
            self.audit(db, 'local-bootstrap', 'initialize', ADMIN_EMAIL)
        return key

    def authenticate(self, address, key, client):
        address = email(address)
        valid = isinstance(key, str) and re.fullmatch(r'[A-Za-z0-9_-]{151}', key) is not None
        now = int(self.clock())
        failure = False
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
            db.execute('DELETE FROM attempts WHERE until<=?', (now,))
            buckets = [digest('ip:' + client), digest('email:' + address)]
            for bucket in buckets:
                attempt = db.execute('SELECT count FROM attempts WHERE hash=?', (bucket,)).fetchone()
                if attempt and attempt['count'] >= 8:
                    raise AccessError('Muitas tentativas. Aguarde 15 minutos.')
            user = db.execute('SELECT * FROM users WHERE email=?', (address,)).fetchone()
            expected = user['key_hash'] if user else digest('unregistered')
            accepted = hmac.compare_digest(expected, digest(key if valid else 'invalid'))
            if not valid or not user or not user['enabled'] or user['deleted'] or not accepted:
                for bucket in buckets:
                    db.execute('INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(hash) DO UPDATE SET count=count+1', (bucket, now + 900))
                failure = True
            else:
                for bucket in buckets:
                    db.execute('DELETE FROM attempts WHERE hash=?', (bucket,))
                token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
                db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)', (digest(token), address, csrf, now + SESSION_SECONDS, user['generation']))
                self.audit(db, address, 'login', address)
        if failure:
            raise AccessError('E-mail ou chave inválidos.')
        return token, csrf

    def session(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{64}', token):
            raise AccessError('Autenticação necessária.')
        with self.db() as db:
            row = db.execute('''SELECT u.email,s.csrf,s.expires FROM sessions s JOIN users u ON s.email=u.email
                WHERE s.hash=? AND s.expires>? AND u.enabled=1 AND u.deleted=0 AND s.generation=u.generation''',
                (digest(token), int(self.clock()))).fetchone()
            if not row:
                raise AccessError('Sessão expirada ou revogada.')
            grants = {r['app']: r['identity'] for r in db.execute('SELECT app,identity FROM grants WHERE email=?', (row['email'],))}
            return dict(row) | {'admin': row['email'] == ADMIN_EMAIL, 'grants': grants}

    def logout(self, token):
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE hash=?', (digest(token),))

    def require_admin(self, db, actor):
        row = db.execute('SELECT enabled,deleted FROM users WHERE email=?', (actor,)).fetchone()
        if actor != ADMIN_EMAIL or not row or not row['enabled'] or row['deleted']:
            raise AccessError('Somente o administrador pode gerenciar acessos.')

    def issue(self, actor, target, grants=None):
        target = email(target)
        if grants is not None:
            if not isinstance(grants, dict) or set(grants) - set(APPS):
                raise ValueError('Aplicativo inválido.')
            for app, identity in grants.items():
                if not isinstance(identity, str) or not identity or len(identity) > 254 or not re.fullmatch(r'[A-Za-z0-9@._+\-]+', identity):
                    raise ValueError('Identidade interna inválida.')
                if app == 'cockpit' and target != ADMIN_EMAIL:
                    raise AccessError('Cockpit reservado ao administrador.')
        key = generate_key()
        with self.db() as db:
            self.require_admin(db, actor)
            db.execute('''INSERT INTO users(email,key_hash,enabled,generation,created) VALUES(?,?,1,1,?) ON CONFLICT(email) DO UPDATE SET
                key_hash=excluded.key_hash,enabled=1,deleted=0,generation=users.generation+1''', (target, digest(key), int(self.clock())))
            db.execute('DELETE FROM sessions WHERE email=?', (target,))
            if grants is not None:
                db.execute('DELETE FROM grants WHERE email=?', (target,))
                db.executemany('INSERT INTO grants VALUES(?,?,?)', ((target, app, identity) for app, identity in grants.items()))
            db.execute('INSERT OR IGNORE INTO grants VALUES(?,?,?)', (target, 'portal', target))
            self.audit(db, actor, 'issue-or-rotate', target)
        return key

    def revoke(self, actor, target):
        target = email(target)
        if target == ADMIN_EMAIL:
            raise AccessError('Não é permitido desativar o administrador inicial.')
        with self.db() as db:
            self.require_admin(db, actor)
            db.execute('UPDATE users SET enabled=0,generation=generation+1 WHERE email=?', (target,))
            db.execute('DELETE FROM sessions WHERE email=?', (target,))
            self.audit(db, actor, 'revoke', target)

    def delete(self, actor, target):
        target = email(target)
        with self.db() as db:
            self.require_admin(db, actor)
            if target == ADMIN_EMAIL:
                raise AccessError('Não é permitido excluir o administrador inicial.')
            row = db.execute('SELECT deleted FROM users WHERE email=?', (target,)).fetchone()
            if not row or row['deleted']:
                raise ValueError('Cadastro não encontrado.')
            db.execute('UPDATE users SET deleted=1,enabled=0,generation=generation+1 WHERE email=?', (target,))
            db.execute('DELETE FROM sessions WHERE email=?', (target,))
            self.audit(db, actor, 'delete', target)

    def users(self, actor):
        with self.db() as db:
            self.require_admin(db, actor)
            return [dict(row) for row in db.execute('SELECT email,enabled,generation,created FROM users WHERE deleted=0 ORDER BY email')]
