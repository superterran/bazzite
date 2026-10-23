#!/usr/bin/env python3
"""Create an idempotent Steam entry for the persistent visible Chrome session."""
import importlib.util
import json
from pathlib import Path
import shutil
import time
from steam_client import evaluate

ROOT = Path(__file__).resolve().parent.parent
NAME = 'Chrome - TV & Automation'

def main():
    evaluate('true')
    spec = importlib.util.spec_from_file_location('artwork', ROOT/'bin/steam-artwork-sync.py')
    artwork = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(artwork)
    entries = []
    for path in (Path.home()/'.local/share/Steam/userdata').glob('*/config/shortcuts.vdf'):
        entries.extend(artwork.shortcuts(path))
    matches = [e for e in entries if e.get('AppName') == NAME]
    if len(matches) > 1:
        raise SystemExit('Duplicate Chrome TV shortcuts found; no changes applied.')
    backup = Path.home()/'.local/state/chrome-tv-setup'/time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, exist_ok=True)
    (backup/'previous-shortcut.json').write_text(json.dumps(matches,indent=2)+'\n')
    launcher = Path.home()/'.local/bin/launch-chrome-tv.sh'
    appid = matches[0]['appid'] if matches else evaluate('SteamClient.Apps.AddShortcut('+','.join(json.dumps(s) for s in [NAME,str(launcher),'',''])+')')
    if not isinstance(appid,int) or appid<=0:
        raise SystemExit('Steam did not create a valid shortcut.')
    evaluate('(async()=>{const id='+str(appid)+';'+
             'await SteamClient.Apps.SetShortcutName(id,'+json.dumps(NAME)+');'+
             'await SteamClient.Apps.SetShortcutExe(id,'+json.dumps(str(launcher))+');'+
             'await SteamClient.Apps.SetShortcutStartDir(id,'+json.dumps(str(Path.home()))+');'+
             'await SteamClient.Apps.SetShortcutLaunchOptions(id,"");return true;})()')
    evaluate(f'controllerConfiguratorStore.LoadEditingConfiguration({appid},0)')
    time.sleep(1)
    before = evaluate('JSON.stringify(controllerConfiguratorStore.EditedConfiguration)')
    (backup/'controller-before.json').write_text(before+'\n')
    expression = '''(async()=>{const s=controllerConfiguratorStore,id=APP;
    for(const [source,mode] of [[3,1],[13,1],[4,3],[5,16],[6,10],[7,10],[12,7],[11,4]]){s.SetControllerSourceMode(id,{action_set_key:'Default',source_binding_key:source,new_mode:mode,enable_virtual_menu_support:true});await s.m_updatingEditingConfigurationPromise;}
    for(const [source,input,mode,key] of [[3,1,1,82],[3,5,1,81],[3,3,1,79],[3,7,1,80],[13,1,1,82],[13,5,1,81],[13,3,1,79],[13,7,1,80],[4,12,3,40],[4,11,3,44],[4,10,3,41],[4,9,3,43],[5,52,16,63],[5,51,16,42]]){s.SetControllerInputBinding(id,{action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,binding_index:0,source_mode:mode,new_binding:{type:1,keyboard_key:{key}}});await s.m_updatingEditingConfigurationPromise;}
    for(const [source,input,mode,button] of [[7,15,10,0],[6,15,10,1],[11,13,4,0]]){s.SetControllerInputBinding(id,{action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,binding_index:0,source_mode:mode,new_binding:{type:2,mouse_button:{button}}});await s.m_updatingEditingConfigurationPromise;}
    // Steam's keyboard enum uses 103 for left Control (not USB HID 224).
    for(const [source,input,mode,key] of [[5,54,16,46],[5,53,16,45],[12,13,7,39]]){
      const address={action_set_key:'Default',source_binding_key:source,input_key:input,activator_index:0,source_mode:mode};
      s.SetControllerInputBinding(id,{...address,binding_index:0,new_binding:{type:1,keyboard_key:{key:103}}});await s.m_updatingEditingConfigurationPromise;
      const bindings=s.EditedConfiguration.sets[0].source_bindings.find(x=>x.key===source).active_group.inputs.find(i=>i.key===input).activators[0].bindings;
      s.SetControllerInputBinding(id,{...address,binding_index:bindings.length>1?1:-1,new_binding:{type:1,keyboard_key:{key}}});await s.m_updatingEditingConfigurationPromise;
    }
    s.SaveEditingConfiguration(id);return JSON.stringify(s.EditedConfiguration);})()'''.replace('APP',str(appid))
    (backup/'controller-after.json').write_text(evaluate(expression,timeout=60)+'\n')
    settings = {'name':NAME,'appid':appid,'steam_gameid':str((appid<<32)|0x02000000),'endpoint':'http://127.0.0.1:9223','profile':str(Path.home()/'.var/app/com.google.Chrome/config/chrome-tv-automation')}
    (Path.home()/'.config/chrome-tv.json').write_text(json.dumps(settings,indent=2)+'\n')
    icon = Path('/var/lib/flatpak/app/com.google.Chrome/current/active/files/extra/product_logo_256.png')
    if icon.exists():
        evaluate('SteamClient.Apps.SetShortcutIcon('+str(appid)+','+json.dumps(str(icon))+')')
    # Sunshine's Desktop/Steam entries already mirror this Game Mode session.
    # Add a convenient launch tile to both known locations; retain all other apps.
    for index,config in enumerate([Path.home()/'.config/sunshine/apps.json',Path.home()/'.var/app/dev.lizardbyte.app.Sunshine/config/sunshine/apps.json']):
        if not config.exists():
            continue
        data = json.loads(config.read_text())
        shutil.copy2(config,backup/('sunshine-'+str(index)+'-original.json'))
        apps = data.setdefault('apps',[])
        entry = {'name':NAME,'detached':['steam steam://rungameid/'+settings['steam_gameid']],'image-path':str(icon) if icon.exists() else ''}
        existing = next((a for a in apps if a.get('name')==NAME),None)
        if existing is not None:
            existing.update(entry)
        else:
            apps.append(entry)
        temporary = config.with_suffix('.tmp')
        temporary.write_text(json.dumps(data,indent=2)+'\n')
        temporary.replace(config)
    print(json.dumps(settings))

if __name__ == '__main__':
    main()
