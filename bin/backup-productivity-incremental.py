#!/usr/bin/python3
"""Consistent encrypted-image incrementals and selective known-good baseline."""
import argparse,fcntl,hashlib,importlib.util,json,os,resource,shutil,subprocess,time,signal,pwd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/var/lib/productivity-recovery');CAP=BASE/'restic-capture'
HOME=Path('/var/home/desktop-secure')
spec=importlib.util.spec_from_file_location('restic',ROOT/'bin/productivity-restic.py');restic=importlib.util.module_from_spec(spec);spec.loader.exec_module(restic)
def run(args,**kw):return subprocess.run(args,check=True,capture_output=True,**kw)
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');a=p.parse_args()
 if os.geteuid()!=0:raise SystemExit('Run as root.')
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077);BASE.mkdir(mode=0o700,exist_ok=True)
 def cancelled(signum,frame):raise SystemExit('Backup interrupted; cleaning its temporary snapshots.')
 signal.signal(signal.SIGTERM,cancelled)
 lock=(BASE/'backup.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 CAP.mkdir(mode=0o700,exist_ok=True);meta=CAP/'metadata';meta.mkdir(exist_ok=True)
 snapshots=[];frozen=False;paused=[]
 stamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());mode='baseline' if a.baseline else 'desktop'
 before=run(['rpm-ostree','status','--json']).stdout
 if json.loads(before).get('transaction'):raise RuntimeError('OS transaction active; capture deferred.')
 manifest={'format':1,'mode':mode,'created_utc':stamp,'volume_uuid':run(['cryptsetup','luksUUID','/var/lib/productivity-volume/desktop-secure.luks'],text=True).stdout.strip(),'home_checksums':{},'account':'desktop-secure','uid':pwd.getpwnam('desktop-secure').pw_uid,'gid':pwd.getpwnam('desktop-secure').pw_gid,'repo_commit':run(['git','-c',f'safe.directory={ROOT}','-C',str(ROOT),'rev-parse','HEAD'],text=True).stdout.strip(),'bootable_bare_metal_restore_tested':False,'application_consistency':'filesystem snapshots; running databases require application-specific verification','excluded':['Steam game downloads and Windows prefix components; user profiles/registry retained, exhaustive game-save audit outstanding','Downloads','AI model downloads','Docker image/build cache','Claude VM bundles/logs/cache','repo dependency folders']}
 try:
  if a.baseline:
   # Pause only running containers briefly so volume and upper-layer capture is
   # stable during the var snapshot. No container shutdown/restart is performed.
   ids=run(['docker','ps','-q','--filter','status=running'],text=True).stdout.split()
   for container in ids:
    # Independent recovery if the backup process dies while containers pause.
    run(['systemd-run','--quiet','--unit=productivity-thaw-'+container[:12],'--on-active=30s','/usr/bin/docker','unpause',container])
    run(['docker','pause',container]);paused.append(container)
  if os.path.ismount(HOME):
   run(['systemd-run','--quiet','--unit=productivity-backup-thaw','--on-active=20s','/usr/sbin/fsfreeze','--unfreeze',str(HOME)])
   run(['fsfreeze','--freeze',str(HOME)]);frozen=True
   for relative in ['.config/dconf/user','.bashrc','.ssh/config','.local/share/gnome-remote-desktop/credentials.ini','.local/share/gnome-shell/extensions/bottom-overview@fthx/metadata.json']:
    file=HOME/relative
    if file.is_file():manifest['home_checksums'][relative]=hashlib.sha256(file.read_bytes()).hexdigest()
  for name,source in ([('root','/sysroot'),('var','/var'),('home','/var/home')] if a.baseline else [('var','/var')]):
   target=CAP/name
   if target.exists():raise RuntimeError('Capture subvolume already exists; inspect previous failure before retrying.')
   run(['btrfs','subvolume','snapshot','-r',source,str(target)]);snapshots.append(target)
  if frozen:run(['fsfreeze','--unfreeze',str(HOME)]);frozen=False
  for container in paused:run(['docker','unpause',container]);run(['systemctl','stop','productivity-thaw-'+container[:12]+'.timer'])
  paused=[]
  run(['systemctl','stop','productivity-backup-thaw.timer'])
  volume=CAP/'var/lib/productivity-volume/desktop-secure.luks'
  run(['cryptsetup','luksHeaderBackup',str(volume),'--header-backup-file',str(meta/'luks.header')])
  (meta/'rpm-ostree.json').write_bytes(before)
  (meta/'recovery-public.json').write_bytes(Path('/etc/productivity-recovery.json').read_bytes())
  (meta/'restic-public.json').write_bytes(Path('/etc/productivity-restic.json').read_bytes())
  (meta/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
  inputs=[volume,meta]
  excludes=[]
  if a.baseline:
   boot=CAP/'boot-files';boot.mkdir(exist_ok=True)
   run(['cp','-a','/boot/.',str(boot)])
   for name,cmd in [('gpt.txt',['sfdisk','--dump','/dev/nvme0n1']),('blkid.txt',['blkid']),('mounts.json',['findmnt','--json']),('subvolumes.txt',['btrfs','subvolume','list','/sysroot']),('uefi.txt',['efibootmgr','-v']),('flatpaks.tsv',['flatpak','list','--columns=application,branch,installation'])]:
    (meta/name).write_bytes(run(cmd).stdout)
   # Preserve the notification credential under the existing public age key,
   # so it can be re-encrypted for a replacement host without its TPM secret.
   cfg=json.loads(Path('/etc/productivity-recovery.json').read_text())
   notification=run(['systemd-creds','decrypt','--name=notification','/etc/credstore.encrypted/productivity-push','-']).stdout
   (meta/'notification.json.age').write_bytes(run(['/home/linuxbrew/.linuxbrew/bin/age','-r',cfg['recipient']],input=notification).stdout);notification=None
   inputs=[CAP/'root',boot,meta]
   var=CAP/'var'
   for entry in var.iterdir():
    if entry.name in {'home','mnt','cache','log','tmp','lib'}:continue
    inputs.append(entry)
   for entry in (var/'lib').iterdir():
    if entry.name in {'docker','productivity-recovery','systemd'}:continue
    inputs.append(entry)
   inputs.extend(x for x in (var/'lib/systemd').iterdir() if x.name!='coredump')
   docker=var/'lib/docker'
   inputs.extend(x for x in [docker/'volumes',docker/'containers'] if x.exists())
   ids=run(['docker','ps','-aq'],text=True).stdout.split()
   if ids:
    inspect=run(['docker','inspect',*ids]).stdout;(meta/'docker-inspect.json').write_bytes(inspect)
    for record in json.loads(inspect):
     upper=record.get('GraphDriver',{}).get('Data',{}).get('UpperDir')
     if upper:
      path=var/Path(upper).relative_to('/var')
      if path.exists():inputs.append(path)
   user=CAP/'home/me'
   for name in ['.config','.var','.bashrc','.bash_profile','.profile','.env','.ssh','.gnupg','.pki','.gitconfig','.git-credentials','.npmrc','.docker','.1password','.steam','.codex','.claude','.agents','.vscode','.kube','.aws','.azure','.oci','.cargo','.bun','.nvm','.homebrew','homebrew','Applications','bin','Documents','repos']:
    path=user/name
    if path.exists() or path.is_symlink():inputs.append(path)
   inputs.extend(x for x in user.iterdir() if x.name.startswith('.') and x.is_file() and x not in inputs)
   local=user/'.local'
   inputs.extend(x for x in local.iterdir() if x.name!='share')
   inputs.extend(x for x in (local/'share').iterdir() if x.name not in {'containers','ramalama','uv','Trash','Steam'})
   steam=local/'share/Steam'
   inputs.extend(x for x in steam.iterdir() if x.name!='steamapps')
   apps=steam/'steamapps'
   inputs.extend(x for x in apps.iterdir() if x.is_file())
   for prefix in (apps/'compatdata').glob('*/pfx'):
    profile=prefix/'drive_c/users/steamuser'
    if profile.exists():inputs.append(profile)
    inputs.extend(x for x in prefix.glob('*.reg') if x.is_file())
   volumes=local/'share/containers/storage/volumes'
   if volumes.exists():inputs.append(volumes)
   inputs.append(CAP/'home/linuxbrew')
   for relative in ['.config/Claude/vm_bundles','.config/Claude/logs','.config/Claude/Cache','.config/Claude/Code Cache']:
    excludes+=['--exclude',str(user/relative)]
   for directory in ['node_modules','.venv','venv','__pycache__','.next','.nuxt','.turbo','.parcel-cache','.pytest_cache','.mypy_cache','.ruff_cache','.cache','.pnpm-store','target']:
    excludes+=['--exclude',str(user/'repos')+'/**/'+directory]
   for pattern in ['**/*.gguf','**/*.safetensors','**/models/ggml-*.bin']:
    excludes+=['--exclude',str(user/'repos')+'/'+pattern]
   # No OS deployment transition may straddle the root/boot capture.
   if run(['rpm-ostree','status','--json']).stdout!=before:raise RuntimeError('OS deployment changed during capture; baseline not committed.')
  paths_fd=os.memfd_create('backup-paths',0);os.write(paths_fd,b'\0'.join(os.fsencode(str(x)) for x in inputs)+b'\0');os.lseek(paths_fd,0,0)
  args=['backup','--host','desktop','--tag',mode,'--group-by','host,tags','--json','--read-concurrency','2',*excludes,'--files-from-raw',f'/proc/self/fd/{paths_fd}']
  log=BASE/(mode+'-latest.log')
  try:
   with log.open('w') as output:result=restic.command(args,stdout=output,stderr=subprocess.STDOUT,pass_fds=(paths_fd,))
  finally:os.close(paths_fd)
  if result.returncode:raise RuntimeError('Restic backup incomplete or failed; protected diagnostic '+str(log))
  records=[json.loads(line) for line in log.read_text().splitlines() if line.startswith('{')]
  summary=next(x for x in reversed(records) if x.get('message_type')=='summary')
  receipt={'mode':mode,'created_utc':stamp,**summary}
  (BASE/(mode+'-latest.json')).write_text(json.dumps(receipt,indent=2)+'\n')
  print(json.dumps(receipt),flush=True)
 finally:
  if frozen:subprocess.run(['fsfreeze','--unfreeze',str(HOME)],capture_output=True)
  for container in paused:subprocess.run(['docker','unpause',container],capture_output=True)
  for snapshot in reversed(snapshots):subprocess.run(['btrfs','subvolume','delete',str(snapshot)],capture_output=True)
  for name in ['metadata','boot-files']:shutil.rmtree(CAP/name,ignore_errors=True)
  subprocess.run(['systemctl','stop','productivity-backup-thaw.timer'],capture_output=True)
if __name__=='__main__':main()
