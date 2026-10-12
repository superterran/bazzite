from pathlib import Path
import configparser,json,shutil,tarfile,time
info=Path('/opt/muos/share/info');storage=Path('/mnt/mmc/MUOS/info');roms=Path('/mnt/sdcard/Roms/!Library/systems');art=storage/'shared-artwork/muos';catalogue=storage/'catalogue'
stamp=time.strftime('%Y%m%d-%H%M%S');backup=storage/'frontend-backups'/stamp;backup.mkdir(parents=True,exist_ok=True)
with tarfile.open(backup/'configuration.tar','w') as t:
 for p in [info/'core',Path('/opt/muos/config/visual'),storage/'name',storage/'collection']:
  if p.exists():t.add(p,arcname=str(p).lstrip('/'))
mapping={'atari5200':('Atari 5200','a5200'),'colecovision':('ColecoVision','gearcoleco'),'arcade':('Arcade','finalburn neo'),'atari2600':('Atari 2600','stella 2014'),'atari7800':('Atari 7800','prosystem'),'gamegear':('Sega Game Gear','genesis plus gx'),'gb':('Nintendo Game Boy','gambatte'),'gba':('Nintendo Game Boy Advance','mgba'),'gbc':('Nintendo Game Boy Color','gambatte'),'lynx':('Atari Lynx','handy'),'mastersystem':('Sega Master System','genesis plus gx'),'megadrive':('Sega Mega Drive - Genesis','genesis plus gx'),'n64':('Nintendo N64','mupen64plus next'),'nes':('Nintendo NES - Famicom','fceumm'),'pcengine':('NEC PC Engine','beetle pce fast'),'sega32x':('Sega 32X','picodrive'),'snes':('Nintendo SNES - SFC','snes9x')}
report={'backup':str(backup),'systems':{},'artwork_copied':0,'artwork_preserved':0,'warnings':[]}
for system,(cat,choice) in mapping.items():
 folder=roms/system
 if not folder.exists():continue
 root=info/'assign'/cat
 cfg=configparser.ConfigParser(strict=False,allow_no_value=True);cfg.read(root/'global.ini')
 lookup=cfg.get('global','lookup',fallback='0')
 corecfg=configparser.ConfigParser(strict=False,allow_no_value=True);corecfg.read(root/(choice+'.ini'))
 core=corecfg.get(choice,'core',fallback='')
 if system=='atari7800':core='prosystem_libretro.so'
 if not core or not (Path('/opt/muos/share/core')/core).exists():
  report['warnings'].append({'system':system,'reason':'Requested core unavailable','choice':choice});continue
 dest=info/'core/!Library/systems'/system;dest.mkdir(parents=True,exist_ok=True)
 (dest/'core.cfg').write_text('\n'.join([core,cat,cat,lookup,choice]))
 (dest/'core.con').write_text('system');(dest/'core.gov').write_text('performance' if system=='n64' else 'ondemand')
 copied=0
 for role in ['box','preview','text']:
  source=art/cat/role
  if not source.exists():continue
  target=catalogue/cat/role;target.mkdir(parents=True,exist_ok=True)
  for f in source.iterdir():
   if not f.is_file():continue
   d=target/f.name
   if d.exists():report['artwork_preserved']+=1;continue
   shutil.copy2(f,d);copied+=1
 report['artwork_copied']+=copied
 games=[f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in ['.a52','.col','.cv','.zip','.nes','.smc','.sfc','.gb','.gbc','.gba','.bin','.a26','.a78','.rom','.gg','.sms','.md','.gen','.32x','.pce','.lnx','.z64','.n64','.v64']]
 report['systems'][system]={'roms':len(games),'core':core,'catalogue':cat,'covers':sum((catalogue/cat/'box'/(f.stem+'.png')).exists() for f in games),'previews':sum((catalogue/cat/'preview'/(f.stem+'.png')).exists() for f in games),'assignment':str(dest/'core.cfg')}
(backup/'review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
