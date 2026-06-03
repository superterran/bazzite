#!/bin/bash
# Idempotent setup for the TV-control feature.
#
# - Installs the 8BitDo USB-wake udev rule (so orb-button can wake the host)
# - Enables tv-orb-listener.service (the evdev → atv pause → tv-switch flow)
#
# Assumes ADB Network Debugging is already enabled on the TV, atv.py + tv.py
# have been paired, and `just deploy-services` has been run. See
# scripts/tv-control/README.md for the full setup walkthrough.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Setting up TV control (8BitDo orb → TV input switch)..."

# 1. udev rule for USB wake on the 8BitDo dongle (2dc8:3106)
UDEV_SRC="$REPO_ROOT/config/udev/rules.d/90-8bitdo-wake.rules"
UDEV_DST="/etc/udev/rules.d/90-8bitdo-wake.rules"
if [[ -f "$UDEV_SRC" ]]; then
    if ! sudo diff -q "$UDEV_SRC" "$UDEV_DST" >/dev/null 2>&1; then
        echo "  Installing udev rule: $UDEV_DST"
        sudo install -m 0644 "$UDEV_SRC" "$UDEV_DST"
        sudo udevadm control --reload
        sudo udevadm trigger --action=change --subsystem-match=usb --attr-match=idVendor=2dc8 || true
    else
        echo "  udev rule already up to date."
    fi
else
    echo "  WARN: $UDEV_SRC missing — skipping udev install"
fi

# 2. Verify the dongle is currently armed for wake (informational)
for f in /sys/bus/usb/devices/*/idVendor; do
    [[ -r "$f" ]] || continue
    [[ "$(cat "$f")" == "2dc8" ]] || continue
    dev="$(dirname "$f")"
    wakeup="$(cat "$dev/power/wakeup" 2>/dev/null || echo unknown)"
    ctl="$(cat "$dev/power/control" 2>/dev/null || echo unknown)"
    echo "  8BitDo dongle at $(basename "$dev"): wakeup=$wakeup control=$ctl"
done

# 3. Enable + start the listener (user-scoped)
if systemctl --user list-unit-files tv-orb-listener.service >/dev/null 2>&1; then
    if ! systemctl --user is-enabled --quiet tv-orb-listener.service; then
        echo "  Enabling tv-orb-listener.service..."
        systemctl --user enable --now tv-orb-listener.service
    elif ! systemctl --user is-active --quiet tv-orb-listener.service; then
        echo "  Starting tv-orb-listener.service..."
        systemctl --user start tv-orb-listener.service
    else
        echo "  tv-orb-listener.service already active."
    fi
else
    echo "  WARN: tv-orb-listener.service not installed — run \`just deploy-services\` first"
fi

echo "tv-control setup complete."
echo "Wake-from-S5 (cold off) also needs BIOS settings — see scripts/tv-control/README.md"
