#!/usr/bin/python3
"""PAM helper: password arrives only on stdin; root broker unlocks the home."""
import json
import os
import resource
import socket
import sys
import ssl

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
try:
    if '--lock' in sys.argv:
        request = {'action': 'lock'}
    else:
        if os.environ.get('PAM_TYPE') != 'auth':
            raise ValueError('Wrong PAM operation')
        password = sys.stdin.buffer.read(1024).rstrip(b'\x00').decode()
        request = {'action': 'unlock', 'username': os.environ.get('PAM_USER'), 'password': password}
    if '--tls' in sys.argv or os.environ.get('PRODUCTIVITY_UNLOCK_TRANSPORT') == 'tls':
        context = ssl.create_default_context(cafile='/etc/productivity-unlock/ca.crt')
        context.load_cert_chain('/etc/productivity-unlock/client.crt', '/etc/productivity-unlock/client.key')
        connection = context.wrap_socket(socket.create_connection(('127.0.0.1', 35921), 5), server_hostname='productivity-unlock')
    else:
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.connect('/run/productivity-unlock/broker.sock')
    with connection:
        connection.settimeout(90)
        connection.sendall(json.dumps(request).encode() + b'\n')
        response = connection.makefile('rb').readline(4096)
        success = json.loads(response).get('ok') is True
    sys.exit(0 if success else 1)
except Exception:
    sys.exit(1)
