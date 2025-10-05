#!/bin/bash
# Switch to Desktop Mode (GNOME) and restart
# This is a convenience script for quickly returning to the GNOME desktop

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse flags
FORCE_RESTART=false
if [[ "${1:-}" == "-f" ]] || [[ "${1:-}" == "--force" ]]; then
    FORCE_RESTART=true
fi

echo "🖥️  Switching to Desktop Mode (GNOME)..."
echo ""

# Step 1: Switch to GNOME session
echo "Step 1/2: Switching to GNOME session..."
"$SCRIPT_DIR/toggle-session.sh" gnome

echo ""

# Step 2: Restart GDM
echo "Step 2/2: Restarting to apply changes..."
echo ""

if [ "$FORCE_RESTART" = true ]; then
    echo "🖥️  Restarting into Desktop Mode..."
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
        echo "  - Run: ./bin/desktop-mode.sh --force"
    else
        echo ""
        echo "🖥️  Restarting into Desktop Mode..."
        sleep 1
        sudo systemctl restart gdm
    fi
fi
