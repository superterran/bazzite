#!/usr/bin/env python3
"""Reconcile compatible battery-save aliases while protecting only the cartridge currently open in RetroArch."""
import argparse,fcntl,hashlib,json,os,shutil,socket,struct,subprocess,time,unicodedata
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.bridge-tmp');tmp.write_bytes(data);tmp.replace(path)
def read_payload(path,rule):
 if not path.is_file():return None
 data=path.read_bytes();offset=rule.get('offset',0);length=rule.get('length')
 if rule.get('size') and len(data)!=rule['size']:raise ValueError('unexpected save size: '+str(path))
 return data[offset:offset+length] if length is not None else data[offset:]
def valid_smw(data):
 if len(data)!=858:return False
 for i in range(6):
  b=data[i*143:(i+1)*143]
  if b==b'\xff'*143:continue
  if (sum(b[:141])+struct.unpack_from('<H',b,141)[0])&65535!=0x5a5a:return False
 return True

def content_key(name):
 return ''.join(c for c in unicodedata.normalize('NFKC',Path(name).stem).casefold() if c.isalnum())

def active_roms():
 """Return launched cartridge names; None means an active process is ambiguous."""
 pids=subprocess.run(['pgrep','-x','retroarch'],stdout=subprocess.PIPE,text=True)
 if pids.returncode==1:return set()
 if pids.returncode!=0:return None
 active=set()
 excluded={'.so','.dll','.dylib','.cfg','.opt','.log','.mkv','.mp4','.bsv','.png','.state'}
 for pid in pids.stdout.split():
  try:
   args=(Path('/proc')/pid/'cmdline').read_bytes().decode(errors='surrogateescape').split('\0')
  except FileNotFoundError:continue
  except OSError:return None
  # Options with attached values are not content. Ignore known non-ROM arguments.
  candidates=[arg for arg in args[1:] if arg and not arg.startswith('-') and
              Path(arg).suffix and Path(arg).suffix.lower() not in excluded]
  if not candidates:return None
  active.update(content_key(arg) for arg in candidates)
 return active

def reconcile(root,state_path,initialize=False,ignore_running=False):
 active=set() if ignore_running else active_roms()
 if active is None:
  status={'status':'Waiting: active RetroArch content could not be identified','updated':0,'conflicts':[],'errors':[],'skipped_games':[],'checked':time.time()}
  atomic(state_path.with_name('save-alias-status.json'),json.dumps(status).encode());return status
 spec=json.loads((root/'.save-aliases.json').read_text());state=json.loads(state_path.read_text()) if state_path.exists() else {};updated=0;conflicts=[];errors=[];skipped=[];host=socket.gethostname()
 # Avoid thousands of failed stats on the handheld's memory card.
 present={str(p.relative_to(root)):p for p in root.rglob('*.srm') if '.stversions' not in p.parts and '.bridge-backups' not in p.parts}
 backups=state_path.parent/'save-alias-backups'
 for group in spec['groups']:
  gid=group['id'];rules=[group['canonical']]+group['aliases'];old=state.get(gid,{});values={}
  names={content_key(rule['path']) for rule in rules}
  if group.get('name'):names.add(content_key(group['name']))
  if names & active:
   skipped.append(group.get('name',gid));continue
  try:
   if group.get('format')=='smw-sa1':
    for rule in rules:
     if rule.get('length')!=858 or (rule.get('size'),rule.get('offset')) not in [(2048,0),(131072,0x1c000)]:raise ValueError('Mario World save mapping is missing its verified format')
   for rule in rules:
    rel=rule['path'];p=present.get(rel)
    if p is None:continue
    payload=read_payload(p,rule)
    if group.get('format')=='smw-sa1' and (not initialize or rel==group['canonical']['path']) and not valid_smw(payload):raise ValueError('invalid Mario World save checksums: '+rel)
    values[rel]=(payload,sha(payload))
  except (ValueError,OSError) as e:errors.append({'game':gid,'reason':str(e)});continue
  if not values:continue
  if len({len(payload) for payload,digest in values.values()})>1:
   errors.append({'game':gid,'reason':'Different save sizes need review'});continue
  canonical=group['canonical']['path']
  if initialize and canonical in values:chosen=values[canonical][0]
  else:
   changed={digest:payload for rel,(payload,digest) in values.items() if old.get(rel)!=digest}
   if len(changed)>1:
    conflicts.append({'game':gid,'files':[{ 'path':rel,'sha256':digest} for rel,(payload,digest) in values.items()]});continue
   if changed:chosen=next(iter(changed.values()))
   else:
    digests={digest for payload,digest in values.values()}
    if len(digests)>1:conflicts.append({'game':gid,'reason':'Aliases differ'});continue
    chosen=next(iter(values.values()))[0]
  digest=sha(chosen);new={}
  for rule in rules:
   rel=rule['path'];dest=root/rel;current=values.get(rel)
   if current is None or current[1]!=digest:
    original=dest.read_bytes() if dest.is_file() else None
    if original is not None:
     backup=backups/gid/(sha(original)+'.srm');backup.parent.mkdir(parents=True,exist_ok=True)
     if not backup.exists():backup.write_bytes(original)
    if 'size' in rule:
     data=bytearray(original if original is not None else b'\xff'*rule['size']);offset=rule.get('offset',0)
     if len(data)!=rule['size'] or len(chosen)!=rule['length']:errors.append({'game':gid,'reason':'Save format mismatch for '+rel});continue
     data[offset:offset+len(chosen)]=chosen;atomic(dest,data)
    else:atomic(dest,chosen)
    present[rel]=dest;updated+=1
   new[rel]=digest
  state[gid]=new
 atomic(state_path,json.dumps(state,indent=2).encode())
 status={'status':'Needs review' if conflicts or errors else 'Waiting for active game to close' if skipped else 'Up to date','updated':updated,'conflicts':conflicts,'errors':errors,'skipped_games':skipped,'checked':time.time()}
 atomic(state_path.with_name('save-alias-status.json'),json.dumps(status,indent=2).encode());return status

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--state');p.add_argument('--watch',action='store_true');p.add_argument('--initialize',action='store_true');a=p.parse_args()
 if not a.root:
  c=json.loads((Path.home()/'.config/rom-save-alias-sync.json').read_text());a.root=c['root'];a.state=c.get('state')
 root=Path(a.root).expanduser();state=Path(a.state).expanduser() if a.state else Path.home()/'.local/state/rom-save-alias-sync.json';state.parent.mkdir(parents=True,exist_ok=True)
 lock=open(state.with_suffix('.lock'),'w')
 while True:
  fcntl.flock(lock,fcntl.LOCK_EX)
  try:print(json.dumps(reconcile(root,state,a.initialize)),flush=True);a.initialize=False
  finally:fcntl.flock(lock,fcntl.LOCK_UN)
  if not a.watch:break
  time.sleep(15)
