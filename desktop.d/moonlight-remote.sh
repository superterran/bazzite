#!/usr/bin/env bash
# Tailscale enrollment remains interactive; never embed an auth key.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo systemctl enable --now tailscaled
sudo install -m 0644 "$REPO_ROOT/config/firewalld/services/moonlight-streams.xml" /etc/firewalld/services/moonlight-streams.xml
sudo firewall-cmd --reload
if ! sudo firewall-cmd --permanent --get-zones | tr ' ' '\n' | rg -qx moonlight-tailnet; then
    sudo firewall-cmd --permanent --new-zone=moonlight-tailnet
fi
sudo firewall-cmd --permanent --zone=moonlight-tailnet --add-interface=tailscale0
sudo firewall-cmd --permanent --zone=moonlight-tailnet --add-service=moonlight-streams
sudo firewall-cmd --reload
printf '%s\n' 'Enroll if needed: sudo tailscale up --hostname=bazzite-desktop --accept-routes=false --accept-dns=false' 'Then add the desktop Tailscale IP in Moonlight: default port for Steam, :48989 for Chrome.'
