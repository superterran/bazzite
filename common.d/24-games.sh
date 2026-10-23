#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -f "$HOME/shared-games/24-games-windows95/cd/WIN/PROGRAM/GAMES.EXE" ]]; then
    game_dir="$HOME/shared-games/24-games-windows95"
elif [[ -f /var/mnt/fast/shared-games/24-games-windows95/cd/WIN/PROGRAM/GAMES.EXE ]]; then
    game_dir=/var/mnt/fast/shared-games/24-games-windows95
else
    echo '24 Games: waiting for shared-games sync; rerun this script when files arrive.'
    exit 0
fi
if ! curl -fsS --max-time 2 http://127.0.0.1:8080/json >/dev/null; then
    echo '24 Games: start Steam with CEF debugging enabled, then rerun this script.'
    exit 0
fi
case "$(hostname)" in *ally*) controller=ally ;; *) controller=dualsense ;; esac
exec python3 "$repo_root/bin/setup-24-games.py" --game-dir "$game_dir" --controller "$controller"
