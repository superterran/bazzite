#!/usr/bin/env bash
# Setup Codex remote-control service
# Keeps the Codex app-server daemon running with remote control enabled so the
# ChatGPT/Codex apps can drive this box. Codex itself is installed by its own
# installer (~/.local/bin/codex -> ~/.codex/packages/standalone/current/bin/codex)
# and self-updates; this only wires up supervision.

set -euo pipefail

echo "Setting up Codex remote-control service..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_SERVICE_DIR="$HOME/.config/systemd/user"
UNIT="codex-remote-control.service"

if ! command -v codex >/dev/null 2>&1 && [[ ! -x "$HOME/.local/bin/codex" ]]; then
    echo "ERROR: codex is not installed. Install it first, then run 'codex login'."
    exit 1
fi

if ! "$HOME/.local/bin/codex" login status 2>/dev/null | grep -q 'Logged in'; then
    echo "WARNING: codex is not logged in; the daemon will start but remote control cannot connect."
    echo "         Run 'codex login' (device-code flow works over SSH) and restart the service."
fi

mkdir -p "$USER_SERVICE_DIR"
if ! cmp -s "$REPO_ROOT/config/systemd/user/$UNIT" "$USER_SERVICE_DIR/$UNIT"; then
    cp "$REPO_ROOT/config/systemd/user/$UNIT" "$USER_SERVICE_DIR/$UNIT"
    echo "  deployed: $UNIT"
fi

systemctl --user daemon-reload
systemctl --user enable "$UNIT" >/dev/null
systemctl --user restart "$UNIT"
echo "Codex remote-control service: $(systemctl --user is-active "$UNIT")"
