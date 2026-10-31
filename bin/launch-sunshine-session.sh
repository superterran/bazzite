#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DISPLAY="${DISPLAY:-:0}"
# The user manager can start before Gamescope and does not inherit its display.
for ((attempt=0; attempt<60; attempt++)); do
    # Socket paths may survive logout. Prefer the actual running compositor,
    # rather than connecting to a stale Gamescope/GNOME path after a switch.
    if systemctl --user is-active --quiet gamescope-session-plus@steam.service; then
        candidates=(gamescope-0)
    elif pgrep -u "$(id -u)" -x gnome-shell >/dev/null; then
        candidates=("${WAYLAND_DISPLAY:-wayland-0}" wayland-0 wayland-1)
    else
        sleep 1
        continue
    fi
    for candidate in "${candidates[@]}"; do
        if [[ -S "$XDG_RUNTIME_DIR/$candidate" ]]; then
            export WAYLAND_DISPLAY="$candidate"
            exec /usr/bin/sunshine "$@"
        fi
    done
    sleep 1
done
echo 'Sunshine: waiting for a Wayland session; systemd will retry.' >&2
exit 1
