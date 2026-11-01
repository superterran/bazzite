#!/usr/bin/python3
"""Validate/restore only an absent secure desktop; refuses existing live volumes."""
import argparse
import json
import os
from pathlib import Path
import pwd
import grp
import shutil
import subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--staging',type=Path,required=True)
    p.add_argument('--apply',action='store_true',help='Install into a fresh host after reviewing the printed plan')
    p.add_argument('--plan',action='store_true')
    args=p.parse_args()
    if os.geteuid()!=0:raise SystemExit('Run with sudo.')
    staging=args.staging.resolve()
    manifest=json.loads((staging/'recovery/manifest.json').read_text())
    image=staging/'var/lib/productivity-volume/desktop-secure.luks'
    if not image.is_file() or image.stat().st_size!=manifest['volume_bytes']:raise SystemExit('Missing/incomplete staged volume.')
    uuid=subprocess.check_output(['/usr/bin/cryptsetup','luksUUID',str(image)],text=True).strip()
    if uuid!=manifest['volume_uuid']:raise SystemExit('Staged volume UUID mismatch.')
    if args.apply and (Path('/var/lib/productivity-volume/desktop-secure.luks').exists() or Path('/etc/productivity-secure.json').exists()):
        raise SystemExit('An encrypted desktop already exists here. Refusing to replace it. Use a fresh host.')
    for database,name,number in [(pwd,'desktop-secure',manifest['uid']),(grp,'desktop-secure',manifest['gid'])]:
        try:entry=database.getpwuid(number) if database is pwd else database.getgrgid(number)
        except KeyError:continue
        if (entry.pw_name if database is pwd else entry.gr_name)!=name:raise SystemExit('Saved UID/GID is occupied by another identity; resolve manually.')
    print(json.dumps({'mode':'apply' if args.apply else 'plan','uid':manifest['uid'],'gid':manifest['gid'],
                      'volume_uuid':uuid,'restores':['encrypted volume','broker metadata','gateway TLS/config','saved gateway OCI image','public backup settings'],
                      'does_not_restore_automatically':['main-user home','SSH/Steam logins','cooling/firewall on different hardware','SMTP/notification credential','Tailscale enrollment']},indent=2))
    if not args.apply:return
    if Path('/var/lib/productivity-secure-bridge').exists():raise SystemExit('Gateway directory already exists; no files changed.')
    try:
        current=pwd.getpwnam('desktop-secure')
        if current.pw_uid!=manifest['uid']:raise SystemExit('Existing account UID does not match saved home ownership.')
    except KeyError:pass
    try:
        if grp.getgrnam('desktop-secure').gr_gid!=manifest['gid']:raise SystemExit('Existing group GID differs from saved ownership.')
    except KeyError:pass
    os.umask(0o077)
    try:grp.getgrnam('desktop-secure')
    except KeyError:subprocess.run(['/usr/sbin/groupadd','--gid',str(manifest['gid']),'desktop-secure'],check=True)
    try:pwd.getpwnam('desktop-secure')
    except KeyError:subprocess.run(['/usr/sbin/useradd','--uid',str(manifest['uid']),'--gid',str(manifest['gid']),
                                  '--home-dir','/var/home/desktop-secure','--no-create-home','--shell','/bin/bash','desktop-secure'],check=True)
    subprocess.run(['/usr/bin/passwd','--lock','desktop-secure'],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['/usr/bin/loginctl','disable-linger','desktop-secure'],check=True)
    home=Path('/var/home/desktop-secure');home.mkdir(mode=0o700,exist_ok=True);os.chown(home,manifest['uid'],manifest['gid'])
    volume=Path('/var/lib/productivity-volume/desktop-secure.luks');volume.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    volume.touch(mode=0o600);subprocess.run(['/usr/bin/chattr','+C',str(volume)],check=True)
    subprocess.run(['/usr/bin/cp','--sparse=always',str(image),str(volume)],check=True)
    shutil.copy2(staging/'recovery/luks.header',volume.with_name('desktop-secure.header'))
    bridge=Path('/var/lib/productivity-secure-bridge')
    if bridge.exists():raise SystemExit('Gateway directory exists; inspect staged/live data before continuing.')
    shutil.copytree(staging/'var/lib/productivity-secure-bridge',bridge,symlinks=True)
    shutil.copy2(staging/'etc/productivity-secure.json','/etc/productivity-secure.json')
    shutil.copy2(staging/'recovery/recovery-public.json','/etc/productivity-recovery.json')
    subprocess.run(['/usr/bin/podman','load','-i',str(staging/'recovery/secure-xrdp.oci')],check=True)
    subprocess.run(['/usr/sbin/restorecon','-RF',str(volume.parent),str(bridge),str(home)],check=True)
    print('Core files restored and still locked. Run the documented deployment steps as me; never rerun volume initialization.')

if __name__=='__main__':main()
