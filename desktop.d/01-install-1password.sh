#!/bin/bash
# Install 1Password (desktop)
set -euo pipefail

echo "Installing 1Password..."

# Ensure repo is present (repo file shipped under config/yum.repos.d/)
if ! rpm -q 1password &>/dev/null || ! rpm -q 1password-cli &>/dev/null; then
    echo "Queuing 1Password packages via rpm-ostree..."
    rpm-ostree install 1password 1password-cli || true
else
    echo "1Password packages already installed"
fi

# Configure 1Password SSH Agent environment
BASHRC="$HOME/.bashrc"
SSH_AGENT_LINE="export SSH_AUTH_SOCK=\"$HOME/.1password/agent.sock\""
if ! grep -Fqx "$SSH_AGENT_LINE" "$BASHRC"; then
    echo "$SSH_AGENT_LINE" >> "$BASHRC"
    echo "Added SSH agent export to .bashrc"
else
    echo "SSH agent export already present in .bashrc"
fi

echo "1Password installation/configuration complete. A reboot may be required to finalize rpm-ostree changes."


