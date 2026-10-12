#!/bin/sh
set -eu
mkdir -p "/opt/muos/share/task/Syncthing Tasks"
cp "/mnt/mmc/MUOS/sync-status/Sync Status.sh" "/opt/muos/share/task/Syncthing Tasks/Sync Status.sh"
chmod 755 "/opt/muos/share/task/Syncthing Tasks/Sync Status.sh"

if [ -f "/mnt/mmc/MUOS/sync-status/sync-artwork.py" ]; then
    /usr/bin/python3 /mnt/mmc/MUOS/sync-status/sync-artwork.py --watch >/tmp/gaming-artwork-sync.log 2>&1 &
fi

if [ -f "/mnt/mmc/MUOS/sync-status/install-save-hook.py" ]; then
    /usr/bin/python3 /mnt/mmc/MUOS/sync-status/install-save-hook.py >/tmp/gaming-save-hook.log 2>&1
fi
if [ -f "/mnt/mmc/MUOS/sync-status/rom-save-alias-sync.py" ]; then
    /usr/bin/python3 /mnt/mmc/MUOS/sync-status/rom-save-alias-sync.py --root /mnt/mmc/MUOS/shared-saves --state /mnt/mmc/MUOS/sync-status/save-alias-state.json --watch >/tmp/gaming-save-watch.log 2>&1 &
fi
