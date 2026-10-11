#!/usr/bin/env python3
"""Launch ZooCube with sharper rendering and the shared GameCube saves."""
import os,xml.etree.ElementTree as ET
from pathlib import Path
home=Path.home()
settings=home/'ES-DE/settings/es_settings.xml'
root=ET.fromstring('<settings>'+settings.read_text().split('?>',1)[1]+'</settings>')
library=Path(next(n.get('value') for n in root if n.get('name')=='ROMDirectory'))
game=library/'systems/gc/ZooCube (USA).rvz'
if not game.exists():raise SystemExit('ZooCube has not finished syncing: '+str(game))
scale='3' if (home/'rom-library').exists() else '6'
wrapper=str(home/'Applications/launch-disc-game.py')
os.execv(wrapper,[wrapper,'dolphin',str(game),
 '-C','GFX.Settings.InternalResolution='+scale,
 '-C','GFX.Settings.AspectRatio=2',
 '-C','GFX.Enhancements.WideScreenHack=False'])
