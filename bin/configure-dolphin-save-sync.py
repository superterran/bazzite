#!/usr/bin/env python3
"""Back up and link Dolphin's per-game memory-card files into the save share."""
import argparse, hashlib, json, shutil, subprocess
from datetime import datetime
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--save-root',required=True)
a=p.parse_args()
if subprocess.run(['pgrep','-x','dolphin-emu'],stdout=subprocess.DEVNULL).returncode==0:
 raise SystemExit('Close Dolphin before connecting its save folders.')
shared=Path(a.save_root).expanduser().resolve()
base=Path.home()/'.var/app/org.DolphinEmu.dolphin-emu'
gc=base/'data/dolphin-emu/GC'
backup=base/'save-backups'/datetime.now().strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True,exist_ok=True)
if gc.exists():shutil.copytree(gc,backup/'GC',symlinks=False)
config=base/'config/dolphin-emu/Dolphin.ini'
if config.exists():shutil.copy2(config,backup/'Dolphin.ini')
links=[]
for region in ['USA','EUR','JAP']:
 for slot in ['Card A','Card B']:
  source=gc/region/slot;dest=shared/'dolphin/GC'/region/slot
  dest.mkdir(parents=True,exist_ok=True)
  if source.is_symlink():
   if source.resolve()!=dest:raise SystemExit('Unexpected existing save link: '+str(source))
   continue
  if source.exists():
   for f in source.iterdir():
    if not f.is_file():raise SystemExit('Unexpected memory-card entry: '+str(f))
    target=dest/f.name
    if target.exists():
     left=hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
     right=hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
     if left!=right:raise SystemExit('Save conflict preserved for review: '+str(f))
    else:shutil.copy2(f,target)
   source.rename(backup/(region+'-'+slot))
  source.parent.mkdir(parents=True,exist_ok=True)
  source.symlink_to(dest,target_is_directory=True)
  links.append(str(source))
print(json.dumps({'backup':str(backup),'save_root':str(shared),'links':links}))
