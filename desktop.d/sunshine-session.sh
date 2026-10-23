#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ! -x /usr/bin/sunshine ]]; then
    echo 'Native Sunshine is not installed; session wrapper skipped.'
    exit 0
fi
unit_dir="$HOME/.config/systemd/user/app-dev.lizardbyte.app.Sunshine.service.d"
mkdir -p "$unit_dir"
install -m 644 "$repo_root/config/systemd/user/app-dev.lizardbyte.app.Sunshine.service.d/session.conf" "$unit_dir/session.conf"
systemctl --user daemon-reload
systemctl --user enable app-dev.lizardbyte.app.Sunshine.service
# Apply on next start; do not interrupt a stream during general system setup.
echo 'Sunshine session environment configured; restart its user service to apply.'
