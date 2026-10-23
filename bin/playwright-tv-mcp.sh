#!/usr/bin/env bash
set -euo pipefail
if ! curl -fsS --max-time 2 http://127.0.0.1:9223/json/version >/dev/null; then
    echo 'Open Chrome - TV & Automation in Steam or Moonlight before using playwright-tv.' >&2
    exit 1
fi
output_dir="$HOME/.local/state/playwright-tv"
mkdir -p "$output_dir"
chmod 700 "$output_dir"
exec /home/linuxbrew/.linuxbrew/bin/playwright-mcp \
    --cdp-endpoint http://127.0.0.1:9223 \
    --caps vision --output-dir "$output_dir"
