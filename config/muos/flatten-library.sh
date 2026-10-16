#!/bin/sh
# Boot-time: expose each shared-library system directly at the ROMS root.
# The Syncthing share lives hidden at /mnt/sdcard/.library; every system folder
# is bind-mounted to /mnt/sdcard/ROMS/<system>, so muOS shows one flat list and
# RetroArch still sees the same content-folder names (arcade, gb, snes, ...),
# which keeps per-folder save routing and core overrides unchanged.
set -u
LIB=/mnt/sdcard/.library/systems
ROMS=/mnt/sdcard/ROMS
[ -d "$LIB" ] || exit 0
for src in "$LIB"/*/; do
    sys=$(basename "$src")
    dest="$ROMS/$sys"
    mkdir -p "$dest"
    mountpoint -q "$dest" || mount --bind "$src" "$dest"
done
