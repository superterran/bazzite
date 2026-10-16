#!/usr/bin/env python3
"""Add save reconciliation to muOS's existing launch script without changing its emulator options."""
from pathlib import Path
import shutil,time
path=Path('/opt/muos/script/launch/lr-general.sh');text=path.read_text();marker='# Gaming fleet shared-save hook'
gate_marker='# Gaming fleet save gate'
gate='/usr/bin/python3 /mnt/mmc/MUOS/sync-status/save-sync-gate.py {} --config /run/muos/storage/syncthing/config.xml --ui muos >/tmp/gaming-save-gate.log 2>&1'
def add_gate(t):
 if gate_marker in t or marker not in t:return t
 lines=t.split('\n');i=lines.index(marker)
 lines.insert(i+1,gate.format('pre')+'  '+gate_marker)
 j=next(k for k in range(i+2,len(lines)) if lines[k].startswith('nice --20 retroarch'))
 lines.insert(j+2,gate.format('post')+'  '+gate_marker)
 return '\n'.join(lines)
if marker in text:
 new=add_gate(text)
 if new!=text:path.write_text(new);print('Save gate added to existing hook')
 else:print('Save launch hook already installed')
 raise SystemExit(0)
needle='nice --20 retroarch -v -f $RA_ARGS -L "$MUOS_SHARE_DIR/core/$CORE" "$FILE"'
if needle not in text:raise SystemExit('Unrecognized muOS launch script; original preserved.')
backup=Path('/mnt/mmc/MUOS/info/frontend-backups')/(time.strftime('%Y%m%d-%H%M%S')+'-lr-general.sh');shutil.copy2(path,backup)
sync='/usr/bin/python3 /mnt/mmc/MUOS/sync-status/rom-save-alias-sync.py --root /mnt/mmc/MUOS/shared-saves --state /mnt/mmc/MUOS/sync-status/save-alias-state.json >/tmp/gaming-save-sync.log 2>&1'
path.write_text(add_gate(text.replace(needle,marker+'\n'+sync+'\n'+needle+'\n'+sync)));print('Save launch hook installed; original backed up:',backup)
