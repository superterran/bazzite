#!/bin/bash
# Install common Flatpak apps (idempotent)
set -euo pipefail

echo "Installing common Flatpaks..."

flatpak install -y flathub \
  com.slack.Slack \
  md.obsidian.Obsidian \
  com.github.tchx84.Flatseal \
  com.mattjakeman.ExtensionManager \
  io.missioncenter.MissionCenter \
  com.github.Matoking.protontricks \
  com.vysp3r.ProtonPlus \
  io.github.flattool.Warehouse \
  || echo "Some Flatpaks may have failed to install, continuing..."

echo "Flatpaks step complete"
