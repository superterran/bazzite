#!/usr/bin/env python3
"""Bring Game Mode home forward without closing games or the private browser."""
import subprocess
from steam_client import evaluate

def main():
    subprocess.run(['steam', 'steam://open/bigpicture'], check=True)
    evaluate("(()=>{SteamUIStore.CloseSideMenus();SteamUIStore.Navigate('/library/home');return true;})()")
    # An already running Chrome viewer/game can retain Gamescope priority even
    # after Steam navigates. Explicitly select Steam's main UI for this tile.
    subprocess.run(['xprop', '-display', ':0', '-root', '-f',
                    'GAMESCOPECTRL_BASELAYER_APPID', '32c', '-set',
                    'GAMESCOPECTRL_BASELAYER_APPID', '413091, 769'], check=True)
    print('Focused Steam Game Mode; private Chrome remains independent.')

if __name__ == '__main__':
    main()
