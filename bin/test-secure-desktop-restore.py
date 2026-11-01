#!/usr/bin/python3
"""Restore an independent encrypted backup copy, unlock read-only, verify files."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
AGE='/home/linuxbrew/.linuxbrew/bin/age'
ZSTD='/home/linuxbrew/.linuxbrew/bin/zstd'


def root_run(args,**kw):
    return subprocess.run(['sudo',*args],check=True,capture_output=True,**kw)


def main():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    spec=importlib.util.spec_from_file_location('runtime',ROOT/'bin/productivity-recovery-runtime.py')
    runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
    keys=runtime.recovery_keys()
    receipt=json.loads(root_run(['/usr/bin/cat','/var/lib/productivity-recovery/latest.json'],text=True).stdout)
    config=json.loads(root_run(['/usr/bin/cat','/etc/productivity-recovery.json'],text=True).stdout)
    target=Path('/var/lib/productivity-recovery/restore-tests')/receipt['created_utc']
    root_run(['/usr/bin/mkdir','-p',str(target)])
    # A separate location is mandatory; production volume/mapping are never targets.
    marker=target/'manifest-test-result.json'
    if marker.exists():raise SystemExit('This backup already has a test directory; inspect before reusing it.')
    fd=os.memfd_create('recovery-identity',0);os.write(fd,(keys['identity']+'\n').encode());os.lseek(fd,0,0)
    mapping='desktop-recovery-test-'+str(os.getpid())
    mount=target/'readonly-home';root_run(['/usr/bin/mkdir','-p',str(mount)])
    opened=False;mounted=False;success=False
    try:
        remote=shlex.join(['cat',receipt['destination']+'/'+receipt['file']])
        source=subprocess.Popen(['ssh','-o','BatchMode=yes',config['ssh_alias'],remote],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        decrypt=subprocess.Popen([AGE,'-d','-i',f'/proc/self/fd/{fd}'],stdin=source.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(fd,));source.stdout.close()
        expand=subprocess.Popen([ZSTD,'-q','-d','-c'],stdin=decrypt.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE);decrypt.stdout.close()
        extract=subprocess.Popen(['sudo','/usr/bin/tar','--sparse','--acls','--xattrs','--selinux','--numeric-owner','-xpf','-','-C',str(target)],stdin=expand.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE);expand.stdout.close()
        _,errors=extract.communicate()
        codes=[source.wait(),decrypt.wait(),expand.wait(),extract.returncode]
        if any(codes):raise RuntimeError('Authenticated decrypt/extract failed; stage codes:'+str(codes))
        manifest=json.loads(root_run(['/usr/bin/cat',str(target/'recovery/manifest.json')],text=True).stdout)
        image=target/'var/lib/productivity-volume/desktop-secure.luks'
        if manifest['volume_uuid']!=keys['uuid']:raise RuntimeError('Recovery record UUID mismatch')
        uuid=root_run(['/usr/bin/cryptsetup','luksUUID',str(image)],text=True).stdout.strip()
        if uuid!=manifest['volume_uuid']:raise RuntimeError('Restored image UUID mismatch')
        root_run(['/usr/bin/cryptsetup','open','--readonly','--key-file','-',str(image),mapping],input=keys['password'].encode())
        opened=True
        check=subprocess.run(['sudo','/usr/sbin/e2fsck','-fn','/dev/mapper/'+mapping],capture_output=True,text=True)
        journal_replayed=False
        if check.returncode==4:
            # A filesystem-consistent online image may retain the recovery bit.
            # Replay only its journal on the disposable COPY, never production.
            root_run(['/usr/bin/tee',str(target/'fsck-before.txt')],input=(check.stdout+check.stderr).encode())
            root_run(['/usr/bin/cryptsetup','close',mapping]);opened=False
            root_run(['/usr/bin/cryptsetup','open','--key-file','-',str(image),mapping],input=keys['password'].encode());opened=True
            replay=subprocess.run(['sudo','/usr/sbin/e2fsck','-p','-E','journal_only','/dev/mapper/'+mapping],capture_output=True,text=True)
            root_run(['/usr/bin/tee',str(target/'journal-replay.txt')],input=(replay.stdout+replay.stderr).encode())
            if replay.returncode not in (0,1):raise RuntimeError('Copied filesystem journal replay failed.')
            root_run(['/usr/bin/cryptsetup','close',mapping]);opened=False
            root_run(['/usr/bin/cryptsetup','open','--readonly','--key-file','-',str(image),mapping],input=keys['password'].encode());opened=True
            check=subprocess.run(['sudo','/usr/sbin/e2fsck','-fn','/dev/mapper/'+mapping],capture_output=True,text=True)
            journal_replayed=True
        if check.returncode!=0:
            root_run(['/usr/bin/tee',str(target/'fsck-after.txt')],input=(check.stdout+check.stderr).encode())
            raise RuntimeError('Restored filesystem check failed; code '+str(check.returncode))
        root_run(['/usr/bin/mount','-o','ro,noload,nodev,nosuid,noexec','/dev/mapper/'+mapping,str(mount)]);mounted=True
        verified=[]
        for relative,expected in manifest['home_checksums'].items():
            digest=root_run(['/usr/bin/sha256sum',str(mount/relative)],text=True).stdout.split()[0]
            if digest!=expected:raise RuntimeError('Restored encrypted-home metadata differs')
            verified.append(relative)
        # Verify that the independently wrapped notification credential decrypts,
        # without writing its plaintext or replacing live service credentials.
        notification=root_run(['/usr/bin/cat',str(target/'recovery/notification.json.age')]).stdout
        os.lseek(fd,0,0)
        data=subprocess.run([AGE,'-d','-i',f'/proc/self/fd/{fd}'],input=notification,capture_output=True,pass_fds=(fd,),check=True).stdout
        record=json.loads(data)
        if not all(record.get(k) for k in ['sender','password','recipient']):raise RuntimeError('Notification recovery data missing')
        record=None;data=None
        bundle=root_run(['git','-c',f'safe.directory={ROOT}','-C',str(ROOT),'bundle','verify',str(target/'recovery/bazzite.bundle')])
        result={'backup':receipt['file'],'tested_utc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip(),
                'age_authentication':'passed','independent_luks_unlock':'passed','filesystem_check':'passed','copy_journal_replayed':journal_replayed,
                'verified_home_files':verified,'notification_credential_decryption':'passed','git_bundle':'verified',
                'fresh_machine_graphical_rebuild':'not tested'}
        root_run(['/usr/bin/tee',str(marker)],input=(json.dumps(result,indent=2)+'\n').encode())
        root_run(['/usr/bin/tee','/var/lib/productivity-recovery/latest-restore-test.json'],input=(json.dumps(result,indent=2)+'\n').encode())
        success=True
        print(json.dumps(result,indent=2))
    finally:
        if mounted:root_run(['/usr/bin/umount',str(mount)])
        if opened:root_run(['/usr/bin/cryptsetup','close',mapping])
        os.close(fd)
        # The extracted copy contains private config. Keep only the test report;
        # remove plaintext host configuration and the duplicate encrypted image.
        for folder in (['home','etc','var','recovery','readonly-home'] if success else []):
            root_run(['/usr/bin/rm','-rf','--',str(target/folder)])

if __name__=='__main__':main()
