#!/bin/bash
# Install 1Password GUI application
# 
# NOTE: 1Password is installed via rpm-ostree at runtime (not container build) because:
# - PostInstall script requires live user session context
# - Needs to discover human users (UID 1000+) for PolicyKit setup
# - Creates user-specific desktop integration and browser permissions
# - Container builds lack the user context needed for proper GUI app setup
# 
# The 1Password repository and GPG keys are configured in the container build,
# but the actual package installation happens here at runtime for proper integration.

set -euo pipefail

echo "Installing 1Password via rpm-ostree..."

# Ensure repo is present (repo file shipped under config/yum.repos.d/)
if ! rpm -q 1password &>/dev/null; then
    echo "Queuing 1Password packages via rpm-ostree..."
    sudo rpm-ostree install 1password || true
else
    echo "1Password packages already installed"
fi

# Configure 1Password SSH Agent environment
echo "Setting up 1Password SSH Agent integration..."
BASHRC="$HOME/.bashrc"
SSH_AGENT_LINE="export SSH_AUTH_SOCK=\"$HOME/.1password/agent.sock\""
if ! grep -Fqx "$SSH_AGENT_LINE" "$BASHRC"; then
    echo "$SSH_AGENT_LINE" >> "$BASHRC"
    echo "✓ Added SSH agent export to .bashrc"
else
    echo "SSH agent export already present in .bashrc, skipping..."
fi

echo "✓ 1Password installation/configuration complete. A reboot may be required to finalize rpm-ostree changes."


