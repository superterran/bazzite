#!/bin/sh
set -eu
mkdir -p "/opt/muos/share/task/Syncthing Tasks"
cp "/mnt/mmc/MUOS/sync-status/Sync Status.sh" "/opt/muos/share/task/Syncthing Tasks/Sync Status.sh"
chmod 755 "/opt/muos/share/task/Syncthing Tasks/Sync Status.sh"
