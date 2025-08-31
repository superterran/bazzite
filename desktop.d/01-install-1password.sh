#!/bin/bash
# Install 1Password
# This script installs 1Password from the official RPM package

set -euo pipefail

echo "Installing 1Password..."

# 1Password SSH Agent
BASHRC="$HOME/.bashrc"
SSH_AGENT_LINE='export SSH_AUTH_SOCK=/home/me/.1password/agent.sock'

if ! grep -Fxq "$SSH_AGENT_LINE" "$BASHRC"; then
    echo "$SSH_AGENT_LINE" >> "$BASHRC"
    echo "Added SSH agent export to .bashrc"
else
    echo "SSH agent export already present in .bashrc"
fi

# Check if 1Password is already installed
if rpm -q 1password &>/dev/null; then
    echo "1Password is already installed, skipping..."
    exit 0
fi

# Install 1Password

echo "Adding 1password-cli from brew..."
brew install --cask 1password-cli

echo "Adding 1Password RPM package..."
rpm-ostree install https://downloads.1password.com/linux/rpm/stable/x86_64/1password-latest.rpm

echo "1Password installation queued. A reboot will be required to complete the installation."


