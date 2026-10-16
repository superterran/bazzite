#!/bin/bash
# Push favorites-sync to the Ally (ES-DE) and enable its 2-minute timer.
set -euo pipefail
H=(-o HostName=10.0.0.79 -o ConnectTimeout=6)
scp -q "${H[@]}" "$(dirname "$0")/favorites-sync.py" ally:.local/bin/favorites-sync.py
ssh "${H[@]}" ally 'chmod 755 ~/.local/bin/favorites-sync.py; mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/favorites-sync.service <<U
[Unit]
Description=Sync game favorites between ES-DE, the desktop and the Anbernic
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 %h/.local/bin/favorites-sync.py --frontend esde --shared /home/bazzite/rom-saves --device ally --library /var/home/bazzite/rom-library
U
sed -e "s/every 2 minutes/every 2 minutes/" > ~/.config/systemd/user/favorites-sync.timer <<U
[Unit]
Description=Sync game favorites every 2 minutes
[Timer]
OnBootSec=1min
OnUnitActiveSec=2min
[Install]
WantedBy=timers.target
U
systemctl --user daemon-reload && systemctl --user enable --now favorites-sync.timer && systemctl --user start favorites-sync.service && journalctl --user -u favorites-sync.service -n 2 --no-pager | tail -1'
