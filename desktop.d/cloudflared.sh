#!/bin/bash
set -euo pipefail

echo "Setting up Cloudflare Tunnel..."

# Check if cloudflared is already running
if systemctl --user is-active cloudflared.service >/dev/null 2>&1; then
    echo "Cloudflare Tunnel already running, skipping..."
    exit 0
fi

# Install cloudflared via Homebrew
if command -v brew >/dev/null 2>&1; then
    if ! command -v cloudflared >/dev/null 2>&1; then
        echo "Installing cloudflared via Homebrew..."
        brew install cloudflared
    else
        echo "cloudflared already installed: $(cloudflared --version)"
    fi
else
    echo "ERROR: Homebrew not found. cloudflared requires Linuxbrew."
    exit 1
fi

# Check for tunnel credentials
if [[ ! -d "$HOME/.cloudflared" ]] || ! ls "$HOME/.cloudflared/"*.json >/dev/null 2>&1; then
    echo "WARNING: No tunnel credentials found in ~/.cloudflared/"
    echo "You need to authenticate and create a tunnel first:"
    echo "  cloudflared login"
    echo "  cloudflared tunnel create desktop"
    echo ""
    echo "Then create ~/.cloudflared/config.yml with your tunnel configuration."
    echo "See config/cloudflared/config.yml.example in this repo for a template."
    exit 0
fi

# Deploy config template if no config exists
if [[ ! -f "$HOME/.cloudflared/config.yml" ]]; then
    echo "WARNING: No config.yml found in ~/.cloudflared/"
    echo "Copy and edit the template from this repo:"
    echo "  cp config/cloudflared/config.yml.example ~/.cloudflared/config.yml"
    exit 0
fi

# Create systemd user service
USER_SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SERVICE_DIR"

SERVICE_PATH="$USER_SERVICE_DIR/cloudflared.service"
if [[ ! -f "$SERVICE_PATH" ]]; then
    echo "Creating cloudflared systemd service..."
    cat > "$SERVICE_PATH" << 'EOF'
[Unit]
Description=Cloudflare Tunnel (desktop)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/linuxbrew/.linuxbrew/bin/cloudflared tunnel --no-autoupdate run desktop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
fi

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now cloudflared.service

# Enable lingering
sudo loginctl enable-linger "$(whoami)"

echo "Cloudflare Tunnel setup completed successfully"
echo ""
echo "Management commands:"
echo "  systemctl --user status cloudflared.service"
echo "  systemctl --user restart cloudflared.service"
echo "  journalctl --user -u cloudflared.service -f"
