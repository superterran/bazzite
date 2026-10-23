#!/usr/bin/env python3
"""Register the shared collection in running Steam and save native input bindings."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import shutil
import time
from steam_client import evaluate

ROOT = Path(__file__).resolve().parent.parent
NAME = '24 Games for Windows 95'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path)
    parser.add_argument('--controller', choices=['dualsense', 'ally'], required=True)
    args = parser.parse_args()
    game = args.game_dir or next((p for p in [Path.home()/'shared-games/24-games-windows95', Path('/var/mnt/fast/shared-games/24-games-windows95')] if (p/'cd/WIN/PROGRAM/GAMES.EXE').exists()), None)
    if game is None or not (game/'cd/WIN/PROGRAM/GAMES.EXE').exists():
        raise SystemExit('Wait for shared-games to sync, or pass --game-dir.')
    game = game.resolve()
    # Confirm the local Steam session is reachable before touching its library.
    evaluate('true')
    helper = importlib.util.spec_from_file_location('artwork', ROOT/'bin/steam-artwork-sync.py')
    artwork = importlib.util.module_from_spec(helper)
    helper.loader.exec_module(artwork)
    entries = []
    for path in (Path.home()/'.local/share/Steam/userdata').glob('*/config/shortcuts.vdf'):
        entries.extend(artwork.shortcuts(path))
    matches = [e for e in entries if '24 games' in e.get('AppName', '').casefold() or '24games' in e.get('AppName', '').casefold()]
    if len(matches) > 1:
        raise SystemExit('Multiple 24 Games entries exist; resolve duplicates before applying.')
    backup = Path.home()/'.local/state/24-games-setup'/time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, exist_ok=True)
    (backup/'previous-shortcuts.json').write_text(json.dumps(matches, indent=2)+'\n')
    launcher = game/'play.sh'
    shutil.copy2(ROOT/'bin/launch-24-games.sh', launcher)
    launcher.chmod(0o755)
    if matches:
        appid = matches[0]['appid']
    else:
        appid = evaluate('SteamClient.Apps.AddShortcut('+','.join(json.dumps(s) for s in [NAME, str(launcher), '', ''])+')')
    if not isinstance(appid, int) or appid <= 0:
        raise SystemExit('Steam did not return a valid shortcut ID.')
    evaluate('(async()=>{'+f'const id={appid};'+
             'await SteamClient.Apps.SetShortcutName(id,'+json.dumps(NAME)+');'+
             'await SteamClient.Apps.SetShortcutExe(id,'+json.dumps(str(launcher))+');'+
             'await SteamClient.Apps.SetShortcutLaunchOptions(id,"");'+
             'await SteamClient.Apps.SetShortcutStartDir(id,'+json.dumps(str(game/'cd/WIN/PROGRAM'))+');return true;})()')
    evaluate(f'controllerConfiguratorStore.LoadEditingConfiguration({appid},0)')
    for _ in range(40):
        config = evaluate('JSON.stringify(controllerConfiguratorStore.EditedConfiguration)')
        if config and json.loads(config).get('sets'):
            break
        time.sleep(.25)
    else:
        raise SystemExit('Controller configuration did not load; connect the intended controller and retry.')
    (backup/'controller-before.json').write_text(config+'\n')
    modes = [[3,1],[13,1],[4,3],[5,16],[6,10],[7,10],[12,7]]
    if args.controller == 'dualsense':
        modes.append([11,4])
    keys = [[s,i,1,k] for s in [3,13] for i,k in [[1,82],[5,81],[3,79],[7,80]]]
    keys += [[4,12,3,40],[4,11,3,44],[4,10,3,41],[4,9,3,59],[5,52,16,41],[5,51,16,43]]
    mouse = [[7,15,10,0],[6,15,10,1],[5,54,16,0],[5,53,16,1],[12,13,7,0]]
    if args.controller == 'dualsense':
        mouse.append([11,13,4,0])
    expression = '''(async()=>{const s=controllerConfiguratorStore,id=APP;
    for(const [source,mode] of MODES){s.SetControllerSourceMode(id,{action_set_key:'Default',source_binding_key:source,new_mode:mode,enable_virtual_menu_support:true});await s.m_updatingEditingConfigurationPromise;}
    for(const [source,input,mode,key] of KEYS){s.SetControllerInputBinding(id,{action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,binding_index:0,source_mode:mode,new_binding:{type:1,keyboard_key:{key}}});await s.m_updatingEditingConfigurationPromise;}
    for(const [source,input,mode,button] of MOUSE){s.SetControllerInputBinding(id,{action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,binding_index:0,source_mode:mode,new_binding:{type:2,mouse_button:{button}}});await s.m_updatingEditingConfigurationPromise;}
    s.SaveEditingConfiguration(id);return JSON.stringify(s.EditedConfiguration);})()'''
    for token,value in [('APP',appid),('MODES',modes),('KEYS',keys),('MOUSE',mouse)]:
        expression = expression.replace(token, json.dumps(value))
    saved = evaluate(expression, timeout=60)
    (backup/'controller-after.json').write_text(saved+'\n')
    for filename,kind in [('cover.png',0),('capsule.png',3),('hero.png',1)]:
        path = game/filename
        if path.exists():
            evaluate('SteamClient.Apps.SetCustomArtworkForApp('+str(appid)+','+json.dumps(base64.b64encode(path.read_bytes()).decode())+',"png",'+str(kind)+')', timeout=40)
    print(json.dumps({'appid':appid,'controller':args.controller,'backup':str(backup),'game':str(game)}))

if __name__ == '__main__':
    main()
