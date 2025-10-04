#!/bin/bash
# Install utility Flatpak apps (idempotent)
# 
# NOTE: Slack and Obsidian are installed by separate scripts (slack.sh and obsidian.sh)
# This script installs additional utility applications only.

set -euo pipefail

echo "Installing utility Flatpaks..."

flatpak install -y flathub \
  com.github.tchx84.Flatseal \
  com.mattjakeman.ExtensionManager \
  io.missioncenter.MissionCenter \
  com.github.Matoking.protontricks \
  com.vysp3r.ProtonPlus \
  io.github.flattool.Warehouse \
  || echo "Some Flatpaks may have failed to install, continuing..."

echo "Utility Flatpaks step complete"
