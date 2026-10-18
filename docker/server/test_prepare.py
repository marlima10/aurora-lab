"""Regression tests for preparation, using isolated folders and a pseudo terminal."""
import os
from pathlib import Path
import select
import shutil
import stat
import subprocess
import tempfile
import unittest

if os.name == 'posix':
    import pty
    import termios


@unittest.skipUnless(os.name == 'posix' and hasattr(os, 'geteuid') and os.geteuid() == 0,
                     'Execute em Linux como root, preferencialmente no container temporario documentado.')
class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aurora-prepare-test-')
        self.root = Path(self.temp.name)
        target = self.root/'docker/server/prepare.sh'
        target.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).with_name('prepare.sh'), target)
        self.command = ['sh', str(target)]
        (self.root/'.env.example').write_text('SERVER_IP=192.0.2.1\n')
        self.secrets = self.root/'secrets'
        self.secrets.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def initialized_database(self):
        path = self.root/'data/samba/private/passdb.tdb'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'existing-database')

    def run_prepare(self):
        return subprocess.run(self.command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)

    def interactive(self, password):
        master, slave = pty.openpty()
        before = termios.tcgetattr(slave)
        process = subprocess.Popen(self.command, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = b''
        try:
            while b'Defina a senha' not in output:
                readable, _, _ = select.select([process.stdout], [], [], 10)
                if not readable:
                    self.fail('O script nao solicitou a senha dentro do prazo')
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    self.fail('O script terminou antes da senha: ' + output.decode())
                output += chunk
            os.write(master, password.encode() + b'\n')
            tail, _ = process.communicate(timeout=10)
            self.assertEqual(before, termios.tcgetattr(slave), 'Configuracao do terminal nao restaurada')
            if password and select.select([master], [], [], 0)[0]:
                self.assertNotIn(password.encode(), os.read(master, 4096), 'Senha ecoada pelo terminal')
            return process.returncode, (output + tail).decode()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout:
                process.stdout.close()
            os.close(master)
            os.close(slave)

    def test_empty_bind_directories_replaced_by_files(self):
        self.initialized_database()
        paths = [self.root/'.env', self.secrets/'octoprint-api.key', self.secrets/'samba-users.txt']
        for path in paths:
            path.mkdir()
        result = self.run_prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(path.is_file() for path in paths))
        self.assertEqual((self.root/'.env').read_text(), 'SERVER_IP=192.0.2.1\n')
        self.assertEqual(stat.S_IMODE(paths[0].stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(paths[1].stat().st_mode), 0o644)
        self.assertEqual(stat.S_IMODE(paths[2].stat().st_mode), 0o600)

    def test_nonempty_directories_preserved(self):
        for relative in ['.env', 'secrets/octoprint-api.key', 'secrets/samba-users.txt']:
            with self.subTest(path=relative):
                folder = self.root/relative
                folder.mkdir()
                preserved = folder/'keep.txt'
                preserved.write_text('preserve')
                result = self.run_prepare()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(relative, result.stderr)
                self.assertNotIn('Defina a senha', result.stdout)
                self.assertEqual(preserved.read_text(), 'preserve')
                preserved.unlink()
                folder.rmdir()

    def test_existing_configuration_keys_and_password_preserved(self):
        values = {self.root/'.env': 'SERVER_IP=192.0.2.77\n',
                  self.secrets/'octoprint-api.key': 'existing-api-key',
                  self.secrets/'samba-users.txt': 'existing-password\n'}
        for path, value in values.items():
            path.write_text(value)
        for _ in range(2):
            result = self.run_prepare()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('Defina a senha', result.stdout)
        for path, value in values.items():
            self.assertEqual(path.read_text(), value)

    def test_new_installation_creates_password_without_exposing_it(self):
        code, output = self.interactive('samba-test-123')
        self.assertEqual(code, 0, output)
        self.assertNotIn('samba-test-123', output)
        self.assertEqual((self.secrets/'samba-users.txt').read_text(), 'samba-test-123\n')

    def test_empty_password_file_is_initialized_without_database(self):
        (self.secrets/'samba-users.txt').touch()
        code, output = self.interactive('new-test-password')
        self.assertEqual(code, 0, output)
        self.assertEqual((self.secrets/'samba-users.txt').read_text(), 'new-test-password\n')

    def test_blank_password_rejected(self):
        code, _ = self.interactive('')
        self.assertNotEqual(code, 0)
        self.assertFalse((self.secrets/'samba-users.txt').exists())

    def test_noninteractive_missing_password_reports_action(self):
        result = self.run_prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('terminal interativo', result.stderr)
        self.assertFalse((self.secrets/'samba-users.txt').exists())

    def test_existing_database_does_not_require_password_again(self):
        self.initialized_database()
        result = self.run_prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.secrets/'samba-users.txt').read_bytes(), b'')
        self.assertEqual((self.root/'data/samba/private/passdb.tdb').read_bytes(), b'existing-database')

    def test_symlinks_rejected_without_modifying_target(self):
        outside = self.root/'original.txt'
        outside.write_text('original')
        outside.chmod(0o640)
        for relative in ['.env', 'secrets/octoprint-api.key', 'secrets/samba-users.txt']:
            with self.subTest(path=relative):
                link = self.root/relative
                link.symlink_to(outside)
                result = self.run_prepare()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('link simbolico', result.stderr)
                self.assertEqual(outside.read_text(), 'original')
                self.assertEqual(stat.S_IMODE(outside.stat().st_mode), 0o640)
                link.unlink()

    def test_special_file_rejected(self):
        fifo = self.secrets/'samba-users.txt'
        os.mkfifo(fifo)
        result = self.run_prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('arquivo regular', result.stderr)
        self.assertTrue(stat.S_ISFIFO(fifo.stat().st_mode))


if __name__ == '__main__':
    unittest.main(verbosity=2)
