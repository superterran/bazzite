#!/usr/bin/env python3
"""Add save reconciliation to muOS's existing launch script without changing its emulator options."""
from pathlib import Path
import shutil,time
path=Path('/opt/muos/script/launch/lr-general.sh');text=path.read_text();marker='# Gaming fleet shared-save hook'
if marker in text:print('Save launch hook already installed');raise SystemExit(0)
needle='nice --20 retroarch -v -f $RA_ARGS -L "$MUOS_SHARE_DIR/core/$CORE" "$FILE"'
if needle not in text:raise SystemExit('Unrecognized muOS launch script; original preserved.')
backup=Path('/mnt/mmc/MUOS/info/frontend-backups')/(time.strftime('%Y%m%d-%H%M%S')+'-lr-general.sh');shutil.copy2(path,backup)
sync='/usr/bin/python3 /mnt/mmc/MUOS/sync-status/rom-save-alias-sync.py --root /mnt/mmc/MUOS/shared-saves --state /mnt/mmc/MUOS/sync-status/save-alias-state.json >/tmp/gaming-save-sync.log 2>&1'
path.write_text(text.replace(needle,marker+'\n'+sync+'\n'+needle+'\n'+sync));print('Save launch hook installed; original backed up:',backup)
