#!/usr/bin/env python3
"""Install a Steam viewer entry for the native private-desktop 1Password app."""
import importlib.util
import json
from pathlib import Path
import time
from steam_client import evaluate

ROOT=Path(__file__).resolve().parent.parent
NAME='1Password'

def main():
    spec=importlib.util.spec_from_file_location('artwork',ROOT/'bin/steam-artwork-sync.py')
    artwork=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(artwork)
    entries=[]
    for path in (Path.home()/'.local/share/Steam/userdata').glob('*/config/shortcuts.vdf'):
        entries.extend(artwork.shortcuts(path))
    matches=[e for e in entries if e.get('AppName')==NAME]
    if len(matches)>1:
        raise SystemExit('Multiple 1Password entries found; refusing to modify them.')
    backup=Path.home()/'.local/state/onepassword-tv'/time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True,exist_ok=True)
    (backup/'shortcut-before.json').write_text(json.dumps(matches,indent=2))
    launcher=str(ROOT/'bin/launch-onepassword-tv.sh')
    appid=matches[0]['appid'] if matches else evaluate('SteamClient.Apps.AddShortcut('+','.join(json.dumps(s) for s in [NAME,launcher,'',''])+')')
    assert isinstance(appid,int) and appid>0
    for method,value in [('SetShortcutName',NAME),('SetShortcutExe',launcher),('SetShortcutStartDir',str(Path.home()))]:
        evaluate(f'SteamClient.Apps.{method}({appid},{json.dumps(value)})')
    evaluate(f'controllerConfiguratorStore.LoadEditingConfiguration({appid},0)')
    time.sleep(1)
    (backup/'controller-before.json').write_text(evaluate('JSON.stringify(controllerConfiguratorStore.EditedConfiguration)'))
    # Same mouse/navigation bindings as Chrome, without its browser zoom chords.
    expression='''(async()=>{const s=controllerConfiguratorStore,id=APP;
    for(const [source,mode] of [[3,1],[13,1],[4,3],[5,16],[6,10],[7,10],[12,7],[11,4]]){s.SetControllerSourceMode(id,{action_set_key:'Default',source_binding_key:source,new_mode:mode,enable_virtual_menu_support:true});await s.m_updatingEditingConfigurationPromise;}
    for(const [source,input,mode,key] of [[3,1,1,82],[3,5,1,81],[3,3,1,79],[3,7,1,80],[13,1,1,82],[13,5,1,81],[13,3,1,79],[13,7,1,80],[4,12,3,40],[4,11,3,44],[4,10,3,41],[4,9,3,43]]){s.SetControllerInputBinding(id,{action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,binding_index:0,source_mode:mode,new_binding:{type:1,keyboard_key:{key}}});await s.m_updatingEditingConfigurationPromise;}
    for(const [source,input,mode,button] of [[7,15,10,0],[6,15,10,1],[11,13,4,0]]){s.SetControllerInputBinding(id,{action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,binding_index:0,source_mode:mode,new_binding:{type:2,mouse_button:{button}}});await s.m_updatingEditingConfigurationPromise;}
    s.SaveEditingConfiguration(id);return JSON.stringify(s.EditedConfiguration);})()'''.replace('APP',str(appid))
    (backup/'controller-after.json').write_text(evaluate(expression,timeout=60))
    icons=list(Path('/usr/share/icons').glob('**/1password.png'))
    if icons:evaluate(f'SteamClient.Apps.SetShortcutIcon({appid},{json.dumps(str(icons[0]))})')
    settings={'appid':appid,'steam_gameid':str((appid<<32)|0x02000000),'name':NAME}
    (Path.home()/'.config/onepassword-tv.json').write_text(json.dumps(settings,indent=2)+'\n')
    print(json.dumps(settings))

if __name__=='__main__':main()
