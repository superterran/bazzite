#!/usr/bin/env bash
set -euo pipefail
GAME_DIR="/var/mnt/fast/shared-games/24-games-windows95"
STEAM_DIR="$HOME/.local/share/Steam"
PROTON_DIR="$STEAM_DIR/steamapps/common/Proton 11.0"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_DIR"
export STEAM_COMPAT_DATA_PATH="$GAME_DIR/compatdata"
export WINEDEBUG=-all
mkdir -p "$STEAM_COMPAT_DATA_PATH"
cd "$GAME_DIR/cd/WIN/PROGRAM"
exec "$PROTON_DIR/proton" waitforexitandrun "$PWD/GAMES.EXE"
