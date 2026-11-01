#!/usr/bin/python3
"""Verify independent Restic volume recovery and overwritten-file history."""
import importlib.util,json,os,resource,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/productivity-recovery')
def root(args,**kw):
 kw.setdefault('check',True);return subprocess.run(['sudo',*args],capture_output=True,**kw)
def restic(args,**kw):return root(['/usr/bin/python3',str(ROOT/'bin/productivity-restic.py'),*args],**kw)
def main():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 spec=importlib.util.spec_from_file_location('keys',ROOT/'bin/productivity-recovery-runtime.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);keys=module.recovery_keys()
 # Prove recovery using the independent 1Password key, not this host's credential.
 base=(ROOT/'bin/productivity-1password.cjs').read_text().split("const title = 'Desktop Encrypted GNOME';")[0]
 body="const i=op(['item','get','6kjfof6obrhbd5hblkbcxailgy','--vault',vault,'--format','json']);const f=i.fields.find(x=>x.id==='resticPassword');if(!f)throw Error('Missing repository key');process.stdout.write(f.value);"
 fetch=subprocess.run(['ssh','-o','BatchMode=yes','closet',"docker exec -i codex-rc sh -c 'ulimit -c 0; exec node -'"],input=(base+body).encode(),capture_output=True)
 if fetch.returncode:raise RuntimeError('Independent repository recovery key unavailable')
 config=json.loads(root(['cat','/etc/productivity-restic.json'],text=True).stdout)
 cmd=['restic','-r',config['repository'],'--password-file','/dev/stdin']
 for option in config['options']:cmd+=['-o',option]
 root([*cmd,'snapshots','--json'],input=fetch.stdout+b'\n');fetch=None
 receipt=json.loads(root(['cat',str(BASE/'desktop-latest.json')],text=True).stdout)
 snapshot=receipt['snapshot_id'];target=BASE/'restic-restore-test';mapping='restic-recovery-test-'+str(os.getpid());opened=False;mounted=False
 root(['install','-d','-m','700',str(target)])
 image_path='/var/lib/productivity-recovery/restic-capture/var/lib/productivity-volume/desktop-secure.luks'
 manifest_path='/var/lib/productivity-recovery/restic-capture/metadata/manifest.json'
 image=target/image_path.lstrip('/');manifest=target/manifest_path.lstrip('/');mount=target/'mounted-home'
 if root(['test','-e',str(image)],check=False).returncode==0:raise RuntimeError('Existing restore test image; inspect before retry.')
 try:
  restic(['restore',snapshot,'--target',str(target),'--sparse','--verify','--include',image_path,'--include',manifest_path])
  metadata=json.loads(root(['cat',str(manifest)],text=True).stdout)
  if root(['cryptsetup','luksUUID',str(image)],text=True).stdout.strip()!=keys['uuid']:raise RuntimeError('Restored volume identity mismatch')
  root(['cryptsetup','open','--key-file','-',str(image),mapping],input=keys['password'].encode());opened=True
  replay=subprocess.run(['sudo','e2fsck','-p','-E','journal_only','/dev/mapper/'+mapping],capture_output=True)
  if replay.returncode not in (0,1):raise RuntimeError('Copy-only journal replay failed')
  root(['cryptsetup','close',mapping]);opened=False
  root(['cryptsetup','open','--readonly','--key-file','-',str(image),mapping],input=keys['password'].encode());opened=True
  root(['e2fsck','-fn','/dev/mapper/'+mapping]);root(['mkdir','-p',str(mount)])
  root(['mount','-o','ro,noload,nodev,nosuid,noexec','/dev/mapper/'+mapping,str(mount)]);mounted=True
  for relative,digest in metadata['home_checksums'].items():
   if root(['sha256sum',str(mount/relative)],text=True).stdout.split()[0]!=digest:raise RuntimeError('Recovered file differs')
  root(['umount',str(mount)]);mounted=False;root(['cryptsetup','close',mapping]);opened=False
  fixture=BASE/'history-fixture';root(['install','-d','-m','700',str(fixture)])
  file=fixture/'document.txt';ids=[]
  for data in [b'original saved version\n',b'overwritten later version\n']:
   root(['tee',str(file)],input=data)
   result=restic(['backup','--host','desktop','--tag','verification','--json',str(file)],text=True)
   records=[json.loads(x) for x in result.stdout.splitlines() if x.startswith('{')];ids.append(next(x['snapshot_id'] for x in reversed(records) if x.get('message_type')=='summary'))
  old=restic(['dump',ids[0],str(file)]).stdout;new=restic(['dump',ids[1],str(file)]).stdout
  if old!=b'original saved version\n' or new!=b'overwritten later version\n':raise RuntimeError('History recovery test failed')
  result={'snapshot_id':snapshot,'independent_restore':'passed','independent_1password_repository_key':'passed','luks_unlock':'passed','copy_journal_replay_and_fsck':'passed','saved_file_hashes':len(metadata['home_checksums']),'older_overwritten_file_recovery':'passed','fresh_machine_boot':'not tested'}
  root(['tee',str(BASE/'incremental-restore-test.json')],input=(json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))
 finally:
  if mounted:root(['umount',str(mount)])
  if opened:root(['cryptsetup','close',mapping])
  # Only this fixed disposable verification directory is removed.
  root(['rm','-rf','--',str(target)])
if __name__=='__main__':main()
