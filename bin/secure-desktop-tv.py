#!/usr/bin/python3
"""Phone-approved, Steam-owned viewer of the existing encrypted GNOME session."""
import ctypes
import json
import os
from pathlib import Path
import resource
import signal
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
CLIENT = '/home/linuxbrew/.linuxbrew/bin/xfreerdp'
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def control(command):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(30)
        connection.connect('/run/productivity-push/request.sock')
        connection.sendall(command.encode() + b'\n')
        return json.loads(connection.makefile('rb').readline(4096))


def notice(text):
    subprocess.run(['/usr/bin/zenity', '--info', '--title=Secure Desktop', '--text=' + text],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    if not Path(CLIENT).exists():
        notice('The Secure Desktop viewer is not installed.')
        return 1
    # The gateway certificate is pinned; no credential or clipboard files shared.
    fingerprint = (ROOT / 'config/secure-productivity/viewer-cert.sha256').read_text().strip()
    request = control('viewer')
    if not request['ok']:
        notice(request['message'])
        return 1
    ticket = request['ticket']
    progress = subprocess.Popen(['/usr/bin/zenity', '--progress', '--pulsate', '--auto-close',
                                 '--title=Secure Desktop', '--text=Approve the Pushover notification on your iPhone.\nUse 1Password to unlock your encrypted desktop.', '--percentage=0'],
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    password = None
    try:
        deadline = time.monotonic() + 305
        while time.monotonic() < deadline:
            if progress.poll() is not None:
                return 0
            result = control('take ' + ticket)
            if result.get('state') == 'ready':
                password = result.pop('password')
                break
            if not result.get('ok'):
                notice('Approval expired. Launch Secure Desktop again to request a new notification.')
                return 1
            time.sleep(.5)
        if password is None:
            return 1
    finally:
        progress.terminate()
        progress.wait()
        if password is None:
            control('cancel ' + ticket)
    # Deliver the password once by anonymous stdin, never argv or disk. A hard
    # Steam stop also terminates the viewer; it never terminates remote GNOME.
    parent = os.getpid()
    def child_setup():
        ctypes.CDLL(None).prctl(1, signal.SIGTERM, 0, 0, 0)
        if os.getppid() != parent:
            os._exit(1)
    child = subprocess.Popen([CLIENT, '/v:100.119.114.55:3392', '/u:desktop-secure', '/d:.',
                              '/sec:tls', '/from-stdin:force', '/cert:fingerprint:sha256:' + fingerprint,
                              '/f', '+dynamic-resolution', '/bpp:24', '+clipboard',
                              '-grab-keyboard', '/t:Secure Desktop', '/log-level:OFF'],
                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             preexec_fn=child_setup)
    try:
        child.stdin.write((password + '\n').encode())
        child.stdin.close()
        password = None
        appid = os.environ.get('SteamAppId', '')
        if appid.isdigit():
            for _ in range(80):
                if child.poll() is not None:
                    break
                found = subprocess.run(['xdotool', 'search', '--pid', str(child.pid), '--name', 'Secure Desktop'],
                                       capture_output=True, text=True)
                if found.returncode == 0:
                    for window in found.stdout.split():
                        subprocess.run(['xprop', '-id', window, '-f', 'STEAM_GAME', '32c', '-set', 'STEAM_GAME', appid],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                time.sleep(.25)
        result = child.wait()
        if result:
            notice('The viewer disconnected. Your encrypted desktop is still running; reopen this shortcut or reconnect with Jump.')
        return 0
    finally:
        password = None
        if child.poll() is None:
            child.terminate()
            child.wait()


if __name__ == '__main__':
    raise SystemExit(main())
