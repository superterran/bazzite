#!/usr/bin/env bash
set -euo pipefail
systemctl --user start onepassword-private.service chrome-private-vnc.service
# A second invocation asks the existing app to show its window.
env -u WAYLAND_DISPLAY DISPLAY=:20 \
    XAUTHORITY="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/chrome-private/Xauthority" \
    /usr/bin/1password --ozone-platform=x11 >/dev/null 2>&1 &
# The viewer belongs to Steam's display, not the private display.
exec env DISPLAY="${DISPLAY:-:1}" GDK_BACKEND=x11 \
    /usr/bin/python3 "$HOME/repos/bazzite/bin/chrome-private-viewer.py" \
    --title '1Password' --focus-helper focus-onepassword-tv.py
