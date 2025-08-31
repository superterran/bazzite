#!/bin/bash
# Setup shell configurations
# This script applies bashrc additions and other shell configurations

set -euo pipefail

echo "Setting up shell configurations..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Apply bashrc additions
if [ -f "$SCRIPT_DIR/config/bashrc-additions" ]; then
    echo "Applying bashrc additions..."
    
    # Create a marker to check if additions are already applied
    MARKER="# Bazzite custom additions"
    
    if ! grep -q "$MARKER" ~/.bashrc 2>/dev/null; then
        echo "" >> ~/.bashrc
        echo "$MARKER" >> ~/.bashrc
        cat "$SCRIPT_DIR/config/bashrc-additions" >> ~/.bashrc
        echo "Bashrc additions applied successfully"
    else
        echo "Bashrc additions already applied, skipping..."
    fi
else
    echo "No bashrc additions file found, skipping..."
fi

# Create local bin directory
mkdir -p ~/.local/bin

# Ensure ~/.local/bin is in PATH (if not already)
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "Adding ~/.local/bin to PATH in bashrc..."
    if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
fi

echo "Shell configuration setup complete!"
