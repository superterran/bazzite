#!/usr/bin/python3
"""Add a local native RDP test path inside the unlocked encrypted home."""
import importlib.util
import os
from pathlib import Path
import pwd
import resource
import subprocess

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
account = pwd.getpwnam('desktop-secure')
home = Path(account.pw_dir)
if not os.path.ismount(home):
    raise SystemExit('Unlock the encrypted desktop first.')
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_secret', root / 'bin/productivity-secret-runtime.py')
runtime_secret = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime_secret)
credential = runtime_secret.credential()
prefix = ['sudo', 'setpriv', f'--reuid={account.pw_uid}', f'--regid={account.pw_gid}', '--init-groups',
          'env', f'HOME={home}', f'XDG_RUNTIME_DIR=/run/user/{account.pw_uid}',
          f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{account.pw_uid}/bus']
def run(*args, **kw):
    return subprocess.run(prefix + list(args), check=True, capture_output=True, text=True, **kw)
certdir = home / '.local/share/gnome-remote-desktop/native-rdp'
run('/usr/bin/mkdir', '-p', str(certdir))
if not (certdir / 'tls.crt').exists():
    run('/usr/bin/openssl', 'req', '-new', '-newkey', 'rsa:3072', '-nodes', '-x509', '-days', '365',
        '-subj', '/CN=desktop-secure-native', '-keyout', str(certdir / 'tls.key'), '-out', str(certdir / 'tls.crt'))
    run('/usr/bin/chmod', '600', str(certdir / 'tls.key'))
for command, value in [('set-tls-key',str(certdir/'tls.key')),('set-tls-cert',str(certdir/'tls.crt')),('set-port','3393')]:
    run('/usr/bin/grdctl', '--headless', 'rdp', command, value)
run('/usr/bin/grdctl', '--headless', 'rdp', 'set-credentials', 'desktop-secure', input=credential['password']+'\n')
credential = None
run('/usr/bin/grdctl', '--headless', 'rdp', 'disable-port-negotiation')
run('/usr/bin/grdctl', '--headless', 'rdp', 'disable-view-only')
run('/usr/bin/gsettings', 'set', 'org.gnome.desktop.remote-desktop.rdp', 'screen-share-mode', 'mirror-primary')
run('/usr/bin/grdctl', '--headless', 'rdp', 'enable')
fingerprint = run('/usr/bin/openssl', 'x509', '-in',str(certdir/'tls.crt'), '-noout', '-fingerprint', '-sha256').stdout.strip().split('=',1)[1]
(root/'config/secure-productivity/native-rdp-cert.sha256').write_text(fingerprint+'\n')
print('Native RDP test enabled on3393; VNC bridge preserved; no credential printed.')
