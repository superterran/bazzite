#!/bin/bash
# Apply the lights-off "Ideal" OpenRGB profile via direct local detection.
#
# History: the service used to run a persistent `openrgb --server -p Ideal`.
# Under flatpak+systemd the server process escaped the unit cgroup, so restarts
# left a stale server holding port 6742 and the new one failed to bind -> a
# restart loop, and at cold boot the off-profile often never applied (RAM stayed
# on its default rainbow). There is no other consumer of the SDK server, so we
# dropped it: this just detects the controllers locally and applies the profile.
#
# Retries because the Corsair I2C RAM and ASUS Aura motherboard are not always
# enumerated the instant graphical-session.target is reached (the i2c `uaccess`
# seat ACL needs the session to be active). ALWAYS exits 0.
set -uo pipefail

FLATPAK="/usr/bin/flatpak run org.openrgb.OpenRGB"
PROFILE="Ideal"
EXPECTED=3          # 2x Corsair Dominator RAM + ASUS B850-I motherboard
MAX_TRIES=30        # ~60s, covers the cold-boot seat-ACL settle window
SETTLE=2

apply() {
    # ASUS Aura occasionally needs a second write to latch the Off mode.
    $FLATPAK --noautoconnect --profile "$PROFILE" 2>/dev/null || true
    sleep 1
    $FLATPAK --noautoconnect --profile "$PROFILE" 2>/dev/null || true
}

count=0
for ((i=1; i<=MAX_TRIES; i++)); do
    count=$($FLATPAK --noautoconnect --list-devices 2>/dev/null | grep -cE '^[0-9]+:' || true)
    if [[ "${count:-0}" -ge "$EXPECTED" ]]; then
        apply
        echo "openrgb-apply: applied '$PROFILE' to $count controllers after $i tries"
        exit 0
    fi
    sleep "$SETTLE"
done

echo "openrgb-apply: only ${count:-0}/$EXPECTED controllers after $MAX_TRIES tries; applying anyway"
apply
exit 0
