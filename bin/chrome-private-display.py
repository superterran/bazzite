#!/usr/bin/python3
"""Start an authenticated virtual Xorg display on its own input seat."""
import os
from pathlib import Path
import secrets
import subprocess

home=Path.home()
runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))/'chrome-private'
runtime.mkdir(mode=0o700,exist_ok=True)
auth=runtime/'Xauthority'
if not auth.exists():
    auth.touch(mode=0o600)
    subprocess.run(['xauth','-f',str(auth),'add',':20','.',secrets.token_hex(16)],check=True)
os.execv('/usr/libexec/Xorg',['Xorg',':20','-config',str(home/'repos/bazzite/config/chrome-private/xorg.conf'),'-modulepath',str(home/'.local/opt/chrome-private/usr/lib64/xorg/modules')+',/usr/lib64/xorg/modules','-seat','seat-browser','-sharevts','-novtswitch','-nolisten','tcp','-auth',str(auth),'-logfile',str(runtime/'Xorg.log'),'-noreset'])
