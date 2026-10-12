#!/bin/bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
settings_path="$HOME/ES-DE/settings/es_settings.xml"
if [[ ! -f "$settings_path" ]]; then
    echo 'Steam artwork sync requires the shared ES-DE library configuration.'
    exit 0
fi
mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
install -m 755 "$repo_root/bin/steam-artwork-sync.py" "$HOME/.local/bin/steam-artwork-sync.py"
install -m 644 "$repo_root/bin/steam_client.py" "$HOME/.local/bin/steam_client.py"
python3 - "$settings_path" <<'PY'
from pathlib import Path
import json,re,sys,xml.etree.ElementTree as ET
root=ET.fromstring('<settings>'+re.sub(r'<\?xml[^>]*\?>','',Path(sys.argv[1]).read_text())+'</settings>')
media=next(n.get('value') for n in root.iter() if n.get('name')=='MediaDirectory')
shared=Path(media).parent.parent
(Path.home()/'.config/steam-artwork-sync.json').write_text(json.dumps({'shared':str(shared)})+'\n')
PY
install -m 644 "$repo_root/config/systemd/user/steam-artwork-sync.service" "$HOME/.config/systemd/user/"
install -m 644 "$repo_root/config/systemd/user/steam-artwork-sync.timer" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now steam-artwork-sync.timer
