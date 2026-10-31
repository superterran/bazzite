#!/usr/bin/env python3
"""Report session state; former Moonlight switching hooks are now harmless."""
import argparse
import os
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
    # Keep stale launch hooks harmless. Logging out can strand the host at GDM
    # when the target session fails; streaming must never depend on relogin.
    print('Automatic session switching is disabled; streaming the current display.')


def switch(mode):
    # Compatibility for an already queued --worker invocation.
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
