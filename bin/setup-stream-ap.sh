#!/usr/bin/env bash
# Direct 5 GHz streaming AP; preserve existing credentials on reapply.
set -euo pipefail
SSID="${STREAM_AP_SSID:-Bazzite}"
IFACE="${STREAM_AP_IFACE:-wlp9s0}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo rfkill unblock wifi
sudo nmcli radio wifi on
if ! nmcli -t -f NAME connection show | rg -qx desk-stream; then
    : "${STREAM_AP_PSK:?set STREAM_AP_PSK for initial hotspot creation}"
    sudo nmcli connection add type wifi ifname "$IFACE" con-name desk-stream autoconnect yes \
      ssid "$SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$STREAM_AP_PSK" \
      ipv4.method shared ipv6.method ignore
fi
sudo nmcli connection modify desk-stream connection.autoconnect yes \
  802-11-wireless.mode ap 802-11-wireless.band a 802-11-wireless.channel 149 \
  802-11-wireless.channel-width 80 802-11-wireless.powersave 2
sudo nmcli connection up desk-stream
sudo install -m 0644 "$REPO_ROOT/config/firewalld/services/moonlight-streams.xml" /etc/firewalld/services/moonlight-streams.xml
sudo firewall-cmd --reload
sudo firewall-cmd --permanent --zone=nm-shared --add-service=moonlight-streams
sudo firewall-cmd --zone=nm-shared --add-service=moonlight-streams
sudo firewall-cmd --permanent --zone=nm-shared --add-masquerade
printf '%s\n' 'Direct AP ready: Steam 10.42.0.1; private Chrome 10.42.0.1:48989.'
iw dev "$IFACE" info
