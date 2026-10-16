#!/usr/bin/env python3
"""Refresh shared battery saves before a game and publish them after closing.

Around the game, save-sync-gate.py waits for Syncthing: pending saves arrive
before launch, and the new save reaches closet before we return to the menu."""
from pathlib import Path
import subprocess,sys
helper=Path.home()/'.local/bin/rom-save-alias-sync.py'
def sync():
 if helper.exists():subprocess.run([sys.executable,str(helper)],stdout=subprocess.DEVNULL,check=False)
gate=Path.home()/'.local/bin/save-sync-gate.py'
stconf=next((p for p in [Path.home()/'.local/state/syncthing/config.xml',Path.home()/'.config/syncthing/config.xml'] if p.exists()),None)
def gatecheck(phase):
 if gate.exists() and stconf:subprocess.run([sys.executable,str(gate),phase,'--config',str(stconf),'--ui','zenity'],stdout=subprocess.DEVNULL,check=False)
family=Path.home()/'.var/app/org.libretro.RetroArch/config/retroarch/family-controls.cfg'
extra=['--appendconfig='+str(family)] if family.exists() else []
gatecheck('pre')
sync()
try:result=subprocess.run(['/usr/bin/flatpak','run','org.libretro.RetroArch',*extra,*sys.argv[1:]])
finally:
 sync();gatecheck('post')
raise SystemExit(result.returncode)
