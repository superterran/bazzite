#!/usr/bin/env python3
"""Hold a game launch until saves are synced, and hold the return until they are uploaded.

  pre   rescan the saves folder and wait until nothing is pending from peers
  post  rescan, then wait until the hub (closet) reports it has every local change

Offline (no peer connected) never blocks: it says so briefly and carries on.
Conflict copies (*.sync-conflict-*) found in the saves folder are announced.
Messages: muOS muxmessage, zenity on the desktop/Ally, or plain stdout.
"""
import argparse,json,os,subprocess,sys,time,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path

HUB='UJYM53V-CHNNOJK-JZQUZGK-FNMVQUD-25BJF4T-RQEVL7C-GKL3ZSU-RQUNTQS'  # closet, always on

class UI:
 def __init__(s,kind):s.kind=kind;s.proc=None
 def show(s,text,seconds=0):
  s.close()
  if s.kind=='muos':
   s.proc=subprocess.Popen(['/opt/muos/frontend/muxmessage','0',text],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  elif s.kind=='zenity' and os.path.exists('/usr/bin/zenity'):
   s.proc=subprocess.Popen(['/usr/bin/zenity','--progress','--pulsate','--no-cancel','--auto-close','--title=Saves','--text='+text],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  print(text,flush=True)
  if seconds:time.sleep(seconds);s.close()
 def close(s):
  if s.proc and s.proc.poll() is None:
   try:s.proc.terminate();s.proc.wait(2)
   except Exception:pass
  s.proc=None

class Syncthing:
 def __init__(s,config):
  root=ET.parse(config).getroot();s.key=root.findtext('gui/apikey')
  addr=root.findtext('gui/address') or '127.0.0.1:8384'
  port=addr.rsplit(':',1)[1]
  s.bases=[f'http://127.0.0.1:{port}/rest','http://[::1]:7070/rest','http://127.0.0.1:7070/rest','http://127.0.0.1:8384/rest']
  s.base=None
 def req(s,path,method='GET'):
  for b in ([s.base] if s.base else s.bases):
   try:
    r=urllib.request.Request(b+path,method=method,headers={'X-API-Key':s.key})
    with urllib.request.urlopen(r,timeout=5) as f:
     s.base=b;t=f.read();return json.loads(t) if t else {}
   except Exception:continue
  raise RuntimeError('Syncthing API unreachable')

def peers(st,folder):
 devs=[d['deviceID'] for d in st.req(f'/config/folders/{folder}')['devices']]
 conns=st.req('/system/connections')['connections']
 return [d for d in devs if conns.get(d,{}).get('connected')]

def wait(cond,timeout,step=1.0):
 end=time.time()+timeout
 while time.time()<end:
  if cond():return True
  time.sleep(step)
 return False

def local_settled(st,folder):
 s=st.req(f'/db/status?folder={folder}')
 return s.get('state')=='idle' and not s.get('needFiles') and not s.get('needDeletes')

def conflicts(st,folder,since):
 path=Path(st.req(f'/config/folders/{folder}')['path'])
 return [p for p in path.rglob('*.sync-conflict-*') if p.stat().st_mtime>=since]

def main():
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['pre','post'])
 a.add_argument('--config',required=True);a.add_argument('--folder',default='rom-saves')
 a.add_argument('--ui',choices=['muos','zenity','none'],default='none');a.add_argument('--timeout',type=int,default=30)
 a=a.parse_args();ui=UI(a.ui);t0=time.time()
 try:
  st=Syncthing(a.config);online=peers(st,a.folder)
 except Exception as e:
  ui.show('Save sync is not running — playing with this device\'s saves.',2);return
 if not online:
  ui.show('Offline — '+('using the saves on this device.' if a.phase=='pre' else 'your save stays here and syncs when Wi-Fi is back.'),2);return
 st.req(f'/db/scan?folder={a.folder}','POST');time.sleep(0.5)
 target=HUB if HUB in online else online[0]
 def uploaded():
  c=st.req(f'/db/completion?folder={a.folder}&device={target}')
  return c.get('completion',0)>=100 and not c.get('needItems') and not c.get('needDeletes')
 done=(lambda:local_settled(st,a.folder)) if a.phase=='pre' else (lambda:local_settled(st,a.folder) and uploaded())
 # Only put a message on screen if the wait is noticeable.
 ok=wait(done,1.5,0.25)
 if not ok:
  ui.show('Syncing saves…' if a.phase=='pre' else 'Uploading saves…')
  ok=wait(done,a.timeout if a.phase=='pre' else max(a.timeout,60))
 ui.close()
 if not ok:
  ui.show('Saves are still syncing in the background.' if a.phase=='post' else 'Could not finish syncing — starting with the newest save here.',2)
 found=conflicts(st,a.folder,t0-600) if a.phase=='post' else []
 if found:
  ui.show(f'Save conflict: kept both copies ({found[0].name}). Ask Doug to check.',4)
 print(json.dumps({'phase':a.phase,'online':len(online),'ok':ok,'seconds':round(time.time()-t0,1),'conflicts':len(found)}),flush=True)

if __name__=='__main__':main()
