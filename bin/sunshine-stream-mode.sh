#!/usr/bin/env bash
# Reconfigure Gamescope to a target HDMI mode and restart the user session so
# Sunshine captures the new KMS plane. Invoked by Sunshine prep-cmd:
#   do:   sunshine-stream-mode.sh start
#   undo: sunshine-stream-mode.sh stop
#
# Constraints:
# - KMS capture pins the stream's pixel dimensions to the HDMI plane, which is
#   bounded by the connected display's EDID. Resolutions the TV doesn't
#   support will silently fall back to gamescope's default.
# - Sunshine sets SUNSHINE_CLIENT_WIDTH / SUNSHINE_CLIENT_HEIGHT for prep-cmd.
# - Linger=yes + GDM autologin re-enter gamescope automatically after
#   loginctl terminate-session. Sunshine itself lives in user@1000.service
#   and survives the session swap.

set -euo pipefail

GAMESCOPE_CONF="$HOME/.config/environment.d/10-gamescope-session.conf"
BACKUP="${GAMESCOPE_CONF}.stream-bak"

restart_seat_session() {
    local sid
    sid=$(loginctl list-sessions --no-legend | awk '$4 == "seat0" {print $1; exit}')
    if [ -n "$sid" ]; then
        loginctl terminate-session "$sid"
    else
        pkill -KILL gamescope || true
    fi
}

case "${1:-}" in
    start)
        W="${2:-${SUNSHINE_CLIENT_WIDTH:-2560}}"
        H="${3:-${SUNSHINE_CLIENT_HEIGHT:-1440}}"

        if grep -q "^SCREEN_WIDTH=${W}$" "$GAMESCOPE_CONF" \
           && grep -q "^SCREEN_HEIGHT=${H}$" "$GAMESCOPE_CONF"; then
            echo "Already at ${W}x${H}; no restart."
            exit 0
        fi

        cp -a "$GAMESCOPE_CONF" "$BACKUP"
        sed -i "s/^SCREEN_WIDTH=.*/SCREEN_WIDTH=${W}/" "$GAMESCOPE_CONF"
        sed -i "s/^SCREEN_HEIGHT=.*/SCREEN_HEIGHT=${H}/" "$GAMESCOPE_CONF"
        echo "Set gamescope output to ${W}x${H}; restarting session."
        restart_seat_session
        ;;
    stop)
        [ -f "$BACKUP" ] || { echo "No backup; nothing to restore."; exit 0; }
        mv "$BACKUP" "$GAMESCOPE_CONF"
        echo "Restored default gamescope env; restarting session."
        restart_seat_session
        ;;
    *)
        cat >&2 <<EOF
Usage: $0 start [WIDTH HEIGHT] | stop
  start  Backup gamescope env, write WxH (defaults to \$SUNSHINE_CLIENT_*),
         terminate seat session — GDM autologin re-enters gamescope.
  stop   Restore backup and restart session.
EOF
        exit 1
        ;;
esac
