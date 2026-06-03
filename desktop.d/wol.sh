#!/bin/bash
# Persist Wake-on-LAN on the active wired NetworkManager connection.
#
# Why NetworkManager rather than a systemd unit doing `ethtool -s`:
# - Survives kernel/driver updates and NIC name changes
# - Re-applied on every link-up by NetworkManager
# - One source of truth (the connection profile)
#
# Prerequisite this script cannot fix:
#   The motherboard BIOS must have "Wake on LAN" / "PCIe device wake" enabled.
#   Without it, the NIC loses power on shutdown and the magic packet is never
#   received. Check after the next reboot.

set -euo pipefail

echo "Configuring Wake-on-LAN..."

# Pick the active wired ethernet connection (works even if there are multiple
# bridges/virtual interfaces also active). One nmcli call gives us both name
# and device — DEVICE isn't a valid field in the per-connection detail form.
IFS=$'\t' read -r CONN IFACE < <(nmcli -t -f NAME,TYPE,DEVICE connection show --active \
        | awk -F: -v OFS=$'\t' '$2=="802-3-ethernet" {print $1, $3; exit}')

if [[ -z "${CONN:-}" || -z "${IFACE:-}" ]]; then
    echo "⚠ No active wired ethernet connection found — skipping."
    exit 0
fi
echo "Active wired connection: '$CONN' on '$IFACE'"

# Check hardware support before we promise anything.
if ! sudo ethtool "$IFACE" 2>/dev/null | grep -q 'Supports Wake-on:.*g'; then
    echo "⚠ NIC '$IFACE' does not advertise magic-packet support — skipping."
    exit 0
fi

CURRENT="$(nmcli -t connection show "$CONN" | awk -F: '/^802-3-ethernet\.wake-on-lan:/ {print $2}')"
if [[ "$CURRENT" == "magic" ]]; then
    echo "✓ Wake-on-LAN already pinned to 'magic' on '$CONN'"
else
    echo "Setting 802-3-ethernet.wake-on-lan=magic on '$CONN' (was: ${CURRENT:-default})..."
    sudo nmcli connection modify "$CONN" 802-3-ethernet.wake-on-lan magic
    # Re-activate so the new setting is applied to the running link.
    sudo nmcli connection up "$CONN" >/dev/null
    echo "✓ Wake-on-LAN persisted"
fi

# Report state so the user can verify.
echo ""
echo "Current Wake-on-LAN state:"
sudo ethtool "$IFACE" | grep -E 'Wake-on:' | sed 's/^/  /'
echo "MAC address: $(cat /sys/class/net/"$IFACE"/address)"
echo ""
echo "Remember to enable Wake-on-LAN in BIOS — Linux can only request it,"
echo "the firmware decides whether to keep the NIC powered after shutdown."
