#!/usr/bin/python3
"""Root-only Restic wrapper. Never prints/deposits repository passwords."""
import json,os,resource,subprocess,sys
from pathlib import Path

def command(args,repository=None,same_password_source=None,**kwargs):
 if os.geteuid()!=0:raise RuntimeError('Run with sudo.')
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 cfg=json.loads(Path('/etc/productivity-restic.json').read_text())
 secret=subprocess.run(['/usr/bin/systemd-creds','decrypt','--name=restic-password','/etc/credstore.encrypted/productivity-restic','-'],capture_output=True,check=True).stdout
 fd=os.memfd_create('restic-password',0);os.write(fd,secret);os.lseek(fd,0,0);secret=None
 env=dict(os.environ,RESTIC_PASSWORD_FILE=f'/proc/self/fd/{fd}',RESTIC_CACHE_DIR='/var/cache/productivity-restic')
 env.pop('RESTIC_PASSWORD',None);env.pop('RESTIC_PASSWORD_COMMAND',None)
 argv=['/usr/bin/restic','-r',repository or cfg['repository']]
 if repository is None or str(repository).startswith('sftp:'):
  for option in cfg['options']:argv+=['-o',option]
  if cfg.get('upload_limit_kib'):argv+=['--limit-upload',str(cfg['upload_limit_kib'])]
 source_fd=None
 if same_password_source is not None:
  if not args or args[0]!='copy':raise ValueError('Same-password source is only supported for copy.')
  source_fd=os.memfd_create('restic-source-password',0);os.write(source_fd,os.pread(fd,65536,0));os.lseek(source_fd,0,0)
  args=[args[0],'--from-repo',str(same_password_source),'--from-password-file',f'/proc/self/fd/{source_fd}',*args[1:]]
 inherited=kwargs.pop('pass_fds',())
 if source_fd is not None:inherited=(*inherited,source_fd)
 try:return subprocess.run(argv+list(args),env=env,pass_fds=(fd,*inherited),**kwargs)
 finally:
  os.close(fd)
  if source_fd is not None:os.close(source_fd)
if __name__=='__main__':sys.exit(command(sys.argv[1:]).returncode)
