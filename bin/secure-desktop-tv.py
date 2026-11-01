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
    native = os.environ.get('SECURE_DESKTOP_BRIDGE') != '1'
    pinfile = 'native-rdp-cert.sha256' if native else 'viewer-cert.sha256'
    fingerprint = (ROOT / 'config/secure-productivity' / pinfile).read_text().strip()
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
    # Keep the local playback buffer short; the default Pulse tlength was250ms.
    os.environ['PULSE_LATENCY_MSEC'] = '50'
    parent = os.getpid()
    def child_setup():
        ctypes.CDLL(None).prctl(1, signal.SIGTERM, 0, 0, 0)
        if os.getppid() != parent:
            os._exit(1)
    endpoint = '/v:127.0.0.1:3393' if native else '/v:100.119.114.55:3392'
    transport = ['/sec:nla', '/gfx:AVC420:on'] if native else ['/sec:tls']
    child = subprocess.Popen([CLIENT, endpoint, '/u:desktop-secure', '/d:.',
                              *transport, '/from-stdin:force', '/cert:fingerprint:sha256:' + fingerprint,
                              '/f', '/size:1920x1080', '+smart-sizing', '/bpp:24', '+clipboard',
                              '/sound:sys:pulse,latency:50', '/audio-mode:0',
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
