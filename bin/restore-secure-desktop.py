#!/usr/bin/python3
"""Decrypt a recovery archive into an EMPTY staging directory, never live paths."""
import argparse
import getpass
import json
import os
from pathlib import Path
import resource
import subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--destination',type=Path,required=True)
    args=p.parse_args()
    if os.geteuid()!=0:raise SystemExit('Run with sudo; restore staging can contain private files.')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    destination=args.destination.resolve()
    if destination in [Path('/'),Path('/var'),Path('/var/home'),Path('/home')]:raise SystemExit('A separate empty staging directory is required.')
    if destination.exists() and any(destination.iterdir()):raise SystemExit('Destination is not empty; no files changed.')
    destination.mkdir(parents=True,mode=0o700,exist_ok=True)
    identity=getpass.getpass('Paste Backup decryption key (age) from 1Password, then Enter: ').strip()
    if not identity.startswith('AGE-SECRET-KEY-'):raise SystemExit('Expected an age secret identity, not the volume password.')
    fd=os.memfd_create('recovery-identity',0);os.write(fd,(identity+'\n').encode());os.lseek(fd,0,0);identity=None
    age='/home/linuxbrew/.linuxbrew/bin/age' if Path('/home/linuxbrew/.linuxbrew/bin/age').exists() else 'age'
    zstd='/home/linuxbrew/.linuxbrew/bin/zstd' if Path('/home/linuxbrew/.linuxbrew/bin/zstd').exists() else 'zstd'
    try:
        a=subprocess.Popen([age,'-d','-i',f'/proc/self/fd/{fd}',str(args.archive)],stdout=subprocess.PIPE,pass_fds=(fd,))
        z=subprocess.Popen([zstd,'-q','-d','-c'],stdin=a.stdout,stdout=subprocess.PIPE);a.stdout.close()
        t=subprocess.Popen(['/usr/bin/tar','--sparse','--acls','--xattrs','--selinux','--numeric-owner','-xpf','-','-C',str(destination)],stdin=z.stdout);z.stdout.close()
        codes=[t.wait(),z.wait(),a.wait()]
        if any(codes):raise SystemExit('Decryption/extraction did not complete; do not install this staging copy.')
        manifest=json.loads((destination/'recovery/manifest.json').read_text())
        print('Authenticated recovery archive extracted. Volume UUID:',manifest['volume_uuid'])
        print('No live files, accounts or services were replaced.')
        print('Next: inspect docs/secure-desktop-recovery.md and run install-restored-secure-desktop.py --plan.')
    finally:os.close(fd)

if __name__=='__main__':main()
