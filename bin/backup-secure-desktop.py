#!/usr/bin/python3
"""Consistent encrypted-home backup, age-encrypted before leaving this host."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import resource
import shlex
import shutil
import subprocess
import time

BASE=Path('/var/lib/productivity-recovery')
REPO=Path('/home/me/repos/bazzite')
HOME=Path('/var/home/desktop-secure')
VOLUME=Path('/var/lib/productivity-volume/desktop-secure.luks')
AGE='/home/linuxbrew/.linuxbrew/bin/age'
ZSTD='/home/linuxbrew/.linuxbrew/bin/zstd'


def run(args,**kw):
    return subprocess.run(args,check=True,capture_output=True,**kw)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',help='Override only for an explicit test backup')
    args=parser.parse_args()
    if os.geteuid()!=0:raise SystemExit('Run with sudo.')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    BASE.mkdir(mode=0o700,parents=True,exist_ok=True)
    lock=(BASE/'backup.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=json.loads(Path('/etc/productivity-recovery.json').read_text())
    stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    work=BASE/'work'/stamp;work.mkdir(parents=True)
    snapshots=BASE/'snapshots';snapshots.mkdir(exist_ok=True)
    var=snapshots/(stamp+'-var');home=snapshots/(stamp+'-home')
    frozen=False
    try:
        account=pwd.getpwnam('desktop-secure')
        manifest={'format':1,'created_utc':stamp,'account':account.pw_name,'uid':account.pw_uid,'gid':account.pw_gid,
                  'volume_uuid':config['uuid'],'volume_bytes':VOLUME.stat().st_size,
                  'recovery_item_id':config['item_id'],'recovery_vault_id':config['vault_id'],
                  'repo_url':'https://github.com/superterran/bazzite',
                  'repo_commit':run(['git','-c',f'safe.directory={REPO}','-C',str(REPO),'rev-parse','HEAD'],text=True).stdout.strip(),
                  'home_checksums':{}}
        # Keys are not fetched here. The backup daemon knows only an age public recipient.
        notification=run(['/usr/bin/systemd-creds','decrypt','--name=notification','/etc/credstore.encrypted/productivity-push','-']).stdout
        wrapped=run([AGE,'-r',config['recipient']],input=notification).stdout
        notification=None
        (work/'notification.json.age').write_bytes(wrapped)
        (work/'recovery-public.json').write_text(json.dumps(config,indent=2)+'\n')
        run(['git','-c',f'safe.directory={REPO}','-C',str(REPO),'bundle','create',str(work/'bazzite.bundle'),'--all'])
        run(['/usr/bin/podman','save','--format','oci-archive','-o',str(work/'secure-xrdp.oci'),'localhost/productivity-secure-xrdp:test'])
        (work/'rpm-ostree.json').write_bytes(run(['/usr/bin/rpm-ostree','status','--json']).stdout)
        (work/'flatpaks.tsv').write_bytes(run(['/usr/bin/flatpak','list','--columns=application,branch,installation']).stdout)
        run(['/usr/bin/cryptsetup','luksHeaderBackup',str(VOLUME),'--header-backup-file',str(work/'luks.header')])
        # An independent timer guarantees thaw even if this process is killed.
        if os.path.ismount(HOME):
            run(['/usr/bin/systemd-run','--quiet','--unit=productivity-backup-thaw','--on-active=20s','/usr/sbin/fsfreeze','--unfreeze',str(HOME)])
            run(['/usr/sbin/fsfreeze','--freeze',str(HOME)]);frozen=True
            for relative in ['.config/dconf/user','.bashrc','.ssh/config','.local/share/gnome-remote-desktop/credentials.ini',
                             '.local/share/gnome-shell/extensions/bottom-overview@fthx/metadata.json']:
                p=HOME/relative
                if p.is_file():manifest['home_checksums'][relative]=hashlib.sha256(p.read_bytes()).hexdigest()
        # Btrfs takes stable backing-image and main-user configuration snapshots.
        run(['/usr/sbin/btrfs','subvolume','snapshot','-r','/var',str(var)])
        run(['/usr/sbin/btrfs','subvolume','snapshot','-r','/var/home',str(home)])
        if frozen:
            run(['/usr/sbin/fsfreeze','--unfreeze',str(HOME)]);frozen=False
        run(['/usr/bin/systemctl','stop','productivity-backup-thaw.timer']) if os.path.ismount(HOME) else None
        (work/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        main_paths=['me/repos/bazzite','me/.bashrc','me/.bash_profile','me/.profile','me/.env','me/.ssh',
                    'me/.config/sunshine','me/.config/systemd/user','me/.config/environment.d',
                    'me/.config/gamescope','me/.config/gamescope-session-plus',
                    'me/.config/steam-artwork-sync.json','me/.config/retired-steam-shortcuts.json',
                    'me/.config/secure-desktop-tv.json','me/.config/hardware-monitor.json','me/.config/hardware-monitor',
                    'me/.config/Claude/claude_desktop_config.json','me/.local/share/Steam/userdata','me/.local/share/Steam/config']
        main_paths=[p for p in main_paths if (home/p).exists() or (home/p).is_symlink()]
        system_paths=['etc/productivity-secure.json','etc/coolercontrol','etc/systemd/system',
                      'etc/pam.d/productivity-secure','etc/productivity-push.env','etc/firewalld','etc/udev/rules.d','etc/ssh']
        system_paths=[p for p in system_paths if (Path('/')/p).exists()]
        tar=['/usr/bin/tar','--sparse','--acls','--xattrs','--selinux','--numeric-owner','--format=pax','--warning=no-file-changed','-c','-f','-',
             '--transform=s,^lib/,var/lib/,','--transform=s,^me/,home/me/,',
             '--transform=s,^manifest.json$,recovery/manifest.json,',
             '--transform=s,^recovery-public.json$,recovery/recovery-public.json,',
             '--transform=s,^notification.json.age$,recovery/notification.json.age,',
             '--transform=s,^bazzite.bundle$,recovery/bazzite.bundle,',
             '--transform=s,^secure-xrdp.oci$,recovery/secure-xrdp.oci,',
             '--transform=s,^rpm-ostree.json$,recovery/rpm-ostree.json,',
             '--transform=s,^flatpaks.tsv$,recovery/flatpaks.tsv,',
             '--transform=s,^luks.header$,recovery/luks.header,',
             '-C',str(var),'lib/productivity-volume/desktop-secure.luks','lib/productivity-secure-bridge',
             '-C',str(home),*main_paths,'-C','/',*system_paths,'-C',str(work),
             'manifest.json','recovery-public.json','notification.json.age','bazzite.bundle','secure-xrdp.oci','rpm-ostree.json','flatpaks.tsv','luks.header']
        destination=args.destination or config['backup_root']
        filename='desktop-secure-'+stamp+'.tar.zst.age'
        sink='''import pathlib,sys,os,hashlib,json
os.umask(0o077)
root=pathlib.Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True,mode=0o700)
name=sys.argv[2];partial=root/(name+'.partial');digest=hashlib.sha256();size=0
with partial.open('xb') as f:
 while True:
  chunk=sys.stdin.buffer.read(1024*1024)
  if not chunk:break
  f.write(chunk);digest.update(chunk);size+=len(chunk)
 f.flush();os.fsync(f.fileno())
# Promotion occurs only after the local pipeline confirms every stage succeeded.
print(json.dumps({'bytes':size,'sha256':digest.hexdigest()}))
'''
        remote=shlex.join(['python3','-c',sink,destination,filename])
        print('Streaming encrypted backup to Closet:',filename,flush=True)
        with (work/'pipeline-errors.log').open('wb') as errors:
            p1=subprocess.Popen(tar,stdout=subprocess.PIPE,stderr=errors)
            p2=subprocess.Popen([ZSTD,'-q','-T2','-3','-c'],stdin=p1.stdout,stdout=subprocess.PIPE,stderr=errors);p1.stdout.close()
            p3=subprocess.Popen([AGE,'-r',config['recipient']],stdin=p2.stdout,stdout=subprocess.PIPE,stderr=errors);p2.stdout.close()
            p4=subprocess.Popen(['/usr/sbin/runuser','-u','me','--','ssh','-o','BatchMode=yes',config['ssh_alias'],remote],stdin=p3.stdout,stdout=subprocess.PIPE,stderr=errors);p3.stdout.close()
            result=p4.communicate()[0]
            codes=[p1.wait(),p2.wait(),p3.wait(),p4.returncode]
            if any(codes):raise RuntimeError('Backup pipeline failed; partial file not promoted. Stage codes:'+str(codes))
        receipt=json.loads(result);receipt.update({'file':filename,'destination':destination,'created_utc':stamp,'repo_commit':manifest['repo_commit']})
        # No plaintext data or keys are sent to Closet outside the age stream.
        promote='import pathlib,sys,json; r=pathlib.Path(sys.argv[1]); n=sys.argv[2]; (r/(n+".partial")).rename(r/n); (r/(n+".receipt.json")).write_text(sys.stdin.read())'
        run(['/usr/sbin/runuser','-u','me','--','ssh','-o','BatchMode=yes',config['ssh_alias'],
             shlex.join(['python3','-c',promote,destination,filename])],input=json.dumps(receipt).encode())
        (BASE/'latest.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt),flush=True)
    finally:
        if frozen:
            subprocess.run(['/usr/sbin/fsfreeze','--unfreeze',str(HOME)],capture_output=True)
        subprocess.run(['/usr/bin/systemctl','stop','productivity-backup-thaw.timer'],capture_output=True)
        for p in [home,var]:
            if p.exists():subprocess.run(['/usr/sbin/btrfs','subvolume','delete',str(p)],capture_output=True)
        shutil.rmtree(work,ignore_errors=True)

if __name__=='__main__':main()
