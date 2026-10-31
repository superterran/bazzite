#!/usr/bin/env python3
"""Select the TV's session without touching an already running Game Mode."""
import argparse
import os
from pathlib import Path
import subprocess
import time

SUNSHINE = 'app-dev.lizardbyte.app.Sunshine.service'
GAME = 'gamescope-session-plus@steam.service'


def run(*args, check=True):
    return subprocess.run(args, check=check, text=True, capture_output=True)


def current_mode():
    game = run('systemctl', '--user', 'is-active', '--quiet', GAME,
               check=False).returncode == 0
    desktop = run('pgrep', '-u', str(os.getuid()), '-x', 'gnome-shell',
                  check=False).returncode == 0
    if game and not desktop:
        return 'game'
    if desktop and not game:
        return 'desktop'
    return 'unknown'


def local_session():
    for line in run('loginctl', 'list-sessions', '--no-legend').stdout.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[1] == str(os.getuid()) and fields[3] == 'seat0':
            return fields[0]
    raise RuntimeError('No local seat0 session; refusing to switch')


def request(mode):
    # This fast path must never focus Steam, issue a Steam URI, or restart it.
    if current_mode() == mode:
        print(f'Already in {mode}; streaming the current display.')
        return
    if current_mode() == 'unknown':
        raise RuntimeError('Session is ambiguous or starting; retry once it is ready')
    local_session()
    # Independent of Sunshine and the graphical session. A fixed unit name
    # prevents two clients from queuing competing session changes.
    run('systemd-run', '--user', '--collect', '--unit=moonlight-session-switch',
        '--property=TimeoutStartSec=150', '/usr/bin/python3',
        str(Path(__file__).resolve()), mode, '--worker')
    print(f'Switching to {mode}; reconnect Moonlight after login completes.')


def switch(mode):
    time.sleep(2)  # Let Sunshine finish the launch-hook response.
    if current_mode() == mode:
        return
    if current_mode() == 'unknown':
        raise RuntimeError('Session changed before switch; refusing to log it out')
    old_session = local_session()
    helper = Path(__file__).with_name('switch-bazzite-session.sh')
    run(str(helper), mode, '--prepare-only')
    run('systemctl', '--user', 'stop', SUNSHINE)
    try:
        run(str(helper), mode)
        deadline = time.monotonic() + 100
        while time.monotonic() < deadline:
            try:
                ready = local_session() != old_session and current_mode() == mode
            except RuntimeError:
                ready = False
            if ready:
                time.sleep(3)
                break
            time.sleep(1)
        else:
            raise RuntimeError('New session did not become ready within 100 seconds')
    finally:
        # Recover streaming even if logout or the target session failed.
        run('systemctl', '--user', 'reset-failed', SUNSHINE, check=False)
        run('systemctl', '--user', 'start', SUNSHINE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['game', 'desktop', 'status'])
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.mode == 'status':
        print(current_mode())
    elif args.worker:
        switch(args.mode)
    else:
        request(args.mode)


if __name__ == '__main__':
    main()
