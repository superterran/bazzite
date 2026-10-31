#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! mountpoint -q /var/home/desktop-secure; then
    echo 'Encrypted desktop locked; keeping its existing 1Password configuration.'
    exit 0
fi
sudo install -m 755 "$repo_root/bin/launch-secure-1password.sh" /usr/local/libexec/launch-secure-1password.sh
sudo /usr/bin/python3 "$repo_root/bin/setup-secure-1password.py"
account_uid=$(id -u desktop-secure)
account_gid=$(id -g desktop-secure)
as_remote=(sudo setpriv "--reuid=$account_uid" "--regid=$account_gid" --init-groups env HOME=/var/home/desktop-secure "XDG_RUNTIME_DIR=/run/user/$account_uid" "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$account_uid/bus")
"${as_remote[@]}" systemctl --user daemon-reload
"${as_remote[@]}" systemctl --user set-environment SSH_AUTH_SOCK=/var/home/desktop-secure/.1password/agent.sock OP_BIOMETRIC_UNLOCK_ENABLED=true
"${as_remote[@]}" env SSH_AUTH_SOCK=/var/home/desktop-secure/.1password/agent.sock OP_BIOMETRIC_UNLOCK_ENABLED=true dbus-update-activation-environment --systemd SSH_AUTH_SOCK OP_BIOMETRIC_UNLOCK_ENABLED
"${as_remote[@]}" systemctl --user enable secure-1password.service
# Don't replace an app process the user already has open. This service will
# launch it automatically in future unlocked sessions.
