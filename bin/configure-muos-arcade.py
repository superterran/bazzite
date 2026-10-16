#!/usr/bin/env python3
"""Run on the muOS Anbernic: per-game arcade cores and the Pac-Man collection.

Reads shared-artwork/muos/arcade-cores.json (published by build-arcade-library.py).
Games listed under mame2003_plus get a content-level core.cfg next to the folder
default (FinalBurn Neo). Collection entries mimic muOS's own writer
(<name>-<FNV1a(path)>.cfg holding path, system dir, name).
"""
import json,tarfile,time
from pathlib import Path

INFO=Path('/opt/muos/share/info');STORE=Path('/mnt/mmc/MUOS/info')
ROMS=Path('/mnt/union/ROMS/arcade')  # flat layout: library systems are bind-mounted at the ROMS root
REL='arcade'
CORE_DIR=INFO/'core/arcade'
COLLECTION=STORE/'collection/Pac-Man'
WANT_CORE='mame2003_plus_libretro.so'

def fnv(s):
 h=2166136261
 for b in s.encode():h=((h^b)*16777619)&0xffffffff
 return h

def main():
 spec=json.loads((STORE/'shared-artwork/muos/arcade-cores.json').read_text())
 report={'core_overrides':[],'collection':[],'warnings':[]}
 base=(CORE_DIR/'core.cfg').read_text().splitlines()
 if not (Path('/opt/muos/share/core')/WANT_CORE).exists():
  raise SystemExit('MAME 2003-Plus core missing on device: '+WANT_CORE)
 choice=next((p.stem for p in (INFO/'assign'/base[1]).glob('*.ini') if WANT_CORE in p.read_text()),'mame2003 plus')
 stamp=time.strftime('%Y%m%d-%H%M%S');backup=STORE/'frontend-backups'/(stamp+'-arcade');backup.mkdir(parents=True,exist_ok=True)
 with tarfile.open(backup/'arcade.tar','w') as t:
  for p in [CORE_DIR,STORE/'collection']:
   if p.exists():t.add(p,arcname=str(p).lstrip('/'))
 for g in spec['mame2003_plus']:
  if not (ROMS/(g+'.zip')).exists():report['warnings'].append('missing rom '+g);continue
  # muOS 2508 content core file: name, core, system, catalogue, lookup, assign choice, mount, dir, file
  (CORE_DIR/(g+'.cfg')).write_text('\n'.join([g,WANT_CORE,base[1],base[2],base[3],choice,'/mnt/union/ROMS/',REL,g+'.zip']))
  report['core_overrides'].append(g)
 COLLECTION.mkdir(parents=True,exist_ok=True)
 for i,g in enumerate(spec['pacman_collection']):
  path=str(ROMS/(g+'.zip'))
  if not Path(path).exists():report['warnings'].append('missing rom '+g);continue
  (COLLECTION/f'{g}-{fnv(path):08X}.cfg').write_text(f'{path}\n{REL}\n{g}');report['collection'].append(g)
 report['backup']=str(backup);report['choice']=choice
 print(json.dumps(report,indent=1))

if __name__=='__main__':main()
