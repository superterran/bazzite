#!/bin/bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
sudo install -o root -g root -m 0755 "$repo_root/bin/quest-hotspot-forwarding.sh" /etc/NetworkManager/dispatcher.d/90-quest-hotspot-forwarding
sudo /etc/NetworkManager/dispatcher.d/90-quest-hotspot-forwarding wlp9s0 up
sudo firewall-cmd --permanent --zone=nm-shared --add-service=steam-streaming
sudo firewall-cmd --zone=nm-shared --add-service=steam-streaming
