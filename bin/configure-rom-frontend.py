#!/usr/bin/env python3
"""Configure local ES-DE for the shared ROM and artwork libraries."""
import argparse, json, shutil, re, xml.etree.ElementTree as ET, subprocess
from pathlib import Path
from datetime import datetime
SYSTEMS={
'atari5200':('atari5200','Atari 5200','a5200','.a52 .bin .zip'),
'colecovision':('colecovision','ColecoVision','gearcoleco','.col .cv .bin .rom .zip'),
'arcade':('arcade','Arcade','fbneo','.zip'),
'atari2600':('atari2600','Atari 2600','stella','.a26 .bin .rom .zip'),
'atari7800':('atari7800','Atari 7800','prosystem','.a78 .bin .zip'),
'gamegear':('gamegear','Sega Game Gear','genesis_plus_gx','.gg .bin .zip'),
'gb':('gb','Nintendo Game Boy','gambatte','.gb .zip'),
'gba':('gba','Nintendo Game Boy Advance','mgba','.gba .zip'),
'gbc':('gbc','Nintendo Game Boy Color','gambatte','.gbc .gb .zip'),
'lynx':('lynx','Atari Lynx','handy','.lnx .lyx .zip'),
'mastersystem':('mastersystem','Sega Master System','genesis_plus_gx','.sms .bin .zip'),
'megadrive':('genesis','Sega Mega Drive','genesis_plus_gx','.md .bin .gen .smd .zip'),
'n64':('n64','Nintendo 64','mupen64plus_next','.z64 .n64 .v64 .zip'),
'nes':('nes','Nintendo NES','nestopia','.nes .fds .zip'),
'pcengine':('pcengine','NEC PC Engine','mednafen_pce_fast','.pce .bin .zip'),
'sega32x':('sega32x','Sega 32X','picodrive','.32x .bin .zip'),
'snes':('snes','Nintendo SNES','snes9x','.smc .sfc .zip'),
'sneswidescreen':('sneswidescreen','SNES Widescreen','bsnes_hd_beta','.smc .sfc .zip'),
'gc':('gc','Nintendo GameCube',None,'.iso .gcm .rvz .gcz .ciso'),
'wii':('wii','Nintendo Wii',None,'.iso .rvz .gcz .wbfs .wad'),
'wiiu':('wiiu','Nintendo Wii U',None,'.wud .wux .wua .rpx'),
'n3ds':('n3ds','Nintendo 3DS',None,'.3ds .cci .cxi')}
def configure(library,artwork):
 library=Path(library).resolve();artwork=Path(artwork).resolve();base=Path.home()/'ES-DE'
 active=subprocess.run(['pgrep','-x','es-de'],stdout=subprocess.DEVNULL).returncode==0
 if active: raise RuntimeError('Close ES-DE before changing its settings.')
 cores=Path.home()/'.var/app/org.libretro.RetroArch/config/retroarch/cores'
 missing=[v[2] for v in SYSTEMS.values() if v[2] and not (cores/(v[2]+'_libretro.so')).exists()]
 if missing: raise RuntimeError('Missing cores: '+str(missing))
 stamp=datetime.now().strftime('%Y%m%d-%H%M%S');backup=base/'backups'/stamp
 backup.mkdir(parents=True,exist_ok=True)
 for folder in ['settings','custom_systems','gamelists']:
  if (base/folder).exists(): shutil.copytree(base/folder,backup/folder)
 for folder in ['settings','custom_systems','gamelists']: (base/folder).mkdir(parents=True,exist_ok=True)
 cfg=base/'settings/es_settings.xml'
 raw=re.sub(r'<\?xml[^>]*\?>','',cfg.read_text() if cfg.exists() else '').strip()
 try: settings=ET.fromstring(raw);wrapped=False
 except ET.ParseError: settings=ET.fromstring('<settings>'+raw+'</settings>');wrapped=True
 def setvalue(name,value):
  node=next((n for n in settings if n.get('name')==name),None)
  if node is None: node=ET.SubElement(settings,'string',{'name':name})
  node.set('value',str(value))
 setvalue('ROMDirectory',library);setvalue('MediaDirectory',artwork/'es-de/media')
 # Default themes use still artwork when no video is present.
 for n in settings:
  if n.get('name')=='AlternativeEmulatorPerGame': n.set('value','true')
 cfg.write_text('<?xml version="1.0"?>\n'+(''.join(ET.tostring(n,encoding='unicode')+'\n' for n in settings) if wrapped else ET.tostring(settings,encoding='unicode')))
 custom=base/'custom_systems/es_systems.xml'
 root=ET.parse(custom).getroot() if custom.exists() else ET.Element('systemList')
 saved_commands={child.findtext('name'):[ET.fromstring(ET.tostring(c)) for c in child.findall('command')[1:]] for child in root}
 for child in list(root):
  if child.findtext('name') in [v[0] for v in SYSTEMS.values()]: root.remove(child)
 counts={}
 for system,(es,title,core,extensions) in SYSTEMS.items():
  rel=Path('variants/widescreen/snes') if system=='sneswidescreen' else Path('systems')/system
  romdir=library/rel
  if system in ['gc','wii','wiiu','n3ds']: romdir.mkdir(parents=True,exist_ok=True)
  if not romdir.exists(): raise RuntimeError('Missing ROM directory: '+str(romdir))
  s=ET.SubElement(root,'system')
  command=(str(Path.home()/'Applications/azahar-gui.AppImage')+' %ROM%' if system=='n3ds' else '/usr/bin/flatpak run info.cemu.Cemu -f -g %ROM%' if system=='wiiu' else '/usr/bin/flatpak run org.DolphinEmu.dolphin-emu -b -e %ROM%' if system in ['gc','wii'] else '/usr/bin/flatpak run org.libretro.RetroArch -L '+str(cores/(core+'_libretro.so'))+' %ROM%')
  if system in ['gc','wii','wiiu']:
   command=str(Path.home()/'Applications/launch-disc-game.py')+(' cemu' if system=='wiiu' else ' dolphin')+' %ROM%'
  for tag,value in [('name',es),('fullname',title),('path','%ROMPATH%/'+str(rel)),('extension',extensions+' '+extensions.upper()),('command',command),('platform','snes' if system=='sneswidescreen' else 'atarilynx' if system=='lynx' else es),('theme','snes' if system=='sneswidescreen' else 'atarilynx' if system=='lynx' else es)]:
   ET.SubElement(s,tag).text=value
  for command in saved_commands.get(es,[]):
   s.find('command').set('label','Shared library default');s.append(command)
  if system=='gc' and not any(c.get('label')=='Road Rage 16:9' for c in s.findall('command')):
   s.find('command').set('label','Shared library default')
   ET.SubElement(s,'command',{'label':'Road Rage 16:9'}).text=str(Path.home()/'Applications/launch-road-rage.py')
  if system=='gc' and not any(c.get('label')=='ZooCube High Resolution' for c in s.findall('command')):
   s.find('command').set('label','Shared library default')
   ET.SubElement(s,'command',{'label':'ZooCube High Resolution'}).text=str(Path.home()/'Applications/launch-zoocube.py')
  if system in ['snes','sneswidescreen']:
   s.find('command').set('label','Shared library default')
   for c in list(s.findall('command')):
    if c.get('label')=='EarthBound Redux Widescreen':s.remove(c)
   ET.SubElement(s,'command',{'label':'EarthBound Redux Widescreen'}).text=str(Path.home()/'Applications/launch-earthbound-widescreen.py')
  gl=ET.Element('gameList');meta_path=artwork/'es-de/metadata'/(es+'.json')
  metadata=json.loads(meta_path.read_text()) if meta_path.exists() else {}
  # Preserve existing play history while replacing stale ROM paths.
  oldpath=base/'gamelists'/es/'gamelist.xml';history={}
  if oldpath.exists():
   try: oldgames=ET.parse(oldpath).findall('game')
   except ET.ParseError:
    wrapped=ET.fromstring('<settings>'+re.sub(r'<\?xml[^>]*\?>','',oldpath.read_text())+'</settings>')
    oldgames=wrapped.findall('gameList/game')
   for g in oldgames: history[Path(g.findtext('path','')).stem]={k:g.findtext(k) for k in ['playcount','lastplayed','favorite','altemulator'] if g.findtext(k)}
  for f in sorted(romdir.rglob('*') if system=='wiiu' else romdir.iterdir()):
   if not f.is_file() or f.suffix.lower() not in extensions.split(): continue
   g=ET.SubElement(gl,'game');ET.SubElement(g,'path').text=str(f)
   values=dict(metadata.get(f.stem,{'name':f.stem}));values.update(history.get(f.stem,{}))
   if system=='gc' and 'road' in f.stem.lower() and 'rage' in f.stem.lower():
    values.update(name='The Simpsons: Road Rage',altemulator='Road Rage 16:9')
   if system=='gc' and f.stem.lower().startswith('zoocube'):
    values.update(name='ZooCube',altemulator='ZooCube High Resolution')
   if system in ['snes','sneswidescreen'] and f.stem=='EarthBound-MBR':
    values.update(name='EarthBound — MaternalBound Redux Widescreen',altemulator='EarthBound Redux Widescreen')
   for k,v in values.items():
    if k in ['name','desc','rating','releasedate','developer','publisher','genre','players','playcount','lastplayed','favorite','altemulator']: ET.SubElement(g,k).text=v
  counts[es]=len(gl)
  oldpath.parent.mkdir(parents=True,exist_ok=True)
  ET.indent(gl);ET.ElementTree(gl).write(oldpath,encoding='utf-8',xml_declaration=True)
 ET.indent(root);ET.ElementTree(root).write(custom,encoding='utf-8',xml_declaration=True)
 launcher=Path.home()/'.local/share/applications/rom-library-es-de.desktop'
 launcher.parent.mkdir(parents=True,exist_ok=True)
 launcher.write_text('[Desktop Entry]\nType=Application\nName=EmulationStation — Shared ROM Library\nExec='+str(Path.home()/'Applications/ES-DE.AppImage')+'\nIcon=applications-games\nCategories=Game;\nTerminal=false\n')
 if (library/'systems/gc/ZooCube (USA).rvz').exists():
  game_entry=launcher.parent/'zoocube.desktop'
  game_entry.write_text('[Desktop Entry]\nType=Application\nName=ZooCube\nExec='+str(Path.home()/'Applications/launch-zoocube.py')+'\nIcon='+str(artwork/'es-de/media/gc/covers/ZooCube (USA).jpg')+'\nCategories=Game;\nTerminal=false\n')
 print(json.dumps({'systems':counts,'ROMDirectory':str(library),'MediaDirectory':str(artwork/'es-de/media'),'backup':str(backup)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--artwork',required=True);a=p.parse_args();configure(a.library,a.artwork)
