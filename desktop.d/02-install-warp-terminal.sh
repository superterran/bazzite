#!/bin/bash
# Install Warp Terminal
# This script installs Warp Terminal from the official RPM package

set -euo pipefail

echo "Installing Warp Terminal..."

# Check if Warp Terminal is already installed
if rpm -q warp-terminal &>/dev/null; then
    echo "Warp Terminal is already installed, skipping..."
    exit 0
fi

# Install Warp Terminal
echo "Adding Warp Terminal RPM package..."
rpm-ostree install warp-terminal

echo "Warp Terminal installation queued. A reboot will be required to complete the installation."
