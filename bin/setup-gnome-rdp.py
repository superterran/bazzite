#!/usr/bin/env python3
"""Configure RDP without putting its password in arguments, logs, or files."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets
import subprocess


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs)


def main():
    home = Path.home()
    directory = home / '.local/share/gnome-remote-desktop'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = directory / 'tls.key'
    cert = directory / 'tls.crt'
    if not key.exists() or not cert.exists():
        run('openssl', 'req', '-new', '-newkey', 'rsa:3072', '-nodes', '-x509',
            '-days', '365', '-subj', '/CN=desktop',
            '-addext', 'subjectAltName=DNS:desktop,DNS:desktop.local,DNS:desktop.tail3758dd.ts.net,IP:10.0.0.226,IP:100.119.114.55',
            '-keyout', str(key), '-out', str(cert))
        key.chmod(0o600)
        cert.chmod(0o644)
    run('grdctl', 'rdp', 'set-tls-key', str(key))
    run('grdctl', 'rdp', 'set-tls-cert', str(cert))
    # Capture privately: this output can contain a password and must never be
    # logged. GNOME's keyring, rather than this script, owns the secret storage.
    status = run('grdctl', 'status', '--show-credentials').stdout
    username = re.search(r'Username:\s*([^\n]*)', status)
    password = re.search(r'Password:\s*([^\n]*)', status)
    missing = ('', '(null)', '(empty)', 'not set', '(none)')
    if not username or not password or username[1].strip().lower() in missing or password[1].strip().lower() in missing:
        # Pass only the public username as an argument. With two piped prompts,
        # this grdctl build buffers both lines in its first read and then fails.
        run('grdctl', 'rdp', 'set-credentials', 'me', input=secrets.token_urlsafe(24) + '\n')
    run('grdctl', 'rdp', 'set-port', '3389')
    run('grdctl', 'rdp', 'disable-port-negotiation')
    run('grdctl', 'rdp', 'disable-view-only')
    run('/usr/bin/gsettings', 'set', 'org.gnome.desktop.remote-desktop.rdp', 'screen-share-mode', 'extend')
    run('grdctl', 'rdp', 'enable')
    run('systemctl', '--user', 'enable', '--now', 'gnome-remote-desktop.service')
    metadata = {'configured_at': datetime.now(timezone.utc).isoformat(),
                'addresses': ['10.0.0.226:3389', '100.119.114.55:3389'],
                'display_mode': 'extend',
                'credentials': 'GNOME keyring; view in Settings > System > Remote Desktop > Desktop Sharing',
                'tls_fingerprint': run('openssl', 'x509', '-in', str(cert), '-noout', '-fingerprint', '-sha256').stdout.strip()}
    (directory / 'setup-info.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('GNOME RDP configured with a virtual monitor and keyboard/mouse control.')
    print('Credentials are in GNOME keyring; no password was printed or saved to a plaintext file.')


if __name__ == '__main__':
    main()
