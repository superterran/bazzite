#!/usr/bin/env bash
# Reconfigure Gamescope (output connector + resolution) and restart the user
# session so Sunshine captures the new KMS plane. Invoked by Sunshine prep-cmd:
#   do:   sunshine-stream-mode.sh start [WIDTH HEIGHT] [CONNECTOR]
#   undo: sunshine-stream-mode.sh stop
#
# Examples (see ~/.config/sunshine/apps.json):
#   start 3440 1440 DP-2     # ultrawide on the virtual DP-2 connector
#   start 2388 1668 DP-2     # iPad Pro 11" on DP-2
#   start                    # client's requested res on the default (TV) connector
#
# How it works:
# - gamescope-session-plus reads OUTPUT_CONNECTOR / SCREEN_WIDTH / SCREEN_HEIGHT
#   from ~/.config/environment.d/10-gamescope-session.conf. We rewrite those,
#   then terminate the seat session; GDM autologin + Linger=yes re-enter
#   gamescope at the new config. Sunshine lives in user@1000.service and survives.
# - Sunshine (capture=kms, no output_name) auto-selects the connector that has an
#   active framebuffer. gamescope drives a single --prefer-output connector, so
#   moving the session to DP-2 moves the only active plane to DP-2 and Sunshine
#   follows. (If two connectors ever end up enabled, set output_name in
#   sunshine.conf to disambiguate.)
# - DP-2 is a virtual connector (forced EDID via kernel kargs, carrying
#   3440x1440 + 2388x1668). It's not bounded by the 16:9 TV EDID on HDMI-A-2.
#   While streaming on DP-2 the TV shows no signal — this is a dedicated remote
#   mode, not a mirror.
#
# Constraints / notes:
# - Sunshine sets SUNSHINE_CLIENT_WIDTH / SUNSHINE_CLIENT_HEIGHT for prep-cmd.
# - A mode the connector's EDID doesn't advertise will fall back to gamescope's
#   default. The DP-2 EDID advertises both target modes; the TV EDID does not.
# - ENABLE_GAMESCOPE_HDR=1 is left as-is; if a virtual-connector stream misbehaves
#   on HDR, drop HDR for the streaming connector here.

set -euo pipefail

GAMESCOPE_CONF="$HOME/.config/environment.d/10-gamescope-session.conf"
BACKUP="${GAMESCOPE_CONF}.stream-bak"

# Set key=value in the conf, replacing an existing line or appending if absent.
set_kv() {
    local key="$1" val="$2"
    if grep -q "^${key}=" "$GAMESCOPE_CONF"; then
        sed -i "s|^${key}=.*|${key}=${val}|" "$GAMESCOPE_CONF"
    else
        echo "${key}=${val}" >> "$GAMESCOPE_CONF"
    fi
}

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
        CONN="${4:-}"   # optional output connector (e.g. DP-2); empty = leave as configured

        # Idempotency: skip the disruptive restart if already at the target config.
        if grep -q "^SCREEN_WIDTH=${W}$" "$GAMESCOPE_CONF" 2>/dev/null \
           && grep -q "^SCREEN_HEIGHT=${H}$" "$GAMESCOPE_CONF" 2>/dev/null \
           && { [ -z "$CONN" ] || grep -q "^OUTPUT_CONNECTOR=${CONN}$" "$GAMESCOPE_CONF" 2>/dev/null; }; then
            echo "Already at ${W}x${H}${CONN:+ on $CONN}; no restart."
            exit 0
        fi

        # Preserve the true original across repeated starts (only back up once).
        [ -f "$BACKUP" ] || cp -a "$GAMESCOPE_CONF" "$BACKUP"

        set_kv SCREEN_WIDTH "$W"
        set_kv SCREEN_HEIGHT "$H"
        [ -n "$CONN" ] && set_kv OUTPUT_CONNECTOR "$CONN"

        echo "Set gamescope to ${W}x${H}${CONN:+ on $CONN}; restarting session."
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
Usage: $0 start [WIDTH HEIGHT] [CONNECTOR] | stop
  start  Back up gamescope env, set WxH (defaults to \$SUNSHINE_CLIENT_*) and
         optionally OUTPUT_CONNECTOR, terminate seat session — GDM autologin
         re-enters gamescope. e.g. 'start 3440 1440 DP-2'
  stop   Restore the backed-up env and restart session.
EOF
        exit 1
        ;;
esac
