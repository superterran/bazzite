#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ! -f "$repo_root/config/secure-productivity/native-rdp-cert.sha256" && ${BAZZITE_CONFIGURE_NATIVE_RDP:-0} != 1 ]]; then
    echo 'Native encrypted RDP has not been provisioned; leaving existing bridge unchanged.'
    exit 0
fi
# Native GNOME binds all addresses. Keep this TV-only endpoint blocked in every
# external zone. Loopback is accepted by the host before zone processing.
rule='rule priority="-20" port port="3393" protocol="tcp" drop'
for zone in $(sudo firewall-cmd --get-zones); do
    sudo firewall-cmd --zone="$zone" --add-rich-rule="$rule" >/dev/null
    sudo firewall-cmd --permanent --zone="$zone" --add-rich-rule="$rule" >/dev/null
done
if [[ ${BAZZITE_CONFIGURE_NATIVE_RDP:-0} == 1 ]]; then
    /usr/bin/python3 "$repo_root/bin/setup-secure-native-rdp.py"
    account_uid=$(id -u desktop-secure)
    account_gid=$(id -g desktop-secure)
    sudo setpriv "--reuid=$account_uid" "--regid=$account_gid" --init-groups \
        env HOME=/var/home/desktop-secure "XDG_RUNTIME_DIR=/run/user/$account_uid" \
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$account_uid/bus" \
        /usr/bin/systemctl --user restart gnome-remote-desktop-headless.service
fi
