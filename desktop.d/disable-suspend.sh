#!/bin/bash
# Disable system suspend on bazzite-desktop.
#
# This is a 24/7 gaming + dev server. s2idle resume is broken on this AMD 9950X +
# RTX 4070 box, so any suspend leaves the machine dead until a hard reset. Bazzite's
# deck.conf ships HandlePowerKey=suspend, so a stray power-button tap = lockup.
#
# Fix: remap the power key to a clean poweroff and mask every sleep target so nothing
# (power key, logind, a stray `systemctl suspend`) can ever suspend the box.
#
# Diagnosed 2026-06-05 after repeated hard resets that were misattributed to thermals.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DROPIN_SRC="$REPO_ROOT/config/logind.conf.d/zz-no-suspend.conf"
DROPIN_DST="/etc/systemd/logind.conf.d/zz-no-suspend.conf"

echo "Disabling system suspend (24/7 server, broken s2idle resume)..."

# 1. Install the logind drop-in (overrides deck.conf's HandlePowerKey=suspend).
sudo mkdir -p /etc/systemd/logind.conf.d
if ! sudo cmp -s "$DROPIN_SRC" "$DROPIN_DST" 2>/dev/null; then
    sudo install -m 0644 "$DROPIN_SRC" "$DROPIN_DST"
    echo "✓ Installed $DROPIN_DST"
    sudo systemctl restart systemd-logind
    echo "✓ Reloaded systemd-logind"
else
    echo "✓ logind drop-in already current"
fi

# Remove the old mis-prefixed drop-in if a previous run left it (99- loses to deck.conf).
if [ -e /etc/systemd/logind.conf.d/99-no-suspend.conf ]; then
    sudo rm -f /etc/systemd/logind.conf.d/99-no-suspend.conf
    echo "✓ Removed stale 99-no-suspend.conf (sorted before deck.conf, ineffective)"
fi

# 2. Mask all sleep targets so suspend can never be entered, by any path.
for t in sleep.target suspend.target hibernate.target hybrid-sleep.target; do
    if [ "$(systemctl is-enabled "$t" 2>/dev/null || true)" != "masked" ]; then
        sudo systemctl mask "$t"
        echo "✓ Masked $t"
    else
        echo "✓ $t already masked"
    fi
done

# 3. Verify.
echo ""
echo "Effective power-key action:"
sudo systemd-analyze cat-config systemd/logind.conf 2>/dev/null | grep -iE '^HandlePowerKey' | tail -1
echo "Sleep targets:"
systemctl is-enabled sleep.target suspend.target hibernate.target hybrid-sleep.target 2>&1 | paste -sd' '
echo ""
echo "✅ Suspend disabled. Power button now does a clean shutdown."
