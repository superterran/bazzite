#!/bin/bash
# Setup Gamescope Display Configuration
# This script configures the gamescope output connector.
# It checks the preferred connector first, then falls back to auto-detection.

set -euo pipefail

echo "Setting up Gamescope display configuration..."

# Preferred gaming display connector — change this if you move cables
PREFERRED_CONNECTOR="DP-4"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create the necessary directories
mkdir -p ~/.config/environment.d

# Function to check if a specific connector is connected
is_connected() {
    local target="$1"
    for status_file in /sys/class/drm/card*/card*-"${target}"/status; do
        if [ -f "$status_file" ] && [ "$(cat "$status_file")" = "connected" ]; then
            return 0
        fi
    done
    return 1
}

# Function to get first connected display of a given type (HDMI or DP)
get_first_connected() {
    local pattern="$1"
    for status_file in /sys/class/drm/card*/card*-${pattern}*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            if [ "$(cat "$status_file")" = "connected" ]; then
                echo "$connector" | sed 's/^card[0-9]*-//'
                return 0
            fi
        fi
    done
    return 1
}

# Determine output connector
PREFERRED_OUTPUT=""

# First: check if the preferred connector is connected
if is_connected "$PREFERRED_CONNECTOR"; then
    PREFERRED_OUTPUT="$PREFERRED_CONNECTOR"
    echo "Preferred connector $PREFERRED_CONNECTOR is connected."
else
    echo "Preferred connector $PREFERRED_CONNECTOR is not connected, auto-detecting..."
    # Fallback: first connected DP, then HDMI
    if DP_OUTPUT=$(get_first_connected "DP"); then
        PREFERRED_OUTPUT="$DP_OUTPUT"
        echo "Found connected DisplayPort display: $PREFERRED_OUTPUT"
    elif HDMI_OUTPUT=$(get_first_connected "HDMI"); then
        PREFERRED_OUTPUT="$HDMI_OUTPUT"
        echo "Found connected HDMI display: $PREFERRED_OUTPUT"
    else
        echo "No HDMI or DisplayPort displays found connected"
        exit 0
    fi
fi

# Create/update the gamescope environment configuration
GAMESCOPE_CONF="$HOME/.config/environment.d/10-gamescope-session.conf"

echo "Setting OUTPUT_CONNECTOR=$PREFERRED_OUTPUT"
cat > "$GAMESCOPE_CONF" << EOF
OUTPUT_CONNECTOR=$PREFERRED_OUTPUT
EOF

echo "Gamescope display configuration updated!"
echo "Configuration saved to: $GAMESCOPE_CONF"
echo ""
echo "The configuration will take effect on the next gamescope session restart."
echo "Current setting: OUTPUT_CONNECTOR=$PREFERRED_OUTPUT"
