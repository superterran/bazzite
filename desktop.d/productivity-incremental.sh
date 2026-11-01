#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if ! sudo test -s /etc/productivity-restic.json; then
    echo 'Initialize Restic explicitly and verify recovery before enabling history.'
    exit 0
fi
if ! sudo test -s /var/lib/productivity-recovery/incremental-restore-test.json; then
    echo 'Independent incremental restore test must pass before switching timers.'
    exit 1
fi
for unit in productivity-incremental.service productivity-incremental.timer productivity-baseline.service; do
    sudo install -m 644 "$repo_root/config/systemd/$unit" /etc/systemd/system/
done
sudo systemctl daemon-reload
sudo systemctl enable --now productivity-incremental.timer
sudo systemctl disable --now productivity-backup.timer
