#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
flatpak info com.google.Chrome >/dev/null
mkdir -p "$HOME/.local/bin"
install -m 755 "$repo_root/bin/launch-chrome-tv.sh" "$HOME/.local/bin/launch-chrome-tv.sh"
install -m 755 "$repo_root/bin/chrome-tv-playwright.py" "$HOME/.local/bin/chrome-tv-playwright.py"
install -m 755 "$repo_root/bin/playwright-tv-mcp.sh" "$HOME/.local/bin/playwright-tv-mcp.sh"
if command -v codex >/dev/null 2>&1 && command -v playwright-mcp >/dev/null 2>&1; then
    codex mcp add playwright-tv -- "$HOME/.local/bin/playwright-tv-mcp.sh"
fi
python3 "$repo_root/bin/setup-chrome-tv.py"
