#!/bin/bash
# Ally cleanup 2026-10-16 - run once:  sudo bash ~/ally-cleanup-20261016.sh
set -u
[ "$(id -u)" = 0 ] || { echo "Run with sudo"; exit 1; }
echo "== Removing system apps"
flatpak uninstall --system -y --noninteractive \
  me.kozec.syncthingtk com.jeffser.Alpaca org.mavlink.qgroundcontrol org.virt_manager.virt-manager \
  io.github.fastrizwaan.WineZGUI io.github.nokse22.Exhibit io.github.pejuko.follamac com.google.Chrome \
  de.leopoldluley.Clapgrep com.ranfdev.DistroShelf io.github.dvlv.boxbuddyrs io.github.flattool.Ignition 2>&1 | grep -vE "^\s*$" | tail -15
echo "== Removing runtimes nothing uses any more"
flatpak uninstall --system --unused -y --noninteractive 2>&1 | tail -3
echo "== Removing leftover Decky plugins (backed up first)"
B=/home/bazzite/.config/cleanup-backup-20261016/decky-plugins; mkdir -p "$B"
for p in decky-syncthing EmuDecky; do
  [ -d "/home/bazzite/homebrew/plugins/$p" ] && cp -a "/home/bazzite/homebrew/plugins/$p" "$B/" && rm -rf "/home/bazzite/homebrew/plugins/$p" && echo "removed $p"
done
chown -R bazzite:bazzite /home/bazzite/.config/cleanup-backup-20261016
systemctl restart plugin_loader 2>/dev/null && echo "Decky restarted"
echo "== Done. Remaining apps:"; flatpak list --app --columns=application | wc -l
