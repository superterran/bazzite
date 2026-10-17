import struct,hashlib,json,shutil,subprocess,time
B=143;R='/var/mnt/fast/rom-saves';C=R+'/cartridge/snes/Super Mario World.srm'
def ok(b):return b==b'\xff'*B or (sum(b[:141])+struct.unpack_from('<H',b,141)[0])&0xffff==0x5a5a
cur=bytearray(open(C,'rb').read())
de=open('/var/mnt/fast/delta-backup/current/GameSave-553cf42f35acf63028a369608742bb5b913c103f-gameSave','rb').read()[0:B]
ws=open('/tmp/arc/iphone/saves/bsnes-hd beta/Super Mario World-widescreen.srm','rb').read()[0x1C000:0x1C000+B]
a=bytes(cur[0:B]);assert ok(a) and ok(de) and ok(ws)
shutil.copy2(C,'/var/mnt/fast/rom-original-backups/save-merges-20261016/Super Mario World.before-merge-%d.srm'%time.time())
cur[0:858]=a+de+ws+a+de+ws
open(C+'.tmp','wb').write(cur);shutil.move(C+'.tmp',C)
d=json.loads(subprocess.run(['python3','/home/me/.local/bin/rom-save-alias-sync.py'],capture_output=True,text=True).stdout)
print('reconcile:',d['status'],'updated',d['updated'],'errors',d['errors'][:2],'conflicts',len(d['conflicts']))
g=next(x for x in json.load(open(R+'/.save-aliases.json'))['groups'] if x['id']=='smw-standard-and-wide')
want=bytes(cur[0:858])
for x in [g['canonical']]+g['aliases']:
  try:dd=open(R+'/'+x['path'],'rb').read();pl=dd[x.get('offset',0):x.get('offset',0)+858];print('MERGED' if pl==want else 'other',x['path'])
  except FileNotFoundError:print('missing',x['path'])
