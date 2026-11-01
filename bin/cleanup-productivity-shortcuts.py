#!/usr/bin/python3
"""Retire only the desktop shortcuts explicitly selected by the user."""
import json
from pathlib import Path
import shutil
import time
from steam_client import evaluate

ENTRIES = {4154030664:'1Password',3789767895:'Chrome - TV & Automation',
           2323161660:'Dusklight',3802447962:'Dusklight'}
backup = Path.home()/'.local/state/steam-shortcut-retirement'/time.strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True)
for source in (Path.home()/'.local/share/Steam/userdata').glob('*/config/shortcuts.vdf'):
    shutil.copy2(source, backup/(source.parents[1].name+'-shortcuts.vdf'))
(backup/'removed.json').write_text(json.dumps(ENTRIES,indent=2)+'\n')
for appid, expected in ENTRIES.items():
    name = evaluate(f'appStore.GetAppOverviewByAppID({appid})?.display_name')
    if name is None: continue
    if name != expected: raise SystemExit('Shortcut identity changed; refusing removal.')
    evaluate(f'SteamClient.Apps.RemoveShortcut({appid})')
policy = Path.home()/'.config/retired-steam-shortcuts.json'
old = json.loads(policy.read_text()) if policy.exists() else {'titles':[]}
old['titles'] = sorted(set(old['titles']) | set(ENTRIES.values()))
policy.write_text(json.dumps(old,indent=2)+'\n')
# Archive only art files belonging to these removed shortcut IDs.
for grid in (Path.home()/'.local/share/Steam/userdata').glob('*/config/grid'):
    for appid in ENTRIES:
        for p in grid.glob(str(appid)+'*'):
            suffix=p.stem.removeprefix(str(appid))
            if suffix in ('','p','_hero','_logo','_icon'):
                target=backup/'grid'/p.name;target.parent.mkdir(exist_ok=True)
                shutil.move(str(p),target)
print('Removed four retired shortcuts; game/application data retained. Backup:',backup)
