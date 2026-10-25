#!/bin/bash
# Keep desktop SSH available on the home LAN and Tailscale; retire WAN SSH/DDNS.
set -euo pipefail
ZONE=FedoraWorkstation
TAILNET_ZONE=moonlight-tailnet
LAN=10.0.0.0/24
SSH_PORT=2222

sudo firewall-cmd --state >/dev/null
for scope in runtime permanent; do
    flags=()
    [[ "$scope" == permanent ]] && flags+=(--permanent)
    fw() { sudo firewall-cmd "${flags[@]}" "$@"; }
    fw --zone="$TAILNET_ZONE" --add-port="$SSH_PORT/tcp"
    fw --zone="$ZONE" --add-rich-rule="rule family=\"ipv4\" source address=\"$LAN\" port port=\"$SSH_PORT\" protocol=\"tcp\" accept"
    fw --zone="$ZONE" --add-rich-rule="rule priority=\"-100\" family=\"ipv4\" source not address=\"$LAN\" port port=\"$SSH_PORT\" protocol=\"tcp\" drop"
    fw --zone="$ZONE" --add-rich-rule="rule priority=\"-100\" family=\"ipv6\" port port=\"$SSH_PORT\" protocol=\"tcp\" drop"
    fw --zone="$ZONE" --remove-port="$SSH_PORT/tcp"
done

# Old DDNS updates would otherwise restore the public WAN address.
sudo systemctl disable --now cloudflare-ddns.timer
sudo systemctl stop cloudflare-ddns.service

echo 'Desktop SSH: LAN IPv4 and Tailscale allowed; WAN IPv4/IPv6 blocked on the physical interface.'
echo 'Cloudflare DDNS timer retired. Existing SSH keys, port and HTTP/MCP tunnels preserved.'
