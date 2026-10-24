#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
install -Dm644 "$REPO_ROOT/config/environment.d/90-jetkvm.conf" \
    "$HOME/.config/environment.d/90-jetkvm.conf"
# The legacy TV EDID advertises timings/color capabilities unsuitable for JetKVM.
if systemctl is-enabled --quiet edid-override-hdmi.service 2>/dev/null; then
    sudo systemctl disable --now edid-override-hdmi.service
fi
echo 'JetKVM display policy installed; select 1920x1080 at 60 Hz in Steam, then restart Game Mode.'
