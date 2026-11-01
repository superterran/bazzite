#!/usr/bin/python3
"""Expiring phone approval for the existing encrypted-home broker."""
import concurrent.futures
import email.message
import hmac
import html
import http.cookies
import http.server
import json
import os
from pathlib import Path
import secrets
import smtplib
import socket
import socketserver
import ssl
import struct
import threading
import time
from urllib.parse import parse_qs

BASE = 'https://desktop.tail3758dd.ts.net'
TTL = 300
GUARD = threading.Lock()
PENDING = {}
LAST_REQUEST = 0
MAIL = None


def broker(password):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(100)
        connection.connect('/run/productivity-unlock/broker.sock')
        connection.sendall(json.dumps({'action': 'unlock', 'username': 'desktop-secure',
                                      'password': password}).encode() + b'\n')
        return json.loads(connection.makefile('rb').readline(4097)).get('ok') is True


def notify(token):
    message = email.message.EmailMessage()
    message['From'] = MAIL['sender']
    message['To'] = MAIL['recipient']
    message['Subject'] = 'Approve Secure Desktop unlock'
    message.set_content('You requested access to the encrypted desktop.\n\n'
                        + BASE + '/#' + token + '\n\n'
                        'Open within 5 minutes, with Tailscale connected. Use 1Password '
                        'to fill Desktop Encrypted GNOME, then confirm. '
                        'Ignore this notification if you did not request it. '
                        'Opening the link alone does not unlock anything.')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20,
                          context=ssl.create_default_context()) as smtp:
        smtp.login(MAIL['sender'], MAIL['password'])
        smtp.send_message(message)


def request_unlock():
    global LAST_REQUEST
    with GUARD:
        now = time.monotonic()
        if now - LAST_REQUEST < 60:
            return {'ok': False, 'message': 'An approval was recently sent. Wait one minute.'}
        token = secrets.token_urlsafe(32)
        PENDING.clear()
        PENDING[token] = {'expires': now + TTL, 'session': secrets.token_urlsafe(32),
                          'csrf': secrets.token_urlsafe(32), 'attempts': 0, 'busy': False}
        LAST_REQUEST = now
    try:
        notify(token)
        return {'ok': True, 'message': 'Approval notification sent. Open it on your phone.'}
    except Exception:
        with GUARD:
            PENDING.pop(token, None)
        # No addresses, credentials, notification tokens or transport details in logs.
        return {'ok': False, 'message': 'Notification delivery failed.'}


PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unlock Secure Desktop</title><style>
body{font:18px system-ui;max-width:28rem;margin:8vh auto;padding:1rem;background:#151923;color:#fff}
input,button{font:inherit;box-sizing:border-box;width:100%;padding:.8rem;margin:.5rem 0}
button{background:#80b8ff;border:0;border-radius:.4rem}label{display:block}small{color:#ccd}
</style><h1>Unlock Secure Desktop</h1>
<p id="status">Open the link from your latest approval notification.</p>
<form id="unlock" action="/unlock" method="post" hidden>
<label>Username<input name="username" value="desktop-secure" autocomplete="username" readonly></label>
<label>Encryption password<input name="password" type="password" autocomplete="current-password" required maxlength="1024"></label>
<input name="csrf" id="csrf" type="hidden"><button>Unlock desktop</button>
<small>Use 1Password → Desktop Encrypted GNOME. This opens your encrypted session; it does not change the TV.</small></form>
<script>
(async()=>{let token=location.hash.slice(1);history.replaceState(null,'','/');
if(!token)return;try{let r=await fetch('/claim',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
let data=await r.json();token='';if(!r.ok)throw Error();document.getElementById('csrf').value=data.csrf;
document.getElementById('unlock').hidden=false;document.getElementById('status').textContent='Requested from desktop. Confirm only if you requested this unlock.';
}catch(e){document.getElementById('status').textContent='This approval expired or was replaced. Request a new notification.'}})();
</script></html>'''


class Web(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(110)

    def reply(self, status, body, content='text/html; charset=utf-8', cookie=None):
        data = body.encode()
        self.send_response(status)
        self.send_header('Content-Type', content)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        # Safari may send Origin: null on form POST with no-referrer.
        # Keep same-origin form provenance while hiding referrers off-site.
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            self.reply(200, 'ready', 'text/plain')
        elif self.path == '/':
            self.reply(200, PAGE)
        else:
            self.reply(404, 'Not found')

    def do_POST(self):
        if self.headers.get('Origin') != BASE or self.headers.get('Host') != BASE[8:]:
            return self.reply(403, 'Invalid origin')
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError()
            raw = self.rfile.read(length)
            if self.path == '/claim':
                token = json.loads(raw)['token']
                if not isinstance(token, str):
                    raise ValueError()
                with GUARD:
                    entry = PENDING.get(token)
                    if not entry or entry['expires'] < time.monotonic():
                        return self.reply(410, '{}', 'application/json')
                    # A link can be claimed only once; reload requires a fresh request.
                    if entry.get('claimed'):
                        return self.reply(410, '{}', 'application/json')
                    entry['claimed'] = True
                    response = json.dumps({'csrf': entry['csrf']})
                    cookie = '__Host-desktop=' + entry['session'] + '; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=300'
                return self.reply(200, response, 'application/json', cookie)
            if self.path != '/unlock':
                return self.reply(404, 'Not found')
            fields = parse_qs(raw.decode(), max_num_fields=4)
            cookies = http.cookies.SimpleCookie(self.headers.get('Cookie', ''))
            session = cookies['__Host-desktop'].value
            csrf = fields['csrf'][0]
            password = fields['password'][0]
            if fields.get('username') != ['desktop-secure'] or not 1 <= len(password) <= 1024:
                raise ValueError()
            with GUARD:
                found = next(((t,e) for t,e in PENDING.items() if hmac.compare_digest(e['session'], session)), None)
                if not found:
                    return self.reply(403, 'Invalid approval')
                token, entry = found
                if (entry['expires'] < time.monotonic() or entry['attempts'] >= 3 or entry['busy']
                        or not entry.get('claimed') or not hmac.compare_digest(entry['csrf'], csrf)):
                    return self.reply(403, 'Approval expired, busy or exhausted. Request another notification.')
                entry['attempts'] += 1
                entry['busy'] = True
            try:
                ok = broker(password)
            except Exception:
                ok = False
            finally:
                password = None
                raw = None
                fields = None
            with GUARD:
                entry['busy'] = False
                if ok:
                    PENDING.pop(token, None)
            if ok:
                return self.reply(200, '<h1>Desktop unlocked</h1><p>Your encrypted GNOME session is ready in Jump. You can close this page.</p>',
                                  cookie='__Host-desktop=; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
            return self.reply(401, '<h1>Unlock did not succeed</h1><p>Go back to retry with the full password from Desktop Encrypted GNOME, or request a new approval.</p>')
        except (ValueError, KeyError, TypeError, http.cookies.CookieError):
            self.reply(400, 'Invalid request')


class Request(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        _, uid, _ = struct.unpack('3i', self.connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid not in (0, 1000):
            result = {'ok': False, 'message': 'Not authorized'}
        elif self.rfile.readline(64).strip() != b'request':
            result = {'ok': False, 'message': 'Invalid command'}
        else:
            result = request_unlock()
        self.wfile.write(json.dumps(result).encode() + b'\n')


class Requests(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


if __name__ == '__main__':
    MAIL = json.loads((Path(os.environ['CREDENTIALS_DIRECTORY']) / 'notification').read_text())
    path = Path('/run/productivity-push/request.sock')
    path.unlink(missing_ok=True)
    control = Requests(str(path), Request)
    path.chmod(0o666)
    threading.Thread(target=control.serve_forever, daemon=True).start()
    http.server.ThreadingHTTPServer(('127.0.0.1', 18742), Web).serve_forever()
