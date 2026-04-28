#!/bin/bash
set -euo pipefail

echo "Setting up LiteLLM AI Routing Proxy..."

# Check if LiteLLM is already running
if systemctl --user is-active litellm-proxy.service >/dev/null 2>&1; then
    echo "LiteLLM proxy already running, skipping..."
    exit 0
fi

LITELLM_DIR="$HOME/.local/share/litellm-proxy"
VENV_DIR="$LITELLM_DIR/venv"
CONFIG_DIR="$HOME/.config/litellm"

# Create venv and install LiteLLM if needed
if [[ ! -f "$VENV_DIR/bin/litellm" ]]; then
    echo "Installing LiteLLM in virtualenv..."
    mkdir -p "$LITELLM_DIR"

    if command -v uv >/dev/null 2>&1; then
        uv venv "$VENV_DIR"
        uv pip install --python "$VENV_DIR/bin/python" 'litellm[proxy]'
    else
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install 'litellm[proxy]'
    fi

    echo "LiteLLM installed"
else
    echo "LiteLLM already installed"
fi

# Deploy config if it doesn't exist
mkdir -p "$CONFIG_DIR"

if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
    echo "Deploying LiteLLM configuration..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    if [[ -f "$SCRIPT_DIR/config/litellm/config.yaml" ]]; then
        cp "$SCRIPT_DIR/config/litellm/config.yaml" "$CONFIG_DIR/config.yaml"
        echo "LiteLLM config deployed from repo template"
    else
        echo "WARNING: No config template found at config/litellm/config.yaml"
        echo "Create one manually at $CONFIG_DIR/config.yaml"
        exit 0
    fi
fi

# Check for environment file with API keys
if [[ ! -f "$CONFIG_DIR/proxy.env" ]]; then
    echo "Creating proxy.env template..."
    cat > "$CONFIG_DIR/proxy.env" << 'EOF'
# LiteLLM Proxy Environment Variables
# Fill in your API keys below
POE_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LITELLM_MASTER_KEY=
EOF
    chmod 600 "$CONFIG_DIR/proxy.env"
    echo "WARNING: Edit $CONFIG_DIR/proxy.env with your API keys before starting"
fi

# Create systemd user service
USER_SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SERVICE_DIR"

SERVICE_PATH="$USER_SERVICE_DIR/litellm-proxy.service"
if [[ ! -f "$SERVICE_PATH" ]]; then
    echo "Creating LiteLLM proxy systemd service..."
    cat > "$SERVICE_PATH" << 'EOF'
[Unit]
Description=LiteLLM AI Routing Proxy
Documentation=https://docs.litellm.ai
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/me
EnvironmentFile=/home/me/.config/litellm/proxy.env
Environment=PATH=/home/me/.local/share/litellm-proxy/venv/bin:/home/linuxbrew/.linuxbrew/bin:/home/me/.nvm/versions/node/v24.14.0/bin:/usr/local/bin:/usr/bin
Environment=HOME=/home/me
Environment=LITELLM_LOG=WARNING
ExecStart=/home/me/.local/share/litellm-proxy/venv/bin/litellm \
    --config /home/me/.config/litellm/config.yaml \
    --port 4000 \
    --host 127.0.0.1
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=litellm-proxy

[Install]
WantedBy=default.target
EOF
fi

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now litellm-proxy.service

echo "LiteLLM proxy setup completed successfully"
echo ""
echo "Proxy: http://localhost:4000"
echo ""
echo "Cost tiers: nano ($0.36/M) → fast ($0.50/M) → mid ($1.40/M) → smart ($7/M) → max ($13/M) → apex ($21/M)"
echo "Auto-router: use model 'auto' for complexity-based routing"
echo ""
echo "Management commands:"
echo "  systemctl --user status litellm-proxy.service"
echo "  systemctl --user restart litellm-proxy.service"
echo "  journalctl --user -u litellm-proxy.service -f"
