#!/usr/bin/env python3
"""Merge source-scoped admin public keys from stdin JSON; never relax service keys."""
import argparse
import base64
from datetime import datetime
import ipaddress
import json
from pathlib import Path
import re
import shutil
import sys


def merge(original, entries):
    lines = original.splitlines()
    for entry in entries:
        key = entry['key'].strip()
        parts = key.split()
        if '\n' in key or '\r' in key or len(parts) < 2 or parts[0] != 'ssh-ed25519':
            raise ValueError('Expected one ED25519 public key per entry')
        decoded = base64.b64decode(parts[1], validate=True)
        if len(decoded) != 51 or not decoded.startswith(b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20'):
            raise ValueError('Invalid ED25519 public key')
        sources = entry['sources']
        if not sources:
            raise ValueError('Administration keys require explicit source addresses')
        for source in sources:
            ipaddress.ip_network(source, strict=False)
        found = False
        for i, line in enumerate(lines):
            if parts[1] not in line.split():
                continue
            found = True
            if re.search(r'(^|,)restrict(,|\s)|command=', line):
                raise ValueError('Refusing to modify a restricted service key')
            source_match = re.search(r'from="([^"]+)"', line)
            if not source_match:
                raise ValueError('Refusing to rewrite an existing unrestricted key')
            combined = list(dict.fromkeys(source_match[1].split(',') + sources))
            lines[i] = (line[:source_match.start()] + 'from="' + ','.join(combined) +
                        '"' + line[source_match.end():])
        if not found:
            lines.append('from="' + ','.join(sources) +
                         '",no-agent-forwarding,no-X11-forwarding ' + key)
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path,
                        default=Path.home() / '.ssh/authorized_keys')
    args = parser.parse_args()
    path = args.file
    original = path.read_text() if path.exists() else ''
    updated = merge(original, json.load(sys.stdin))
    if updated != original:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.exists():
            shutil.copy2(path, path.with_name(path.name + '.before-fleet-' +
                         datetime.now().strftime('%Y%m%d-%H%M%S-%f')))
        temp = path.with_name(path.name + '.fleet-tmp')
        temp.write_text(updated)
        temp.chmod(0o600)
        temp.replace(path)
    print('Administration keys configured; existing service restrictions preserved.')


if __name__ == '__main__':
    main()
