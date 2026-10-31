#!/usr/bin/env bash
# GNOME productivity access with a client-sized virtual monitor.
set -euo pipefail

# Retired in favor of the independent encrypted desktop. Explicit rollback only.
if [[ "${BAZZITE_ENABLE_LEGACY_PRODUCTIVITY:-0}" != 1 ]]; then
    echo 'Legacy productivity setup skipped; encrypted GNOME is the default.'
    exit 0
fi
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$repo_root/bin/setup-gnome-rdp.py"

for scope in runtime permanent; do
    flags=()
    [[ "$scope" == permanent ]] && flags+=(--permanent)
    sudo firewall-cmd "${flags[@]}" --zone=moonlight-tailnet --add-port=3389/tcp
    sudo firewall-cmd "${flags[@]}" --zone=FedoraWorkstation --add-rich-rule='rule family="ipv4" source address="10.0.0.0/24" port port="3389" protocol="tcp" accept'
    sudo firewall-cmd "${flags[@]}" --zone=FedoraWorkstation --add-rich-rule='rule priority="-100" family="ipv4" source NOT address="10.0.0.0/24" port port="3389" protocol="tcp" drop'
    sudo firewall-cmd "${flags[@]}" --zone=FedoraWorkstation --add-rich-rule='rule priority="-100" family="ipv6" port port="3389" protocol="tcp" drop'
done
