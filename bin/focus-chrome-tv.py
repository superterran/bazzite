#!/usr/bin/env python3
"""Launch or focus the same Steam-managed Chrome session from Moonlight."""
import json
from pathlib import Path
import subprocess
import time
import urllib.request
from steam_client import evaluate

def ready():
    try:
        with urllib.request.urlopen('http://127.0.0.1:9223/json/version',timeout=2) as response:
            return 'Chrome/' in json.load(response).get('Browser','')
    except (OSError,ValueError):
        return False

def main():
    settings=json.loads((Path.home()/'.config/chrome-tv.json').read_text())
    appid=int(settings['appid'])
    if not ready():
        subprocess.run(['steam','steam://rungameid/'+settings['steam_gameid']],check=True)
        for _ in range(45):
            if ready():
                break
            time.sleep(1)
        else:
            raise SystemExit('Chrome did not become ready within 45 seconds.')
    evaluate('(()=>{SteamUIStore.SetRunningApp('+str(appid)+');SteamUIStore.NavigateToRunningApp();return true;})()')
    print('Focused Chrome - TV & Automation in the shared Game Mode session.')

if __name__=='__main__':
    main()
