from pathlib import Path
import json,shutil
info=Path('/opt/muos/share/info')
for system,cat,choice,core,bios in [('atari5200','Atari 5200','a5200','a5200_libretro.so',False),('colecovision','ColecoVision','gearcoleco','gearcoleco_libretro.so',True)]:
 assign=info/'assign'/cat;assign.mkdir(parents=True,exist_ok=True)
 (assign/'global.ini').write_text('[global]\nname='+cat+'\ndefault='+choice+'\ncatalogue='+cat+'\nlookup=0\n\n[friendly]\n'+system+'\n'+('coleco\n' if system=='colecovision' else 'a5200\n'))
 (assign/(choice+'.ini')).write_text('['+choice+']\nname='+choice+'\ncore='+core+'\nbios_required='+str(int(bios))+'\nexternal=0\n\n[launch]\nprep=\nexec=/opt/muos/script/launch/lr-general.sh\ndone=\n')
 for sub in ['!Library/systems/'+system,'ATARI5200' if system=='atari5200' else 'COLECO']:
  dest=info/'core'/sub;dest.mkdir(parents=True,exist_ok=True)
  (dest/'core.cfg').write_text('\n'.join([core,cat,cat,'0',choice]));(dest/'core.con').write_text('system');(dest/'core.gov').write_text('ondemand')
 if system=='atari5200':
  cfg=info/'config/a5200';cfg.mkdir(exist_ok=True);(cfg/'a5200.opt').write_text('a5200_bios = "internal"\n')
# Old ATARI800 directory is demonstrably a 2600 set, already deduplicated into the shared 2600 library.
dest=info/'core/ATARI800';dest.mkdir(parents=True,exist_ok=True)
(dest/'core.cfg').write_text('stella2014_libretro.so\nAtari 2600\nAtari 2600\n0\nstella 2014');(dest/'core.con').write_text('system');(dest/'core.gov').write_text('ondemand')
p=Path('/mnt/mmc/MUOS/info/name/folder.json');x=json.loads(p.read_text());x.update(atari800='Atari 2600 (older local copy)',atari5200='Atari 5200',coleco='ColecoVision (BIOS required)',colecovision='ColecoVision (BIOS required)');p.write_text(json.dumps(x,indent=2))
print('Additional assignments installed; ColecoVision requires colecovision.rom.')
