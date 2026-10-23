#!/usr/bin/env bash
set -euo pipefail
profile_dir="$HOME/.var/app/com.google.Chrome/config/chrome-tv-automation"
mkdir -p "$profile_dir"
chmod 700 "$profile_dir"
# Steam supplies the game's Xwayland display. Manual launches use it too.
if [[ -z "${DISPLAY:-}" ]]; then
    if [[ -S /tmp/.X11-unix/X1 ]]; then export DISPLAY=:1; else export DISPLAY=:0; fi
fi
exec flatpak run com.google.Chrome \
    --user-data-dir="$profile_dir" \
    --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223 \
    --ozone-platform=x11 --start-maximized \
    --no-first-run --no-default-browser-check \
    --disable-background-mode "${@:-chrome://newtab/}"
