#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if ! sudo test -s /etc/credstore.encrypted/productivity-push; then
    echo 'Phone approval not provisioned; encrypted notification credential required.'
    exit 0
fi
sudo install -m 755 "$repo_root/bin/productivity-push.py" /usr/local/libexec/productivity-push.py
sudo install -m 644 "$repo_root/config/systemd/productivity-push.service" /etc/systemd/system/productivity-push.service
sudo systemctl daemon-reload
sudo systemctl enable --now productivity-push.service
# Only create this mapping when none exists. Never replace another Serve app.
if [[ $(tailscale serve status) == 'No serve config' ]]; then
    sudo tailscale serve --bg --yes http://127.0.0.1:18742
fi
