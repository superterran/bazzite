#!/usr/bin/env python3
"""Launch verified MaternalBound Redux widescreen with shared in-game saves."""
import os,shutil,sys,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
home=Path.home();settings=home/'ES-DE/settings/es_settings.xml'
tree=ET.fromstring('<settings>'+settings.read_text().split('?>',1)[1]+'</settings>')
library=Path(next(n.get('value') for n in tree if n.get('name')=='ROMDirectory'))
save_root=library.parent/'rom-saves'
rom=library/'variants/widescreen/snes/EarthBound-MBR.smc'
if not rom.exists():raise SystemExit('EarthBound widescreen has not finished syncing.')
retro=home/'.var/app/org.libretro.RetroArch/config/retroarch'
core=retro/'cores/bsnes_hd_beta_libretro.so'
runtime=home/'.config/gaming-fleet';runtime.mkdir(parents=True,exist_ok=True)
options=retro/'config/bsnes-hd beta/EarthBound-MBR.opt'
if options.exists() and not options.with_suffix('.opt.before-widescreen').exists():shutil.copy2(options,options.with_suffix('.opt.before-widescreen'))
base=retro/'config/bsnes-hd beta/bsnes-hd beta.opt'
values={}
for line in (options.read_text() if options.exists() else base.read_text() if base.exists() else '').splitlines():
 key,sep,value=line.partition('=')
 if sep:values[key.strip()]=value.strip()
values.update(bsnes_mode7_wsMode='"all"',bsnes_mode7_widescreen='"16:9"',bsnes_mode7_wsobj='"unsafe"')
options.parent.mkdir(parents=True,exist_ok=True)
options.write_text(''.join(k+' = '+v+'\n' for k,v in values.items()))
(save_root/'retroarch/bsnes-hd beta/snes').mkdir(parents=True,exist_ok=True)
states=retro/'states/widescreen';states.mkdir(parents=True,exist_ok=True)
cfg=runtime/'earthbound-widescreen.cfg'
cfg.write_text('savefile_directory = "'+str(save_root/'retroarch')+'"\nsavestate_directory = "'+str(states)+'"\nsort_savefiles_enable = "true"\nsort_savefiles_by_content_enable = "true"\nsavefiles_in_content_dir = "false"\nsavestate_auto_load = "false"\ncore_options_path = "'+str(options)+'"\n')
if '--prepare' in sys.argv:
 print('EarthBound widescreen configuration ready:',cfg)
 raise SystemExit(0)
sys.path.insert(0,str(home/'.local/bin'))
from retroarch_session import run_session
# This core writes SRAM on content unload, not RetroArch's autosave timer.
with cfg.open('a') as f:
 f.write('network_cmd_enable = "true"\nnetwork_cmd_port = "55356"\n')
helper=home/'.local/bin/rom-save-alias-sync.py'
gate=home/'.local/bin/save-sync-gate.py'
stconf=next((p for p in [home/'.local/state/syncthing/config.xml',home/'.config/syncthing/config.xml'] if p.exists()),None)
def gatecheck(phase):
 if gate.exists() and stconf:subprocess.run([sys.executable,str(gate),phase,'--config',str(stconf),'--ui','zenity'],check=False)
gatecheck('pre')
if helper.exists():subprocess.run([sys.executable,str(helper)],stdout=subprocess.DEVNULL)
try:result=run_session(['/usr/bin/flatpak','run','org.libretro.RetroArch','--appendconfig='+str(cfg),'-L',str(core),str(rom)],55356)
finally:
 if helper.exists():subprocess.run([sys.executable,str(helper)],stdout=subprocess.DEVNULL)
 gatecheck('post')
raise SystemExit(result)
