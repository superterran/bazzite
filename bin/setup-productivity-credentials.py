#!/usr/bin/env python3
"""Configure an independent GNOME backend using private stdin credentials."""
import pwd
import re
import subprocess

account = pwd.getpwnam('desktop-remote')
prefix = ['sudo', '-u', account.pw_name, 'env', f'HOME={account.pw_dir}',
          f'XDG_RUNTIME_DIR=/run/user/{account.pw_uid}',
          f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{account.pw_uid}/bus']


def run(*args, **kwargs):
    return subprocess.run(prefix + ['/usr/bin/grdctl', '--headless', *args],
                          check=True, text=True, capture_output=True, **kwargs)


status = subprocess.check_output(['/usr/bin/grdctl', 'status', '--show-credentials'], text=True)
match = re.search(r'Password:\s*([^\n]+)', status.split('VNC:')[0])
if not match or len(match[1].strip()) < 8:
    raise SystemExit('Existing GNOME RDP credential is required.')
run('vnc', 'set-password', input=match[1].strip()[:8] + '\n')
for args in [('set-port', '5902'), ('set-auth-method', 'password'),
             ('disable-view-only',), ('disable-port-negotiation',), ('enable',)]:
    run('vnc', *args)
print('Independent GNOME VNC credentials configured without exposing password.')
