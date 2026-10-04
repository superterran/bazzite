#!/usr/bin/env bash
# gpu-game-guard — free VRAM for Steam games by toggling the always-on GPU AI stack.
#
# Any running Steam game (detected via Steam's `reaper SteamLaunch AppId=` wrapper)
# => stop the GPU stack. No game running => start it back up.
#
# Stateless/baseline model: "no game" means everything managed here should be up.
# Supervision differs per service, so each has an explicit control method:
#   *.service  -> systemctl --user (these are `docker run` units; docker stop just
#                 makes systemd relaunch them, so we must drive the unit)
#   docker     -> plain `docker start/stop` (no systemd unit)
#
# Deployed + managed from ~/repos/bazzite (source of truth). See CLAUDE.md.

set -uo pipefail
export PATH="/usr/bin:/usr/local/bin:$PATH"

# name -> control method ("<unit>.service" or literal "docker")
declare -A CTRL=(
    [kokoro-tts.service]=service
    [ollama.service]=service
    [speaches-stt]=docker
)

POLL_SECS="${GPU_GAME_GUARD_POLL:-5}"
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

game_running() {
    # Real games launch as: .../reaper SteamLaunch AppId=<n> -- ...
    # The opengamepad-ui / Steam client itself does NOT match this pattern.
    pgrep -f 'SteamLaunch AppId=[0-9]' >/dev/null 2>&1
}

apply() {  # $1 = start|stop
    local action="$1"
    for name in "${!CTRL[@]}"; do
        case "${CTRL[$name]}" in
            service)
                # `docker run` units land in "failed" after SIGTERM; clear it so
                # the next start is clean and reliable.
                [ "$action" = "start" ] && systemctl --user reset-failed "$name" >/dev/null 2>&1
                systemctl --user "$action" "$name" >/dev/null 2>&1 ;;
            docker)  docker "$action" "$name" >/dev/null 2>&1 ;;
        esac
        log "$action -> $name"
    done
}

prev="unknown"   # unknown on boot so first poll converges to the right baseline
log "gpu-game-guard started (poll ${POLL_SECS}s, managing: ${!CTRL[*]})"

while true; do
    if game_running; then state="game"; else state="idle"; fi
    if [ "$state" != "$prev" ]; then
        [ "$state" = "game" ] && apply stop || apply start
        prev="$state"
    fi
    sleep "$POLL_SECS"
done
