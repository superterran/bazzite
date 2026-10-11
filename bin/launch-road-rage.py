#!/usr/bin/env python3
"""Launch the user's Road Rage disc image with its region-specific 16:9 code."""
import os
import subprocess
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

home = Path.home()
settings = home / 'ES-DE/settings/es_settings.xml'
root = ET.fromstring('<settings>' + settings.read_text().split('?>', 1)[1] + '</settings>')
library = Path(next(n.get('value') for n in root if n.get('name') == 'ROMDirectory'))
game = None
game_id = None
for candidate in sorted((library / 'systems/gc').glob('*')):
    if candidate.suffix.lower() not in ['.iso', '.gcm', '.rvz', '.gcz']:
        continue
    if candidate.suffix.lower() in ['.iso', '.gcm']:
        with candidate.open('rb') as stream:
            candidate_id = stream.read(6).decode('ascii', errors='replace')
        if candidate_id in ['GSPE69', 'GSPP69']:
            game, game_id = candidate, candidate_id
            break
    elif 'road' in candidate.name.lower() and 'rage' in candidate.name.lower():
        game = candidate
        break
if game is None:
    message = ('Road Rage is ready to add.\n\nPut your GameCube disc image in:\n' +
               str(library / 'systems/gc') + '\n\nThen launch this entry again.')
    if shutil.which('zenity'):
        subprocess.run(['zenity', '--info', '--title=The Simpsons: Road Rage', '--text=' + message])
    elif shutil.which('notify-send'):
        subprocess.run(['notify-send', 'The Simpsons: Road Rage', message])
    else:
        print(message)
    raise SystemExit(0)
codes = {
    'GSPE69': '0428DF34 3FBB8000\n0428DF38 40638E39\n0428DF40 3FC04000\n0428DF44 3FE38E39',
    'GSPP69': '042AA9D4 3FBB8000\n042AA9D8 40638E39\n042AA9E0 3FC04000\n042AA9E4 3FE38E39',
}
for section in ['config', 'data']:
    config = home / '.var/app/org.DolphinEmu.dolphin-emu' / section / 'dolphin-emu/GameSettings'
    config.mkdir(parents=True, exist_ok=True)
    for region, code in codes.items():
        path = config / (region + '.ini')
        old = path.read_text() if path.exists() else ''
        if '$Fleet 16:9 Widescreen' not in old:
            path.write_text(old + '\n[Gecko]\n$Fleet 16:9 Widescreen\n' + code +
                            '\n[Gecko_Enabled]\n$Fleet 16:9 Widescreen\n')
wrapper = str(home / 'Applications/launch-disc-game.py')
internal_resolution = '3' if (home / 'rom-library').exists() else '6'
os.execv(wrapper, [wrapper, 'dolphin', str(game),
                     '-C', 'Dolphin.Core.EnableCheats=True',
                     '-C', 'Dolphin.Display.Fullscreen=True',
                     '-C', 'GFX.Settings.AspectRatio=1',
                     '-C', 'GFX.Settings.Crop=True',
                     '-C', 'GFX.Settings.InternalResolution=' + internal_resolution,
                     '-C', 'GFX.Enhancements.WideScreenHack=False'])
