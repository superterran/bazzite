#!/usr/bin/python3
"""Root-only login bridge for one fixed LUKS-backed GNOME home.

No keys are stored by the broker. Each login verifies the complete passphrase
against LUKS, including while the volume is already open. Only a root peer may
unlock; the desktop owner can request session shutdown and volume locking.
"""
import json
import os
from pathlib import Path
import pwd
import resource
import socket
import socketserver
import struct
import subprocess
import threading
import time
import ssl

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
CONFIG = json.loads(Path('/etc/productivity-secure.json').read_text())
ACCOUNT = pwd.getpwnam(CONFIG['account'])
VOLUME = CONFIG['volume']
MAPPING = 'desktop-secure-home'
HOME = ACCOUNT.pw_dir
GUARD = threading.Lock()


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def userctl(*args):
    env = dict(os.environ, HOME=HOME, XDG_RUNTIME_DIR=f'/run/user/{ACCOUNT.pw_uid}',
               DBUS_SESSION_BUS_ADDRESS=f'unix:path=/run/user/{ACCOUNT.pw_uid}/bus')
    return run(['/usr/bin/setpriv', f'--reuid={ACCOUNT.pw_uid}', f'--regid={ACCOUNT.pw_gid}',
                '--init-groups', '/usr/bin/systemctl', '--user', *args], env=env)


def unlock(password):
    if not isinstance(password, str) or not 32 <= len(password) <= 128 or '\x00' in password:
        return False
    key = password.encode()
    # Check the full key even if a previous login already mounted the home.
    test = subprocess.run(['/usr/bin/cryptsetup', 'open', '--test-passphrase', '--key-file', '-', VOLUME],
                          input=key, capture_output=True, timeout=30)
    if test.returncode:
        time.sleep(1)
        return False
    device = f'/dev/mapper/{MAPPING}'
    if not Path(device).exists():
        run(['/usr/bin/cryptsetup', 'open', '--key-file', '-', VOLUME, MAPPING], input=key, timeout=30)
    if not os.path.ismount(HOME):
        run(['/usr/bin/mount', '-o', 'nodev,nosuid', device, HOME])
    # The encrypted account never lingers or starts before its home is unlocked.
    run(['/usr/bin/systemctl', 'start', f'productivity-secure-session@{ACCOUNT.pw_uid}.service'])
    run(['/usr/bin/systemctl', 'start', f'user@{ACCOUNT.pw_uid}.service'])
    userctl('start', 'remote-productivity-shell.service', 'gnome-remote-desktop-headless.service',
            'productivity-vnc-tls-adapter.service')
    for _ in range(100):
        try:
            with socket.create_connection(('127.0.0.1', 5915), .25) as probe:
                probe.settimeout(1)
                if probe.recv(12) == b'RFB 003.008\n':
                    return True
        except OSError:
            pass
        time.sleep(.1)
    return False


def lock():
    run(['/usr/bin/systemctl', 'stop', f'productivity-secure-session@{ACCOUNT.pw_uid}.service'])
    run(['/usr/bin/systemctl', 'stop', f'user@{ACCOUNT.pw_uid}.service'])
    if os.path.ismount(HOME):
        run(['/usr/bin/umount', HOME])
    if Path(f'/dev/mapper/{MAPPING}').exists():
        run(['/usr/bin/cryptsetup', 'close', MAPPING])


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(90)
        if isinstance(self.connection, ssl.SSLSocket):
            # Only the gateway's client certificate is signed by this local CA.
            names = dict(pair for part in self.connection.getpeercert()['subject'] for pair in part)
            peer_uid = 0 if names.get('commonName') == 'productivity-gateway' else -1
        else:
            _, peer_uid, _ = struct.unpack('3i', self.connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        result = {'ok': False}
        try:
            raw = self.rfile.readline(4097)
            if len(raw) > 4096:
                raise ValueError('Request too large')
            request = json.loads(raw)
            action = request.get('action')
            if action == 'unlock' and peer_uid == 0 and request.get('username') == ACCOUNT.pw_name:
                with GUARD:
                    result['ok'] = unlock(request.get('password'))
            elif action == 'lock' and peer_uid in (0, ACCOUNT.pw_uid):
                # Reply first, because stopping the user's manager kills its caller.
                self.wfile.write(b'{"ok":true}\n')
                self.wfile.flush()
                time.sleep(.5)
                with GUARD:
                    lock()
                print('Encrypted desktop locked', flush=True)
                return
            elif action == 'status' and peer_uid in (0, ACCOUNT.pw_uid):
                result = {'ok': True, 'unlocked': os.path.ismount(HOME)}
        except Exception as error:
            # Deliberately omit exception messages, request content and commands.
            print(f'Encrypted desktop request failed: {type(error).__name__}', flush=True)
        self.wfile.write(json.dumps(result).encode() + b'\n')


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


class TLSServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def get_request(self):
        connection, address = super().get_request()
        try:
            connection.settimeout(15)
            return TLS_CONTEXT.wrap_socket(connection, server_side=True), address
        except Exception:
            connection.close()
            raise


tls_directory = Path('/var/lib/productivity-secure-bridge/unlock-tls')
TLS_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
TLS_CONTEXT.minimum_version = ssl.TLSVersion.TLSv1_2
TLS_CONTEXT.load_cert_chain(tls_directory / 'server.crt', tls_directory / 'server.key')
TLS_CONTEXT.load_verify_locations(tls_directory / 'ca.crt')
TLS_CONTEXT.verify_mode = ssl.CERT_REQUIRED
tls_server = TLSServer(('127.0.0.1', 35921), Handler)
threading.Thread(target=tls_server.serve_forever, daemon=True).start()


socket_path = '/run/productivity-unlock/broker.sock'
Path(socket_path).unlink(missing_ok=True)
with Server(socket_path, Handler) as server:
    # Caller identities are checked using kernel credentials, not JSON claims.
    os.chmod(socket_path, 0o666)
    print('Encrypted desktop broker ready', flush=True)
    notify = os.environ.get('NOTIFY_SOCKET')
    if notify:
        if notify.startswith('@'):
            notify = '\x00' + notify[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as status:
            status.connect(notify)
            status.sendall(b'READY=1')
    server.serve_forever()
