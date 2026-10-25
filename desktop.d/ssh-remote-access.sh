#!/bin/bash
# Setup key-based SSH for LAN and Tailscale access
# This script retains SSH hardening (pubkey-only, non-standard port).
# Public SSH/DDNS retired; desktop.superterran.net points to the tailnet IP.

set -euo pipefail

echo "Setting up private SSH remote access..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_PORT=2222

# ============================================================
# 1. Harden SSH for internet exposure
# ============================================================
echo "Configuring SSH hardening..."

HARDENED_CONF="/etc/ssh/sshd_config.d/00-hardened.conf"
if [[ -f "$HARDENED_CONF" ]] && grep -q "AuthenticationMethods publickey" "$HARDENED_CONF"; then
    echo "SSH hardening already configured."
else
    echo "Creating hardened SSH drop-in config..."
    sudo tee "$HARDENED_CONF" > /dev/null << 'SSHEOF'
# Hardened SSH for internet exposure
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
MaxAuthTries 3
MaxSessions 5
PubkeyAuthentication yes
AuthenticationMethods publickey
X11Forwarding no
PermitEmptyPasswords no
SSHEOF
    echo "SSH hardening config created."
fi

# ============================================================
# 2. Set SSH to listen on non-standard port
# ============================================================
echo "Configuring SSH port..."

PORT_CONF="/etc/ssh/sshd_config.d/01-port.conf"
if [[ -f "$PORT_CONF" ]] && grep -q "Port $SSH_PORT" "$PORT_CONF"; then
    echo "SSH port already set to $SSH_PORT."
else
    echo "Setting SSH listen port to $SSH_PORT..."
    sudo tee "$PORT_CONF" > /dev/null << PORTEOF
Port $SSH_PORT
PORTEOF
    echo "SSH port config created."
fi

# Allow the port in SELinux
if command -v semanage >/dev/null 2>&1; then
    if ! semanage port -l | grep ssh_port_t | grep -q "$SSH_PORT"; then
        echo "Adding port $SSH_PORT to SELinux SSH policy..."
        sudo semanage port -a -t ssh_port_t -p tcp "$SSH_PORT" 2>/dev/null \
            || sudo semanage port -m -t ssh_port_t -p tcp "$SSH_PORT"
    else
        echo "SELinux already allows SSH on port $SSH_PORT."
    fi
fi

# Validate and apply SSH config
echo "Validating SSH configuration..."
if sudo sshd -t; then
    echo "SSH config valid, restarting sshd..."
    sudo systemctl restart sshd
    echo "sshd restarted on port $SSH_PORT."
else
    echo "ERROR: SSH config validation failed, not restarting." >&2
    exit 1
fi

# Private SSH access supersedes the retired public DDNS setup.
bash "$SCRIPT_DIR/desktop.d/ssh-private-access.sh"
