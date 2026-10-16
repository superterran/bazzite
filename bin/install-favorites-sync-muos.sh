#!/bin/bash
# Push favorites-sync to the muOS Anbernic; runs every 2 minutes from the boot hook.
set -euo pipefail
export SSHPASS=root; S=(sshpass -e); O=(-o PubkeyAuthentication=no -o ConnectTimeout=6)
"${S[@]}" scp -q "${O[@]}" "$(dirname "$0")/favorites-sync.py" root@10.0.0.40:/mnt/mmc/MUOS/sync-status/favorites-sync.py
"${S[@]}" ssh "${O[@]}" root@10.0.0.40 'H=/mnt/mmc/MUOS/init/gaming-sync-status.sh
CMD="/usr/bin/python3 /mnt/mmc/MUOS/sync-status/favorites-sync.py --frontend muos --shared /mnt/mmc/MUOS/shared-saves --device anbernic --watch 120"
grep -q favorites-sync.py $H || printf "\nif [ -f /mnt/mmc/MUOS/sync-status/favorites-sync.py ]; then\n    %s >/tmp/gaming-favorites.log 2>&1 &\nfi\n" "$CMD" >> $H
pgrep -f "favorites-sync.py --frontend" >/dev/null || setsid sh -c "$CMD >/tmp/gaming-favorites.log 2>&1 </dev/null &"
sleep 3; cat /tmp/gaming-favorites.log; ls /mnt/mmc/MUOS/shared-saves/favorites/'
