#!/bin/bash
# Install Slack Flatpak apps (idempotent)
set -euo pipefail

echo "Installing Slack Flatpaks..."

flatpak install -y flathub \
  com.slack.Slack  \
    || echo "Slack Flatpak may have failed to install, continuing..."

echo "Slack Flatpak step complete"
