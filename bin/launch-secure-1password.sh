#!/usr/bin/env bash
set -euo pipefail
# The user manager starts only after its encrypted home is unlocked. Wait for
# the headless compositor, which becomes ready after its service process starts.
for attempt in {1..100}; do
    if [[ -S "$XDG_RUNTIME_DIR/${WAYLAND_DISPLAY:-wayland-productivity}" ]]; then
        exec /opt/1Password/1password --silent
    fi
    sleep 0.1
done
echo 'Encrypted GNOME Wayland display is not ready for 1Password.' >&2
exit 1
