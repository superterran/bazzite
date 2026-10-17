import json,shutil,subprocess,time,os,sys
sys.argv=['x'];exec(open('/tmp/arc/merge/sm64union.py').read().split("import shutil,time,sys")[0])
R='/var/mnt/fast/rom-saves'
g=next(x for x in json.load(open(R+'/.save-aliases.json'))['groups'] if x['name']=='Super Mario 64 (U) [!]')
paths=[g['canonical']['path']]+[a['path'] for a in g['aliases']]
cur_path=next((R+'/'+p for p in paths if os.path.exists(R+'/'+p)),None)
base=bytearray(open('/var/mnt/fast/delta-backup/legacy-dropbox-retroarch/saves/Super Mario 64 (U) [!].srm','rb').read())
cur=bytearray(open(cur_path,'rb').read()) if cur_path else bytearray(base)
c=fileA(cur,'>')
if c:  # fold in anything played since
  U['flags']|=c['flags']
  for i in range(25):U['stars'][i]|=c['stars'][i]
  for i in range(15):U['coins'][i]=max(U['coins'][i],c['coins'][i])
if cur_path: shutil.copy2(cur_path,'/var/mnt/fast/rom-original-backups/save-merges-20261016/Super Mario 64.before-%d.srm'%time.time())
out=bytearray(cur if c else base)
blk=build(U,'>',b'DA');out[0:0x38]=blk;out[0x38:0x70]=blk
for p in paths:
  q=R+'/'+p;os.makedirs(os.path.dirname(q),exist_ok=True);open(q+'.tmp','wb').write(out);shutil.move(q+'.tmp',q)
d=json.loads(subprocess.run(['python3','/home/me/.local/bin/rom-save-alias-sync.py'],capture_output=True,text=True).stdout)
print('SM64 file A now',nstars(fileA(open(R+'/'+paths[0],'rb').read(),'>')),'stars; reconcile',d['status'],'updated',d['updated'],'conflicts',len(d['conflicts']))
