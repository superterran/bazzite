#!/bin/bash
# Setup VSCode Tunnel Service
# This script creates a systemd service to keep VSCode tunnel always available

set -euo pipefail

echo "Setting up VSCode tunnel service..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if VSCode is available
if ! command -v code >/dev/null 2>&1; then
    echo "ERROR: VSCode is not installed. Please install VSCode first."
    exit 1
fi

echo "VSCode version: $(code --version | head -1)"

# Create systemd user service directory if it doesn't exist
USER_SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SERVICE_DIR"

# Check if service already exists
SERVICE_NAME="vscode-tunnel.service"
SERVICE_PATH="$USER_SERVICE_DIR/$SERVICE_NAME"

if [[ -f "$SERVICE_PATH" ]] && systemctl --user is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "VSCode tunnel service already exists and is enabled"
    if systemctl --user is-active "$SERVICE_NAME" >/dev/null 2>&1; then
        echo "VSCode tunnel service is already running"
        echo ""
        echo "Current tunnel status:"
        systemctl --user status "$SERVICE_NAME" --no-pager -l || true
        exit 0
    fi
else
    echo "Creating VSCode tunnel systemd service..."
    
    # Create the systemd service file
    cat > "$SERVICE_PATH" << 'SERVICEEOF'
[Unit]
Description=VSCode Tunnel Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/code tunnel --accept-server-license-terms
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
SERVICEEOF

    echo "VSCode tunnel service file created at $SERVICE_PATH"
fi

# Reload systemd user daemon
echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

# Enable the service
echo "Enabling VSCode tunnel service..."
systemctl --user enable "$SERVICE_NAME"

# Start the service
echo "Starting VSCode tunnel service..."
systemctl --user start "$SERVICE_NAME"

# Enable lingering for the user so service starts on boot
echo "Enabling user lingering for persistent service..."
sudo loginctl enable-linger "$(whoami)"

# Wait a moment for the service to initialize
sleep 3

echo ""
echo "VSCode Tunnel Setup Complete!"
echo "============================="
echo "Service status: $(systemctl --user is-active "$SERVICE_NAME" 2>/dev/null || echo 'unknown')"
echo "Service enabled: $(systemctl --user is-enabled "$SERVICE_NAME" 2>/dev/null || echo 'unknown')"
echo ""
echo "The VSCode tunnel service will:"
echo "- Start automatically when the system boots"
echo "- Restart automatically if it crashes"
echo "- Be accessible from vscode.dev and other machines"
echo ""
echo "To check service status:"
echo "  systemctl --user status $SERVICE_NAME"
echo ""
echo "To view service logs:"
echo "  journalctl --user -u $SERVICE_NAME -f"
echo ""
echo "To stop the service:"
echo "  systemctl --user stop $SERVICE_NAME"
echo ""
echo "To disable the service:"
echo "  systemctl --user disable $SERVICE_NAME"
echo ""

# Show initial status
echo "Current service status:"
systemctl --user status "$SERVICE_NAME" --no-pager -l || true

echo ""
echo "Note: The tunnel URL will appear in the service logs."
echo "Use 'journalctl --user -u $SERVICE_NAME -f' to see the tunnel URL when it's ready."
