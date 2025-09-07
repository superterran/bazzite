#!/bin/bash
set -euo pipefail

echo "Setting up Warp Terminal..."

# Check if Warp Terminal is already installed
if rpm -q warp-terminal &>/dev/null; then
    echo "Warp Terminal already installed, skipping..."
    exit 0
fi

# On immutable systems like Bazzite, install via rpm-ostree
# Note: This requires the repository to be configured in the container image
if command -v rpm-ostree &>/dev/null; then
    echo "Installing Warp Terminal via rpm-ostree..."
    
    # Check if already scheduled for installation
    if rpm-ostree status | grep -q "warp-terminal"; then
        echo "Warp Terminal already scheduled for installation, skipping..."
        echo "Note: A reboot is required for Warp Terminal to become available"
        exit 0
    fi
    
    # Verify the repository is available
    if ! dnf search warp-terminal &>/dev/null; then
        echo "Error: Warp Terminal package not found in repositories."
        echo "Make sure the container image includes the Warp repository configuration."
        exit 1
    fi
    
    # Install Warp Terminal - requires reboot for availability
    sudo rpm-ostree install warp-terminal
    
    echo "✓ Warp Terminal scheduled for installation via rpm-ostree"
    echo "Note: A reboot is required for Warp Terminal to become available"
    
else
    echo "Warning: rpm-ostree not found. This script is designed for immutable systems."
    echo "For traditional package managers, use: sudo dnf install warp-terminal"
    exit 1
fi

echo "Warp Terminal setup completed successfully"
