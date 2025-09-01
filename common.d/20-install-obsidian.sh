#!/bin/bash
# Install common Flatpak apps (idempotent)
set -euo pipefail

echo "Installing Obsidian Flatpaks..."

flatpak install -y flathub \
  md.obsidian.Obsidian  \
    || echo "Obsidian Flatpak may have failed to install, continuing..."

echo "Obsidian Flatpak step complete"
