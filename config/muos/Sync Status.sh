#!/bin/sh
# HELP: Show live ROM, artwork, save sync and connected peers. Read-only; returns after 20 seconds.
# ICON: syncthing
set -e
. /opt/muos/script/var/func.sh
FRONTEND stop
trap 'FRONTEND start task' EXIT
SYNC_TICK=0
while [ "$SYNC_TICK" -lt 4 ]; do
 python3 /mnt/mmc/MUOS/sync-status/syncthing-status.py --clear
 TBOX sleep 5
 SYNC_TICK=$((SYNC_TICK + 1))
done
