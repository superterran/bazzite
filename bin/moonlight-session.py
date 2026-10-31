#!/usr/bin/env python3
"""Ensure the requested session, preserving an already running Game Mode."""
import argparse
import os
from pathlib import Path
import subprocess

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


def request(mode):
    current = current_mode()
    if current == mode:
        print('Requested session already running; streaming current display untouched.')
        return
    if current == 'unknown':
        raise RuntimeError('Session is starting or ambiguous; retry once it is ready')
    # The shared Steam/GNOME helper owns orderly graphical target teardown.
    run(str(Path(__file__).with_name('switch-bazzite-session.sh')), mode)


def switch(mode):
    # Compatibility for earlier callers; cleanup now lives in the shared helper.
    request(mode)


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
