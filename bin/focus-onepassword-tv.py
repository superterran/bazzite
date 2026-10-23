#!/usr/bin/env python3
"""Focus the Steam viewer without launching another 1Password instance."""
import json
from pathlib import Path
import subprocess
from steam_client import evaluate

settings=json.loads((Path.home()/'.config/onepassword-tv.json').read_text())
appid=int(settings['appid'])
evaluate(f'(()=>{{SteamUIStore.SetRunningApp({appid});SteamUIStore.NavigateToRunningApp();return true;}})()')
subprocess.run(['xprop','-display',':0','-root','-f','GAMESCOPECTRL_BASELAYER_APPID','32c','-set','GAMESCOPECTRL_BASELAYER_APPID',f'413091, {appid}, 769'],check=True)
