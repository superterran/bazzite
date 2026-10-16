#!/usr/bin/env python3
"""Sync game favorites across ES-DE (desktop, Ally) and muOS (Anbernic).

Each device appends only to its own file in the shared saves folder
(<shared>/favorites/<device>.json: {key: [favorite, unix_time]}), so Syncthing
never sees conflicting writes. Every run:
  1. read local favorites, diff against the last run, record changes with a timestamp;
  2. merge all devices' files, newest change per game wins (so un-favoriting syncs too);
  3. apply the merged result locally (ES-DE only while ES-DE is closed, since it
     rewrites gamelists itself while running).
Keys are paths relative to the shared ROM library root, e.g. systems/arcade/mspacman.zip.
"""
import argparse,json,os,re,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path

def load(p,default):
 try:return json.loads(Path(p).read_text())
 except Exception:return default

def save(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp')
 tmp.write_text(json.dumps(data,indent=1,sort_keys=True));tmp.replace(p)

class ESDE:
 def __init__(s,home,library):
  s.home=Path(home);s.library=Path(library)
  root=ET.parse(s.home/'custom_systems/es_systems.xml').getroot()
  s.systems={x.findtext('name'):x.findtext('path').replace('%ROMPATH%/','') for x in root}
 def can_apply(s):
  return subprocess.run(['pgrep','-x','es-de'],stdout=subprocess.DEVNULL).returncode!=0
 def _games(s):
  for name,rel in s.systems.items():
   gl=s.home/'gamelists'/name/'gamelist.xml'
   yield name,rel,gl
 def _key(s,rel,path):
  p=path[2:] if path.startswith('./') else os.path.relpath(path,s.library/rel)
  return f'{rel}/{p}'
 def read(s):
  fav=set()
  for name,rel,gl in s._games():
   if not gl.exists():continue
   for g in ET.parse(gl).getroot().findall('game'):
    if (g.findtext('favorite') or '').strip()=='true':fav.add(s._key(rel,g.findtext('path','')))
  return fav
 def apply(s,want):
  changed=[]
  for name,rel,gl in s._games():
   mine={k:v for k,v in want.items() if k.startswith(rel+'/') and '/' not in k[len(rel)+1:]}
   if not mine:continue
   if not gl.exists():
    gl.parent.mkdir(parents=True,exist_ok=True);gl.write_text('<?xml version="1.0"?>\n<gameList>\n</gameList>\n')
   tree=ET.parse(gl);root=tree.getroot();seen=set();dirty=False
   for g in root.findall('game'):
    k=s._key(rel,g.findtext('path',''));seen.add(k)
    if k not in mine:continue
    node=g.find('favorite');cur=node is not None and (node.text or '').strip()=='true'
    if mine[k] and not cur:
     if node is None:node=ET.SubElement(g,'favorite')
     node.text='true';dirty=True;changed.append(('+',k))
    elif not mine[k] and cur:
     g.remove(node);dirty=True;changed.append(('-',k))
   for k,v in mine.items():
    f=k[len(rel)+1:]
    if v and k not in seen and (s.library/rel/f).exists():
     g=ET.SubElement(root,'game');ET.SubElement(g,'path').text='./'+f;ET.SubElement(g,'favorite').text='true'
     dirty=True;changed.append(('+',k))
   if dirty:
    ET.indent(tree);tmp=gl.with_suffix('.tmp');tree.write(tmp,encoding='unicode',xml_declaration=True);tmp.replace(gl)
  return changed

class MuOS:
 # plain ASCII folder name: the exFAT card mangles symbols like the star
 COLL=Path('/mnt/mmc/MUOS/info/collection/Favorites');ROMS='/mnt/union/ROMS/'
 def can_apply(s):return True
 def _key(s,path):
  rel=path[len(s.ROMS):] if path.startswith(s.ROMS) else path
  top=rel.split('/',1)[0]
  return ('systems/'+rel) if top==top.lower() else 'anbernic/'+rel   # lowercase dirs are the shared library
 def _path(s,key):
  if key.startswith('systems/'):return s.ROMS+key[len('systems/'):]
  if key.startswith('anbernic/'):return s.ROMS+key[len('anbernic/'):]
  return None
 def _entries(s):
  out={}
  if s.COLL.exists():
   for f in s.COLL.glob('*.cfg'):
    lines=f.read_text().split('\n')
    if lines and lines[0]:out[s._key(lines[0])]=f
  return out
 def read(s):return set(s._entries())
 def apply(s,want):
  have=s._entries();changed=[];s.COLL.mkdir(parents=True,exist_ok=True)
  for k,v in want.items():
   if v and k not in have:
    p=s._path(k)
    if not p or not Path(p).exists():continue
    rel=os.path.dirname(p)[len(s.ROMS):];stem=os.path.basename(p).rsplit('.',1)[0]
    h=2166136261
    for b in p.encode():h=((h^b)*16777619)&0xffffffff
    (s.COLL/f'{stem}-{h:08X}.cfg').write_text(f'{p}\n{rel}\n{stem}');changed.append(('+',k))
   elif not v and k in have:
    have[k].unlink();changed.append(('-',k))
  return changed

def run(adapter,shared,device,state):
 now=int(time.time());fav=adapter.read();last=set(load(state,{}).get('last',[]))
 mine_p=Path(shared)/'favorites'/f'{device}.json';mine=load(mine_p,{})
 first=not Path(state).exists()
 for k in fav-last:mine[k]=[True,now]
 for k in (last-fav) if not first else ():mine[k]=[False,now]
 save(mine_p,mine)
 merged={}
 for f in (Path(shared)/'favorites').glob('*.json'):
  for k,(v,t) in load(f,{}).items():
   if k not in merged or t>merged[k][1]:merged[k]=(v,t)
 want={k:v for k,(v,t) in merged.items()}
 changed=[]
 if adapter.can_apply():
  changed=adapter.apply(want);fav=adapter.read()
 save(state,{'last':sorted(fav),'updated':now})
 return {'device':device,'local_favorites':len(fav),'applied':changed,'deferred':not adapter.can_apply()}

def main():
 a=argparse.ArgumentParser();a.add_argument('--frontend',choices=['esde','muos'],required=True)
 a.add_argument('--shared',required=True,help='Syncthing rom-saves folder');a.add_argument('--device',required=True)
 a.add_argument('--esde-home',default=str(Path.home()/'ES-DE'));a.add_argument('--library',default='/var/mnt/fast/rom-library')
 a.add_argument('--state');a.add_argument('--watch',type=int,default=0,help='repeat every N seconds')
 a=a.parse_args()
 state=a.state or str(Path.home()/'.local/state/favorites-sync.json') if a.frontend=='esde' else (a.state or '/mnt/mmc/MUOS/sync-status/favorites-state.json')
 adapter=ESDE(a.esde_home,a.library) if a.frontend=='esde' else MuOS()
 while True:
  r=run(adapter,a.shared,a.device,state)
  if r['applied'] or not a.watch:print(json.dumps(r),flush=True)
  if not a.watch:break
  time.sleep(a.watch)

if __name__=='__main__':main()
