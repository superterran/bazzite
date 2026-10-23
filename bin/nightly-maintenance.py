#!/usr/bin/python3
"""Run all enabled Bazzite updates at 05:00; reboot only after idle checks."""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('decky_maintenance', Path(__file__).with_name('decky-maintenance.py'))
decky = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decky)
STATE = Path('/var/lib/bazzite-nightly-maintenance')


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120).stdout


def within_window(now):
    return now.hour == 5


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def staged_update(status):
    return any(d.get('staged') and not d.get('booted') for d in status['deployments'])


def pending_reboot():
    status = json.loads(command(['rpm-ostree', 'status', '--json']))
    if staged_update(status) or Path('/run/reboot-required').exists():
        return True
    marker = STATE / 'pending.json'
    if marker.exists():
        return json.loads(marker.read_text()).get('boot_id') == boot_id()
    return False


def fingerprint():
    parts = [command(['flatpak', 'list', '--system', '--columns=ref,active']),
             command(['runuser', '-u', 'me', '--', 'flatpak', 'list', '--user', '--columns=ref,active']),
             command(['runuser', '-u', 'me', '--', '/home/linuxbrew/.linuxbrew/bin/brew', 'list', '--versions'])]
    loader = decky.BASE / 'services/PluginLoader'
    if loader.exists():
        parts.append(hashlib.sha256(loader.read_bytes()).hexdigest())
    for base in sorted((decky.BASE / 'plugins').iterdir()):
        for name in ('package.json', 'plugin.json', 'dist/index.js', 'main.py'):
            path = base / name
            if path.is_file():
                parts.append(str(path) + hashlib.sha256(path.read_bytes()).hexdigest())
    return hashlib.sha256('\n'.join(parts).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Report policy/state only; never update or reboot')
    args = parser.parse_args()
    reason = decky.busy_reason()
    if args.check:
        print(json.dumps({'in_5am_window': within_window(datetime.now()), 'busy': reason,
                          'reboot_pending': pending_reboot(), 'fingerprint': fingerprint()}), flush=True)
        return
    if not within_window(datetime.now()) or reason:
        print('Deferred:', reason or 'Outside the 05:00–06:00 maintenance window', flush=True)
        return
    STATE.mkdir(parents=True, exist_ok=True)
    before = fingerprint()
    # Use the distribution's updater, with its current enabled system/Flatpak/Brew modules.
    # Do not use uupd --apply: the final game check must happen immediately before reboot.
    failure = None
    try:
        subprocess.run(['systemctl', 'start', 'uupd.service'], check=True, timeout=2700)
        reason = decky.busy_reason()
        if not reason:
            subprocess.run(['/usr/bin/python3', str(Path(__file__).with_name('decky-maintenance.py'))], check=True, timeout=900)
        else:
            print('Decky update deferred:', reason, flush=True)
    except (subprocess.SubprocessError, OSError) as exc:
        failure = exc
    if fingerprint() != before:
        marker = {'boot_id': boot_id(), 'updated_at': datetime.now().isoformat()}
        (STATE / 'pending.json').write_text(json.dumps(marker) + '\n')
    if failure:
        raise RuntimeError('Update cycle failed; leaving reboot for the next successful cycle') from failure
    if not pending_reboot():
        print('No changes requiring a maintenance restart', flush=True)
        return
    # Recheck after downloads: a game may have started while updates were running.
    reason = decky.busy_reason()
    if reason or not within_window(datetime.now()):
        print('Reboot deferred:', reason or 'Maintenance window ended', flush=True)
        return
    print('Updates ready; no running game detected. Rebooting.', flush=True)
    subprocess.run(['systemctl', 'reboot'], check=True)


if __name__ == '__main__':
    main()
