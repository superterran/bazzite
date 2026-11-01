#!/usr/bin/python3
"""Copy the completed encrypted local baseline to NAS, then verify and retain."""
import importlib.util,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/productivity-recovery');LOCAL='/var/mnt/fast/backups/desktop-restic-staging'
spec=importlib.util.spec_from_file_location('r',ROOT/'bin/productivity-restic.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def main():
 if os.geteuid()!=0:raise SystemExit('Run as root.')
 os.umask(0o077)
 local=json.loads((BASE/'local-baseline-latest.json').read_text())
 source=json.loads(r.command(['snapshots','--json','--tag','baseline'],repository=LOCAL,capture_output=True,check=True).stdout)
 point=next(x for x in source if x['id']==local['snapshot_id'])
 # Fail closed if NAS authentication/reachability is unavailable. Timer retries.
 r.command(['snapshots','--json'],capture_output=True,check=True)
 with (BASE/'baseline-replication.log').open('w') as log:
  r.command(['copy','--tag','baseline'],same_password_source=LOCAL,stdout=log,stderr=subprocess.STDOUT,check=True)
 remote=json.loads(r.command(['snapshots','--json','--tag','baseline'],capture_output=True,check=True).stdout)
 matches=[x for x in remote if x.get('tree')==point['tree'] and x.get('time')==point['time'] and x.get('hostname')==point.get('hostname')]
 if len(matches)!=1:raise RuntimeError('Could not uniquely verify the copied baseline tree/time.')
 receipt={**local,'transport':'local-stage-copied','staging_repository':LOCAL,'repository':json.loads(Path('/etc/productivity-restic.json').read_text())['repository'],'local_snapshot_id':local['snapshot_id'],'snapshot_id':matches[0]['id'],'nas_completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 (BASE/'baseline-latest.json').write_text(json.dumps(receipt,indent=2)+'\n')
 subprocess.run(['/usr/bin/python3',str(ROOT/'bin/finalize-productivity-backup.py'),'--imported-baseline'],check=True)
 subprocess.run(['/usr/bin/python3',str(ROOT/'bin/audit-productivity-backup.py')],check=True)
 (BASE/'replication-complete.json').write_text(json.dumps(receipt,indent=2)+'\n')
 subprocess.run(['systemctl','disable','--now','productivity-replicate.timer'],check=True,capture_output=True)
 print('NAS replication, independent config recovery, scoped retention and exclusion audit passed.',flush=True)
if __name__=='__main__':main()
