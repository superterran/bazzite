#!/usr/bin/env python3
"""Read-only Syncthing status for muOS and other fleet devices."""
import argparse,json,urllib.request,urllib.parse,xml.etree.ElementTree as E
from pathlib import Path
from datetime import datetime
def collect(config):
 root=E.parse(config).getroot();key=root.findtext('gui/apikey')
 address=root.findtext('gui/address','127.0.0.1:8384');port=address.rsplit(':',1)[-1]
 def api(route):
  for candidate in dict.fromkeys([port,'7070']):
   try:
    req=urllib.request.Request('http://127.0.0.1:'+candidate+'/rest/'+route,headers={'X-API-Key':key})
    with urllib.request.urlopen(req,timeout=3) as response:return json.load(response)
   except urllib.error.URLError as error:last_error=error
  raise last_error
 folders=api('config/folders');devices={d['deviceID']:d.get('name') or 'Device' for d in api('config/devices')}
 connections=api('system/connections')['connections'];result={'checked':datetime.now().strftime('%H:%M:%S'),'connected':[devices.get(i,'Device') for i,c in connections.items() if c.get('connected')],'folders':{}}
 for folder in folders:
  if folder['id'] not in ['rom-library','rom-artwork','rom-saves']:continue
  s=api('db/status?folder='+urllib.parse.quote(folder['id']))
  result['folders'][folder['id']]={k:s.get(k,0) for k in ['state','needFiles','needBytes','pullErrors','receiveOnlyChangedFiles']}
  result['folders'][folder['id']]['paused']=folder.get('paused',False)
 return result
def summary(s,connected=True):
 if s['paused']:return 'Paused'
 if s['pullErrors']:return 'Sync error - check management'
 if s['receiveOnlyChangedFiles']:return 'Local changes need review'
 if s['needFiles']:return str(s['needFiles'])+' files left ('+str(round(s['needBytes']/1048576,1))+' MB)'
 if s['state']=='idle':return 'Up to date' if connected else 'Waiting for connection'
 return s['state'].replace('-',' ').capitalize()
def render(d):
 lines=['SYNCTHING STATUS  '+d['checked'],'','Connected: '+(', '.join(d['connected']) or 'No peers - offline')]
 for fid,title in [('rom-library','ROMs'),('rom-artwork','Artwork'),('rom-saves','Saves')]:
  lines+=['',title+': '+(summary(d['folders'][fid],bool(d['connected'])) if fid in d['folders'] else 'Not configured')]
 bridge=Path('/mnt/mmc/MUOS/sync-status/save-alias-status.json')
 if bridge.exists():
  try:
   b=json.loads(bridge.read_text());lines+=['','Save mapping: '+b.get('status','Unknown')]
   if b.get('skipped_games'):lines+=['Playing: '+', '.join(dict.fromkeys(b['skipped_games']))]
  except (OSError,ValueError):pass
 lines+=['','Status refreshes every 5 seconds.','Returns to Task Toolkit after 20 seconds.']
 return '\n'.join(lines)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',default='/run/muos/storage/syncthing/config.xml');p.add_argument('--json',action='store_true');p.add_argument('--clear',action='store_true');args=p.parse_args()
 if args.clear:print('\033[2J\033[H',end='',flush=True)
 try:
  d=collect(args.config);print(json.dumps(d) if args.json else render(d),flush=True)
 except Exception:
  print('SYNCTHING STATUS\n\nSyncthing unavailable.\nCheck Wi-Fi and enabled Web Services.\nNo files were changed.',flush=True)
