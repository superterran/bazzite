#!/usr/bin/env python3
"""Back up RetroArch settings and use per-core, per-console shared battery saves."""
import argparse,json,re,shutil,subprocess,tarfile,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--save-root',required=True);p.add_argument('--muos',action='store_true');a=p.parse_args()
if subprocess.run(['pgrep','-x','retroarch'],stdout=subprocess.DEVNULL).returncode==0:raise SystemExit('Close RetroArch before changing save paths.')
root=Path(a.save_root).expanduser();(root/'retroarch').mkdir(parents=True,exist_ok=True)
if a.muos:
 configs=[(Path('/opt/muos/share/info/config/retroarch.cfg'),Path('/opt/muos/share/info/config'))];backup=Path('/mnt/mmc/MUOS/info/frontend-backups')/(time.strftime('%Y%m%d-%H%M%S')+'-save-paths')
else:
 flat=Path.home()/'.var/app/org.libretro.RetroArch/config/retroarch';native=Path.home()/'.local/share/Steam/steamapps/common/RetroArch';configs=[(flat/'retroarch.cfg',flat/'config')]
 libraryfile=Path.home()/'.local/share/Steam/steamapps/libraryfolders.vdf'
 libraries=[Path.home()/'.local/share/Steam']+[Path(v) for v in re.findall(r'"path"\s*"([^"]+)"',libraryfile.read_text() if libraryfile.exists() else '')]
 seen=set()
 for library in libraries:
  native=library/'steamapps/common/RetroArch'
  if (native/'retroarch.cfg').exists() and str(native.resolve()) not in seen:
   configs.append((native/'retroarch.cfg',native/'config'));seen.add(str(native.resolve()))
 backup=Path.home()/'.local/state/retroarch-save-backups'/(time.strftime('%Y%m%d-%H%M%S')+'-save-paths')
backup.mkdir(parents=True,exist_ok=True)
with tarfile.open(backup/'settings.tar.gz','w:gz') as t:
 for cfg,overrides in configs:
  for source in [cfg,overrides]:
   if source.exists():t.add(source,arcname=str(source).lstrip('/'),recursive=True)
def patch(path,values):
 text=path.read_text() if path.exists() else ''
 for key,value in values.items():
  line=key+' = '+json.dumps(value)
  if re.search(r'^'+re.escape(key)+r'\s*=',text,re.M):text=re.sub(r'^'+re.escape(key)+r'\s*=.*$',lambda _:line,text,flags=re.M)
  else:text+='\n'+line+'\n'
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
# Canonical lower-case console paths prevent same-name games on different systems
# from overwriting each other in cores that support several consoles.
platforms={'arcade':(['FinalBurn Neo'],['arcade','FBNEO','FBA']),'atari2600':(['Stella','Stella 2014'],['atari2600','ATARI800','ATARI2600']),'atari5200':(['a5200'],['atari5200','ATARI5200']),'atari7800':(['ProSystem'],['atari7800','ATARI7800']),'colecovision':(['Gearcoleco'],['colecovision','COLECO']),'gamegear':(['Genesis Plus GX'],['gamegear','GG']),'gb':(['Gambatte'],['gb','GB']),'gba':(['mGBA','gpSP'],['gba','GBA']),'gbc':(['Gambatte'],['gbc','GBC']),'lynx':(['Handy'],['lynx','LYNX']),'mastersystem':(['Genesis Plus GX'],['mastersystem','MS']),'megadrive':(['Genesis Plus GX'],['megadrive','genesis','MD']),'n64':(['Mupen64Plus-Next'],['n64','N64']),'nes':(['Nestopia','FCEUmm','Mesen'],['nes','FC','NES','retroarch']),'pcengine':(['Beetle PCE Fast'],['pcengine','PCE']),'sega32x':(['PicoDrive'],['sega32x','SEGA32X']),'snes':(['Snes9x','Snes9x 2010','bsnes-hd beta'],['snes','SFC','SNES'])}
written=[]
for cfg,overrides in configs:
 patch(cfg,{'savefile_directory':str(root/'retroarch'),'sort_savefiles_enable':'true','sort_savefiles_by_content_enable':'true','savestate_auto_load':'false','cloud_sync_enable':'false'})
 for platform,(cores,folders) in platforms.items():
  for core in cores:
   for folder in folders:
    dest=root/'retroarch'/core/platform;dest.mkdir(parents=True,exist_ok=True)
    path=overrides/core/(folder+'.cfg');patch(path,{'savefile_directory':str(dest),'sort_savefiles_enable':'false','sort_savefiles_by_content_enable':'false','savestate_auto_load':'false'});written.append(str(path))
print(json.dumps({'backup':str(backup),'configs':[str(c) for c,o in configs],'folder_overrides':len(written),'save_root':str(root),'save_states':'Existing local state paths preserved; automatic loading disabled'}))
