#!/usr/bin/env python3
"""Launch or focus the same Steam-managed Chrome session from Moonlight."""
import json
from pathlib import Path
import subprocess
import time
from steam_client import evaluate

def main():
    settings=json.loads((Path.home()/'.config/chrome-tv.json').read_text())
    appid=int(settings['appid'])
    running=evaluate('SteamUIStore.RunningApps.map(a=>a.appid)') or []
    if appid not in running:
        subprocess.run(['steam','steam://rungameid/'+settings['steam_gameid']],check=True)
        for _ in range(45):
            if evaluate('SteamUIStore.WindowStore.GetAppWindowIDs('+str(appid)+').length>0'):
                break
            time.sleep(1)
        else:
            raise SystemExit('Chrome viewer did not become ready within 45 seconds.')
    evaluate('(()=>{SteamUIStore.SetRunningApp('+str(appid)+');SteamUIStore.NavigateToRunningApp();return true;})()')
    time.sleep(.3)
    focus=subprocess.run(['xprop','-display',':0','-root','GAMESCOPE_FOCUSED_APP'],capture_output=True,text=True)
    if 'GAMESCOPE_FOCUSED_APP(CARDINAL)' in focus.stdout and str(appid) not in focus.stdout:
        # Use Gamescope's existing app-priority control when Steam keeps another
        # running game's priority above the newly opened viewer.
        subprocess.run(['xprop','-display',':0','-root','-f','GAMESCOPECTRL_BASELAYER_APPID','32c','-set','GAMESCOPECTRL_BASELAYER_APPID',f'413091, {appid}, 769'],check=True)
    print('Focused Chrome - TV & Automation in the shared Game Mode session.')

if __name__=='__main__':
    main()
