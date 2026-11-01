#!/usr/bin/python3
"""Stream the saved baseline tree and verify bulk-data exclusions actually held."""
import fnmatch,json,os,subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/productivity-recovery');CAP=str(BASE/'restic-capture')
if os.geteuid()!=0:raise SystemExit('Run as root.')
os.umask(0o077)
local='--local-baseline' in sys.argv
snapshot=json.loads((BASE/('local-baseline-latest.json' if local else 'baseline-latest.json')).read_text())['snapshot_id']
extra=['--local-repository','/var/mnt/fast/backups/desktop-restic-staging'] if local else []
patterns=json.loads((ROOT/'config/productivity-backup-excludes.json').read_text())['capture_relative']
patterns += ['home/me/Downloads','home/me/models','home/me/.ollama','home/me/.local/share/ramalama','home/me/.local/share/Steam/steamapps/common','home/me/.local/share/Steam/steamapps/shadercache','home/me/.config/Claude/vm_bundles']
patterns=[CAP+'/'+p for p in patterns]
def compile_path(pattern):
 components=pattern.strip('/').split('/');expression='^/'
 for index,component in enumerate(components):
  if component=='**':expression+='.*' if index==len(components)-1 else '(?:[^/]+/)*'
  else:
   expression+=re.escape(component).replace(r'\*','[^/]*').replace(r'\?','[^/]')
   if index<len(components)-1:expression+='/'
 return re.compile(expression+r'(?:/.*)?$')
compiled=[compile_path(p) for p in patterns]
deps={'node_modules','.venv','venv','__pycache__','.next','.nuxt','.turbo','.parcel-cache','.pytest_cache','.mypy_cache','.ruff_cache','.cache','.pnpm-store','target'}
files=0;violations=[]
with (BASE/'scope-audit-errors.log').open('w') as errors:
 process=subprocess.Popen([sys.executable,str(ROOT/'bin/productivity-restic.py'),*extra,'ls','--json',snapshot],stdout=subprocess.PIPE,stderr=errors)
 for line in process.stdout:
  value=json.loads(line)
  if value.get('message_type')!='node' or value.get('type')!='file':continue
  files+=1;path=value['path'];bad=any(p.match(path) for p in compiled)
  if path.startswith(CAP+'/home/me/repos/'):
   relative=path.split('/home/me/repos/',1)[1]
   bad|=bool(set(Path(relative).parts[:-1]) & deps)
   bad|=path.endswith(('.gguf','.safetensors')) or ('/models/ggml-' in path and path.endswith('.bin'))
  bad|=fnmatch.fnmatch(path,CAP+'/home/me/.local/share/Steam/steamapps/compatdata/*/pfx/drive_c/windows/*')
  if bad and len(violations)<25:violations.append(path)
 if process.wait():raise SystemExit('Snapshot listing failed; scope has not been verified.')
report={'snapshot_id':snapshot,'files_examined':files,'excluded_bulk_data_absent':not violations,'violation_examples':violations}
(BASE/('local-baseline-scope-audit.json' if local else 'baseline-scope-audit.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='violation_examples'},indent=2))
if violations:raise SystemExit('Excluded bulk data found. Inspect the protected scope report before claiming completion.')
