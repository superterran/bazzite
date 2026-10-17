#!/usr/bin/env python3
"""Bridge RetroArch iOS cloud sync (iCloud Drive) <-> the Syncthing rom-saves fleet. Runs on the Air.

RetroArch on the phone syncs saves/<Core>/<Game>.srm into its iCloud container and keeps
manifest.server = [{path, hash: md5}] describing that remote copy. RetroArch does a three-way
diff (server manifest / last-synced manifest / local file): a file whose server hash changed
while the phone's copy did not is downloaded; if both changed it is a conflict and left alone.

Each phone save maps to a game group in rom-saves/.save-aliases.json via its core + name
(alias paths are retroarch/<Core>/<system>/<Game>.srm). The bridge keeps a member copy at
ios/<Core>/<Game>.srm in that group, using the same size/offset rule as the matching alias, and
rom-save-alias-sync.py (run after this) fans changes between it and every other device.

  phone changed, member unchanged  -> copy phone file into ios/ member
  member changed, phone unchanged  -> write phone file + update manifest.server hash
  both changed                     -> leave both, report conflict (versions are kept everywhere)
First run (no state) treats the fleet as current: members are seeded from the group's
canonical save and pushed to the phone, never the reverse.
"""
import argparse,hashlib,json,os,shutil,time
from pathlib import Path

md5=lambda b:hashlib.md5(b).hexdigest()

def atomic(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.bridge-tmp');t.write_bytes(data);t.replace(p)

def main():
 a=argparse.ArgumentParser()
 a.add_argument('--icloud',default=os.path.expanduser('~/Library/Mobile Documents/iCloud~com~libretro~dist~RetroArch/Documents'))
 a.add_argument('--saves',default=os.path.expanduser('~/RomSaves'))
 a.add_argument('--state',default=os.path.expanduser('~/.local/state/ios-retroarch-bridge.json'))
 a.add_argument('--dry-run',action='store_true')
 a.add_argument('--reconcile',action='store_true',help='then run rom-save-alias-sync.py (same process tree, so one macOS privacy grant covers both)')
 a=a.parse_args()
 try:run(a)
 finally:
  if a.reconcile and not a.dry_run:
   import subprocess,sys
   subprocess.run([sys.executable,str(Path(__file__).with_name('rom-save-alias-sync.py')),'--root',a.saves,'--state',os.path.expanduser('~/.local/state/rom-save-alias-sync.json')])

def run(a):
 ic=Path(a.icloud);rs=Path(a.saves);statep=Path(a.state)
 spec_p=rs/'.save-aliases.json';man_p=ic/'manifest.server'
 if not spec_p.exists() or not man_p.exists():print(json.dumps({'status':'waiting','why':'saves or manifest not present yet'}));return
 spec=json.loads(spec_p.read_text());manifest=json.loads(man_p.read_text())
 first=not statep.exists();state=json.loads(statep.read_text()) if not first else {}
 # (core, game) -> (group, rule of the matching alias)
 index={}
 for g in spec['groups']:
  for r in [g['canonical']]+g['aliases']:
   parts=r['path'].split('/')
   if len(parts)==4 and parts[0]=='retroarch':index.setdefault((parts[1],Path(parts[3]).stem),[]).append((g,r))
 report={'pushed_to_phone':[],'pulled_from_phone':[],'linked':[],'conflicts':[],'unmatched':[]}
 spec_dirty=False;man_dirty=False
 phone_saves=[p for p in (ic/'saves').rglob('*.srm') if p.is_file()]
 for p in phone_saves:
  rel=str(p.relative_to(ic));parts=rel.split('/')
  if len(parts)!=3:continue
  core,game=parts[1],Path(parts[2]).stem
  hits={g['id']:(g,r) for g,r in index.get((core,game),[])}
  if len(hits)!=1:report['unmatched'].append(rel);continue
  g,rule=next(iter(hits.values()))
  member=f'ios/{core}/{parts[2]}'
  if not any(x['path']==member for x in g['aliases']):
   g['aliases'].append({k:v for k,v in rule.items() if k!='path'}|{'path':member});spec_dirty=True;report['linked'].append(rel)
  mp=rs/member;phone=p.read_bytes();ph=md5(phone);st=state.get(rel,{})
  if first or not mp.exists():
   # seed member from the fleet's current save so the reconciler never treats the old phone file as new
   src=next((rs/x['path'] for x in [g['canonical']]+g['aliases'] if x['path']!=member and (rs/x['path']).is_file() and (rs/x['path']).stat().st_size==len(phone)),None)
   data=src.read_bytes() if src else phone
   if not a.dry_run:atomic(mp,data)
   st={'phone':ph,'member':md5(data)}
  mem=mp.read_bytes() if mp.exists() else b'';mh=md5(mem)
  phone_changed=ph!=st.get('phone');member_changed=mh!=st.get('member')
  if phone_changed and member_changed and ph!=mh:
   report['conflicts'].append(rel)
  elif phone_changed and ph!=mh:
   if not a.dry_run:atomic(mp,phone)
   st={'phone':ph,'member':ph};report['pulled_from_phone'].append(rel)
  elif mh!=ph and (member_changed or first):
   if not a.dry_run:
    backup=statep.parent/'ios-bridge-backups'/f'{ph}-{parts[2]}';backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():backup.write_bytes(phone)
    atomic(p,mem)
   for e in manifest:
    if e['path']==rel:e['hash']=mh
   man_dirty=True;st={'phone':mh,'member':mh};report['pushed_to_phone'].append(rel)
  else:st={'phone':ph,'member':mh}
  state[rel]=st
 if not a.dry_run:
  if spec_dirty:atomic(spec_p,json.dumps(spec,indent=2).encode())
  if man_dirty:
   manifest.sort(key=lambda e:e['path'].encode())
   atomic(man_p,(json.dumps(manifest,indent=2)+'\n').encode())
  statep.parent.mkdir(parents=True,exist_ok=True);atomic(statep,json.dumps(state,indent=1).encode())
 report['status']='dry-run' if a.dry_run else 'ok';report['checked']=len(phone_saves);report['time']=time.strftime('%F %T')
 print(json.dumps(report))

if __name__=='__main__':main()
