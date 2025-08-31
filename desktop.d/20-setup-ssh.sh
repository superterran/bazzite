#!/bin/bash
# Setup SSH remote connections
# This script enables SSH service for remote connections using ujust

set -euo pipefail

echo "Setting up SSH remote connections..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if SSH is already enabled
if systemctl is-enabled sshd.service >/dev/null 2>&1; then
    echo "SSH service is already enabled, skipping..."
else
    echo "Enabling SSH service for remote connections..."
    
    # Use ujust to enable SSH on boot
    if command -v ujust >/dev/null 2>&1; then
        ujust toggle-ssh enable
        echo "SSH service enabled successfully via ujust"
    else
        echo "ujust command not found, falling back to systemctl..."
        sudo systemctl enable --now sshd.service
        echo "SSH service enabled successfully via systemctl"
    fi
fi

# Ensure SSH service is running
if ! systemctl is-active sshd.service >/dev/null 2>&1; then
    echo "Starting SSH service..."
    sudo systemctl start sshd.service
    echo "SSH service started successfully"
else
    echo "SSH service is already running"
fi

# Show SSH connection information
echo ""
echo "SSH Setup Complete!"
echo "===================="
echo "SSH is now enabled and running on this system."
echo ""
echo "Connection information:"
echo "- SSH service: $(systemctl is-active sshd.service 2>/dev/null || echo 'unknown')"
echo "- SSH port: $(sudo ss -tlnp | grep :22 | head -1 | awk '{print $4}' | cut -d: -f2 || echo '22')"
echo "- Local IP addresses:"
ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print "  - " $2}' | cut -d'/' -f1 || echo "  - Unable to detect IP addresses"
echo ""
echo "To connect from another machine:"
echo "  ssh $(whoami)@<ip_address>"
echo ""
echo "Note: Make sure your firewall allows SSH connections on port 22"
echo "You may need to configure your router for external access"
