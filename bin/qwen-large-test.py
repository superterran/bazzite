#!/usr/bin/env python3
"""Download verified 122B weights and measure bounded hybrid inference."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

HOME = Path.home()
ROOT = HOME / '.local/opt/llama-b11588'
RUNTIME = ROOT / 'llama-b11588'
DEST = HOME / 'models/hybrid-test/qwen122-q3km'
OUT = HOME / '.local/state/hybrid-test/large'
REV = '51eab4d59d53f573fb9206cb3ce613f1d0aa392b'
FILES = [
 ('Qwen3.5-122B-A10B-Q3_K_M-00001-of-00003.gguf',10943552,'e70ec702564603c9b24b03d7b456fb6ed7b9b18fc32867e350a29961c45fd3ed'),
 ('Qwen3.5-122B-A10B-Q3_K_M-00002-of-00003.gguf',49587318592,'f8c42a060c826b8526dd72e363b87ac23e9753f622b641af2d4ae037e435fa8b'),
 ('Qwen3.5-122B-A10B-Q3_K_M-00003-of-00003.gguf',6822619808,'419e7efab336499ae3a6fc25924fdf65b3954ed301f3b227bae1f83f88049bbf'),
]

def range_download(url,path,size):
 parts=path.parent/(path.name+'.parts')
 parts.mkdir(exist_ok=True)
 count=8 if size>1000000000 else 1
 span=(size+count-1)//count
 def chunk(i):
  start=i*span
  end=min(size,(i+1)*span)-1
  part=parts/str(i)
  for attempt in range(6):
   have=part.stat().st_size if part.exists() else 0
   if have==end-start+1: return part
   if have>end-start+1: raise RuntimeError('Oversize download part')
   try:
    begin=start+have
    req=urllib.request.Request(url,headers={'Range':f'bytes={begin}-{end}'})
    with urllib.request.urlopen(req,timeout=60) as response:
     expected=f'bytes {begin}-{end}/{size}'
     if response.status!=206 or response.headers.get('Content-Range')!=expected:
      raise RuntimeError('Server did not honor range')
     with part.open('ab') as f:
      left=end-begin+1
      while left:
       block=response.read(min(left,4*1024*1024))
       if not block: raise RuntimeError('Short download')
       f.write(block)
       left-=len(block)
    return part
   except Exception:
    if attempt==5: raise
    time.sleep(2**attempt)
 with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
  chunks=list(pool.map(chunk,range(count)))
 assembled=path.with_suffix('.assembling')
 with assembled.open('wb') as dest:
  for part in chunks:
   with part.open('rb') as source:
    while block:=source.read(8*1024*1024): dest.write(block)
 assembled.replace(path)
 for part in chunks: part.unlink()
 parts.rmdir()

def fetch(item):
 name,size,digest=item
 path=DEST/name
 if not path.exists() or path.stat().st_size!=size:
  url=f'https://huggingface.co/unsloth/Qwen3.5-122B-A10B-GGUF/resolve/{REV}/Q3_K_M/{name}'
  range_download(url,path,size)
 with path.open('rb') as f:
  actual=hashlib.file_digest(f,'sha256').hexdigest()
 if path.stat().st_size!=size or actual!=digest:
  raise RuntimeError('Checksum mismatch: '+name)
 print('VERIFIED '+name,flush=True)

def main():
 DEST.mkdir(parents=True,exist_ok=True)
 OUT.mkdir(parents=True,exist_ok=True)
 print('Downloading pinned 122B Q3_K_M',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  list(pool.map(fetch,FILES))
 (OUT/'source.json').write_text(json.dumps({'revision':REV,'files':FILES},indent=2))
 subprocess.run(['systemctl','--user','stop','qwen-hybrid'],check=True)
 print('Stopped 35B server; starting large-model measurements',flush=True)
 env=dict(os.environ)
 env['LD_LIBRARY_PATH']=str(RUNTIME)+':'+str(ROOT/'cudart-llama-b11588-bin-ubuntu-cuda-12.8-x64')
 scenarios=[('layers8',['-ngl','8']),('experts44',['-ngl','99','-ncmoe','44']),('experts42',['-ngl','99','-ncmoe','42'])]
 results=[]
 for label,placement in scenarios:
  command=[str(RUNTIME/'llama-bench'),'-m',str(DEST/FILES[0][0]),'-p','512','-n','128','-b','512','-ub','128','-t','16','-fa','on','-r','2','-o','json']+placement
  print('START '+label,flush=True)
  started=time.time()
  with (OUT/(label+'.stderr')).open('w') as err:
   try:
    run=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=err,text=True,timeout=600)
    (OUT/(label+'.json')).write_text(run.stdout)
    data=json.loads(run.stdout) if run.returncode==0 else []
    result={'label':label,'placement':placement,'returncode':run.returncode,'seconds':time.time()-started,'benchmarks':data}
   except (subprocess.TimeoutExpired,json.JSONDecodeError) as e:
    result={'label':label,'error':str(e)}
  results.append(result)
  (OUT/'results.json').write_text(json.dumps(results,indent=2))
  print(json.dumps(result),flush=True)
 print('DONE',flush=True)

if __name__=='__main__':
 main()
