#!/usr/bin/env python3
"""Configure the fleet's versioned save share using the local Syncthing API."""
import argparse,json,os,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--config',required=True)
p.add_argument('--path',required=True)
p.add_argument('--host-path')
p.add_argument('--peer',action='append',required=True)
p.add_argument('--receive-only',action='store_true')
p.add_argument('--owner',type=int)
a=p.parse_args()
root=Path(a.host_path or a.path).expanduser()
root.mkdir(parents=True,exist_ok=True)
if a.owner is not None:os.chown(root,a.owner,a.owner)
key=ET.parse(Path(a.config).expanduser()).findtext('gui/apikey')
def api(route,data=None,method=None):
 req=urllib.request.Request('http://127.0.0.1:8384/rest/'+route,
  data=None if data is None else json.dumps(data).encode(),
  headers={'X-API-Key':key,'Content-Type':'application/json'},method=method)
 with urllib.request.urlopen(req,timeout=30) as r:
  b=r.read();return json.loads(b) if b else None
existing=next((f for f in api('config/folders') if f['id']=='rom-saves'),None)
if existing and Path(existing['path']).expanduser()!=Path(a.path).expanduser():
 raise SystemExit('Existing save share has a different path; review before changing it.')
folder=existing or api('config/defaults/folder')
folder.update(id='rom-saves',label='ROM Saves',path=a.path,
 type='receiveonly' if a.receive_only else 'sendreceive',ignorePerms=True,
 devices=[{'deviceID':d} for d in a.peer],rescanIntervalS=60,
 versioning={'type':'simple','params':{'keep':'30'},'cleanupIntervalS':3600,'fsType':'basic','fsPath':''})
api('config/folders/rom-saves' if existing else 'config/folders',folder,'PUT' if existing else 'POST')
print(json.dumps({'folder':'rom-saves','path':a.path,'type':folder['type'],'versionHistory':30}))
