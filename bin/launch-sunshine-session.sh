#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DISPLAY="${DISPLAY:-:0}"
# The user manager can start before Gamescope and does not inherit its display.
for ((attempt=0; attempt<60; attempt++)); do
    for candidate in "${WAYLAND_DISPLAY:-gamescope-0}" gamescope-0 wayland-0 wayland-1; do
        if [[ -S "$XDG_RUNTIME_DIR/$candidate" ]]; then
            export WAYLAND_DISPLAY="$candidate"
            exec /usr/bin/sunshine "$@"
        fi
    done
    sleep 1
done
echo 'Sunshine: waiting for a Wayland session; systemd will retry.' >&2
exit 1
