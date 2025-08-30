#!/bin/bash
# Smart setup script that detects system type and runs appropriate configuration

set -euo pipefail

echo "Bazzite Custom Setup"
echo "===================="

# Detect system type
SYSTEM_TYPE="unknown"

# Check if we're on a handheld device
if grep -qi "ROG Ally\|Steam Deck\|GPD" /sys/devices/virtual/dmi/id/product_name 2>/dev/null; then
    SYSTEM_TYPE="handheld"
elif grep -qi "desktop\|tower" /sys/devices/virtual/dmi/id/chassis_type 2>/dev/null; then
    SYSTEM_TYPE="desktop"
else
    # Fallback: assume desktop if we can't detect
    SYSTEM_TYPE="desktop"
fi

echo "Detected system type: $SYSTEM_TYPE"
echo ""

# Run common user setup
echo "Running common user setup..."
if [ -f "./user-setup.sh" ]; then
    ./user-setup.sh
else
    echo "user-setup.sh not found, downloading..."
    curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/user-setup.sh | bash
fi

echo ""

# Run system-specific setup
if [ "$SYSTEM_TYPE" == "desktop" ]; then
    echo "Running desktop-specific setup (OpenRGB configuration)..."
    if [ -f "./desktop-setup.sh" ]; then
        ./desktop-setup.sh
    else
        echo "desktop-setup.sh not found, downloading..."
        curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/desktop-setup.sh | bash
    fi
elif [ "$SYSTEM_TYPE" == "handheld" ]; then
    echo "Handheld system detected - skipping desktop-specific configurations"
    echo "OpenRGB and other desktop features will not be configured"
fi

echo ""
echo "Setup complete! Please reboot to ensure all changes take effect."
echo ""
echo "What was configured:"
echo "- Common Flatpak applications"
echo "- User services (ollama, sunshine, etc.)"
if [ "$SYSTEM_TYPE" == "desktop" ]; then
    echo "- OpenRGB with 'Ideal' profile (lights off)"
    echo "- OpenRGB auto-start service"
fi
echo ""
echo "Manual steps remaining:"
echo "- Sign into your applications (Chrome, Slack, etc.)"
echo "- Configure GNOME extensions as needed"
echo "- Set up development tools"
