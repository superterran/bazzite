#!/usr/bin/env bash
# Allow gaming Syncthing TCP only on the existing Tailscale interface zone.
set -euo pipefail
TAILNET_ZONE=moonlight-tailnet
if ! sudo firewall-cmd --get-active-zones | grep -q "$TAILNET_ZONE"; then
    printf 'Existing Tailscale firewall zone is not active; configure the tailnet first.\n' >&2
    exit 1
fi
if ! sudo firewall-cmd --permanent --zone="$TAILNET_ZONE" --query-port=22000/tcp >/dev/null; then
    sudo firewall-cmd --permanent --zone="$TAILNET_ZONE" --add-port=22000/tcp
fi
if ! sudo firewall-cmd --zone="$TAILNET_ZONE" --query-port=22000/tcp >/dev/null; then
    sudo firewall-cmd --zone="$TAILNET_ZONE" --add-port=22000/tcp
fi
