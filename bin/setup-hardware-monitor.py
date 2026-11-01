#!/usr/bin/python3
"""Idempotently add Hardware Monitor to the running Steam client."""
import importlib.util
import json
from pathlib import Path
import time
from steam_client import evaluate

root = Path(__file__).resolve().parent.parent
name = 'Hardware Monitor'
spec = importlib.util.spec_from_file_location('artwork', root / 'bin/steam-artwork-sync.py')
artwork = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artwork)
matches = []
for path in (Path.home() / '.local/share/Steam/userdata').glob('*/config/shortcuts.vdf'):
    matches.extend(e for e in artwork.shortcuts(path) if e.get('AppName') == name)
if len(matches) > 1:
    raise SystemExit('Multiple Hardware Monitor entries; refusing ambiguous changes.')
backup = Path.home() / '.local/state/hardware-monitor' / time.strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True, exist_ok=True)
(backup / 'shortcut-before.json').write_text(json.dumps(matches, indent=2))
launcher = str(root / 'bin/launch-hardware-monitor.sh')
appid = matches[0]['appid'] if matches else evaluate('SteamClient.Apps.AddShortcut(' + ','.join(json.dumps(s) for s in [name, launcher, '', '']) + ')')
assert isinstance(appid, int) and appid > 0
for method, value in [('SetShortcutName', name), ('SetShortcutExe', launcher), ('SetShortcutStartDir', str(Path.home()))]:
    evaluate(f'SteamClient.Apps.{method}({appid},{json.dumps(value)})')
settings = {'appid': appid, 'steam_gameid': str((appid << 32) | 0x02000000), 'name': name, 'launcher': launcher}
(Path.home() / '.config/hardware-monitor.json').write_text(json.dumps(settings, indent=2) + '\n')
print(json.dumps(settings))
import runpy
runpy.run_path(str(root / 'bin/setup-hardware-monitor-artwork.py'), run_name='__main__')
