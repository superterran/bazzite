#!/usr/bin/env python3
"""Publish synced artwork to muOS's active catalogue without replacing newer local art."""
from pathlib import Path
import argparse,fcntl,shutil,time,json
p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');a=p.parse_args()
lock=open('/tmp/gaming-artwork-sync.lock','w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit(0)
root=Path('/mnt/mmc/MUOS/info');source=root/'shared-artwork/muos';target=root/'catalogue'
while True:
 count=0
 for src in source.rglob('*'):
  if not src.is_file() or src.suffix.lower() not in ['.png','.txt']:continue
  dest=target/src.relative_to(source)
  if dest.exists() and dest.stat().st_mtime_ns>=src.stat().st_mtime_ns:continue
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);count+=1
 (root/'shared-artwork-status.json').write_text(json.dumps({'updated_at':time.time(),'copied':count}))
 if not a.watch:break
 time.sleep(300)
