#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if ! sudo test -s /etc/productivity-recovery.json; then
    echo 'Initialize recovery settings explicitly before enabling backups.'
    exit 0
fi
for dependency in age zstd; do
    if [[ ! -x /home/linuxbrew/.linuxbrew/bin/$dependency ]]; then brew install "$dependency"; fi
done
for unit in productivity-backup.service productivity-backup.timer; do
    sudo install -m 644 "$repo_root/config/systemd/$unit" /etc/systemd/system/
done
sudo systemctl daemon-reload
if sudo test -s /var/lib/productivity-recovery/incremental-restore-test.json && systemctl is-enabled --quiet productivity-incremental.timer; then
    echo 'Verified incremental history owns the nightly schedule; full archive remains manual.'
else
    sudo systemctl enable --now productivity-backup.timer
fi
