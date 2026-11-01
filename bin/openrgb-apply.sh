#!/bin/bash
# Direct lights-off writes; no persistent SDK server or stale profile matching.
set -euo pipefail
rgb=(/usr/bin/flatpak run org.openrgb.OpenRGB --noautoconnect)
for ((attempt=1; attempt<=30; attempt++)); do
    listing=$("${rgb[@]}" --list-devices) || { sleep 2; continue; }
    mapfile -t ram < <(printf '%s\n' "$listing" | sed -n 's/^\([0-9][0-9]*\): Corsair Vengeance RGB DDR5$/\1/p')
    mapfile -t board < <(printf '%s\n' "$listing" | sed -n 's/^\([0-9][0-9]*\): ASUS ROG STRIX B850-I GAMING WIFI$/\1/p')
    if [[ ${#ram[@]} -eq 2 && ${#board[@]} -eq 1 ]]; then
        # 120 is the controller-supported address range, not a physical LED count.
        # Black all addresses, including the MSI AIO attached to these headers.
        "${rgb[@]}" --device "${ram[0]}" --mode Direct --color 000000 \
          --device "${ram[1]}" --mode Direct --color 000000 \
          --device "${board[0]}" --zone 0 --size 120 --zone 1 --size 120 --mode Direct --color 000000
        echo "openrgb-apply: lights-off writes completed for both Corsair DIMMs and ASUS headers"
        exit 0
    fi
    sleep 2
done
echo 'openrgb-apply: expected two Corsair DIMMs and one ASUS controller were not detected' >&2
exit 1
