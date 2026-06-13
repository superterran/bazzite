#!/usr/bin/env bash
# setup-stream-ap.sh — recreate the local "Bazzite" 5GHz streaming AP on the
# onboard MT7925 (WiFi 7) so an iPad/Moonlight client pairs DIRECTLY to bazzite,
# bypassing the xFi pod/mesh/backhaul. bazzite keeps internet on wired eno1 and
# shares it (NAT) to the AP. AP IP / Moonlight target: 10.42.0.1
#
# PSK is NOT stored in git. Pass it in:  STREAM_AP_PSK='yourpass' ./setup-stream-ap.sh
set -euo pipefail
SSID="${STREAM_AP_SSID:-Bazzite}"
PSK="${STREAM_AP_PSK:?set STREAM_AP_PSK to the wifi password}"
IFACE="${STREAM_AP_IFACE:-wlp9s0}"
sudo rfkill unblock wifi || true
sudo nmcli radio wifi on || true
sudo nmcli connection delete desk-stream 2>/dev/null || true
sudo nmcli connection add type wifi ifname "$IFACE" con-name desk-stream autoconnect yes \
  ssid "$SSID" \
  802-11-wireless.mode ap 802-11-wireless.band a 802-11-wireless.channel 149 \
  wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK" \
  ipv4.method shared ipv6.method ignore
sudo nmcli connection up desk-stream
sudo firewall-cmd --permanent --zone=nm-shared --add-masquerade || true
echo "AP '$SSID' up on 10.42.0.1 (5GHz ch36). Point Moonlight at 10.42.0.1."
