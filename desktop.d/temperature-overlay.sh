#!/bin/bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$HOME/.config/gamescope-session-plus/sessions.d/steam"
mkdir -p "$(dirname "$dest")"
line="source \"$repo_root/config/gamescope-temperature-overlay.sh\""
if ! grep -Fqx "$line" "$dest" 2>/dev/null; then printf "%s\n" "$line" >> "$dest"; fi
