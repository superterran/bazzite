#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
flatpak info com.google.Chrome >/dev/null
mkdir -p "$HOME/.local/bin"
install -m 755 "$repo_root/bin/launch-chrome-tv.sh" "$HOME/.local/bin/launch-chrome-tv.sh"
install -m 755 "$repo_root/bin/chrome-tv-playwright.py" "$HOME/.local/bin/chrome-tv-playwright.py"
python3 "$repo_root/bin/setup-chrome-tv.py"
