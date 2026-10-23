#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo install -Dm755 "$REPO_ROOT/bin/decky-maintenance.py" /usr/local/libexec/bazzite/decky-maintenance.py
for unit in decky-maintenance.service decky-maintenance.timer; do
    sudo install -Dm644 "$REPO_ROOT/config/systemd/system/$unit" "/etc/systemd/system/$unit"
done
sudo systemctl daemon-reload
if systemctl is-enabled --quiet nightly-maintenance.timer; then
    sudo systemctl disable --now decky-maintenance.timer
else
    sudo systemctl enable --now decky-maintenance.timer
fi
