#!/usr/bin/python3
"""Request phone approval without changing Steam, display or session state."""
import json
import socket
with socket.socket(socket.AF_UNIX) as connection:
    connection.settimeout(30)
    connection.connect('/run/productivity-push/request.sock')
    connection.sendall(b'request\n')
    result = json.loads(connection.makefile('rb').readline(4096))
print(result['message'])
raise SystemExit(0 if result['ok'] else 1)
