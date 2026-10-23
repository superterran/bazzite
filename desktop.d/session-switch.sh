#!/usr/bin/env bash
# Repair desktop Game Mode launcher on DX images lacking steamosctl.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if command -v steamosctl >/dev/null; then
    echo 'Native steamosctl available; fallback not needed.'
    exit 0
fi
install -Dm755 "$REPO_ROOT/bin/desktop-mode" "$HOME/.local/bin/desktop-mode"
install -Dm755 "$REPO_ROOT/bin/switch-bazzite-session.sh" "$HOME/.local/bin/switch-bazzite-session.sh"
python3 - "$REPO_ROOT" <<'PYSETUP'
from pathlib import Path
import shutil
home=Path.home()
source=Path('/usr/share/gnome-shell/extensions/logomenu@aryan_k')
target=home/'.local/share/gnome-shell/extensions/logomenu@aryan_k'
if source.exists():
    shutil.copytree(source,target,dirs_exist_ok=True)
    entry=target/'extension.js'
    text=entry.read_text().replace("Util.spawn(['steamosctl', 'switch-to-game-mode']);", "Util.spawn(['"+str(home/'.local/bin/switch-bazzite-session.sh')+"', 'game']);")
    entry.write_text(text)
entry=home/'.local/share/applications/return-to-gamemode.desktop'
entry.parent.mkdir(parents=True,exist_ok=True)
entry.write_text('[Desktop Entry]\nType=Application\nName=Return to Game Mode\nExec='+str(home/'.local/bin/switch-bazzite-session.sh')+' game\nIcon=steam\nTerminal=false\n')
PYSETUP
