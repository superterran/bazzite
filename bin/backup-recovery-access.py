#!/usr/bin/env python3
"""Bootstrap read-only Restic recovery using1Password, without original SSH files.
--setup escrows the EXISTING NAS admin identity; --verify tests escrow via the
already-authorized NAS1Password automation. Normal recovery uses owner's op CLI.
"""
import argparse,json,os,resource,shlex,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ITEM='6kjfof6obrhbd5hblkbcxailgy'
def service_record(material=None):
 base=(ROOT/'bin/productivity-1password.cjs').read_text().split("const title = 'Desktop Encrypted GNOME';")[0]
 body="const material="+json.dumps(material or {})+";"+"""
const item=op(['item','get','6kjfof6obrhbd5hblkbcxailgy','--vault',vault,'--format','json']);
let changed=false;
for(const [id,type,label,value] of (material.fields||[])){
 const f=item.fields.find(x=>x.id===id);
 if(f && f.value!==value)throw Error('Recovery escrow differs; review before rotation');
 if(!f){item.fields.push({id,type,label,value});changed=true;}
}
if(changed)op(['item','edit',item.id,'--vault',vault,'--format','json','-'],JSON.stringify(item));
const result=op(['item','get',item.id,'--vault',vault,'--format','json']);
process.stdout.write(JSON.stringify(result));
"""
 r=subprocess.run(['/usr/bin/python3',str(ROOT/'bin/closet-backup-ssh.py'),'--auto-route','--',"docker exec -i codex-rc sh -c 'ulimit -c 0; exec node -'"],input=(base+body).encode(),capture_output=True,timeout=120)
 if r.returncode:raise RuntimeError('Protected recovery-record operation failed; no credential output logged.')
 return json.loads(r.stdout)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--setup',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--address',default='10.0.0.75');p.add_argument('restic_args',nargs=argparse.REMAINDER);a=p.parse_args()
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
 if a.setup:
  private=Path('/home/me/.ssh/id_ed25519_truenas').read_text()
  lines=subprocess.check_output(['ssh-keygen','-F','closet.local','-f','/home/me/.ssh/known_hosts'],text=True).splitlines()
  pin=next(' '.join(x.split()[1:3]) for x in lines if not x.startswith('#') and ' ssh-ed25519 ' in x)
  record=service_record({'fields':[['nasSshPrivateKey','CONCEALED','NAS recovery SSH private key (existing identity)',private],['nasSshHostKey','STRING','NAS pinned SSH host key',pin],['nasSshUser','STRING','NAS SSH username','root'],['nasSshAddress','STRING','NAS LAN address','10.0.0.75'],['nasTailnetAddress','STRING','NAS Tailscale address','100.101.167.38']]})
  print('Existing NAS identity and host pin escrowed in1Password; no NAS access policy changed.')
 elif a.verify:record=service_record()
 else:
  r=subprocess.run(['op','item','get',ITEM,'--vault','Closet','--format','json'],capture_output=True)
  if r.returncode:raise SystemExit('Sign into your1Password CLI/account first. No NAS access is needed to retrieve the record.')
  record=json.loads(r.stdout)
 fields={x['id']:x.get('value','') for x in record['fields']}
 for required in ['nasSshPrivateKey','nasSshHostKey','resticPassword']:
  if not fields.get(required):raise SystemExit('Missing recovery credential field: '+required)
 args=a.restic_args
 if args[:1]==['--']:args=args[1:]
 if a.verify or a.setup:args=['snapshots','--json']
 if not args:args=['snapshots']
 if args[0] not in {'snapshots','ls','dump','restore','stats','check'}:raise SystemExit('Recovery tool permits read/recovery commands only.')
 if args[0]=='restore':
  if '--target' not in args:raise SystemExit('Restore requires a separate --target argument naming an empty staging directory.')
  target=Path(args[args.index('--target')+1]).resolve()
  if target in map(Path,['/','/home','/var','/var/home']) or (target.exists() and any(target.iterdir())):raise SystemExit('Restore target must be separate and empty.')
 fds=[]
 try:
  for name,value in [('nas-identity',fields['nasSshPrivateKey']),('repository-password',fields['resticPassword'])]:
   fd=os.memfd_create(name,0);os.fchmod(fd,0o600);os.write(fd,(value.rstrip()+'\n').encode());os.lseek(fd,0,0);fds.append(fd)
  # Descendant SSH can reopen the still-live parent's anonymous600-mode key.
  key=f'/proc/{os.getpid()}/fd/{fds[0]}';password=f'/proc/{os.getpid()}/fd/{fds[1]}'
  with tempfile.TemporaryDirectory(prefix='desktop-recovery-public-') as temp:
   known=Path(temp)/'known_hosts';known.write_text('closet-recovery '+fields['nasSshHostKey']+'\n')
   ssh=['ssh','-F','/dev/null','-i',key,'-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=closet-recovery','-o','UserKnownHostsFile='+str(known),'-o','ConnectTimeout=12','-s','root@'+a.address,'sftp']
   env=dict(os.environ,RESTIC_PASSWORD_FILE=password);env.pop('RESTIC_PASSWORD',None);env.pop('RESTIC_PASSWORD_COMMAND',None)
   cmd=['restic','-r','sftp:closet-recovery:/mnt/storage/backups/desktop-restic','-o','sftp.command='+shlex.join(ssh),*args]
   if args[0]=='restore' and os.geteuid()!=0:cmd=['sudo','--preserve-env=RESTIC_PASSWORD_FILE',*cmd]
   result=subprocess.run(cmd,env=env,capture_output=a.verify or a.setup)
   if result.returncode:raise SystemExit('Recovery access failed; private credential output was not logged.')
   if a.verify or a.setup:
    snapshots=json.loads(result.stdout);print('Independent escrowed SSH + repository-key access passed:',len(snapshots),'snapshots; original local identity/agent not used.')
 finally:
  for fd in fds:os.close(fd)
if __name__=='__main__':main()
