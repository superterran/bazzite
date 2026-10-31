#!/usr/bin/python3
"""Initialize a new, separate encrypted home; never replace the working account.

Run as root with the 1Password record supplied on stdin by the runtime helper.
"""
import json
import os
from pathlib import Path
import pwd
import resource
import subprocess
import sys

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.umask(0o077)
secret = json.load(sys.stdin)
password = secret['password']
if len(password) < 32:
    raise SystemExit('Strong passphrase required')
if Path('/etc/productivity-secure.json').exists():
    raise SystemExit('Encrypted desktop already initialized; use the deployment script, not data migration.')
repo = Path('/home/me/repos/bazzite')
account = 'desktop-secure'
home = Path('/var/home/desktop-secure')
volume = Path('/var/lib/productivity-volume/desktop-secure.luks')
mapping = 'desktop-secure-home'


def run(args, **kwargs):
    try:
        return subprocess.run(args, check=True, capture_output=True, **kwargs)
    except subprocess.CalledProcessError as error:
        sys.stderr.buffer.write(error.stderr)
        raise


try:
    user = pwd.getpwnam(account)
except KeyError:
    run(['/usr/bin/useradd', '--create-home', '--home-dir', str(home), '--shell', '/bin/bash',
         '--comment', 'Encrypted virtual GNOME desktop', account])
    user = pwd.getpwnam(account)
run(['/usr/bin/loginctl', 'disable-linger', account])
volume.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
if volume.exists():
    if '--resume' not in sys.argv:
        raise SystemExit('Volume already exists; refusing to format or overwrite it')
    run(['/usr/bin/cryptsetup', 'open', '--test-passphrase', '--key-file', '-', str(volume)], input=password.encode())
else:
    volume.touch(mode=0o600)
    run(['/usr/bin/chattr', '+C', str(volume)])
    with volume.open('r+b') as output:
        output.truncate(64 * 1024**3)
    run(['/usr/bin/cryptsetup', 'luksFormat', '--batch-mode', '--type', 'luks2',
         '--pbkdf', 'argon2id', '--pbkdf-memory', '262144', '--iter-time', '1000',
         '--key-file', '-', str(volume)], input=password.encode())
    run(['/usr/bin/cryptsetup', 'open', '--key-file', '-', str(volume), mapping], input=password.encode())
    run(['/usr/bin/mkfs.ext4', '-q', '-L', 'secure-gnome', '-E', 'lazy_itable_init=1,lazy_journal_init=1',
         f'/dev/mapper/{mapping}'])
if not Path(f'/dev/mapper/{mapping}').exists():
    run(['/usr/bin/cryptsetup', 'open', '--key-file', '-', str(volume), mapping], input=password.encode())
if not os.path.ismount(home):
    run(['/usr/bin/mount', '-o', 'nodev,nosuid', f'/dev/mapper/{mapping}', str(home)])
run(['/usr/bin/rsync', '-aHAX', f'--chown={account}:{account}', '--exclude=.cache/',
     '/var/home/desktop-remote/', str(home) + '/'])
os.chown(home, user.pw_uid, user.pw_gid)
home.chmod(0o700)
run(['/usr/bin/restorecon', '-RF', str(home)])

# Independent session units and preferences live inside the encrypted home.
config = home / '.config'
unit_dir = config / 'systemd/user'
unit_dir.mkdir(parents=True, exist_ok=True)
sources = repo / 'config/productivity-bridge'
for unit in ['remote-productivity-shell.service', 'productivity-vnc-tls-adapter.service']:
    (unit_dir / unit).write_text((sources / unit).read_text())
for unit in ['remote-productivity-shell.service', 'productivity-vnc-tls-adapter.service']:
    link = unit_dir / 'default.target.wants' / unit
    link.parent.mkdir(exist_ok=True)
    link.unlink(missing_ok=True)
    link.symlink_to('../' + unit)
drop = unit_dir / 'productivity-vnc-tls-adapter.service.d'
drop.mkdir(exist_ok=True)
(drop / 'ports.conf').write_text('[Service]\nEnvironment=PRODUCTIVITY_VNC_BACKEND_PORT=5914\nEnvironment=PRODUCTIVITY_VNC_ADAPTER_PORT=5915\n')
applications = home / '.local/share/applications'
applications.mkdir(parents=True, exist_ok=True)
(applications / 'lock-encrypted-desktop.desktop').write_text((repo / 'config/secure-productivity/lock-desktop.desktop').read_text())
run(['/usr/bin/chown', '-R', f'{account}:{account}', str(config), str(home / '.local')])

# Configure the copied GNOME data on a private bus, without starting a session.
runtime = Path('/run/productivity-configure')
runtime.mkdir(mode=0o700, exist_ok=True)
os.chown(runtime, user.pw_uid, user.pw_gid)
program = '''import subprocess,sys
password=sys.stdin.buffer.read().decode()
def run(*args,**kw):
 r=subprocess.run(args,capture_output=True,**kw)
 if r.returncode:
  sys.stderr.buffer.write(r.stderr)
  raise SystemExit(r.returncode)
run('/usr/bin/grdctl','--headless','vnc','set-password',input=password[:8].encode()+bytes([10]))
run('/usr/bin/grdctl','--headless','vnc','set-port','5914')
run('/usr/bin/grdctl','--headless','vnc','disable-port-negotiation')
run('/usr/bin/gsettings','set','org.gnome.desktop.remote-desktop.vnc.headless','enable','true')
run('/usr/bin/gsettings','set','org.gnome.desktop.session','idle-delay','0')
run('/usr/bin/gsettings','set','org.gnome.desktop.screensaver','lock-enabled','false')
'''
run(['/usr/bin/setpriv', f'--reuid={user.pw_uid}', f'--regid={user.pw_gid}', '--init-groups', '/usr/bin/env', f'HOME={home}', f'XDG_RUNTIME_DIR={runtime}', f'USER={account}', f'LOGNAME={account}',
     '/usr/bin/dbus-run-session', '--', '/usr/bin/python3', '-c', program], input=password.encode())
settings = {'account': account, 'volume': str(volume), 'credential_item_id': secret['item_id'],
            'credential_vault_id': secret['vault_id'], 'rdp_address': '100.119.114.55:3392'}
Path('/etc/productivity-secure.json').write_text(json.dumps(settings, indent=2) + '\n')
run(['/usr/bin/umount', str(home)])
run(['/usr/bin/cryptsetup', 'close', mapping])
print('Created and locked a 64GiB LUKS2 home; original desktop account preserved.')
