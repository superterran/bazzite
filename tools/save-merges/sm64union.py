import struct,zlib
# SaveFile (0x38): capLevel u8, capArea u8, capPos 3*s16, flags u32 @8, courseStars[25] @0x0C, coinScores[15] @0x25, sig u16 @0x34, chk u16 @0x36
def parse(blk,end):
  return dict(head=blk[0:2],cappos=struct.unpack(end+'3h',blk[2:8]),flags=struct.unpack(end+'I',blk[8:12])[0],stars=bytearray(blk[0x0C:0x25]),coins=bytearray(blk[0x25:0x34]))
def build(f,end,sig):
  b=bytearray(0x38);b[0:2]=f['head'];b[2:8]=struct.pack(end+'3h',*f['cappos']);b[8:12]=struct.pack(end+'I',f['flags'])
  b[0x0C:0x25]=f['stars'];b[0x25:0x34]=f['coins'];b[0x34:0x36]=sig
  struct.pack_into(end+'H',b,0x36,sum(b[:0x36])&0xffff);return bytes(b)
def valid(blk,end):return (sum(blk[:0x36])&0xffff)==struct.unpack(end+'H',blk[0x36:0x38])[0] and struct.unpack(end+'I',blk[8:12])[0]&1
def fileA(e,end,base=0):
  for off in (base,base+0x38):
    blk=e[off:off+0x38]
    if len(blk)==0x38 and valid(blk,end):return parse(blk,end)
def from_state(raw):
  for data in [raw]:
    for swap in (False,True):
      e=data if not swap else b''.join(data[i:i+4][::-1] for i in range(0,len(data)-3,4))
      i=e.find(b'DA')
      while i!=-1:
        b=i-0x34
        if b>=0 and valid(e[b:b+0x38],'>'):return parse(e[b:b+0x38],'>')
        i=e.find(b'DA',i+1)
def nstars(f):return sum(bin(x&0x7f).count('1') for x in f['stars'])
GHOST='/var/mnt/fast/shared-games/ghostship/default.sav'
src={'ghostship':fileA(open(GHOST,'rb').read(),'<'),
 'dropbox2021':fileA(open('/var/mnt/fast/delta-backup/legacy-dropbox-retroarch/saves/Super Mario 64 (U) [!].srm','rb').read(),'>'),
 'state2019':from_state(open('/var/mnt/fast/delta-backup/legacy-dropbox-retroarch/states/Super Mario 64 (U) [!].state','rb').read()),
 'allySD_eep':fileA(open('/var/mnt/slow/superterran-ally/SD Card/Emulation/roms/n64/Super Mario 64 (U) [!].eep','rb').read(),'>')}
U=dict(src['ghostship']);U['stars']=bytearray(U['stars']);U['coins']=bytearray(U['coins'])
for k,f in src.items():
  print(f'{k:12} {nstars(f)}★ flags {f["flags"]:#010x}')
  U['flags']|=f['flags']
  for i in range(25):U['stars'][i]|=f['stars'][i]
  for i in range(15):U['coins'][i]=max(U['coins'][i],f['coins'][i])
print('UNION       ',nstars(U),'★ flags',hex(U['flags']))
import shutil,time,sys
if 'write' in sys.argv:
  g=bytearray(open(GHOST,'rb').read())
  shutil.copy2(GHOST,'/var/mnt/fast/rom-original-backups/save-merges-20261016/ghostship-default.before-union-%d.sav'%time.time())
  blk=build(U,'<',g[0x34:0x36])
  g[0:0x38]=blk;g[0x38:0x70]=blk
  open(GHOST+'.tmp','wb').write(g);shutil.move(GHOST+'.tmp',GHOST)
  chk=fileA(open(GHOST,'rb').read(),'<');print('ghostship file A now',nstars(chk),'★ valid',chk is not None)
