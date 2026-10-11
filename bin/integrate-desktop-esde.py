#!/usr/bin/env python3
"""Add local ES-DE to Steam and preserve existing ROM shortcut save identities."""
from pathlib import Path
import struct,json,shlex,hashlib,zipfile,xml.etree.ElementTree as ET,shutil,datetime,subprocess,time,os,zlib
def read_vdf(b):
 def parse(i):
  d={}
  while b[i]!=8:
   t=b[i];i+=1;j=b.index(0,i);k=b[i:j].decode();i=j+1
   if t==0:v,i=parse(i)
   elif t==1:j=b.index(0,i);v=b[i:j].decode();i=j+1
   elif t==2:v=struct.unpack_from('<I',b,i)[0];i+=4
   else:raise ValueError(t)
   d[k]=v
  return d,i+1
 return parse(0)
def encode(d):
 b=b''
 for k,v in d.items():
  b+=bytes([0 if isinstance(v,dict) else 2 if isinstance(v,int) else 1])+k.encode()+b'\0'
  b+=encode(v) if isinstance(v,dict) else struct.pack('<I',v) if isinstance(v,int) else v.encode()+b'\0'
 return b+b'\x08'
def hashes(p):
 if p.suffix.lower()=='.zip':
  with zipfile.ZipFile(p) as z:return {hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
 return {hashlib.sha256(p.read_bytes()).hexdigest()}
if subprocess.run(['pgrep','-x','es-de'],stdout=subprocess.DEVNULL).returncode==0:raise RuntimeError('Close ES-DE before changing its launch settings.')
home=Path.home();vdf=home/'.local/share/Steam/userdata/35894255/config/shortcuts.vdf'
old=vdf.read_bytes();parsed,end=read_vdf(old);shortcuts=parsed['shortcuts']
base=home/'ES-DE';sysfile=base/'custom_systems/es_systems.xml';systems=ET.parse(sysfile)
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=base/'backups'/('steam-integration-'+stamp);backup.mkdir(parents=True)
shutil.copy2(vdf,backup/'shortcuts.vdf');shutil.copy2(sysfile,backup/'es_systems.xml');shutil.copy2(base/'settings/es_settings.xml',backup/'es_settings.xml')
report=[]
for entry in shortcuts.values():
 opts=shlex.split(entry.get('LaunchOptions',''))
 if 'org.libretro.RetroArch' not in opts or '-L' not in opts:continue
 core=Path(opts[opts.index('-L')+1]).name
 rom=Path(opts[-1])
 if not rom.is_file():raise RuntimeError('Shortcut ROM is missing: '+str(rom))
 wanted=hashes(rom)
 matched=[]
 for s in systems.findall('system'):
  systemname=s.findtext('name')
  if (core.startswith('mesen') and systemname!='nes') or (core.startswith('bsnes') and systemname not in ['snes','sneswidescreen']):continue
  gp=base/'gamelists'/systemname/'gamelist.xml'
  if not gp.exists():continue
  gl=ET.parse(gp);changed=False
  for game in gl.findall('game'):
   candidate=Path(game.findtext('path'))
   if candidate.is_file() and candidate.stat().st_size<50_000_000 and wanted.intersection(hashes(candidate)):
    label='Existing Steam shortcut: '+entry['AppName']
    if not any(c.get('label')==label for c in s.findall('command')):
     default=s.find('command');default.set('label','Shared library default')
     ET.SubElement(s,'command',{'label':label}).text='/usr/bin/flatpak '+entry['LaunchOptions']
    node=game.find('altemulator')
    if node is None:node=ET.SubElement(game,'altemulator')
    node.text=label;changed=True;matched.append(str(candidate))
  if changed:
   dest=backup/'gamelists'/systemname;dest.mkdir(parents=True,exist_ok=True);shutil.copy2(gp,dest/'gamelist.xml')
   ET.indent(gl);gl.write(gp,encoding='utf-8',xml_declaration=True)
 report.append({'name':entry['AppName'],'core':core,'existing_rom':str(rom),'matched_library_roms':matched})
ET.indent(systems);systems.write(sysfile,encoding='utf-8',xml_declaration=True)
cfg=base/'settings/es_settings.xml';raw=cfg.read_text();raw=raw.replace('name="AlternativeEmulatorPerGame" value="false"','name="AlternativeEmulatorPerGame" value="true"')
if 'AlternativeEmulatorPerGame' not in raw:raw+='\n<bool name="AlternativeEmulatorPerGame" value="true" />\n'
cfg.write_text(raw)
name='EmulationStation (Local ROM Library)';exe='"'+str(home/'Applications/ES-DE.AppImage')+'"'
if not any('emulationstation' in e.get('AppName','').lower() or 'es-de' in e.get('AppName','').lower() for e in shortcuts.values()):
 pids=subprocess.check_output(['pgrep','-x','steam'],text=True).split()
 if len(pids)!=1:raise RuntimeError('Expected exactly one Steam process')
 env=dict(x.split('=',1) for x in Path('/proc/'+pids[0]+'/environ').read_text().split(chr(0)) if '=' in x)
 subprocess.run(['steam','-shutdown'],env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  if subprocess.run(['pgrep','-x','steam'],stdout=subprocess.DEVNULL).returncode!=0:break
  time.sleep(.2)
 else:raise RuntimeError('Steam did not stop; no shortcut changed.')
 # Read again after Steam has flushed its own current data.
 current=vdf.read_bytes();d,e=read_vdf(current);items=d['shortcuts']
 entry={'appid':zlib.crc32((exe+name).encode())|0x80000000,'AppName':name,'Exe':exe,'StartDir':'"'+str(home/'Applications')+'"','icon':'','ShortcutPath':'','LaunchOptions':'','IsHidden':0,'AllowDesktopConfig':1,'AllowOverlay':1,'OpenVR':0,'Devkit':0,'DevkitGameID':'','DevkitOverrideAppID':0,'LastPlayTime':0,'FlatpakAppID':'','tags':{'0':'Emulation'}}
 key=str(max([int(x) for x in items]+[-1])+1)
 # Insert one new child into the existing root, preserving every old entry byte.
 updated=current[:e-2]+bytes([0])+key.encode()+b'\0'+encode(entry)+current[e-2:]
 check,_=read_vdf(updated)
 assert all(check['shortcuts'][k]==v for k,v in items.items())
 shutil.copy2(vdf,backup/'shortcuts-after-steam-flush.vdf')
 tmp=vdf.with_suffix('.vdf.new');tmp.write_bytes(updated);tmp.replace(vdf)
 subprocess.Popen(['steam','-silent'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'steam_entry':name,'preserved_rom_launches':report,'backup':str(backup)},indent=2))
