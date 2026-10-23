#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for script in decky-maintenance.py nightly-maintenance.py; do
    sudo install -Dm755 "$REPO_ROOT/bin/$script" "/usr/local/libexec/bazzite/$script"
done
for unit in nightly-maintenance.service nightly-maintenance.timer; do
    sudo install -Dm644 "$REPO_ROOT/config/systemd/system/$unit" "/etc/systemd/system/$unit"
done
sudo systemctl daemon-reload
# One timer owns the full cycle; do not race a second Decky job or uupd run.
sudo systemctl disable --now uupd.timer decky-maintenance.timer
sudo systemctl enable --now nightly-maintenance.timer
