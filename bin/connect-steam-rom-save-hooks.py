#!/usr/bin/env python3
"""Retain existing Steam shortcut IDs while adding pre/post save reconciliation."""
import importlib.util,json,shlex,shutil,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.local/bin'))
from steam_client import evaluate
spec=importlib.util.spec_from_file_location('art',str(Path.home()/'.local/bin/steam-artwork-sync.py'));art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
config=Path.home()/'.local/share/Steam/userdata/35894255/config';rows=art.shortcuts(config/'shortcuts.vdf');jobs=[]
for e in rows:
 args=shlex.split(e.get('LaunchOptions',''))
 if e.get('Exe','').strip('"')!='/usr/bin/flatpak' or args[:2]!=['run','org.libretro.RetroArch']:continue
 jobs.append({'id':e['appid'],'name':e['AppName'],'options':shlex.join(args[2:])})
if jobs:
 backup=Path.home()/'.local/state/steam-library-cleanup'/(time.strftime('%Y%m%d-%H%M%S')+'-save-hooks');backup.mkdir(parents=True);shutil.copy2(config/'shortcuts.vdf',backup/'shortcuts.vdf')
 exe='"'+str(Path.home()/'Applications/launch-shared-retroarch.py')+'"';start='"'+str(Path.home()/'Applications')+'"'
 expr='(()=>{for(const j of '+json.dumps(jobs)+'){SteamClient.Apps.SetShortcutExe(j.id,'+json.dumps(exe)+');SteamClient.Apps.SetShortcutStartDir(j.id,'+json.dumps(start)+');SteamClient.Apps.SetAppLaunchOptions(j.id,j.options);SteamClient.Apps.SetShortcutName(j.id,j.name);}return true;})()'
 assert evaluate(expr) is True
print(json.dumps({'updated':[j['name'] for j in jobs],'ids_preserved':True}))
