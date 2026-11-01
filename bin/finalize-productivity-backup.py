#!/usr/bin/python3
"""Wait for current baseline, verify saved config, exercise nightly history."""
import hashlib,importlib.util,json,os,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/productivity-recovery')
spec=importlib.util.spec_from_file_location('r',ROOT/'bin/productivity-restic.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def run(args,**kwargs):return subprocess.run(args,check=True,capture_output=True,**kwargs)
def main():
 if os.geteuid()!=0:raise SystemExit('Run as root.')
 os.umask(0o077)
 if '--imported-baseline' not in sys.argv:
  deadline=time.monotonic()+3*3600
  while True:
   state=run(['systemctl','show','productivity-baseline.service','-p','ActiveState','--value'],text=True).stdout.strip()
   if state not in {'active','activating','deactivating'}:break
   if time.monotonic()>deadline:raise RuntimeError('Baseline verification deadline exceeded; capture may still be running.')
   time.sleep(5)
  result=run(['systemctl','show','productivity-baseline.service','-p','Result','--value'],text=True).stdout.strip()
  if result!='success':raise RuntimeError('Baseline failed; old backup remains available. Inspect protected baseline log.')
 else:
  if json.loads((BASE/'baseline-latest.json').read_text()).get('transport')!='local-stage-copied':raise RuntimeError('No successful imported baseline receipt.')
 receipt=json.loads((BASE/'baseline-latest.json').read_text());snapshot=receipt['snapshot_id']
 # Apply the same explicit replaceable-cache/model policy to this already-running
 # first capture without uploading all other data again. Never rewrite globally.
 before=json.loads(r.command(['snapshots','--json','--tag','baseline'],capture_output=True,check=True).stdout)
 filters=[]
 for pattern in json.loads((ROOT/'config/productivity-backup-excludes.json').read_text())['capture_relative']:
  filters+=['--exclude',str(BASE/'restic-capture'/pattern)]
 with (BASE/'baseline-filter.log').open('w') as log:r.command(['rewrite','--forget',*filters,snapshot],stdout=log,stderr=subprocess.STDOUT,check=True)
 after=json.loads(r.command(['snapshots','--json','--tag','baseline'],capture_output=True,check=True).stdout)
 new=[x for x in after if x['id'] not in {y['id'] for y in before}]
 if len(new)>1:raise RuntimeError('Ambiguous filtered baseline; inspect without deleting anything else.')
 if new:
  receipt['unfiltered_snapshot_id']=snapshot;snapshot=new[0]['id'];receipt['snapshot_id']=snapshot
  receipt['filters_applied']=json.loads((ROOT/'config/productivity-backup-excludes.json').read_text())['capture_relative']
  (BASE/'baseline-latest.json').write_text(json.dumps(receipt,indent=2)+'\n')

 expected=json.loads((BASE/'baseline-file-checksums.json').read_text())
 for path,digest in expected.items():
  data=r.command(['dump',snapshot,path],capture_output=True,check=True).stdout
  if hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('Baseline restored config checksum mismatch.')
 with (BASE/'restic-check.log').open('w') as log:r.command(['check'],stdout=log,stderr=subprocess.STDOUT,check=True)
 # Exercises the actual scheduled service, including scoped retention/prune.
 run(['systemctl','start','productivity-incremental.service'])
 desktop=json.loads((BASE/'desktop-latest.json').read_text())
 stats=json.loads(r.command(['stats','--mode','raw-data','--json'],capture_output=True,check=True).stdout)
 snapshots=json.loads(r.command(['snapshots','--json'],capture_output=True,check=True).stdout)
 if not any(x['id']==snapshot and 'baseline' in x.get('tags',[]) for x in snapshots):raise RuntimeError('Protected baseline absent after retention.')
 report={'baseline_snapshot':snapshot,'desktop_snapshot':desktop['snapshot_id'],'critical_config_files_restored_and_matched':len(expected),'repository_check':'passed','scheduled_service_and_retention':'passed','second_desktop_added_bytes':desktop['data_added_packed'],'initial_desktop_added_bytes':7690365546,'restic_raw_data_stats':stats,'fresh_machine_boot':'not tested','completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 (BASE/'completed-backup-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
