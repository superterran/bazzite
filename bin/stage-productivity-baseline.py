#!/usr/bin/python3
"""Preserve the in-flight frozen capture locally when its NAS is unavailable."""
import importlib.util,json,os,shutil,signal,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/productivity-recovery');CAP=BASE/'restic-capture';LOCAL=BASE/'local-capture'
DEST=Path('/var/mnt/fast/backups/desktop-restic-staging')
spec=importlib.util.spec_from_file_location('r',ROOT/'bin/productivity-restic.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def run(args,**kwargs):return subprocess.run(args,check=True,capture_output=True,**kwargs)
def main():
 if os.geteuid()!=0:raise SystemExit('Run as root.')
 os.umask(0o077)
 if '--execute' in sys.argv:
  # Private mount namespace: canonical backup paths without changing host mounts.
  run(['mount','--bind',str(LOCAL),str(CAP)])
  run(['mount','-o','remount,bind,ro',str(CAP)])
  args=json.loads((BASE/'local-stage-arguments.json').read_text())
  with (BASE/'local-baseline-latest.log').open('w') as log:
   result=r.command(args,repository=str(DEST),stdout=log,stderr=subprocess.STDOUT)
  if result.returncode:raise RuntimeError('Local baseline failed; frozen local-capture retained for diagnosis.')
  records=[json.loads(x) for x in (BASE/'local-baseline-latest.log').read_text().splitlines() if x.startswith('{')]
  summary=next(x for x in reversed(records) if x.get('message_type')=='summary')
  receipt={'mode':'baseline','transport':'local-staged','repository':str(DEST),**summary}
  (BASE/'local-baseline-latest.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
  return
 if LOCAL.exists() or DEST.exists():raise SystemExit('Local staging already exists; inspect before retrying.')
 DEST.parent.mkdir(parents=True,exist_ok=True)
 if shutil.disk_usage(DEST.parent).free<200*2**30:raise SystemExit('Less than200GiB free; staging refused.')
 mainpid=int(run(['systemctl','show','productivity-baseline.service','-p','MainPID','--value'],text=True).stdout)
 pids=run(['pgrep','-P',str(mainpid),'-x','restic'],text=True).stdout.split()
 if len(pids)!=1:raise RuntimeError('Expected exactly one in-flight baseline process.')
 pid=pids[0];argv=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0');argv=[os.fsdecode(x) for x in argv if x]
 args=argv[argv.index('backup'):]
 index=args.index('--files-from-raw')+1;fdnumber=int(args[index].rsplit('/',1)[1])
 fd=os.open(f'/proc/{pid}/fd/{fdnumber}',os.O_RDONLY)
 try:selection=os.pread(fd,1024*1024,0)
 finally:os.close(fd)
 if not selection.endswith(b'\0') or not selection:raise RuntimeError('Incomplete source selection.')
 if any(not os.fsdecode(p).startswith(str(CAP)+'/') for p in selection.split(b'\0') if p):raise RuntimeError('Unexpected source path outside frozen capture.')
 LOCAL.mkdir(mode=0o700)
 for name in ['root','var','home']:
  source=CAP/name
  if run(['btrfs','property','get','-ts',str(source),'ro'],text=True).stdout.strip()!='ro=true':raise RuntimeError('Source snapshot is not read-only.')
  run(['btrfs','subvolume','snapshot','-r',str(source),str(LOCAL/name)])
 for name in ['metadata','boot-files']:
  (LOCAL/name).mkdir(mode=0o700);run(['cp','-a',str(CAP/name)+'/.',str(LOCAL/name)])
 (BASE/'local-stage-selection.nul').write_bytes(selection);args[index]=str(BASE/'local-stage-selection.nul')
 for pattern in json.loads((ROOT/'config/productivity-backup-excludes.json').read_text())['capture_relative']:
  args+=['--exclude',str(CAP/pattern)]
 (BASE/'local-stage-arguments.json').write_text(json.dumps(args))
 # Local copies are now independent. End only the stalled uploader, not NAS/apps.
 run(['systemctl','stop','productivity-baseline.service'])
 # Keep the old target directory as the private-namespace bind mount point.
 CAP.mkdir(mode=0o700,exist_ok=True)
 result=r.command(['init'],repository=str(DEST),capture_output=True)
 if result.returncode:raise RuntimeError('Local encrypted repository initialization failed.')
 result=subprocess.run(['unshare','--mount','--propagation','private','/usr/bin/python3',str(Path(__file__).resolve()),'--execute'])
 if result.returncode:raise RuntimeError('Local baseline unsuccessful; snapshots retained.')
 for name in ['home','var','root']:run(['btrfs','subvolume','delete',str(LOCAL/name)])
 for name in ['metadata','boot-files']:shutil.rmtree(LOCAL/name)
 LOCAL.rmdir()
 print('Encrypted baseline staged on separate NVMe. NAS replication is still required.',flush=True)
if __name__=='__main__':main()
