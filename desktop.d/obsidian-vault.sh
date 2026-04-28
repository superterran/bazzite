#!/bin/bash
# Set up Obsidian vault sync + git backup services
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_SRC="$REPO_ROOT/config/systemd/user"
SERVICE_DST="$HOME/.config/systemd/user"
VAULT_DIR="$HOME/Documents/Cloud Vault"

echo "Setting up Obsidian vault services..."

# --- Dependencies ---

# Install ob (obsidian-headless) for Obsidian Sync
if ! command -v ob >/dev/null 2>&1; then
    echo "Installing obsidian-headless (ob)..."
    npm install -g obsidian-headless
else
    echo "  ✓ ob already installed: $(ob --version 2>/dev/null || echo 'ok')"
fi

# Ensure inotify-tools is available (system package on Fedora/Bazzite)
if ! command -v inotifywait >/dev/null 2>&1; then
    echo "WARNING: inotifywait not found. Install inotify-tools (rpm-ostree install inotify-tools)."
fi

# --- Vault setup ---

mkdir -p "$HOME/Documents"

if [[ ! -d "$VAULT_DIR/.git" ]]; then
    echo "WARNING: $VAULT_DIR is not a git repository."
    echo "  Clone your vault backup repo first, e.g.:"
    echo "  git clone git@github.com:superterran/obsidian-vault-backup.git \"$VAULT_DIR\""
else
    echo "  ✓ Vault git repo exists"
fi

# --- Deploy service files ---

mkdir -p "$SERVICE_DST"

deploy_unit() {
    local unit="$1"
    if [[ -f "$SERVICE_SRC/$unit" ]]; then
        cp "$SERVICE_SRC/$unit" "$SERVICE_DST/$unit"
        echo "  ✓ Deployed $unit"
    else
        echo "  WARNING: $SERVICE_SRC/$unit not found, skipping"
    fi
}

deploy_unit obsidian-sync.service
deploy_unit obsidian-vault-watcher.service
deploy_unit obsidian-vault-pull.service
deploy_unit obsidian-vault-pull.timer

systemctl --user daemon-reload

# --- Enable and start services ---

enable_service() {
    local unit="$1"
    systemctl --user enable --now "$unit" 2>/dev/null && \
        echo "  ✓ Enabled and started $unit" || \
        echo "  WARNING: Failed to enable $unit"
}

enable_service obsidian-sync.service
enable_service obsidian-vault-watcher.service
enable_service obsidian-vault-pull.timer

# Enable linger so services survive logout
sudo loginctl enable-linger "$(whoami)" 2>/dev/null || true

echo ""
echo "Obsidian vault services setup complete."
echo ""
echo "Management:"
echo "  systemctl --user status obsidian-sync.service"
echo "  systemctl --user status obsidian-vault-watcher.service"
echo "  systemctl --user list-timers obsidian-vault-pull.timer"
