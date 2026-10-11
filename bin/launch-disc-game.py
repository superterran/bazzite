#!/usr/bin/env python3
"""Launch Dolphin/Cemu with the connected controller, preserving game saves."""
import configparser,json,os,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
emulator,game=sys.argv[1:3]
app='info.cemu.Cemu' if emulator=='cemu' else 'org.DolphinEmu.dolphin-emu'
probe="""import ctypes,json
class GUID(ctypes.Structure):_fields_=[('data',ctypes.c_ubyte*16)]
s=ctypes.CDLL('libSDL2-2.0.so.0');s.SDL_Init(0x2000)
s.SDL_GameControllerNameForIndex.restype=ctypes.c_char_p
s.SDL_JoystickGetDeviceGUID.restype=GUID
d=[]
for i in range(s.SDL_NumJoysticks()):
 n=s.SDL_GameControllerNameForIndex(i)
 if n:d.append({'name':n.decode(),'guid':bytes(s.SDL_JoystickGetDeviceGUID(i).data).hex()})
s.SDL_Quit();print(json.dumps(d))
"""
try:
 devices=json.loads(subprocess.check_output(['flatpak','run','--command=python3','info.cemu.Cemu','-c',probe],stderr=subprocess.DEVNULL,timeout=10))
except (subprocess.SubprocessError,ValueError):
 devices=[]
devices.sort(key=lambda d:('Steam Virtual' not in d['name'],'DualSense' not in d['name']))
if devices:
 device=devices[0];base=Path.home()/'.var/app'/app/'config'
 if emulator=='cemu':
  path=base/'Cemu/controllerProfiles/controller0.xml'
  if path.exists():
   backup=path.with_suffix('.xml.before-fleet')
   if not backup.exists():shutil.copy2(path,backup)
   tree=ET.parse(path);root=tree.getroot()
   controller=next((c for c in root.findall('controller') if c.findtext('api')=='SDLController'),None)
   if controller is not None:
    controller.find('uuid').text='0_'+device['guid']
    controller.find('display_name').text=device['name']
    tree.write(path,encoding='utf-8',xml_declaration=True)
 else:
  path=base/'dolphin-emu/GCPadNew.ini'
  if path.exists():
   backup=path.with_suffix('.ini.before-fleet')
   if not backup.exists():shutil.copy2(path,backup)
   cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str;cfg.read(path)
   cfg['GCPad1']['Device']='SDL/0/'+device['name']
   with path.open('w') as f:cfg.write(f)
args=['flatpak','run',app]+(['-f','-g',game] if emulator=='cemu' else ['-b','-e',game,'-C','Dolphin.Display.Fullscreen=True'])
args+=sys.argv[3:]
os.execvp('flatpak',args)

