#!/usr/bin/env python3
"""Register a synced Dusklight installation with the running Steam client."""
import argparse
import importlib.util
import json
from pathlib import Path
from steam_client import evaluate

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game-dir', type=Path, required=True)
args = parser.parse_args()
from steam_shortcut_policy import retired
if retired('Dusklight'):
    raise SystemExit('Dusklight shortcuts were retired on this host; game files retained.')
game = args.game_dir.resolve()
launcher = game / 'play.sh'
if not launcher.is_file() or not (game / 'Dusklight-v2.0.3-linux-x86_64.AppImage').is_file():
    raise SystemExit('Wait for the complete Dusklight folder to sync first.')
for path in [launcher, game / 'Dusklight-v2.0.3-linux-x86_64.AppImage']:
    path.chmod(path.stat().st_mode | 0o111)
evaluate('true')
spec = importlib.util.spec_from_file_location('art', Path(__file__).with_name('steam-artwork-sync.py'))
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)
matches = [row for path in (Path.home()/'.local/share/Steam/userdata').glob('*/config/shortcuts.vdf')
           for row in art.shortcuts(path) if row.get('AppName') == 'Dusklight']
if len(matches) > 1:
    raise SystemExit('Multiple Dusklight shortcuts found; no Steam changes applied.')
appid = matches[0]['appid'] if matches else evaluate('SteamClient.Apps.AddShortcut(' + ','.join(json.dumps(s) for s in ['Dusklight', str(launcher), '', '']) + ')')
if not isinstance(appid, int) or appid <= 0:
    raise SystemExit('Steam did not return a valid shortcut ID.')
evaluate('(async()=>{const id='+str(appid)+';'+
         'await SteamClient.Apps.SetShortcutName(id,"Dusklight");'+
         'await SteamClient.Apps.SetShortcutExe(id,'+json.dumps(str(launcher))+');'+
         'await SteamClient.Apps.SetShortcutStartDir(id,'+json.dumps(str(game))+');'+
         'await SteamClient.Apps.SetShortcutLaunchOptions(id,"");'+
         'await SteamClient.Apps.SetShortcutIcon(id,'+json.dumps(str(game/'icon.png'))+');return true;})()')
print(json.dumps({'appid': appid, 'game': str(game), 'user_data': str(game/'user-data')}))
