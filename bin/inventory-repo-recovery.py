#!/usr/bin/env python3
"""Size repo-local recovery candidates without reading or printing their contents.
This is an inventory, not a backup; dependency exclusions need review.
"""
import argparse,json,os,subprocess
from pathlib import Path
SKIP={'.git','node_modules','.venv','venv','__pycache__','.next','.nuxt','.turbo','.parcel-cache','.pytest_cache','.mypy_cache','.ruff_cache','.cache','.pnpm-store','target'}
def git(root,*args):
 r=subprocess.run(['git','-C',str(root),*args],capture_output=True)
 if r.returncode:raise RuntimeError('git inventory failed')
 return r.stdout

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.home()/'repos');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 repositories=[];outside=0;outside_bytes=0
 for directory,dirs,files in os.walk(a.root,followlinks=False):
  here=Path(directory)
  if '.git' in dirs or '.git' in files:repositories.append(here)
  dirs[:]=[d for d in dirs if d not in SKIP]
 # Each nested repo owns its subtree; do not accidentally count it twice.
 roots=set(repositories);report=[];errors=[]
 for root in repositories:
  try:
   tracked=set(os.fsdecode(x) for x in git(root,'ls-files','-z').split(b'\0') if x)
   modified=set(os.fsdecode(x) for x in git(root,'diff','HEAD','--name-only','-z').split(b'\0') if x)
   candidates=[];size=0
   for directory,dirs,files in os.walk(root,followlinks=False):
    here=Path(directory);dirs[:]=[d for d in dirs if d not in SKIP and here/d not in roots]
    for name in files:
     path=here/name;relative=str(path.relative_to(root))
     if name=='.git':continue
     if path.suffix in {'.gguf','.safetensors'} or (name.startswith('ggml-') and name.endswith('.bin') and 'models' in path.parts):continue
     if relative in tracked and relative not in modified:continue
     try:n=path.lstat().st_size
     except OSError:continue
     candidates.append({'path':relative,'bytes':n,'kind':'modified-tracked' if relative in tracked else 'untracked-or-ignored'})
     size+=n
   refs=git(root,'for-each-ref','--format=%(refname) %(objectname)').decode().splitlines()
   # Local Git objects can contain commits absent from every remote. Preserve
   # history via a bundle during capture, not just these working-tree candidates.
   metadata=0
   dot=root/'.git'
   if dot.is_dir():
    for directory,dirs,files in os.walk(dot):
     for name in files:
      try:metadata+=(Path(directory)/name).lstat().st_size
      except OSError:pass
   report.append({'repository':str(root),'candidate_bytes':size,'git_metadata_bytes':metadata,'refs':refs,'files':candidates})
  except Exception:errors.append(str(root))
 total=sum(r['candidate_bytes'] for r in report);metadata=sum(r['git_metadata_bytes'] for r in report)
 result={'is_backup':False,'root':str(a.root),'dependency_directory_exclusions':sorted(SKIP- {'.git'}),'repositories':report,'errors':errors,
         'candidate_bytes':total,'git_metadata_bytes':metadata,'limitations':['Excluded dependency directories require review for local edits.','Git metadata estimate is not a bundle or proof of remote availability.','Files outside discovered repositories and external worktree common Git directories need separate coverage.','Untracked-or-ignored candidates are not all secrets and may include generated output.']}
 a.output.parent.mkdir(parents=True,exist_ok=True);os.umask(0o077);a.output.write_text(json.dumps(result,indent=2)+'\n');os.chmod(a.output,0o600)
 print(json.dumps({'repositories':len(report),'errors':len(errors),'candidate_GiB':round(total/2**30,3),'git_metadata_GiB':round(metadata/2**30,3),'private_report':str(a.output),'largest_candidate_repositories':[{'repository':r['repository'],'GiB':round(r['candidate_bytes']/2**30,3)} for r in sorted(report,key=lambda x:x['candidate_bytes'],reverse=True)[:8]]},indent=2))
if __name__=='__main__':main()
