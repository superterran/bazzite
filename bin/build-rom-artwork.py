#!/usr/bin/env python3
"""Build shared ES-DE artwork and muOS derivatives from existing library assets."""
import argparse,json,shutil,os,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from PIL import Image
MAP={
'arcade':('arcade','Arcade'),'atari2600':('atari2600','Atari 2600'),'atari7800':('atari7800','Atari 7800'),
'gamegear':('gamegear','Sega Game Gear'),'gb':('gb','Nintendo Game Boy'),'gba':('gba','Nintendo Game Boy Advance'),
'gbc':('gbc','Nintendo Game Boy Color'),'lynx':('lynx','Atari Lynx'),'mastersystem':('mastersystem','Sega Master System'),
'megadrive':('genesis','Sega Mega Drive - Genesis'),'n64':('n64','Nintendo N64'),'nes':('nes','Nintendo NES - Famicom'),
'pcengine':('pcengine','NEC PC Engine'),'sega32x':('sega32x','Sega 32X'),'snes':('snes','Nintendo SNES - SFC')}
def refresh(output):
 output=Path(output);meta=json.loads((output/'mapping.json').read_text());count=0
 for entry in meta:
  for kind,sourcekind,bounds in [('box','covers',(250,220)),('preview','screenshots',(250,188))]:
   srcs=[p for kind in [sourcekind,'miximages'] for ext in ['.png','.jpg','.jpeg'] if (p:=output/'es-de/media'/entry['es_system']/kind/(entry['basename']+ext)).exists()]
   if not srcs: continue
   src=srcs[0]; dest=output/'muos'/entry['catalogue']/kind/(entry['basename']+'.png')
   if dest.exists() and dest.stat().st_mtime>=src.stat().st_mtime:
    with Image.open(dest) as existing:
     if existing.width<=bounds[0] and existing.height<=bounds[1]: continue
   dest.parent.mkdir(parents=True,exist_ok=True)
   with Image.open(src) as im:
    im=im.convert('RGBA');im.thumbnail(bounds,Image.Resampling.LANCZOS)
    tmp=dest.with_suffix('.tmp');im.save(tmp,format='PNG');tmp.replace(dest)
   os.utime(dest,(src.stat().st_mtime,src.stat().st_mtime));count+=1
 return count
def build(manifest,media,output):
 data=json.loads(Path(manifest).read_text());media=Path(media);output=Path(output)
 aliases=defaultdict(list)
 for a in data['duplicate_aliases']: aliases[a['canonical']].append(Path(a['source']).stem)
 old=Path('/var/mnt/slow/superterran-ally/SD Card/Emulation/roms')
 metadata={};mapping=[];coverage=[]
 for system,(es,cat) in MAP.items():
  legacy=old/('genesis' if system=='megadrive' else system)/'gamelist.xml'
  games={}
  if legacy.exists():
   for g in ET.parse(legacy).findall('game'):
    games[Path(g.findtext('path','')).stem.casefold()]={c.tag:c.text or '' for c in g if c.tag not in ['image','video','thumbnail','path','playcount','lastplayed']}
  metadata[es]={}
  for row in data['files']:
   if row['system']!=system: continue
   basename=Path(row['destination']).stem
   wide=row['variant']=='widescreen'; esname='sneswidescreen' if wide else es
   names=list(dict.fromkeys([basename,Path(row['source']).stem]+aliases[row['destination']]))
   if basename in ['SMW-WS','SMW-XW']: names+=['Super Mario World','Super Mario World (USA)']
   if basename=='SuperMetroid-WS': names+=['Super Metroid','Super Metroid (JU)']
   if basename in ['EarthBound-MBR','EarthBound - MaternalBound Redux']: names+=['EarthBound','EarthBound (USA)']
   found=[]
   for kind in ['covers','screenshots','marquees','miximages','titlescreens','3dboxes','backcovers','physicalmedia']:
    candidate=next((p for name in names for ext in ['.png','.jpg','.jpeg'] if (p:=media/es/kind/(name+ext)).is_file()),None)
    if candidate:
     target=output/'es-de/media'/esname/kind/(basename+candidate.suffix)
     target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(candidate,target);found.append(kind)
   if not found:
    candidate=next((p for name in names for ext in ['.png','.jpg'] if (p:=Path(row['source']).parent/'images'/(name+'-image'+ext)).is_file()),None)
    if candidate:
     target=output/'es-de/media'/esname/'miximages'/(basename+candidate.suffix)
     target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(candidate,target);found.append('miximages')
   gm=next((games[n.casefold()] for n in names if n.casefold() in games),{'name':basename})
   metadata.setdefault(esname,{})[basename]=gm
   if not wide: mapping.append({'es_system':esname,'catalogue':cat,'basename':basename})
   coverage.append({'system':system,'variant':row['variant'],'basename':basename,'media_types':found})
 (output/'es-de/metadata').mkdir(parents=True,exist_ok=True)
 for es,gm in metadata.items(): (output/'es-de/metadata'/(es+'.json')).write_text(json.dumps(gm,indent=2))
 (output/'mapping.json').write_text(json.dumps(mapping,indent=2))
 derivative_count=refresh(output)
 totals={'ROMs':len(coverage),'with_media':sum(bool(r['media_types']) for r in coverage),'with_cover':sum('covers' in r['media_types'] for r in coverage),'with_screenshot':sum('screenshots' in r['media_types'] for r in coverage),'muos_images_generated':derivative_count}
 (output/'coverage.json').write_text(json.dumps({'totals':totals,'games':coverage},indent=2))
 print(json.dumps(totals),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--output',required=True);p.add_argument('--manifest');p.add_argument('--source-media');a=p.parse_args()
 if a.refresh: print('Updated handheld images:',refresh(a.output))
 else: build(a.manifest,a.source_media,a.output)
