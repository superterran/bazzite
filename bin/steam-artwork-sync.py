#!/usr/bin/env python3
"""Share Steam artwork by title, preserving each machine's shortcut IDs."""
import argparse,base64,hashlib,json,os,re,shutil,socket,struct,time,unicodedata
from pathlib import Path
from steam_client import evaluate

ROLES={'portrait':'p','landscape':'','hero':'_hero','logo':'_logo','icon':'_icon','layout':''}
TYPES={'portrait':0,'landscape':3,'hero':1,'logo':2}
def shortcuts(path):
 data=path.read_bytes();index=0
 def string():
  nonlocal index
  end=data.index(0,index);value=data[index:end].decode(errors='replace');index=end+1;return value
 def obj():
  nonlocal index
  result={}
  while index<len(data):
   kind=data[index];index+=1
   if kind==8:return result
   key=string()
   if kind==0:value=obj()
   elif kind==1:value=string()
   elif kind==2:value=struct.unpack_from('<I',data,index)[0];index+=4
   elif kind==7:value=struct.unpack_from('<Q',data,index)[0];index+=8
   else:raise ValueError('Unsupported Steam shortcut field')
   result[key]=value
  return result
 return list(obj().get('shortcuts',{}).values())
def identity(title):
 normalized=unicodedata.normalize('NFKC',title).replace('’',"'").casefold().strip()
 slug=re.sub(r'[^a-z0-9]+','-',normalized).strip('-')[:70]
 return slug+'--'+hashlib.sha256(normalized.encode()).hexdigest()[:10]
def atomic_json(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)
def digest(path):return hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
def sync(shared,user_id):
 home=Path.home();config=home/'.local/share/Steam/userdata'/user_id/'config'
 entries=shortcuts(config/'shortcuts.vdf');grid=config/'grid';grid.mkdir(exist_ok=True)
 host=socket.gethostname();root=shared/'steam';assets=root/'assets'
 mapping={str(e['appid']):{'title':e['AppName'],'key':identity(e['AppName'])} for e in entries}
 atomic_json(root/'devices'/(host+'.json'),mapping)
 all_mapping={}
 for f in (root/'devices').glob('*.json'):
  try:all_mapping.update(json.loads(f.read_text()))
  except (ValueError,OSError):continue
 statepath=home/'.local/state/steam-artwork-sync.json'
 state=json.loads(statepath.read_text()) if statepath.exists() else {'files':{},'icons':{}}
 local={};exported=0;applied=0;ui=[]
 for f in grid.iterdir():
  m=re.fullmatch(r'(\d+)(p|_hero|_logo|_icon)?\.(png|jpg|jpeg|webp|ico|json)',f.name,re.I)
  if not m:continue
  appid,suffix,ext=m.groups();role='layout' if ext=='json' else next(k for k,v in ROLES.items() if k!='layout' and v==(suffix or ''))
  if int(appid)>0xffffffff:appid=str((int(appid)>>32)&0xffffffff)
  key=all_mapping.get(appid,{}).get('key')
  if key is None:
   if int(appid)>=0x80000000:continue
   key='steam-'+appid
  local.setdefault((key,role),[]).append((f,appid))
 for e in entries:
  icon=Path(e.get('icon','').strip('"')).expanduser()
  if icon.is_file() and icon.suffix.lower() in ['.png','.jpg','.jpeg','.webp','.ico']:
   local.setdefault((identity(e['AppName']),'icon'),[]).append((icon,str(e['appid'])))
 for (key,role),files in local.items():
  f,appid=max(files,key=lambda v:v[0].stat().st_mtime_ns)
  stamp=f.stat().st_mtime_ns;size=f.stat().st_size;statekey=key+'/'+role
  old=state['files'].get(statekey,{})
  if old.get('mtime')==stamp and old.get('size')==size:sha=old['sha']
  else:sha=digest(f)
  if old.get('sha')!=sha:
   directory=assets/key/role;directory.mkdir(parents=True,exist_ok=True)
   dest=directory/(sha+f.suffix.lower())
   if not dest.exists():shutil.copy2(f,dest)
   candidate=directory/(str(stamp)+'-'+sha[:12]+'-'+host+'.json')
   if role=='layout':candidate=candidate.with_name(candidate.stem+'.meta.json')
   atomic_json(candidate,{'sha':sha,'file':dest.name,'timestamp':stamp,'source':host})
   exported+=1
  state['files'][statekey]={'sha':sha,'mtime':stamp,'size':size}
 keys={v['key']:k for k,v in mapping.items()}
 for directory in assets.iterdir() if assets.exists() else []:
  appid=keys.get(directory.name)
  if appid is None:
   if not directory.name.startswith('steam-'):continue
   appid=directory.name[6:]
  for role,suffix in ROLES.items():
   rd=directory/role
   if not rd.exists():continue
   candidates=[]
   for f in rd.glob('*.json'):
    try:
     data=json.loads(f.read_text())
     if 'file' in data and (rd/data['file']).is_file():candidates.append(data)
    except (ValueError,OSError):continue
   if not candidates:continue
   best=max(candidates,key=lambda v:(v['timestamp'],v['sha']))
   src=rd/best['file'];dest=grid/(appid+suffix+src.suffix)
   current=local.get((directory.name,role),[])
   current_sha=digest(max(current,key=lambda v:v[0].stat().st_mtime_ns)[0]) if current else None
   if current_sha!=best['sha'] or not dest.exists():
    for f in grid.glob(appid+suffix+'.*'):
     if (f.suffix=='.json')==(role=='layout') and f!=dest:f.unlink()
    shutil.copy2(src,dest);applied+=1
    if role in TYPES and src.suffix in ['.png','.jpg','.jpeg']:
     ui.append({'id':int(appid),'role':role,'data':base64.b64encode(src.read_bytes()).decode(),'format':'jpg' if src.suffix in ['.jpg','.jpeg'] else 'png'})
   if role=='icon' and appid in mapping and state['icons'].get(appid)!=str(dest):
    ui.append({'id':int(appid),'role':'icon','path':str(dest)})
   state['files'][directory.name+'/'+role]={'sha':best['sha'],'mtime':dest.stat().st_mtime_ns if dest.exists() else src.stat().st_mtime_ns,'size':src.stat().st_size}
 if ui:
  try:
   for offset in range(0,len(ui),8):
    chunk=ui[offset:offset+8]
    expr='(async()=>{for(const a of '+json.dumps(chunk)+'){if(a.role==="icon")SteamClient.Apps.SetShortcutIcon(a.id,a.path);else await SteamClient.Apps.SetCustomArtworkForApp(a.id,a.data,a.format,'+json.dumps(TYPES)+'[a.role]);}return true;})()'
    evaluate(expr,timeout=40)
    for item in chunk:
     if item['role']=='icon':state['icons'][str(item['id'])]=item['path']
  except Exception as e:print('Steam artwork refresh deferred:',type(e).__name__)
 atomic_json(statepath,state)
 print(json.dumps({'host':host,'shortcuts':len(entries),'exported':exported,'applied':applied}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--shared');p.add_argument('--user-id',default='35894255');a=p.parse_args()
 if not a.shared:a.shared=json.loads((Path.home()/'.config/steam-artwork-sync.json').read_text())['shared']
 sync(Path(a.shared).expanduser(),a.user_id)
