#!/usr/bin/env bash
set -euo pipefail
game_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$game_dir/user-data"
exec "$game_dir/Dusklight-v2.0.3-linux-x86_64.AppImage" --user-dir "$game_dir/user-data" "$@"
