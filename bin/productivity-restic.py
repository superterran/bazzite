#!/usr/bin/python3
"""Root-only Restic wrapper. Never prints/deposits repository passwords."""
import json,os,resource,subprocess,sys
from pathlib import Path

def command(args,**kwargs):
 if os.geteuid()!=0:raise RuntimeError('Run with sudo.')
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 cfg=json.loads(Path('/etc/productivity-restic.json').read_text())
 secret=subprocess.run(['/usr/bin/systemd-creds','decrypt','--name=restic-password','/etc/credstore.encrypted/productivity-restic','-'],capture_output=True,check=True).stdout
 fd=os.memfd_create('restic-password',0);os.write(fd,secret);os.lseek(fd,0,0);secret=None
 env=dict(os.environ,RESTIC_PASSWORD_FILE=f'/proc/self/fd/{fd}',RESTIC_CACHE_DIR='/var/cache/productivity-restic')
 argv=['/usr/bin/restic','-r',cfg['repository']]
 for option in cfg['options']:argv+=['-o',option]
 inherited=kwargs.pop('pass_fds',())
 try:return subprocess.run(argv+list(args),env=env,pass_fds=(fd,*inherited),**kwargs)
 finally:os.close(fd)
if __name__=='__main__':sys.exit(command(sys.argv[1:]).returncode)
