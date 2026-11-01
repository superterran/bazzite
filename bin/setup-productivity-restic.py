#!/usr/bin/python3
"""Store the repository password in 1Password and a host-encrypted credential."""
import json,os,subprocess,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
base=(ROOT/'bin/productivity-1password.cjs').read_text().split("const title = 'Desktop Encrypted GNOME';")[0]
body="""
const item=op(['item','get','6kjfof6obrhbd5hblkbcxailgy','--vault',vault,'--format','json']);
let field=item.fields.find(f=>f.id==='resticPassword');
if(!field){field={id:'resticPassword',type:'CONCEALED',label:'Incremental backup repository password',value:crypto.randomBytes(48).toString('base64url')};item.fields.push(field);op(['item','edit',item.id,'--vault',vault,'--format','json','-'],JSON.stringify(item));}
process.stdout.write(JSON.stringify({password:field.value}));
"""
remote=['ssh','-o','BatchMode=yes','closet',"docker exec -i codex-rc sh -c 'ulimit -c 0; exec node -'"]
r=subprocess.run(remote,input=base+body,text=True,capture_output=True,timeout=120)
if r.returncode:raise SystemExit('Protected 1Password repository-key setup failed; no credential output logged.')
password=json.loads(r.stdout)['password'].encode()
subprocess.run(['sudo','install','-d','-m','700','/etc/credstore.encrypted'],check=True)
subprocess.run(['sudo','systemd-creds','encrypt','--name=restic-password','-','/etc/credstore.encrypted/productivity-restic'],input=password,check=True,capture_output=True)
password=None
config={'repository':'sftp:closet:/mnt/storage/backups/desktop-restic','options':['sftp.command=ssh -F /dev/null -i /home/me/.ssh/id_ed25519_truenas -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 -o UserKnownHostsFile=/home/me/.ssh/known_hosts -s root@closet.local sftp'], 'recovery_item':'Desktop Secure Recovery','retention':{'daily':7,'weekly':4,'monthly':3}}
subprocess.run(['sudo','tee','/etc/productivity-restic.json'],input=json.dumps(config).encode(),stdout=subprocess.DEVNULL,check=True)
subprocess.run(['sudo','chmod','600','/etc/productivity-restic.json'],check=True)
print('Repository password saved in 1Password and host-encrypted systemd credential; no plaintext key file.')
