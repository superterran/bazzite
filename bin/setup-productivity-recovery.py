#!/usr/bin/python3
"""Initialize/read public backup settings; secret keys stay only in 1Password."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser();p.add_argument('--initialize',action='store_true');a=p.parse_args()
s=importlib.util.spec_from_file_location('recovery',Path(__file__).with_name('productivity-recovery-runtime.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=m.recovery_keys(existing_only=not a.initialize)
config={k:r[k] for k in ['item_id','vault_id','title','uuid','recipient']}
config.update({'ssh_alias':'closet','backup_root':'/mnt/storage/backups/desktop-secure','account':'desktop-secure'})
subprocess.run(['sudo','tee','/etc/productivity-recovery.json'],input=json.dumps(config,indent=2)+'\n',text=True,capture_output=True,check=True)
subprocess.run(['sudo','chmod','600','/etc/productivity-recovery.json'],check=True)
print('Public backup settings installed. Private recovery keys remain in 1Password.')
