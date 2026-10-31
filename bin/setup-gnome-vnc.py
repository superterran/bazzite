#!/usr/bin/env python3
"""Enable GNOME's virtual-monitor VNC backend for use over Tailscale."""
import re
import subprocess


def run(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kwargs)


def main():
    # Reuse the first eight characters of the existing RDP credential, privately.
    # Classic VNC authentication has an eight-byte password limit.
    status = run('grdctl', 'status', '--show-credentials').stdout
    rdp = status.split('VNC:')[0]
    match = re.search(r'Password:\s*([^\n]+)', rdp)
    if not match or len(match[1].strip()) < 8:
        raise SystemExit('Configure the RDP credential first; no changes made.')
    run('grdctl', 'vnc', 'set-password', input=match[1].strip()[:8] + '\n')
    for args in [('set-port', '5901'), ('disable-port-negotiation',),
                 ('set-auth-method', 'password'), ('disable-view-only',)]:
        run('grdctl', 'vnc', *args)
    run('/usr/bin/gsettings', 'set', 'org.gnome.desktop.remote-desktop.vnc',
        'screen-share-mode', 'extend')
    # Transport encryption comes from Tailscale. Setup must install firewall
    # restrictions before enabling this backend.
    run('/usr/bin/gsettings', 'set', 'org.gnome.desktop.remote-desktop.vnc',
        'encryption', "['none']")
    run('grdctl', 'vnc', 'enable')
    print('GNOME virtual-monitor VNC enabled on port 5901; password not displayed.')


if __name__ == '__main__':
    main()
