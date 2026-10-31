#!/usr/bin/env python3
"""Install pinned, explicit SSH routes to the Mini and its independent KVM."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess

HOSTS = {
    'mac-mini': {
        'user': 'superterran', 'lan': 'mac-mini.local',
        'tailnet': '100.90.54.59', 'dns': 'mac-mini.tail3758dd.ts.net',
        'key': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP6vS8Z0wgRgify5hx2OsEjlOcFw/iaGqNiKhcLO/dFm',
    },
    'kvm-mini': {
        'user': 'root', 'lan': '10.0.0.112',
        'tailnet': '100.102.2.16', 'dns': 'kvm-mini.tail3758dd.ts.net',
        'key': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFPu7/wETz5v8F07jzzX40h6QEpjQU7bXmq5A2jb9VT/',
    },
}


def replace(path, text):
    if path.exists() and path.read_text() == text:
        return
    if path.exists():
        backup = path.with_name(path.name + '.before-fleet-' +
                                datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        shutil.copy2(path, backup)
    temporary = path.with_name(path.name + '.fleet-tmp')
    temporary.write_text(text)
    temporary.chmod(0o600)
    temporary.replace(path)


def configure(host, identity, transport):
    ssh = Path.home() / '.ssh'
    ssh.mkdir(mode=0o700, exist_ok=True)
    identity_setting = identity
    identity_path = Path(identity).expanduser()
    if not identity_path.is_file():
        raise RuntimeError(f'Identity does not exist: {identity_path}')
    target = HOSTS[host]
    config = ssh / 'config'
    original = config.read_text() if config.exists() else ''
    include = 'Include ~/.ssh/fleet-access/*.conf'
    # Insert before the first Host/Match stanza, keeping top-level integration
    # includes (notably OrbStack) in their established position.
    updated = original
    if include not in original.splitlines():
        match = re.search(r'(?im)^\s*(Host|Match)\s', original)
        offset = match.start() if match else len(original)
        updated = original[:offset] + '\n' + include + '\n\n' + original[offset:]
    managed = ssh / 'fleet-access'
    managed.mkdir(mode=0o700, exist_ok=True)
    aliases = [host]
    if host == 'kvm-mini':
        aliases += ['jetkvm', 'jetkvm-mini']
    stanzas = [
        (aliases, target[transport]),
        ([host + '-lan', target['lan']], target['lan']),
        ([host + '-tailnet', target['dns'], target['tailnet']], target['tailnet']),
    ]
    text = '# Managed by repos/bazzite/bin/fleet-ssh-client.py\n'
    for names, address in stanzas:
        text += f'Host {" ".join(names)}\n'
        text += f'  HostName {address}\n  User {target["user"]}\n'
        text += f'  IdentityFile "{identity_setting}"\n'
        text += ('  IdentityAgent none\n  IdentitiesOnly yes\n'
                 '  AddressFamily inet\n'
                 '  ForwardAgent no\n  StrictHostKeyChecking yes\n'
                 f'  HostKeyAlias fleet-{host}\n'
                 '  UserKnownHostsFile ~/.ssh/fleet-known-hosts\n'
                 '  CheckHostIP no\n  ConnectTimeout 8\n'
                 '  ConnectionAttempts 2\n  ServerAliveInterval 15\n'
                 '  ServerAliveCountMax 3\n  TCPKeepAlive yes\n'
                 '  PreferredAuthentications publickey\n'
                 '  PasswordAuthentication no\n  BatchMode yes\n\n')
    text += 'Host *\n'
    pins = ssh / 'fleet-known-hosts'
    previous_pins = pins.read_text().splitlines() if pins.exists() else []
    alias = f'fleet-{host}'
    retained = [line for line in previous_pins if not line.startswith(alias + ' ')]
    replace(pins, '\n'.join(retained + [alias + ' ' + target['key']]) + '\n')
    replace(managed / (host + '.conf'), text)
    # Validate the complete proposed config before changing the entry point.
    temporary = ssh / 'config.fleet-validate'
    temporary.write_text(updated)
    temporary.chmod(0o600)
    try:
        subprocess.run(['ssh', '-G', '-F', str(temporary), host], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    finally:
        temporary.unlink()
    replace(config, updated)
    print(f'Configured {host}: {target[transport]} as {target["user"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', choices=HOSTS)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--transport', choices=['lan', 'tailnet'], default='tailnet')
    args = parser.parse_args()
    configure(args.host, args.identity, args.transport)


if __name__ == '__main__':
    main()
