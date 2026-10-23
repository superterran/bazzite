#!/usr/bin/env bash
set -euo pipefail
# Steam owns only this viewer; the browser keeps running as a user service.
systemctl --user start chrome-private-browser.service chrome-private-vnc.service
for ((attempt=0; attempt<60; attempt++)); do
    if python3 -c 'import socket; s=socket.create_connection(("127.0.0.1",5905),timeout=.5); s.close()' 2>/dev/null; then break; fi
    sleep .25
done
export GDK_BACKEND=x11
if [[ -z "${DISPLAY:-}" ]]; then export DISPLAY=:1; fi
exec /usr/bin/python3 "$HOME/repos/bazzite/bin/chrome-private-viewer.py"
