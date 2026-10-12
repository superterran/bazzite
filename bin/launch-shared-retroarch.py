#!/usr/bin/env python3
"""Refresh shared battery saves before a game and publish them after closing."""
from pathlib import Path
import subprocess,sys
helper=Path.home()/'.local/bin/rom-save-alias-sync.py'
def sync():
 if helper.exists():subprocess.run([sys.executable,str(helper)],stdout=subprocess.DEVNULL,check=False)
sync()
try:result=subprocess.run(['/usr/bin/flatpak','run','org.libretro.RetroArch',*sys.argv[1:]])
finally:sync()
raise SystemExit(result.returncode)
