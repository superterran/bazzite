#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if ! mountpoint -q /var/home/desktop-secure; then
    echo 'Encrypted home locked; leaving saved extension configuration untouched.'
    exit 0
fi
account_uid=$(id -u desktop-secure)
account_gid=$(id -g desktop-secure)
sudo setpriv "--reuid=$account_uid" "--regid=$account_gid" --init-groups \
    env HOME=/var/home/desktop-secure "XDG_RUNTIME_DIR=/run/user/$account_uid" \
    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$account_uid/bus" \
    /usr/bin/python3 "$repo_root/bin/setup-bottom-overview.py"
