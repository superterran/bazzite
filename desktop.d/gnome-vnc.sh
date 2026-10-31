#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Accept only tailnet clients, including when other interfaces allow high ports.
for scope in runtime permanent; do
    flags=()
    [[ "$scope" == permanent ]] && flags+=(--permanent)
    sudo firewall-cmd "${flags[@]}" --zone=moonlight-tailnet --add-port=5901/tcp
    for zone in FedoraWorkstation nm-shared docker; do
        for family in ipv4 ipv6; do
            sudo firewall-cmd "${flags[@]}" --zone="$zone" --add-rich-rule="rule priority=\"-100\" family=\"$family\" port port=\"5901\" protocol=\"tcp\" drop"
        done
    done
done
python3 "$repo_root/bin/setup-gnome-vnc.py"
