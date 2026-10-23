#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
GAME_DIR="${GAMES24_DIR:-}"
if [[ -z "$GAME_DIR" ]]; then
    for candidate in "$script_dir" "$HOME/shared-games/24-games-windows95" /var/mnt/fast/shared-games/24-games-windows95; do
        if [[ -f "$candidate/cd/WIN/PROGRAM/GAMES.EXE" ]]; then GAME_DIR="$candidate"; break; fi
    done
fi
[[ -n "$GAME_DIR" && -f "$GAME_DIR/cd/WIN/PROGRAM/GAMES.EXE" ]] || { echo '24 Games shared files are not available.' >&2; exit 1; }
STEAM_DIR="${STEAM24_DIR:-$HOME/.local/share/Steam}"
PROTON_DIR="${PROTON24_DIR:-$STEAM_DIR/steamapps/common/Proton 11.0}"
[[ -x "$PROTON_DIR/proton" ]] || { echo 'Install Proton 11.0 in Steam before launching 24 Games.' >&2; exit 1; }
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_DIR"
export STEAM_COMPAT_DATA_PATH="${GAMES24_COMPAT_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/24-games-windows95/compatdata}"
export WINEDEBUG=-all
mkdir -p "$STEAM_COMPAT_DATA_PATH"
cd "$GAME_DIR/cd/WIN/PROGRAM"
exec "$PROTON_DIR/proton" waitforexitandrun "$PWD/GAMES.EXE"
