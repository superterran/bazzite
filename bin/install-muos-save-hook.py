#!/usr/bin/env python3
"""Add save reconciliation to muOS's existing launch script without changing its emulator options."""
from pathlib import Path
import shutil,time
marker='# Gaming fleet shared-save hook'
gate_marker='# Gaming fleet save gate'
gate='/usr/bin/python3 /mnt/mmc/MUOS/sync-status/save-sync-gate.py {} --config /run/muos/storage/syncthing/config.xml --ui muos >/tmp/gaming-save-gate.log 2>&1'
def add_gate(t):
 if gate_marker in t or marker not in t:return t
 lines=t.split('\n');i=lines.index(marker)
 lines.insert(i+1,gate.format('pre')+'  '+gate_marker)
 j=next(k for k in range(i+2,len(lines)) if lines[k].startswith('nice --20 retroarch'))
 lines.insert(j+2,gate.format('post')+'  '+gate_marker)
 return '\n'.join(lines)
needle='nice --20 retroarch -v -f $RA_ARGS -L "$MUOS_SHARE_DIR/core/$CORE" "$FILE"'
configured='nice --20 retroarch -v -f --config "$MUOS_SHARE_DIR/info/config/retroarch.cfg" $RA_ARGS -L "$MUOS_SHARE_DIR/core/$CORE" "$FILE"'
sync='/usr/bin/python3 /mnt/mmc/MUOS/sync-status/rom-save-alias-sync.py --root /mnt/mmc/MUOS/shared-saves --state /mnt/mmc/MUOS/sync-status/save-alias-state.json >/tmp/gaming-save-sync.log 2>&1'

def update(text):
 if needle not in text and configured not in text:
  raise ValueError('Unrecognized muOS launch script; original preserved.')
 # muOS can leave a stock regular config where its symlink was expected.
 # Select the shared-save config explicitly rather than depending on that link.
 text=text.replace(needle,configured)
 if marker not in text:text=text.replace(configured,marker+'\n'+sync+'\n'+configured+'\n'+sync)
 return add_gate(text)

def main():
 path=Path('/opt/muos/script/launch/lr-general.sh');text=path.read_text()
 try:new=update(text)
 except ValueError as error:raise SystemExit(str(error))
 if new==text:
  print('Save launch hook and explicit shared-save config already installed');return
 backups=Path('/mnt/mmc/MUOS/info/frontend-backups');backups.mkdir(parents=True,exist_ok=True)
 backup=backups/(time.strftime('%Y%m%d-%H%M%S')+'-lr-general.sh');shutil.copy2(path,backup)
 path.write_text(new);print('Save launch hook updated; original backed up:',backup)

if __name__=='__main__':main()
