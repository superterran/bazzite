#!/usr/bin/python3
"""Loopback RFB adapter: xrdp VNC auth through GNOME's anonymous TLS channel.

No passwords are stored, read or logged here. The complete VNC authentication
exchange is forwarded unchanged; only the channel-security negotiation differs.
"""
import select
import socket
import ssl
import threading
import os

BACKEND_PORT = int(os.environ.get('PRODUCTIVITY_VNC_BACKEND_PORT', '5902'))
LISTEN_PORT = int(os.environ.get('PRODUCTIVITY_VNC_ADAPTER_PORT', '5903'))


def exact(sock, size):
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError('Peer closed connection')
        data += chunk
    return data


def session(client):
    upstream = None
    try:
        client.settimeout(15)
        upstream = socket.create_connection(('127.0.0.1', BACKEND_PORT), 5)
        client.sendall(exact(upstream, 12))
        version = exact(client, 12)
        print(f'VNC adapter client version: {version.decode().strip()}', flush=True)
        if version not in (b'RFB 003.003\n', b'RFB 003.008\n'):
            raise ValueError('Unsupported RFB version')
        upstream.sendall(b'RFB 003.008\n')
        offered = exact(upstream, exact(upstream, 1)[0])
        if 18 not in offered:
            raise ValueError('GNOME TLS channel missing')
        upstream.sendall(b'\x12')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # GNOME uses anonymous-DH TLS on loopback. It has no TLS1.3 equivalent.
        context.set_ciphers('aNULL:@SECLEVEL=0')
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        upstream = context.wrap_socket(upstream)
        print('VNC adapter upstream TLS established', flush=True)
        auth_types = exact(upstream, exact(upstream, 1)[0])
        if 2 not in auth_types:
            raise ValueError('Password authentication missing')
        if version == b'RFB 003.003\n':
            client.sendall(b'\x00\x00\x00\x02')
        else:
            client.sendall(b'\x01\x02')
            if exact(client, 1) != b'\x02':
                raise ValueError('Password authentication required')
        upstream.sendall(b'\x02')
        client.settimeout(None)
        upstream.settimeout(None)
        while True:
            ready = [upstream] if upstream.pending() else []
            if not ready:
                ready, _, _ = select.select([client, upstream], [], [])
            for source in ready:
                data = source.recv(65536)
                if not data:
                    return
                (upstream if source is client else client).sendall(data)
    except (OSError, EOFError, ValueError) as error:
        print(f'VNC adapter session ended: {type(error).__name__}', flush=True)
    finally:
        client.close()
        if upstream is not None:
            upstream.close()


def serve(address, family):
    with socket.create_server((address, LISTEN_PORT), family=family) as listener:
        print(f'VNC TLS adapter listening on {address}:{LISTEN_PORT}', flush=True)
        while True:
            connection, _ = listener.accept()
            threading.Thread(target=session, args=(connection,), daemon=True).start()


threading.Thread(target=serve, args=('::1', socket.AF_INET6), daemon=True).start()
serve('127.0.0.1', socket.AF_INET)
