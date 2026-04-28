#!/bin/bash
set -euo pipefail

echo "Setting up Syncthing..."

# Check if Syncthing is already running
if systemctl --user is-active syncthing.service >/dev/null 2>&1; then
    echo "Syncthing already running, skipping..."
    exit 0
fi

# Install Syncthing via Homebrew
if command -v brew >/dev/null 2>&1; then
    if ! command -v syncthing >/dev/null 2>&1; then
        echo "Installing Syncthing via Homebrew..."
        brew install syncthing
    else
        echo "Syncthing already installed: $(syncthing --version | head -1)"
    fi
else
    echo "ERROR: Homebrew not found. Syncthing requires Linuxbrew."
    exit 1
fi

# Create systemd user service
USER_SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SERVICE_DIR"

SERVICE_PATH="$USER_SERVICE_DIR/syncthing.service"
if [[ ! -f "$SERVICE_PATH" ]]; then
    echo "Creating Syncthing systemd service..."
    cat > "$SERVICE_PATH" << 'EOF'
[Unit]
Description=Syncthing - Open Source Continuous File Synchronization
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/linuxbrew/.linuxbrew/bin/syncthing serve --no-browser --logflags=0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
fi

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now syncthing.service

# Enable lingering so it starts on boot
sudo loginctl enable-linger "$(whoami)"

echo "Syncthing setup completed successfully"
echo ""
echo "Web UI: http://localhost:8384"
echo "Configure shared folders and remote devices via the web UI."
echo ""
echo "Management commands:"
echo "  systemctl --user status syncthing.service"
echo "  systemctl --user restart syncthing.service"
echo "  journalctl --user -u syncthing.service -f"
