#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DISPLAY="${DISPLAY:-:0}"
# The user manager can start before Gamescope and does not inherit its display.
for ((attempt=0; attempt<60; attempt++)); do
    # Prefer the compositor's actual environment over stale user-manager vars
    # left behind by the previous GNOME/Game Mode login.
    compositor_pid=$(pgrep -u "$(id -u)" -x gnome-shell | head -n1 || true)
    if [[ -n "$compositor_pid" && -r "/proc/$compositor_pid/environ" ]]; then
        while IFS= read -r -d '' entry; do
            case "$entry" in
                DISPLAY=*|WAYLAND_DISPLAY=*|XAUTHORITY=*) export "$entry" ;;
            esac
        done < "/proc/$compositor_pid/environ"
    fi
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
