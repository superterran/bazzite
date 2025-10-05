#!/bin/bash
# Switch to Gaming Mode (Gamescope) with HDMI display and restart
# This is a convenience script that combines session switching and display configuration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse flags
FORCE_RESTART=false
if [[ "${1:-}" == "-f" ]] || [[ "${1:-}" == "--force" ]]; then
    FORCE_RESTART=true
fi

echo "🎮 Switching to Gaming Mode..."
echo ""

# Step 1: Configure Gamescope display to use HDMI
echo "Step 1/3: Configuring display for HDMI..."

# Find connected HDMI display
HDMI_DISPLAY=""
for status_file in /sys/class/drm/card*/card*-HDMI*/status; do
    if [ -f "$status_file" ]; then
        connector=$(basename $(dirname "$status_file"))
        status=$(cat "$status_file")
        if [ "$status" = "connected" ]; then
            HDMI_DISPLAY=$(echo "$connector" | sed 's/^card[0-9]*-//')
            break
        fi
    fi
done

if [ -z "$HDMI_DISPLAY" ]; then
    echo "⚠️  Warning: No connected HDMI display found"
    echo "Available displays:"
    "$SCRIPT_DIR/switch-display.sh" list
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
else
    echo "✓ Found HDMI display: $HDMI_DISPLAY"
    
    # Set the display configuration
    mkdir -p ~/.config/environment.d
    GAMESCOPE_CONF="$HOME/.config/environment.d/10-gamescope-session.conf"
    echo "OUTPUT_CONNECTOR=$HDMI_DISPLAY" > "$GAMESCOPE_CONF"
    echo "✓ Display configured for $HDMI_DISPLAY"
fi

echo ""

# Step 2: Switch to Gamescope session
echo "Step 2/3: Switching to Gamescope session..."
"$SCRIPT_DIR/toggle-session.sh" gamescope

echo ""

# Step 3: Restart GDM
echo "Step 3/3: Restarting to apply changes..."
echo ""

if [ "$FORCE_RESTART" = true ]; then
    echo "🎮 Restarting into Gaming Mode..."
    sleep 1
    sudo systemctl restart gdm
else
    echo "This will log you out and restart GDM."
    read -p "Ready to restart now? [Y/n] " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        echo "Changes saved but not applied."
        echo "To apply changes:"
        echo "  - Log out and log back in"
        echo "  - Reboot the system"
        echo "  - Run: sudo systemctl restart gdm"
        echo "  - Run: ./bin/gaming-mode.sh --force"
    else
        echo ""
        echo "🎮 Restarting into Gaming Mode..."
        sleep 1
        sudo systemctl restart gdm
    fi
fi
