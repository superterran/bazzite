import struct,hashlib,json,shutil,subprocess,time
S=0x65C;R='/var/mnt/fast/rom-saves';C=R+'/cartridge/snes/Super Metroid.srm'
def slot(d,i):return bytes(d[0x10+i*S:0x10+(i+1)*S])
def put(d,i,s):
  d[0x10+i*S:0x10+(i+1)*S]=s;c=sum(struct.unpack('<%dH'%(S//2),s))&0xffff
  for b,v in [(0,c),(8,c^0xffff),(0x1FF0,c),(0x1FF8,c^0xffff)]:struct.pack_into('<H',d,b+2*i,v)
cur=bytearray(open(C,'rb').read())
phone=open('/tmp/arc/iphone/saves/Snes9x/Super Metroid.srm','rb').read()
delta=open('/var/mnt/fast/delta-backup/current/GameSave-da957f0d63d14cb441d215462904c4fa8519c613-gameSave','rb').read()
shutil.copy2(C,'/var/mnt/fast/rom-original-backups/save-merges-20261016/Super Metroid.before-merge-%d.srm'%time.time())
out=bytearray(cur);put(out,1,slot(phone,0));put(out,2,slot(delta,0))
assert slot(out,0)==slot(cur,0)
open(C+'.tmp','wb').write(out);shutil.move(C+'.tmp',C)
r=subprocess.run(['python3','/home/me/.local/bin/rom-save-alias-sync.py'],capture_output=True,text=True).stdout
d=json.loads(r);print('reconcile:',d['status'],'updated',d['updated'],'errors',d['errors'][:2],'conflicts',len(d['conflicts']))
m=hashlib.sha256(out).hexdigest();g=next(x for x in json.load(open(R+'/.save-aliases.json'))['groups'] if x['id']=='super-metroid-standard-and-wide')
for x in [g['canonical']]+g['aliases']:
  try:h=hashlib.sha256(open(R+'/'+x['path'],'rb').read()).hexdigest()
  except FileNotFoundError:h='missing'
  print('MERGED' if h==m else h[:10],x['path'])
