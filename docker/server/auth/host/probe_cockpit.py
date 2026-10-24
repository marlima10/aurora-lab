"""Read-only native-login rehearsal through a temporary root-private Unix socket.

Never opens a TCP listener, touches the running Cockpit service, or grants sudo.
The exact same socket-activation mechanism is used by the optional SSO unit.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import pwd
import signal
import socket
import tempfile
import time
from urllib.parse import urlsplit


def probe(username, origin):
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or parsed.port != 9090 or not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Informe a origem HTTPS exata do Cockpit, na porta 9090.')
    user = pwd.getpwnam(username)
    if user.pw_uid == 0 or os.geteuid() != 0:
        raise ValueError('Execute como root e selecione uma conta local sem UID zero.')
    with tempfile.TemporaryDirectory(prefix='aurora-cockpit-probe-') as private, tempfile.TemporaryDirectory(prefix='aurora-cockpit-origin-') as configuration:
        directory = Path(private)
        config = Path(configuration)
        config.chmod(0o755)
        (config / 'cockpit').mkdir(mode=0o755)
        path = config / 'cockpit/cockpit.conf'
        path.write_text('[WebService]\nOrigins = ' + origin + ' wss://' + parsed.netloc + '\nProtocolHeader = X-Forwarded-Proto\nAllowUnencrypted = true\n')
        path.chmod(0o644)
        endpoint = directory / 'sso.sock'
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(endpoint))
        endpoint.chmod(0o600)
        listener.listen(16)
        pid = os.fork()
        if pid == 0:
            os.setsid()
            log = os.open(str(directory / 'native.log'), os.O_WRONLY | os.O_CREAT, 0o600)
            null = os.open('/dev/null', os.O_RDONLY)
            os.dup2(null, 0)
            os.dup2(log, 1)
            os.dup2(log, 2)
            os.dup2(listener.fileno(), 3)
            os.set_inheritable(3, True)
            env = {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin', 'LANG':'C.UTF-8', 'LISTEN_FDS':'1', 'LISTEN_PID':str(os.getpid()),
                   'XDG_CONFIG_DIRS':str(config), 'HOME':user.pw_dir, 'USER':username, 'LOGNAME':username}
            os.initgroups(username, user.pw_gid)
            os.setgid(user.pw_gid)
            os.setuid(user.pw_uid)
            os.execve('/usr/lib/cockpit/cockpit-ws', ['cockpit-ws', '--for-tls-proxy', '--local-session=/usr/bin/cockpit-bridge'], env)
        try:
            listener.close()
            time.sleep(1)

            class Connection(http.client.HTTPConnection):
                def connect(self):
                    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    self.sock.settimeout(10)
                    self.sock.connect(str(endpoint))

            connection = Connection(parsed.netloc, timeout=10)
            connection.request('GET', '/cockpit/login', headers={'Host':parsed.netloc, 'Origin':origin, 'X-Forwarded-Proto':'https', 'Accept':'application/json'})
            response = connection.getresponse()
            payload = response.read()
            content_type = response.getheader('Content-Type', '')
            connection.close()
            data = json.loads(payload)
            uid = int(Path('/proc/' + str(pid) + '/status').read_text().split('Uid:', 1)[1].split()[0])
            # The local-session response intentionally omits a user name; validate the OS identity.
            record = {'http_status':response.status, 'json_fields':sorted(data), 'json_response':'application/json' in content_type,
                      'process_uid_matches_local_account':uid == user.pw_uid, 'private_unix_mode':oct(endpoint.stat().st_mode & 0o777),
                      'tcp_port_opened':False, 'password_requested':False}
            if response.status != 200 or not record['json_response'] or not record['process_uid_matches_local_account']:
                raise RuntimeError('O ensaio nativo não confirmou o acesso esperado.')
            return record
        finally:
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True)
    parser.add_argument('--origin', required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.user, args.origin)))
