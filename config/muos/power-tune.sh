#!/bin/sh
# Anbernic battery tuning (2026-10-16): fewer background wakeups.
set -u
H=/mnt/mmc/MUOS/init/gaming-sync-status.sh
cp -p "$H" "$H.bak-powertune" 2>/dev/null
# save reconciler: launch hook already runs it around every game; drop the 15 s watch loop
sed -i 's|--state /mnt/mmc/MUOS/sync-status/save-alias-state.json --watch >/tmp/gaming-save-watch.log 2>&1 &|--state /mnt/mmc/MUOS/sync-status/save-alias-state.json >/tmp/gaming-save-watch.log 2>\&1|' "$H"
# artwork: copy once per boot instead of rescanning every 5 minutes
sed -i 's|sync-artwork.py --watch >|sync-artwork.py >|' "$H"
# favorites: every 10 minutes
sed -i 's|--device anbernic --watch 120|--device anbernic --watch 600|' "$H"
for p in $(pgrep -f "rom-save-alias-sync.py.*--watch") $(pgrep -f "sync-artwork.py --watch") $(pgrep -f "sync-status/favorites-sync.py"); do kill "$p" 2>/dev/null; done
setsid /usr/bin/python3 /mnt/mmc/MUOS/sync-status/favorites-sync.py --frontend muos --shared /mnt/mmc/MUOS/shared-saves --device anbernic --watch 600 >/tmp/gaming-favorites.log 2>&1 </dev/null &
# Syncthing: full rescans daily for the big read-only folders (changes still arrive immediately)
python3 - <<'P'
import json,urllib.request,xml.etree.ElementTree as ET
k=ET.parse("/run/muos/storage/syncthing/config.xml").getroot().findtext("gui/apikey")
for port in (8384,7070):
  try:
    b=f"http://127.0.0.1:{port}/rest"
    def api(m,p,body=None):
      r=urllib.request.Request(b+p,method=m,data=json.dumps(body).encode() if body is not None else None,headers={"X-API-Key":k,"Content-Type":"application/json"})
      t=urllib.request.urlopen(r,timeout=20).read();return json.loads(t) if t else None
    for fid in ("rom-library","rom-artwork"):
      f=api("GET",f"/config/folders/{fid}");f["rescanIntervalS"]=86400;api("PUT",f"/config/folders/{fid}",f)
    print("syncthing rescans set to daily via",port);break
  except Exception as e: continue
P
grep -nE "alias-sync|sync-artwork|favorites-sync" "$H"
echo "background python loops now:"; pgrep -fa python3 | grep -v pgrep | cut -c1-120
