#!/usr/bin/env python3
"""Assign both radiator fan headers to the saved Kraken coolant profile."""
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib


def run(*args):
    subprocess.run(args, check=True)


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run with sudo')
    root = Path(__file__).resolve().parents[1]
    desired = json.loads((root / 'config/kraken-coolant-profile.json').read_text())
    profile = desired['profile']
    config = Path('/etc/coolercontrol/config.toml')
    original = config.read_text()
    parsed = tomllib.loads(original)
    board = next(uid for uid, name in parsed['devices'].items() if name == 'nct6799')
    saved_profile = next(p for p in parsed['profiles'] if p['uid'] == profile['uid'])
    if saved_profile['temp_source'] != profile['temp_source']:
        raise RuntimeError('Coolant source differs from saved hardware identity')
    source = profile['temp_source']['device_uid']
    if 'Kraken' not in parsed['devices'][source]:
        raise RuntimeError('Expected Kraken coolant device not found')
    section = '[device-settings.' + board + ']'
    before, rest = original.split(section, 1)
    body, after = rest.split('\n\n', 1)
    for channel in ('fan2', 'fan7'):
        body, count = re.subn(r'(?m)^' + channel + r' = .*$',
                             channel + ' = { profile_uid = "' + profile['uid'] + '" }', body)
        if count != 1:
            raise RuntimeError('Expected radiator header setting missing')
    updated = before + section + body + '\n\n' + after
    marker = 'uid = "' + profile['uid'] + '"'
    begin = re.search(r'(?m)^' + re.escape(marker) + r'$', updated).start()
    end = updated.find('[[profiles]]', begin)
    if end < 0:
        raise RuntimeError('Expected following profile missing')
    block, count = re.subn(r'(?m)^speed_profile = .*$',
                          'speed_profile = ' + json.dumps(profile['speed_profile']),
                          updated[begin:end])
    if count != 1:
        raise RuntimeError('Expected coolant curve missing')
    updated = updated[:begin] + block + updated[end:]
    tomllib.loads(updated)
    backup = config.with_name('config.toml.before-coolant-' +
                              datetime.now().strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(config, backup)
    fallback = Path('/etc/systemd/system/coolercontrold.service.d/fan-fallback.conf')
    fallback.parent.mkdir(parents=True, exist_ok=True)
    fallback.parent.chmod(0o755)
    fallback.write_text((root / 'config/systemd/system/coolercontrold.service.d/fan-fallback.conf').read_text())
    fallback.chmod(0o644)
    run('restorecon', '-RF', str(fallback.parent))
    run('systemctl', 'daemon-reload')
    run('systemctl', 'disable', '--now', 'fan-curve.service')
    run('systemctl', 'stop', 'coolercontrold.service')
    try:
        config.write_text(updated)
        run('systemctl', 'start', 'coolercontrold.service')
    except BaseException:
        config.write_text(original)
        run('systemctl', 'start', 'coolercontrold.service')
        run('systemctl', 'enable', '--now', 'fan-curve.service')
        raise
    print('Radiator headers assigned to coolant; pump profile unchanged; backup:', backup)


if __name__ == '__main__':
    main()
