#!/bin/bash
# Setup Gamescope Display Configuration
# This script configures gamescope to prioritize HDMI over DisplayPort when available

set -euo pipefail

echo "Setting up Gamescope display configuration..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create the necessary directories
mkdir -p ~/.config/environment.d

# Function to get connected HDMI displays
get_connected_hdmi() {
    for status_file in /sys/class/drm/card*/card*-HDMI*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            local status=$(cat "$status_file")
            if [ "$status" = "connected" ]; then
                # Convert card2-HDMI-A-2 to HDMI-A-2
                echo "$connector" | sed 's/^card[0-9]*-//'
                return 0
            fi
        fi
    done
    return 1
}

# Function to get connected DisplayPort displays  
get_connected_dp() {
    for status_file in /sys/class/drm/card*/card*-DP*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            local status=$(cat "$status_file")
            if [ "$status" = "connected" ]; then
                # Convert card2-DP-2 to DP-2
                echo "$connector" | sed 's/^card[0-9]*-//'
                return 0
            fi
        fi
    done
    return 1
}

# Check for connected displays and set preference
PREFERRED_OUTPUT=""

# First priority: HDMI
if HDMI_OUTPUT=$(get_connected_hdmi); then
    PREFERRED_OUTPUT="$HDMI_OUTPUT"
    echo "Found connected HDMI display: $PREFERRED_OUTPUT"
# Second priority: DisplayPort  
elif DP_OUTPUT=$(get_connected_dp); then
    PREFERRED_OUTPUT="$DP_OUTPUT"
    echo "Found connected DisplayPort display: $PREFERRED_OUTPUT"
else
    echo "No HDMI or DisplayPort displays found connected"
    exit 0
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
