#!/bin/bash
# Setup OpenRGB configuration
# This script configures OpenRGB with the custom profile and systemd service

set -euo pipefail

echo "Setting up OpenRGB configuration..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing OpenRGB Flatpak..."
flatpak install -y flathub org.openrgb.OpenRGB || echo "OpenRGB Flatpak may have failed to install, continuing..."

# Configure OpenRGB
echo "Configuring OpenRGB for desktop..."
mkdir -p ~/.config/OpenRGB
mkdir -p ~/.config/systemd/user

# Copy OpenRGB configuration files from the repo
if [ -f "$SCRIPT_DIR/config/openrgb/Ideal.orp" ]; then
    echo "Installing OpenRGB profile 'Ideal'..."
    cp "$SCRIPT_DIR/config/openrgb/Ideal.orp" ~/.config/OpenRGB/
fi

if [ -f "$SCRIPT_DIR/config/openrgb/LightsOff.orp" ]; then
    echo "Installing OpenRGB profile 'LightsOff'..."
    cp "$SCRIPT_DIR/config/openrgb/LightsOff.orp" ~/.config/OpenRGB/
fi

if [ -f "$SCRIPT_DIR/config/openrgb/OpenRGB.json" ]; then
    echo "Installing OpenRGB configuration..."
    cp "$SCRIPT_DIR/config/openrgb/OpenRGB.json" ~/.config/OpenRGB/
fi

echo "OpenRGB will automatically load the 'Ideal' profile to turn off all lights on startup."

if [ -f "$SCRIPT_DIR/config/systemd/user/openrgb.service" ]; then
    echo "Installing OpenRGB systemd service..."
    cp "$SCRIPT_DIR/config/systemd/user/openrgb.service" ~/.config/systemd/user/
    
    # Reload systemd and enable the service
    systemctl --user daemon-reload
    systemctl --user enable openrgb.service || true
    
    # Only start if OpenRGB flatpak is installed
    if flatpak list --app | grep -q org.openrgb.OpenRGB; then
        echo "Starting OpenRGB service..."
        systemctl --user start openrgb.service || echo "Failed to start OpenRGB service - will start on next login"
    else
        echo "OpenRGB Flatpak not found. Install it first: flatpak install flathub org.openrgb.OpenRGB"
    fi
else
    echo "OpenRGB systemd service file not found, skipping..."
fi

echo "OpenRGB setup complete!"
