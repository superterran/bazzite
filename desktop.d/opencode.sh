#!/bin/bash
set -euo pipefail

echo "Setting up OpenCode Web UI..."

# Check if OpenCode is already running
if systemctl --user is-active opencode-web.service >/dev/null 2>&1; then
    echo "OpenCode Web UI already running, skipping..."
    exit 0
fi

# Install OpenCode via Homebrew
if command -v brew >/dev/null 2>&1; then
    if ! command -v opencode >/dev/null 2>&1; then
        echo "Installing OpenCode via Homebrew..."
        brew install opencode
    else
        echo "OpenCode already installed"
    fi
else
    echo "ERROR: Homebrew not found. OpenCode requires Linuxbrew."
    exit 1
fi

# Deploy OpenCode config if it doesn't exist
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
mkdir -p "$OPENCODE_CONFIG_DIR"

if [[ ! -f "$OPENCODE_CONFIG_DIR/opencode.json" ]]; then
    echo "Deploying OpenCode configuration..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    if [[ -f "$SCRIPT_DIR/config/opencode/opencode.json" ]]; then
        cp "$SCRIPT_DIR/config/opencode/opencode.json" "$OPENCODE_CONFIG_DIR/opencode.json"
        echo "OpenCode config deployed from repo template"
    else
        echo "WARNING: No config template found, creating minimal config..."
        cat > "$OPENCODE_CONFIG_DIR/opencode.json" << 'CONFIGEOF'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "qwen3:8b":          { "name": "Qwen 3 8B (local)" },
        "qwen2.5-coder:7b":  { "name": "Qwen 2.5 Coder 7B (local)" },
        "mistral-nemo":      { "name": "Mistral Nemo 12B (local)" }
      }
    }
  }
}
CONFIGEOF
    fi
fi

# Create systemd user service
USER_SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SERVICE_DIR"

SERVICE_PATH="$USER_SERVICE_DIR/opencode-web.service"
if [[ ! -f "$SERVICE_PATH" ]]; then
    echo "Creating OpenCode Web systemd service..."
    cat > "$SERVICE_PATH" << 'EOF'
[Unit]
Description=OpenCode Web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/var/home/me
Environment=PATH=/home/linuxbrew/.linuxbrew/bin:/home/me/.nvm/versions/node/v24.14.0/bin:/usr/local/bin:/usr/bin
ExecStart=/home/linuxbrew/.linuxbrew/bin/opencode web --port 3333 --hostname 0.0.0.0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
fi

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now opencode-web.service

# Enable lingering
sudo loginctl enable-linger "$(whoami)"

echo "OpenCode Web UI setup completed successfully"
echo ""
echo "Web UI: http://localhost:3333"
echo ""
echo "Management commands:"
echo "  systemctl --user status opencode-web.service"
echo "  systemctl --user restart opencode-web.service"
echo "  journalctl --user -u opencode-web.service -f"
