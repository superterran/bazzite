#!/usr/bin/env python3
"""Apply a BPS patch only when source, patch, and output CRCs validate."""
import argparse,struct,zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--patch',required=True);p.add_argument('--output',required=True);a=p.parse_args()
source=Path(a.source).read_bytes();patch=Path(a.patch).read_bytes()
assert patch[:4]==b'BPS1','Not a BPS patch'
source_crc,target_crc,patch_crc=struct.unpack('<III',patch[-12:])
assert zlib.crc32(source)==source_crc,'Source ROM does not match this patch'
assert zlib.crc32(patch[:-4])==patch_crc,'Patch checksum failed'
index=4
def number():
 global index
 value=0;shift=1
 while True:
  b=patch[index];index+=1;value+=(b&127)*shift
  if b&128:return value
  shift<<=7;value+=shift
def delta():
 n=number();return -(n>>1) if n&1 else n>>1
size=number();target_size=number();metadata=number();index+=metadata
assert size==len(source),'Source size does not match'
target=bytearray();source_pos=0;target_pos=0
while len(target)<target_size:
 action=number();length=(action>>2)+1;kind=action&3
 if kind==0:target.extend(source[len(target):len(target)+length])
 elif kind==1:target.extend(patch[index:index+length]);index+=length
 elif kind==2:
  source_pos+=delta();assert 0<=source_pos<=len(source)-length
  target.extend(source[source_pos:source_pos+length]);source_pos+=length
 else:
  target_pos+=delta();assert 0<=target_pos<len(target)
  for _ in range(length):target.append(target[target_pos]);target_pos+=1
assert len(target)==target_size and zlib.crc32(target)==target_crc,'Patched ROM checksum failed'
dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
if dest.exists():assert dest.read_bytes()==target,'Output already exists with different contents'
else:dest.write_bytes(target)
print(f'Validated BPS patch: {source_crc:08x} -> {target_crc:08x}; {len(target)} bytes')
