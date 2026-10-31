#!/usr/bin/python3
"""Preserve user settings while making the existing 1Password agent default."""
import os
from pathlib import Path
import pwd
import re
import subprocess

account = pwd.getpwnam('desktop-secure')
home = Path(account.pw_dir)
repo = Path(__file__).resolve().parents[1]
if not os.path.ismount(home):
    raise SystemExit('Unlock the encrypted desktop first; no changes made.')


def write(path, content, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(mode)
    os.chown(path, account.pw_uid, account.pw_gid)
    parent = path.parent
    while parent != home:
        os.chown(parent, account.pw_uid, account.pw_gid)
        parent = parent.parent


config = repo / 'config/secure-productivity'
write(home / '.config/environment.d/20-1password.conf', (config / '1password-agent.conf').read_text())
write(home / '.config/systemd/user/secure-1password.service', (config / 'secure-1password.service').read_text(), 0o644)
rc = home / '.bashrc'
text = rc.read_text() if rc.exists() else ''
begin = '# BEGIN managed encrypted-desktop 1Password agent'
end = '# END managed encrypted-desktop 1Password agent'
text = re.sub(re.escape(begin) + r'.*?' + re.escape(end) + r'\n?', '', text, flags=re.S)
text = text.rstrip() + '\n\n' + begin + '\nexport SSH_AUTH_SOCK="$HOME/.1password/agent.sock"\nexport OP_BIOMETRIC_UNLOCK_ENABLED=true\n' + end + '\n'
write(rc, text, 0o644)
ssh = home / '.ssh/config'
existing = ssh.read_text() if ssh.exists() else ''
if not re.search(r'^\s*IdentityAgent\s+.*\.1password/agent\.sock', existing, re.M):
    write(ssh, existing.rstrip() + '\n\nHost *\n    IdentityAgent ~/.1password/agent.sock\n')
# Make the native application visible in this user's app menu only. The host's
# package entry is Hidden=true; leave it unchanged for the gaming account.
desktop = Path('/usr/share/applications/1password.desktop').read_text()
desktop = re.sub(r'^Hidden=true\n?', '', desktop, flags=re.M)
write(home / '.local/share/applications/1password.desktop', desktop, 0o644)
print('1Password agent defaults and app startup configured; user customizations preserved.')
