#!/bin/sh
set -eu
mkdir -p "/opt/muos/share/task/Syncthing Tasks"
cp "/mnt/mmc/MUOS/sync-status/Sync Status.sh" "/opt/muos/share/task/Syncthing Tasks/Sync Status.sh"
chmod 755 "/opt/muos/share/task/Syncthing Tasks/Sync Status.sh"

if [ -f "/mnt/mmc/MUOS/sync-status/sync-artwork.py" ]; then
    /usr/bin/python3 /mnt/mmc/MUOS/sync-status/sync-artwork.py --watch >/tmp/gaming-artwork-sync.log 2>&1 &
fi
